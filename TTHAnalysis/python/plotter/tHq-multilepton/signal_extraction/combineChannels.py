#!/usr/bin/env python
import sys, os, re, shutil, shlex
from subprocess import Popen, PIPE

def combineCards(cards, chans, oname):
    try:
        assert( all(['2lss' in c for c in cards[:-1]]) )
        assert( '2lss-mm' in cards[0] )
        assert( '2lss-em' in cards[:-1][1] )
        assert( '2lss-ee' in cards[:-1][2] )
        assert( '3l' in cards[-1] )
    except AssertionError:
        print "Warning, cards out of order? Assuming mm, em, ee, 3l"
    except IndexError: pass
    assert( len(cards) == len(chans) )

    chanargs = ' '.join(['%s=%s' % (chn,cn) for chn,cn in zip(chans, cards)])
    combinecmd = shlex.split('combineCards.py %s'%chanargs)

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
        except OSError: pass


    with open(oname, 'w') as cfile:
        cfile.write(ccard)

    # Copy the root files (and make a copy of the card while 
    # we're at it, because why not):
    for card,cdir in zip(cards,inputdirs):
        shutil.copy(card, os.path.join(odir, cdir))
        shutil.copy(card.replace('card.txt', 'input.root'),
                          os.path.join(odir, cdir))

def main(args, options):
    inputdirs = args
    assert( all([os.path.isdir(d) for d in inputdirs]) )

    dn2cards = {} # dirname -> cards
    dn2files = {} # dirname -> files
    for dname in inputdirs:
        dn2cards[dname] = sorted([os.path.join(dname,c) for c in
                                     os.listdir(dname) if c.endswith('card.txt')])
        dn2files[dname] = sorted([os.path.join(dname,c) for c in
                                     os.listdir(dname) if c.endswith('input.root')])

    ncards = len(dn2cards.values()[0])
    nfiles = len(dn2files.values()[0])
    assert( ncards == nfiles )
    assert( all([len(c) == ncards for c in dn2cards.values()]) )
    assert( all([len(c) == nfiles for c in dn2files.values()]) )

    print ("Input directories OK, found %d cards to combine "
           "from %d directories" % (ncards, len(inputdirs)))

    chans = {
        2 : ['mm','lll'],
        3 : ['mm','em','lll'],
        4 : ['mm','em','ee','lll'],
    }[len(inputdirs)]


    for cards in zip(*tuple(dn2cards.values())):
        print "combining %s" % ' '.join([os.path.basename(c) for c in cards]),
        tagpat = re.compile(r'.*\_([\dpm]+\_[\dpm]+)\.card\.txt')
        tags = list(set([re.match(tagpat, c).groups()[0] for c in cards]))
        assert(len(tags) == 1)

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

    Note that you need to have 'combineCards.py' in your path. Try:
    cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-o","--outdir", dest="outdir",
                      type="string", default="combined/")
    (options, args) = parser.parse_args()


    main(args, options)
