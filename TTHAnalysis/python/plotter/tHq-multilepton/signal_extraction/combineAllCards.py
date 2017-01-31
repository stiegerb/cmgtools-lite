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
dir3 = sys.argv[3]

assert( os.path.isdir(dir1) and os.path.isdir(dir2) and os.path.isdir(dir3) )

dir1cards = sorted([c for c in os.listdir(dir1) if c.endswith('card.txt')])
dir2cards = sorted([c for c in os.listdir(dir2) if c.endswith('card.txt')])
dir3cards = sorted([c for c in os.listdir(dir3) if c.endswith('card.txt')])
dir1files = sorted([c for c in os.listdir(dir1) if c.endswith('input.root')])
dir2files = sorted([c for c in os.listdir(dir2) if c.endswith('input.root')])
dir3files = sorted([c for c in os.listdir(dir3) if c.endswith('input.root')])

assert( len(dir1cards) == len(dir2cards) and len(dir1cards) == len(dir3cards) )
assert( len(dir1files) == len(dir2files) and len(dir1files) == len(dir3files) )
assert( len(dir1cards) == len(dir1files) )

print "Input directories OK, found %d cards to combine" % len(dir1cards)

def combineTwo(card1, card2, card3, oname):
    assert( '2lss-mm' in card1 and '2lss-em' in card2 and '3l' in card3 )
    assert( os.path.exists(card1) and  os.path.exists(card2) and os.path.exists(card3) )

    p = Popen(['combineCards.py', "mm=%s"%card1, "em=%s"%card2, "lll=%s"%card3 ], stdout=PIPE)
    ccard = p.communicate()[0]

    odir = os.path.dirname(oname)
    if not os.path.isdir(odir):
        os.system('mkdir -p %s' % os.path.join(odir, dir1))
        os.system('mkdir -p %s' % os.path.join(odir, dir2))
        os.system('mkdir -p %s' % os.path.join(odir, dir3))


    with open(oname, 'w') as cfile:
        cfile.write(ccard)

    # Copy also the root files:
    shutil.copy(card1.replace('card.txt', 'input.root'), os.path.join(odir, dir1))
    shutil.copy(card2.replace('card.txt', 'input.root'), os.path.join(odir, dir2))
    shutil.copy(card3.replace('card.txt', 'input.root'), os.path.join(odir, dir3))

for card1, card2, card3 in zip(dir1cards, dir2cards, dir3cards):
    print "... combining %-30s %-30s %-30s" % (card1, card2, card3),
    tag = re.match(r'.*\_([\dpm]+\_[\dpm]+)\.card\.txt', card1).groups()[0]
    oname = os.path.join('combined', 'tHq_%s.card.txt' % tag)
    print "to", oname

    combineTwo(os.path.join(dir1, card1),
               os.path.join(dir2, card2),
               os.path.join(dir3, card3),
               oname=oname)
