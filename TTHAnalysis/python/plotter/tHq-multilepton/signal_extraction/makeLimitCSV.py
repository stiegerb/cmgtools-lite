#!/usr/bin/env python
import sys, os, re, shutil
from subprocess import Popen, PIPE

"""
Look for all files starting matching limit*.dat, extract the
limit, one sigma, and two sigma bands, and the point from the
file name, and convert this into a csv to be used for plotting.

Output format should be:
cf,twosigdown,onesigdown,exp,onesigup,twosigup
with the filename being limits_cv_0p5/1p0/1p5.dat
"""
indir = sys.argv[1]
assert(os.path.isdir(indir))

limfiles = [f for f in os.listdir(sys.argv[1])
                       if f.startswith('limit') and f.endswith('.dat')]

limdata = {} # (cv,ct) -> (2sd, 1sd, lim, 1su, 2su)
for lfile in sorted(limfiles):
    # Figure out from the filename where we are
    tag = re.match(r'.*\_([\dpm]+\_[\dpm]+).*\.dat', lfile)
    if tag == None:
        print "Couldn't figure out this one: %s" %lfile
        continue

    tag = tag.groups()[0]
    # Turn the tag into floats:
    tag = tag.replace('p', '.')
    tag = tag.replace('m', '-')
    cv,ct = tuple(map(float, tag.split('_')))
    
    # Now read the file and extract the limit
    with open(os.path.join(indir, lfile), 'r') as limfile:
        liminfo = []
        for line in limfile.readlines():
            if not line.startswith('Expected'): continue
            liminfo.append(float(line.rsplit('<', 1)[1].strip()))

    limdata[(cv,ct)] = tuple(liminfo)

for cv_ in [0.5, 1.0, 1.5]:
    with open('limits_cv_%s.dat'%str(cv_).replace('.','p'), 'w') as csvfile:
        csvfile.write('cf,twosigdown,onesigdown,exp,onesigup,twosigup\n')
        for cv,ct in sorted(limdata.keys()):
            if not cv == cv_: continue
            csvfile.write(','.join(map(str, (cv,ct)+limdata[(cv,ct)])) + '\n')
