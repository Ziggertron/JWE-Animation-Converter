JWE Animation Converter
=======================

Run JWE-Animation-Converter.exe. Keep this entire folder together.
No separate Python installation is required. Blender 5.0 must be installed.
The app detects Blender 5 under C:\Program Files\Blender Foundation; use Browse
if Blender is elsewhere. The packaged binary dependencies target Blender's
Python 3.11 on Windows x64. Other Blender versions are not verified.

1. Browse to a dinosaur or character OVL in your installed game's ovldata.
   Keep its companion OVS files in their original location.
2. Choose the matching game and click Read archive.
3. Choose the dedicated skeleton MS2 for animation-only GLBs. Choose a model
   MS2 instead if you want geometry. Archives with several armatures require
   selecting their dedicated skeleton to avoid guessing the animation target.
4. Select animation containers (all are selected initially). Each container
   may contain many clips. Ctrl-click to select specific containers.
5. Choose an output folder outside the game directory and click Export.

Each clip produces its own animated GLB with its recorded frame rate.
Skeleton-only GLBs contain animated bone nodes; viewers that only display
meshes may appear empty. Import into Blender to inspect the skeleton, or use
a compatible mesh MS2. These GLBs are intended for animation extraction.
They do not reproduce every aspect of the game's animation blending system.
No textures or game-specific material shaders are exported.

Each run creates a unique output subfolder containing GLBs, extracted assets,
conversion-report.json, job.json, worker-result.json, and conversion.log.
Failures are reported rather than silently producing a static model.
Cancel stops Blender; completed exports and extracted files remain available.
Game archives are only read. This application does not modify the game or
save Blender preferences. Large compressed animation sets can take minutes.

Compatibility
-------------
JWE 1 / Blender 5.0: tested against the installed Triceratops archive.
JWE 2 and JWE 3: game presets are exposed but NOT tested here. Support depends
on the bundled Cobra Tools parser. Some JWE 3 BANIS features remain experimental
upstream. No guarantee that every animation or archive is supported.

Source / license
----------------
app.py and worker.py are included. This application is distributed under
GPL-3.0; see LICENSE. Cobra Tools source is included in cobra/ with its own
LICENSE and attribution. Upstream: https://github.com/OpenNaja/cobra-tools
Base revision: 8d43de41d (2026-09-28).
Local compatibility fix: plugin/modules_import/anim.py defaults missing
action_group to an empty string in Blender 5's fcurve creation.
Bundled third-party dependencies and their licenses are included under deps/.
The upstream Cobra Tools source includes its Oodle support component.
Blender and game assets are not bundled.

To rebuild the GUI executable with Python 3.10 and PyInstaller:
  python -m pip install pyinstaller
  python -m PyInstaller --onefile --windowed --name JWE-Animation-Converter app.py
Place the resulting executable beside worker.py, cobra/, and deps/.
