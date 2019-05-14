#!/usr/bin/env python
import os
import re
import shutil
import shlex
import time

from subprocess import Popen
from subprocess import PIPE


def combineCards(cards, chans, oname):
    assert(len(cards) == len(chans))

    chanargs = ' '.join(['%s_13TeV=%s' % (chn, cn) for chn,cn in zip(chans, cards)])
    combinecmd = shlex.split('combineCards.py %s' % chanargs)

    try:
        p = Popen(combinecmd, stdout=PIPE)
        ccard = p.communicate()[0]
    except OSError:
        print ("combine command not known. Try this: "
               "cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -")
        return

    odir = os.path.dirname(oname)
    inputdirs = [os.path.dirname(c) for c in cards]
    for dirname in inputdirs:
        try:
            os.system('mkdir -p %s' % os.path.join(odir, dirname))
        except OSError:
            pass

    with open(oname, 'w') as cfile:
        cfile.write(ccard)

    # Copy the root files (and make a copy of the card while
    # we're at it, because why not):
    for card, cdir in zip(cards, inputdirs):
        shutil.copy(card, os.path.join(odir, cdir))
        file = get_filepath_from_card(card)
        shutil.copy(file, os.path.join(odir, cdir))


def get_filepath_from_card(card):
    with open(card, "r") as cardfile:
        line = (l for l in cardfile if l.startswith("shapes")).next()
        path = line.split()[3]
        filepath = os.path.join(os.path.dirname(card), path)
        if not os.path.exists(filepath):
            print "file %s from card %s not found?" % (filepath, card)
        return filepath


def main(args, options):
    inputdirs = args
    assert(all([os.path.isdir(d) for d in inputdirs])), "inputs are not directories"

    dn2cards = {}  # dirname -> cards
    for dname in inputdirs:
        dn2cards[dname] = sorted([os.path.join(dname, c) for c in
                                  os.listdir(dname) if c.endswith('card.txt')])

    npoints = len(dn2cards.values()[0])
    assert(all([len(c) == npoints for c in dn2cards.values()])), "too many card files?"

    print ("Input directories OK, found %d points to combine "
           "from %d directories" % (npoints, len(inputdirs)))

    chans = ["tHq_" + b.strip() for b in options.binnames.split(',')]
    assert(len(chans) == len(inputdirs)), "unequal number of inputdirs and channel names"

    # Make sure channel names and order of input directories is the same
    assert(all([b in d for b,d in zip(options.binnames.split(','), inputdirs)])),\
        "Inconsistent order between channel names and input directories"

    print "Using channel names:", chans

    for cards in [[dn2cards[d][n] for d in inputdirs] for n in range(npoints)]:
        print "combining %s" % ' '.join([os.path.basename(c) for c in cards]),

        # Check consistency of cards
        tagpat = re.compile(r'.*\_([\dpm]+\_[\dpm]+)\.card\.txt')
        tags = list(set([re.match(tagpat, c).groups()[0] for c in cards]))
        if len(tags) > 1:
            print ">>> Warning, mismatching cards?", tags
            time.sleep(2)

        oname = os.path.join(options.outdir, 'tHq_%s.card.txt' % tags[0])
        print "to %s" % oname

        combineCards(cards, chans, oname)


if __name__ == '__main__':
    from optparse import OptionParser
    usage = """
    %prog [options] dir1/ dir2/ [dir3/ dir4/]

    Call combineCards.py on all tuples of *.card.txt files in the
    input directories and store the output in combined/
    Copy also the input.root files to the output directory.

    Assumes the input directories (channels) are ordered as follows:
    2lss_mm, 2lss_em, 3l, bb_3m, bb_4m, bb_dilep

    Change this order (and the output bin names) by using -c/--binnames

    Note that you need to have 'combineCards.py' in your path. Try:
    cd /afs/cern.ch/user/s/stiegerb/combine707/ ; cmsenv ; cd -
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--outdir", dest="outdir",
                      type="string", default="combined/")
    parser.add_option("-c", "--binnames", dest="binnames",
                      type="string", default="2lss_mm,2lss_em,3l,bb_3m,bb_4m,bb_dilep",
                      help="Comma separated list of bin names ('tHq_' will be prepended)")
    (options, args) = parser.parse_args()

    main(args, options)
