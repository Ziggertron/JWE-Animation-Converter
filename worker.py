"""Blender subprocess: read-only game input, extracted assets and animated GLB output."""
import sys, os, json, pathlib, logging, importlib.util, re, struct, traceback
ROOT = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT/'deps'), str(ROOT/'cobra')]
import bpy
logging.basicConfig(level=logging.INFO)
logging.success = logging.info
from generated.formats.ovl import OvlFile
from modules.formats.shared import DummyReporter

class Reporter(DummyReporter):
    def show_info(self, msg): print(msg, flush=True)
    def show_warning(self, msg): print('WARNING: '+str(msg), flush=True)
    def show_error(self, msg, files=()): raise RuntimeError(str(msg))
    def report_error_files(self, operation):
        import contextlib
        @contextlib.contextmanager
        def check():
            errors=[]
            yield errors
            if errors: raise RuntimeError(f'{operation} failed for: '+', '.join(errors))
        return check()

def load_archive(job):
    ovl=OvlFile();ovl.reporter=Reporter()
    ovl.load(job['ovl'],commands={'game':job['game']})
    return ovl

def validate_glb(path):
    with open(path,'rb') as f:
        magic,version,size=struct.unpack('<4sII',f.read(12))
        if magic!=b'glTF' or version!=2 or size!=path.stat().st_size: raise RuntimeError('Invalid GLB header')
        length,kind=struct.unpack('<II',f.read(8))
        if kind!=0x4e4f534a: raise RuntimeError('Missing GLB JSON')
        data=json.loads(f.read(length))
    anims=data.get('animations',[])
    if not anims or not any(a.get('channels') for a in anims):
        raise RuntimeError('Export has no animation channels: '+path.name)
    return sum(len(a['channels']) for a in anims)

def main(job):
    output=pathlib.Path(job['output']);output.mkdir(parents=True,exist_ok=True)
    if job['mode']=='inspect':
        ovl=load_archive(job)
        names=list(ovl.loaders)
        result={'models':sorted(n for n in names if n.lower().endswith('.ms2')),
                'animations':sorted(n for n in names if n.lower().endswith(('.manis','.banis')))}
        if not result['models']: raise RuntimeError('No MS2 skeleton/model in this archive. Choose a dinosaur or character OVL.')
        if not result['animations']: raise RuntimeError('No MANIS/BANIS animations in this archive. Choose a dinosaur or character OVL.')
        return result
    ovl=load_archive(job)
    wanted=[job['model']]+job['animations']
    assets=output/'extracted';assets.mkdir()
    ovl.extract(str(assets),only_names=wanted)
    # Register in the factory-startup process only; never save user preferences.
    spec=importlib.util.spec_from_file_location('cobra_converter',ROOT/'cobra/__init__.py',submodule_search_locations=[str(ROOT/'cobra')])
    addon=importlib.util.module_from_spec(spec);sys.modules[spec.name]=addon
    spec.loader.exec_module(addon);addon.register()
    from plugin import import_ms2,import_manis,import_banis
    from plugin.modules_import.anim import Animation
    def asset(name):
        hits=list(assets.rglob(name))
        if len(hits)!=1: raise RuntimeError('Could not uniquely locate extracted '+name)
        return str(hits[0])
    reporter=Reporter()
    import_ms2.load(reporter,filepath=asset(job['model']),quadrify=False,merge_vertices=False)
    scene=bpy.context.scene
    armatures=[o for o in scene.objects if o.type=='ARMATURE']
    if len(armatures)!=1:
        raise RuntimeError(f'Model contains {len(armatures)} armatures. Select its dedicated skeleton MS2 for reliable animation matching.')
    arm=armatures[0]
    bpy.context.view_layer.objects.active=arm
    arm.select_set(True)
    exported=[];failures=[]
    for container in job['animations']:
        previous=set(bpy.data.actions)
        print('IMPORTING '+container,flush=True)
        importer=import_manis if container.lower().endswith('.manis') else import_banis
        args={'disable_ik':True} if importer==import_manis else {}
        importer.load(reporter,filepath=asset(container),**args)
        actions=[a for a in bpy.data.actions if a not in previous]
        for action in actions:
            curves=Animation().get_data(action).fcurves
            paths=[c.data_path for c in curves]
            if not any(p.startswith('pose.bones[') for p in paths):
                failures.append({'clip':action.name,'error':'No skeletal animation channels'});continue
            try:
                # Isolate each clip to preserve its individual frame rate and name.
                for ob in scene.objects:
                    ob.select_set(ob.type in ('ARMATURE','MESH'))
                    if ob.animation_data:
                        ob.animation_data.action=None
                        for track in ob.animation_data.nla_tracks: track.mute=True
                arm.animation_data.action=action
                if action.slots: arm.animation_data.action_slot=action.slots[0]
                fps=int(action.get('fps',30))
                scene.render.fps=max(1,fps);scene.render.fps_base=1
                scene.frame_start=int(action.frame_range[0]);scene.frame_end=int(action.frame_range[1])
                scene.frame_set(scene.frame_start)
                safe=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',action.name).rstrip('. ')[:150] or 'animation'
                path=output/(safe+'.glb');counter=2
                while path.exists(): path=output/(safe+f'_{counter}.glb');counter+=1
                result=bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
                    export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_force_sampling=True,
                    export_frame_range=True,export_skins=True,export_materials='NONE',export_cameras=False,
                    export_lights=False,export_extras=True)
                if 'FINISHED' not in result: raise RuntimeError('Blender export cancelled')
                channels=validate_glb(path)
                exported.append({'file':path.name,'clip':action.name,'fps':fps,'channels':channels,
                                 'frames':[scene.frame_start,scene.frame_end]})
                print('EXPORTED '+path.name,flush=True)
            except Exception as err:
                failures.append({'clip':action.name,'error':str(err)})
                traceback.print_exc()
        for ob in scene.objects:
            if ob.animation_data: ob.animation_data_clear()
        for action in actions: bpy.data.actions.remove(action)
    report={'exported':exported,'failed':failures,'ovl':job['ovl'],'model':job['model']}
    (output/'conversion-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not exported: raise RuntimeError('No animated GLB files exported. See the conversion log.')
    return report

if __name__=='__main__':
    job_path=pathlib.Path(sys.argv[sys.argv.index('--')+1])
    job=json.loads(job_path.read_text(encoding='utf-8'))
    try: result={'ok':True,'result':main(job)}
    except Exception as err:
        traceback.print_exc();result={'ok':False,'error':str(err)}
    pathlib.Path(job['result']).write_text(json.dumps(result,indent=2),encoding='utf-8')
    if not result['ok']: sys.exit(1)
