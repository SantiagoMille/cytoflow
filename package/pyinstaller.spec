import sys, os, re, weakref, glob, logging
from PyInstaller.compat import is_win, is_darwin, is_linux

from PyInstaller.building.datastruct import TOC, unique_name

def toc_setitem(self, key, value):
    if isinstance(key, slice):
        if key == slice(None, None, None):
            # special case: set the entire list
            self.filenames = set()
            self.clear()
            self.extend(value)
            return
        else:
            raise KeyError("TOC.__setitem__ doesn't handle slices")

    else:
        old_value = self[key]
        old_name = unique_name(old_value)
        self.filenames.remove(old_name)

        new_name = unique_name(value)
        if new_name not in self.filenames:
            self.filenames.add(new_name)
            super(TOC, self).__setitem__(key, value)
        
TOC.__setitem__ = toc_setitem

def toc_iadd(self, other):
    for entry in other:
        self.append(entry)
    return self
    
TOC.__iadd_= toc_iadd

a = Analysis(['../cytoflowgui/run.py'],
             pathex=['cytoflowgui/'],
             binaries=[('d3dcompiler_47.dll', '.')] if is_win else None,
             datas=[('../cytoflowgui/preferences.ini', 'cytoflowgui'),
                    ('../cytoflowgui/images', '.'),
                    ('../cytoflowgui/op_plugins/images', 'cytoflowgui/op_plugins/images'),
                    ('../cytoflowgui/view_plugins/images', 'cytoflowgui/view_plugins/images'),
                    ('../cytoflowgui/editors/images', 'cytoflowgui/editors/images'),
                    ('../cytoflowgui/help', 'cytoflowgui/help'),
                    ('../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs', '.'),
                    ('icon.png', '.'),
                    ('cytoflow.desktop', '.'),
                    ('set_launcher_icon', '.')],
             hookspath=['package/hooks'],
             runtime_hooks=['package/hooks/rthook_qtapi.py',
                            'package/hooks/rthook_qt5webengine.py',
                            'package/hooks/rthook_qtconf.py'],
             excludes=[
             	# Unused modules
             	'tornado', 'babel', 'IPython', 
             	'ipykernel', 'jedi', 'notebook', 'pytest', 'readline', 
             	'sphinx', 'tkinter', 'zmq',
             	
             	# Unused Qt5 libraries
                 'PyQt5.QtBluetooth', 'PyQt5.QtDesigner',
                 'PyQt5.QtHelp', 'PyQt5.QtLocation',
                 'PyQt5.QtMultimediaWidgets', 'PyQt5.QtNfc', 
                 'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets',
                 'PyQt5.QtSensors', 'PyQt5.QtSerialPort', 'PyQt5.QtSql',
                 'PyQt5.QtTest', 'PyQt5.QtWebSockets', 'PyQt5.QtXml',
                 'PyQt5.QtXmlPatterns',
                 ],

             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None)

# remove a few libraries that cause crashes if we don't use the system
# versions

remove_strs = ["glib", "gobject", "gthread", "libX", "libICE", "libdrm", "terminfo"]

# on linux, Anaconda version of fontconfig looks for the config bundled with
# Anaconda instead of the system config.  this breaks the fonts when you
# run on a system that you didn't build on

remove_strs.append('libfontconfig')
remove_strs.append('libuuid')

lol = [ [x for x in a.binaries if x[0].find(y) >= 0] for y in remove_strs]
remove_binaries = [item for sublist in lol for item in sublist]
logging.info("Removing binaries: {}".format(remove_binaries))

a.binaries = a.binaries - remove_binaries

# pull out all that silly terminfo stuff
remove_strs = ['terminfo']
lol = [ [x for x in a.datas if x[1].find(y) >= 0] for y in remove_strs]
remove_datas = [item for sublist in lol for item in sublist]
logging.info("Removing datas: {}".format(remove_datas))

a.datas = a.datas - remove_datas

# replace the module cytoflow/_version.py with a fixed version from versioneer
logging.info("Freezing dynamic version")
a.pure -= [('cytoflow._version', None, None)]
sys.path.insert(0, os.getcwd())
from versioneer import get_versions, write_to_version_file
version_file = os.path.join(os.getcwd(), '_version.py')
open(version_file, 'a').close()
versions = get_versions()
write_to_version_file(version_file, versions)
a.pure += [('cytoflow._version', version_file, 'PYMODULE')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# get rid of the leftover version file once it's compiled
os.unlink(version_file)

exe = EXE(pyz,
          a.scripts,
          [],
          #[('u', None, 'OPTION'), ('v', None, 'OPTION')],
          exclude_binaries=True,
          name='cytoflow',
          debug=False,
          #debug=True,
          strip=False,
          upx=False,
          console=False,
          #console=True,
          bootloader_ignore_signals=False,
          icon='icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='cytoflow',
               icon='icon.ico')

if sys.platform == 'darwin':
   app = BUNDLE(coll,
                name = "Cytoflow.app",
                icon = "icon.icns",
                bundle_identifier=None)


