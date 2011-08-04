#!/usr/bin/env python

#
#  Showtime mediacenter
#  Copyright (C) 2011 Andreas Oman
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import zipfile
import json
import os
import shutil


if len(sys.argv) < 2:
    print "Invalid number of of args"
    print "Usage: %s <output directory> <plugin> [<plugin>...]" % sys.argv[0]

    sys.exit(0)

outpath = sys.argv[1]
outdata = []

print "Output to %s" % outpath

try:
    os.makedirs(outpath)
except:
    pass

def have_pid(pid):
    for p in outdata:
        if p['id'] == pid:
            return True
    return False

for ppath in sys.argv[2:]:
    confpath = os.path.join(ppath, 'plugin.json')
    try:
        f = open(confpath)
    except IOError:
        print "Path '%s' is not a valid plugin. Missing plugin.json, skipping" % ppath
        continue

    pconf = json.loads(f.read())
    f.close()

    if 'id' not in pconf:
        print '%s lacks "id" field' % confpath
        continue

    pid = pconf['id']

    if have_pid(pid):
        print "Path '%s' contains ID '%s' that is already indexed" % (ppath, pid)
        continue

    zf = zipfile.ZipFile(os.path.join(outpath, '%s.zip' % pid), 'w',
                         zipfile.ZIP_DEFLATED)
    zf.writestr('plugin.json', json.dumps(pconf))

    for f in os.listdir(ppath):
        if f[0] == '.' or f[-1] == '~' or f == 'plugin.json':
            continue
        ff = os.path.join(ppath, f)
        
        if os.path.isfile(ff):
            if f[-4:] in ['.png', '.jpg']:
                comp = zipfile.ZIP_STORED
            else:
                comp = zipfile.ZIP_DEFLATED

            zf.write(ff, f, comp)

    zf.close()

    # Rewrite pconf a bit to fit full repo index (plugins.json)

    if 'icon' in pconf:
        img = pconf['icon']
        suffix = img.split('.')[1]
        tgt = '%s.%s' % (pid, suffix)
        shutil.copyfile(os.path.join(ppath, pconf['icon']),
                        os.path.join(outpath, tgt))
        pconf['icon'] = tgt

    pconf['downloadURL'] = '%s.zip' % pid
    outdata.append(pconf)

f = open(os.path.join(outpath, 'plugins-v1.json'), 'w')

plugin_index = {
    'version': 1,
    'plugins': outdata}

f.write(json.dumps(plugin_index, indent=1))
f.close()
