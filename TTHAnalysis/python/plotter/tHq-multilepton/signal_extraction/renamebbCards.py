#! /usr/bin/env python
import os
import re
import sys
import shutil

PREFIX = "tHq_bb"

# See https://twiki.cern.ch/twiki/pub/CMS/SingleTopHiggsGeneration13TeV/reweight_encondig.txt
POINTS = [
    "1_m1",
    "1_m3",
    "1_m2",
    "1_m1p5",
    "1_m1p25",
    "1_m0p75",
    "1_m0p5",
    "1_m0p25",
    "1_m0",
    "1_0p25",
    "1_0p5",
    "1_0p75",
    "1_1",
    "1_1p25",
    "1_1p5",
    "1_2",
    "1_3",
    "0p5_m3",
    "0p5_m2",
    "0p5_m1p5",
    "0p5_m1p25",
    "0p5_m1",
    "0p5_m0p75",
    "0p5_m0p5",
    "0p5_m0p25",
    "0p5_m0",
    "0p5_0p25",
    "0p5_0p5",
    "0p5_0p75",
    "0p5_1",
    "0p5_1p25",
    "0p5_1p5",
    "0p5_2",
    "0p5_3",
    "1p5_m3",
    "1p5_m2",
    "1p5_m1p5",
    "1p5_m1p25",
    "1p5_m1",
    "1p5_m0p75",
    "1p5_m0p5",
    "1p5_m0p25",
    "1p5_m0",
    "1p5_0p25",
    "1p5_0p5",
    "1p5_0p75",
    "1p5_1",
    "1p5_1p25",
    "1p5_1p5",
    "1p5_2",
    "1p5_3",
]

POSTFIX = {n:k for n,k in enumerate(POINTS)}
OUTPUTROOT = "renamed"

for filename in os.listdir(sys.argv[1]):
    m = re.match("tH_(3m|4m|dilep)_(\d*)\.(txt|root)", filename)
    if not m: continue

    chan, point, ext = m.groups()
    point = int(point)

    assert point in range(51), "point %s outside range(51)" % point

    outdir = os.path.join(OUTPUTROOT, "bb_%s" % chan)
    try:
        os.makedirs(outdir)
    except OSError:
        pass

    if ext == 'txt':
        newname = "%s_%s_%s.card.%s" % (PREFIX, chan, POSTFIX[point], ext)
    else:
        newname = filename

    newloc = os.path.join(outdir, newname)
    oldloc = os.path.join(sys.argv[1], filename)
    print "%s --> %s" % (oldloc, newloc)

    shutil.copy(oldloc, newloc)
