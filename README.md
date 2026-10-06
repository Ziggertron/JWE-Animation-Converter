# JWE Animation Converter

A Windows tool for extracting Jurassic World Evolution animations from OVL archives and exporting them as individual GLB files.

## Features

- Lists the models and animation containers inside an OVL archive.
- Exports one GLB per animation clip with its recorded frame rate.
- Supports skeleton-only exports or exports with a skinned mesh and rig.
- Includes the Windows executable and full source code.
- Reads game files without modifying them.

## Requirements

- Windows 64-bit.
- Blender 5.0 installed.
- Jurassic World Evolution game files, including any companion OVS files.

The Windows version does not require a separate Python installation. The source version requires Python 3.10 or newer with Tkinter.

## Getting started

1. Download and extract the Windows package. Keep the entire folder together.
2. Run `JWE-Animation-Converter.exe`.
3. Select your installed Blender 5.0 executable if it is not detected automatically.
4. Browse to a dinosaur or character OVL archive.
5. Choose the matching game and click **Read archive**.
6. Select a skeleton or model:
   - **Skeleton MS2:** exports animated bones without a visible mesh.
   - **Mesh MS2:** includes the skinned mesh and rig.
7. Select the animation containers you want to export.
8. Choose an output folder outside the game directory and click **Export animations to GLB**.

Keep companion OVS files beside their original OVL archive. Each animation container may contain several clips, and large sets can take several minutes to process.

## Output

Each conversion creates a separate output folder containing:

- One `.glb` file per exported animation clip.
- Extracted model and animation assets.
- `conversion-report.json` with clip names, frame rates, and export results.
- Diagnostic files and `conversion.log`.

Skeleton-only GLBs may appear empty in viewers that display only meshes. Import them into Blender to inspect the animated bones.

## Compatibility

Tested with **Jurassic World Evolution 1 and Blender 5.0** using the Triceratops archive. The test exported **43 animated skeleton GLBs with zero failed clips**. Additional checks confirmed valid animation data and changing bone transforms.

JWE 2 and JWE 3 presets are available but remain unverified. Compatibility depends on the bundled Cobra Tools parser, and some JWE 3 animation formats are experimental.

## Limitations

- Mesh export is implemented but has not been verified in the included tests.
- Textures and game-specific material shaders are not exported.
- There is no separate static-pose GLB export option.
- Exported clips do not reproduce the game's full animation blending system.
- Models containing multiple armatures require a dedicated skeleton MS2.
- Not every archive or animation format is guaranteed to work.

## Running from source

Keep `app.py`, `worker.py`, `cobra/`, and `deps/` together.

Run:

```powershell
python app.py
```

If using the source download package, you can also launch `run-source.bat`.

To build the Windows executable, run `build-windows.bat`, or use:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name JWE-Animation-Converter app.py
```

Place the resulting executable beside `worker.py`, `cobra/`, and `deps/`.

## Credits and license

This converter uses [Cobra Tools](https://github.com/OpenNaja/cobra-tools) to read OVL archives and import models and animations.

The application is distributed under **GPL-3.0**. See `LICENSE` and the bundled third-party license files for details.

Blender and game assets are not included.
