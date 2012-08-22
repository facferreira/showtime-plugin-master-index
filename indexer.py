#!/usr/bin/env python

#
#  Showtime mediacenter
#  Copyright (C) 2011 Andreas Oman
#  Copyright (C) 2012 Fabio Ferreira
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
import hashlib
import codecs
import datetime
import time
import urllib2
import json

if len(sys.argv) < 2:
    print "Invalid number of of args"
    print "Usage: %s <output directory> <plugin> [<plugin>...]" % sys.argv[0]

    sys.exit(0)

outpath = sys.argv[1]
outdata = []

plugins_used = []

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

    txt = f.read()
    f.close()

    try:
        pconf = json.loads(txt.decode('utf8'))
    except UnicodeDecodeError:
        pconf = json.loads(txt.decode('latin-1'))
    except ValueError, err:
        print '%s broken JSON: %s' % (confpath, err)
        continue
    except:
        print '%s broken JSON' % (confpath, )
        raise
        

    if 'id' not in pconf:
        print '%s lacks "id" field' % confpath
        continue

    pid = pconf['id']
    ver = pconf['version']

    plugins_used.append(pid);

    if have_pid(pid):
        print "Path '%s' contains ID '%s' that is already indexed" % (ppath, pid)
        continue

    print " * Including %s (%s)" % (pid, ver)

    zippath = os.path.join(outpath, '%s.zip' % pid)

    zf = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED)
    zf.writestr('plugin.json', json.dumps(pconf))

    for root, dirs, files in os.walk(ppath):
        for f in files:
            if f[0] == '.' or f[-1] == '~' or f == 'plugin.json':
                continue
            ff = os.path.join(root, f)
            if os.path.isfile(ff):
                intname = os.path.join(root[len(ppath)+1:], f)
                print "    '%s'" % intname
                if f[-4:] in ['.png', '.jpg']:
                    comp = zipfile.ZIP_STORED
                else:
                    comp = zipfile.ZIP_DEFLATED

                zf.write(ff, intname, comp)

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

    z = open(zippath)
    h = hashlib.new('sha1')
    h.update(z.read())
    pconf['hash'] = h.hexdigest()
    z.close()

    outdata.append(pconf)
    print


# Parse original repository maintaned by Andreas Oman, including only the plugins not included so far
response = urllib2.urlopen('http://showtime.lonelycoder.com/plugins/plugins-v1.json')
json_data = json.loads(response.read())
for plugin in json_data["plugins"]:
    if plugin["id"] not in plugins_used:
        plugin["icon"] = 'http://showtime.lonelycoder.com/plugins/' + plugin["id"] + ".png"
        plugin["downloadURL"] = 'http://showtime.lonelycoder.com/plugins/' + plugin["id"] + ".zip"
        outdata.append(plugin)


f = open(os.path.join(outpath, 'plugins-v1.json'), 'w')

plugin_index = {
    'version': 1,
    'plugins': outdata}

f.write(json.dumps(plugin_index, indent=1))
f.close()


from operator import itemgetter
outdata = sorted(outdata, key=itemgetter('title'))

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    return "".join(html_escape_table.get(c,c) for c in text)

f = codecs.open(os.path.join(outpath, 'plugins.html'), 'w', 'utf-8')

print >>f, '<table class="plugin-table">'
print >>f, '<tr>'
print >>f, '  <th>Application</th>'
print >>f, '  <th>Version</th>'
print >>f, '  <th>Short description</th>'
print >>f, '  <th>Author</th>'
print >>f, '</tr>'

for i,a in enumerate(outdata):
    print >>f, '<tr class="%s">' % ('plugin-row-even', 'plugin-row-odd')[i&1]
    if 'homepage' in a:
        print >>f, '<td class="plugin-title"><a href="%s">%s</a></td>' % \
            (a['homepage'], html_escape(a['title']))
    else:
        print >>f, '<td class="plugin-title">%s</td>' % html_escape(a['title'])
    print >>f, '<td>%s</td>' % html_escape(a['version'])

    s = ''
    if 'synopsis' in a:
        s += '<span class="plugin-synopsis">' + a['synopsis'] + '</span>'
    if 'description' in a:
        s += '<span class="plugin-desc">'+a['description'] + '</span>'

    print >>f, '<td>%s</td>' % s
    print >>f, '<td>%s</td>' % html_escape(a.get('author', '???'))
    print >>f, '</tr>'

print >>f, '</table>'


print >>f, '<p>List of plugins last updated on %s</p>' % time.ctime()

f.close()