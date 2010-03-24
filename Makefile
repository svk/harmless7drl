# This makefile builds the Windows executable.
# It's very specific to my own Windows environment;
#  if you need to do a Windows build tailor as needed.

# If you want to play the game and you're on Linux, 
# you do not need to build anything: simply run
#   python harmless7drl.py

WPY26="C:\Program Files\Python26\python.exe"
P2E_EXTRAS=SDL.dll libtcod-mingw.dll harmless-font-13x23.png LICENSE.Bitstream
# may need msvcr80.dll
SZIP="C:\Program Files\7-Zip\7z.exe"

ALL_EXTRAS=README LICENSE

clean:
	rm -f errars
	rm -f *.pyc
	rm -f savegame-*-harmless7drl.gz
	rm -rf harmless7drl-win32
	rm -rf build
	rm -f debug.7drl.txt
	rm -f harmless7drl-*.txt
	rm -rf harmless7drl

harmless7drl-win32:
	rm -rf dist
	rm -rf harmless7drl-win32
	$(WPY26) py2exe_setup.py py2exe
	cp $(P2E_EXTRAS) dist
	cp $(ALL_EXTRAS) dist
	cp windows.cfg dist/harmless7drl.cfg
	mv dist harmless7drl-win32
	upx harmless7drl-win32\python26.dll

harmless7drl:
	rm -rf dist
	rm -rf harmless7drl
	mkdir dist
	cp *.py dist
	cp -r cerealizer dist
	cp $(ALL_EXTRAS) dist
	cp standard.cfg dist/harmless7drl.cfg
	mv dist harmless7drl

harmless7drl.tar.gz: harmless7drl
	tar cvfz harmless7drl.tar.gz harmless7drl

harmless7drl-win32.zip: harmless7drl-win32
	$(SZIP) a -r harmless7drl-win32.zip harmless7drl-win32
