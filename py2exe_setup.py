from distutils.core import setup
import py2exe

setup(windows=['core.py'],
      bundle_files=1,
      zipfile = None,
)
