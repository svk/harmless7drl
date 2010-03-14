from distutils.core import setup
import py2exe

p2e_options = dict (
        ascii = True,
        excludes = [ '_ssl', 'pyreadline', 'difflib', 'doctest', 'locale', 'optparse', 'pickle', 'calendar' ],
        dll_excludes = [ 'msvcr71.dll', 'python25.dll' ],
        compressed = True,
)

setup(windows=['harmless7drl.py'],
      bundle_files=1,
      zipfile = None,
      name = 'Harmless7DRL',
      version = '1.0',
      author = 'kaw',
      options = { 'py2exe': p2e_options }
)
