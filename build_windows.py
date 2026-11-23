"""Package on Windows with Python 3.11/3.12. No cross-compilation claim."""
import sys
from pathlib import Path


def build_options():
    root=Path(__file__).resolve().parent
    return ['--noconfirm','--clean','--onedir','--windowed','--name','SplintFit',
            '--collect-all','pyvista','--collect-all','pyvistaqt','--collect-all','vtkmodules',
            '--hidden-import','PyQt6.QtOpenGLWidgets','--hidden-import','PyQt6.QtOpenGL',
            '--exclude-module','PySide6','--exclude-module','PyQt5','--exclude-module','PySide2',
            '--add-data',str(root/'FUSION_FORM.md')+':.',
            '--add-data',str(root/'viewer_template.html')+':.',
            '--add-data',str(root/'fusion')+':fusion',str(root/'app.py')]


if __name__=='__main__':
    if sys.platform!='win32':raise SystemExit('Run BUILD_WINDOWS.bat on Windows; this build is not a cross-compiler.')
    import PyInstaller.__main__
    PyInstaller.__main__.run(build_options())
