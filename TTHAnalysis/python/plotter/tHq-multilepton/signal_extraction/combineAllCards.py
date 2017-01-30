#!/usr/bin/env python
import sys, os, re, shutil
from subprocess import Popen, PIPE

"""
Call combineCards.py on all pairs of *.card.txt files in the
two directories and store the output in combined/
Copy also the input.root files to the output directory.
"""

dir1 = sys.argv[1]
dir2 = sys.argv[2]

assert( os.path.isdir(dir1) and os.path.isdir(dir2) )

dir1cards = sorted([c for c in os.listdir(dir1) if c.endswith('card.txt')])
dir2cards = sorted([c for c in os.listdir(dir2) if c.endswith('card.txt')])
dir1files = sorted([c for c in os.listdir(dir1) if c.endswith('input.root')])
dir2files = sorted([c for c in os.listdir(dir2) if c.endswith('input.root')])

assert( len(dir1cards) == len(dir2cards) )
assert( len(dir1files) == len(dir2files) )
assert( len(dir1cards) == len(dir1files) )

print "Input directories OK, found %d cards to combine" % len(dir1cards)

def combineTwo(card1, card2, oname):
    assert( '2lss' in card1 and '3l' in card2 )
    assert( os.path.exists(card1) and  os.path.exists(card2) )

    p = Popen(['combineCards.py', "ss2l=%s"%card1, "l3=%s"%card2], stdout=PIPE)
    ccard = p.communicate()[0]

    odir = os.path.dirname(oname)
    if not os.path.isdir(odir):
        os.system('mkdir -p %s' % os.path.join(odir, dir1))
        os.system('mkdir -p %s' % os.path.join(odir, dir2))

    with open(oname, 'w') as cfile:
        cfile.write(ccard)

    # Copy also the root files:
    shutil.copy(card1.replace('card.txt', 'input.root'), os.path.join(odir, dir1))
    shutil.copy(card2.replace('card.txt', 'input.root'), os.path.join(odir, dir2))

for card1, card2 in zip(dir1cards, dir2cards):
    print "... combining %-30s %-30s" % (card1, card2),
    tag = re.match(r'.*\_([\dpm]+\_[\dpm]+)\.card\.txt', card1).groups()[0]
    oname = os.path.join('combined', 'tHq_%s.card.txt' % tag)
    print "to", oname

    combineTwo(os.path.join(dir1, card1),
               os.path.join(dir2, card2),
               oname=oname)
