WPY26="C:\Program Files\Python26\python.exe"
P2E_EXTRAS=SDL.dll msvcr80.dll libtcod-mingw.dll arial10x10.png

ALL_EXTRAS=README

clean:
	rm -f *.pyc
	rm -f savegame-*-harmless7drl.gz
	rm -rf harmless7drl-win32
	rm -rf build

harmless7drl-win32:
	rm -rf dist
	rm -rf harmless7drl-win32
	$(WPY26) py2exe_setup.py py2exe
	cp $(P2E_EXTRAS) dist
	cp $(ALL_EXTRAS) dist
	mv dist\core.exe dist\harmless7drl.exe
	mv dist harmless7drl-win32
