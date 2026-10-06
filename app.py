import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pathlib, sys, os, json, threading, subprocess, queue, datetime, tempfile

ROOT=pathlib.Path(sys.executable).parent if getattr(sys,'frozen',False) else pathlib.Path(__file__).parent
GAME_ROOT=r'C:\Program Files (x86)\Steam\steamapps\common\Jurassic World Evolution\Win64\ovldata'

def find_blender():
    base=pathlib.Path(r'C:\Program Files\Blender Foundation')
    hits=sorted(base.glob('Blender 5*/blender.exe'),reverse=True)
    return str(hits[0]) if hits else ''

class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title('JWE Animation Converter — OVL to GLB');self.geometry('850x720');self.minsize(720,600)
        self.events=queue.Queue();self.busy=False;self.scan=None;self.process=None
        self.ovl=tk.StringVar();self.blender=tk.StringVar(value=find_blender())
        self.destination=tk.StringVar(value=str(pathlib.Path.home()/'Documents'/'JWE Animations'))
        self.game=tk.StringVar(value='Jurassic World Evolution');self.model=tk.StringVar();self.status=tk.StringVar(value='Choose an OVL, then click Read archive.')
        box=ttk.Frame(self,padding=18);box.pack(fill='both',expand=True);box.columnconfigure(1,weight=1)
        ttk.Label(box,text='OVL → animated GLB',font=('Segoe UI',18,'bold')).grid(row=0,column=0,columnspan=3,sticky='w',pady=(0,8))
        ttk.Label(box,text='One GLB per animation clip. Keep companion OVS files beside the OVL.').grid(row=1,column=0,columnspan=3,sticky='w',pady=(0,14))
        self.path_row(box,2,'OVL archive',self.ovl,self.pick_ovl)
        self.path_row(box,3,'Blender 5.0',self.blender,lambda:self.pick_file(self.blender,'Blender executable',[('Executable','*.exe')]))
        self.path_row(box,4,'Output folder',self.destination,self.pick_output)
        ttk.Label(box,text='Game').grid(row=5,column=0,sticky='w',pady=5)
        ttk.Combobox(box,textvariable=self.game,values=['Jurassic World Evolution','Jurassic World Evolution 2','Jurassic World Evolution 3'],state='readonly').grid(row=5,column=1,sticky='ew')
        self.read=ttk.Button(box,text='Read archive',command=self.inspect);self.read.grid(row=5,column=2,padx=(8,0))
        ttk.Label(box,text='Skeleton / model').grid(row=6,column=0,sticky='w',pady=8)
        self.models=ttk.Combobox(box,textvariable=self.model,state='readonly');self.models.grid(row=6,column=1,columnspan=2,sticky='ew')
        ttk.Label(box,text='Choose a skeleton MS2 for animations only, or a mesh MS2 to include geometry.').grid(row=7,column=0,columnspan=3,sticky='w')
        ttk.Label(box,text='Animation containers (Ctrl / Shift to select)').grid(row=8,column=0,columnspan=3,sticky='w',pady=(12,4))
        self.animations=tk.Listbox(box,selectmode='extended',exportselection=False,height=8);self.animations.grid(row=9,column=0,columnspan=3,sticky='nsew');box.rowconfigure(9,weight=1)
        buttons=ttk.Frame(box);buttons.grid(row=10,column=0,columnspan=3,sticky='ew',pady=10)
        ttk.Button(buttons,text='Select all',command=lambda:self.animations.select_set(0,'end')).pack(side='left')
        self.convert=ttk.Button(buttons,text='Export animations to GLB',command=self.start_convert,state='disabled');self.convert.pack(side='left',padx=10)
        self.cancel=ttk.Button(buttons,text='Cancel',command=self.stop,state='disabled');self.cancel.pack(side='left')
        ttk.Button(buttons,text='Open output',command=self.open_output).pack(side='right')
        ttk.Label(box,textvariable=self.status,wraplength=790).grid(row=11,column=0,columnspan=3,sticky='w')
        self.progress=ttk.Progressbar(box,mode='indeterminate');self.progress.grid(row=12,column=0,columnspan=3,sticky='ew',pady=8)
        self.log=tk.Text(box,height=10,wrap='word',state='disabled');self.log.grid(row=13,column=0,columnspan=3,sticky='nsew');box.rowconfigure(13,weight=1)
        ttk.Label(box,text='Tested with JWE 1 and Blender 5.0. Other games are experimental. Textures are not exported.').grid(row=14,column=0,columnspan=3,sticky='w',pady=(8,0))
        self.after(100,self.poll);self.protocol('WM_DELETE_WINDOW',self.close)
    def path_row(self,box,row,label,var,command):
        ttk.Label(box,text=label).grid(row=row,column=0,sticky='w',pady=6)
        ttk.Entry(box,textvariable=var).grid(row=row,column=1,sticky='ew')
        ttk.Button(box,text='Browse…',command=command).grid(row=row,column=2,padx=(8,0))
    def pick_file(self,var,title,types):
        path=filedialog.askopenfilename(title=title,filetypes=types)
        if path: var.set(path)
    def pick_ovl(self):
        path=filedialog.askopenfilename(title='Choose dinosaur or character OVL',initialdir=GAME_ROOT,filetypes=[('OVL archives','*.ovl')])
        if path:self.ovl.set(path)
    def pick_output(self):
        path=filedialog.askdirectory(title='Choose output folder')
        if path:self.destination.set(path)
    def open_output(self):
        path=getattr(self,'last_output',self.destination.get())
        if pathlib.Path(path).is_dir():os.startfile(path)
    def inputs(self):
        if not pathlib.Path(self.blender.get()).is_file():raise ValueError('Select your Blender 5.0 blender.exe.')
        source=pathlib.Path(self.ovl.get())
        if not source.is_file() or source.suffix.lower()!='.ovl':raise ValueError('Select an existing OVL archive.')
        return {'ovl':str(source.resolve()),'game':self.game.get()}
    def inspect(self):
        if self.busy:return
        try:
            job=self.inputs();job.update(mode='inspect',output=tempfile.mkdtemp(prefix='jwe-scan-'))
            self.scan=None;self.models['values']=[];self.animations.delete(0,'end');self.launch(job)
        except Exception as err:messagebox.showerror('Cannot read archive',str(err))
    def start_convert(self):
        if self.busy:return
        try:
            job=self.inputs()
            if not self.scan or self.scan[:2]!=(job['ovl'],job['game']):raise ValueError('The archive or game changed. Click Read archive again.')
            selected=[self.animations.get(i) for i in self.animations.curselection()]
            if not selected or self.model.get() not in self.models['values']:raise ValueError('Choose a model and at least one animation container.')
            out=pathlib.Path(self.destination.get()).resolve()
            source=pathlib.Path(job['ovl']).parent
            if out==source or source in out.parents:raise ValueError('Choose an output folder outside the game archive folder.')
            run=out/(pathlib.Path(job['ovl']).stem+'_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
            run.mkdir(parents=True);self.last_output=str(run)
            job.update(mode='convert',model=self.model.get(),animations=selected,output=str(run));self.launch(job)
        except Exception as err:messagebox.showerror('Cannot convert',str(err))
    def launch(self,job):
        self.busy=True;self.read['state']='disabled';self.convert['state']='disabled';self.cancel['state']='normal';self.progress.start()
        self.status.set('Reading archive…' if job['mode']=='inspect' else 'Extracting and exporting animations…')
        blender=self.blender.get()
        threading.Thread(target=self.run,args=(job,blender),daemon=True).start()
    def run(self,job,blender):
        try:
            out=pathlib.Path(job['output']);job['result']=str(out/'worker-result.json')
            jobpath=out/'job.json';jobpath.write_text(json.dumps(job,indent=2),encoding='utf-8')
            with (out/'conversion.log').open('w',encoding='utf-8') as log:
                self.process=subprocess.Popen([blender,'--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'worker.py'),'--',str(jobpath)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
                for line in self.process.stdout:
                    log.write(line);log.flush();self.events.put(('log',line))
                code=self.process.wait();self.process=None
            resultpath=pathlib.Path(job['result'])
            if not resultpath.exists():raise RuntimeError(f'Blender stopped (exit {code}). See {out / "conversion.log"}.')
            result=json.loads(resultpath.read_text(encoding='utf-8'))
            if not result['ok']:raise RuntimeError(result['error']+'\nLog: '+str(out/'conversion.log'))
            self.events.put(('done',(job,result['result'])))
        except Exception as err:self.events.put(('error',str(err)))
    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='log':
                    self.log['state']='normal';self.log.insert('end',value)
                    if int(self.log.index('end').split('.')[0])>1200:self.log.delete('1.0','300.0')
                    self.log.see('end');self.log['state']='disabled'
                else:
                    self.busy=False;self.progress.stop();self.read['state']='normal';self.cancel['state']='disabled'
                    if kind=='error':self.status.set('Stopped. See details below.');messagebox.showerror('Conversion stopped',value)
                    else:
                        job,result=value
                        if job['mode']=='inspect':
                            self.models['values']=result['models'];self.model.set(next((m for m in result['models'] if 'skeleton' in m.lower()),result['models'][0]))
                            for name in result['animations']:self.animations.insert('end',name)
                            self.animations.select_set(0,'end');self.scan=(job['ovl'],job['game'],result)
                            self.status.set(f'{len(result["models"])} models, {len(result["animations"])} animation containers. Ready to export.')
                        else:
                            count=len(result['exported']);failed=len(result['failed']);self.status.set(f'Exported {count} animated GLBs; {failed} clips skipped. Output: {job["output"]}')
                            messagebox.showinfo('Export complete',f'Exported {count} animated GLBs.\nSkipped clips: {failed}\n\n{job["output"]}')
                    self.convert['state']='normal' if self.scan else 'disabled'
        except queue.Empty:pass
        self.after(100,self.poll)
    def stop(self):
        if self.process:self.process.terminate();self.status.set('Cancelling… Completed exports will remain in the output folder.')
    def close(self):
        if self.busy:
            if not messagebox.askyesno('Close converter','Stop the current conversion and close?'):return
            self.stop()
        self.destroy()

if __name__=='__main__':
    app=App()
    if '--smoke-test' in sys.argv:
        app.withdraw();app.update()
        target=pathlib.Path(sys.argv[sys.argv.index('--smoke-test')+1])
        target.write_text(json.dumps({'window_title':app.title(),'blender':app.blender.get(),'worker_present':(ROOT/'worker.py').exists(),'widgets_created':True}),encoding='utf-8')
        app.destroy()
    else:app.mainloop()
