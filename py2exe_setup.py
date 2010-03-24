from distutils.core import setup
import py2exe

p2e_options = dict (
        ascii = True,
        excludes = [ '_ssl', 'pyreadline', 'difflib', 'doctest', 'locale', 'optparse', 'pickle', 'calendar' ],
        dll_excludes = [ 'msvcr71.dll', 'python25.dll' ],
        compressed = True,
)

setup(windows=[{
        'script': 'harmless7drl.py',
        'icon_resources': [(1, 'harmless7drl.ico')],
      }],
      bundle_files=1,
      zipfile = None,
      name = 'Harmless7DRL',
      version = '1.0',
      author = 'kaw',
      options = { 'py2exe': p2e_options }
)
