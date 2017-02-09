#!/usr/bin/env python
import sys, os, re, shlex
from subprocess import Popen, PIPE

def getLimits(card):
    """
    Run combine on a single card, return a tuple of 
    (cv,ct,twosigdown,onesigdown,exp,onesigup,twosigup)
    """
    # Turn the tag into floats:
    tag = re.match(r'.*\_([\dpm]+\_[\dpm]+).*\.card\.txt', os.path.basename(card))
    if tag == None:
        print "Couldn't figure out this one: %s" % card
        return

    tag = tag.groups()[0]
    tag = tag.replace('p', '.').replace('m','-')
    cv,ct = tuple(map(float, tag.split('_')))
    print "%-40s CV=%5.2f, Ct=%5.2f : " % (card, cv, ct),

    combinecmd = "combine -M Asymptotic --run blind --rAbsAcc 0.0005 --rRelAcc 0.0005"
    try:
        p = Popen(shlex.split(combinecmd) + [card] , stdout=PIPE)
        comboutput = p.communicate()[0]
    except OSError:
        print "combine command not known. Try this: cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -"
        return

    liminfo = []
    for line in comboutput.split('\n'):
        if not line.startswith('Expected'): continue
        liminfo.append(float(line.rsplit('<', 1)[1].strip()))

    print "%5.2f, %5.2f, \033[92m%5.2f\033[0m, %5.2f, %5.2f" % (tuple(liminfo))
    return cv, ct, tuple(liminfo)

def main(args, options):

    inputdir = args[0]
    assert( os.path.isdir(inputdir) )

    tag = "_"+options.tag if options.tag else ""

    cards = sorted([os.path.join(inputdir, c) for c in
                    os.listdir(inputdir) if c.endswith('card.txt')])
    print "Found %d cards to run" % len(cards)

    limdata = {} # (cv,ct) -> (2sd, 1sd, lim, 1su, 2su)
    for card in cards:
        cv, ct, liminfo = getLimits(card)
        limdata[(cv,ct)] = liminfo

    fnames = []
    for cv_ in [0.5, 1.0, 1.5]:
        csvfname = 'limits%s_cv_%s.csv' % (tag, str(cv_).replace('.','p'))
        with open(csvfname, 'w') as csvfile:
            csvfile.write('cv,cf,twosigdown,onesigdown,exp,onesigup,twosigup\n')
            for cv,ct in sorted(limdata.keys()):
                if not cv == cv_: continue
                csvfile.write(','.join(map(str, (cv,ct)+limdata[(cv,ct)])) + '\n')
        fnames.append(csvfname)

    print "All done. Wrote limits to: %s" % (" ".join(fnames))
    return 0

if __name__ == '__main__':
    from optparse import OptionParser
    usage = """
    %prog [options] dir/]

    Call combine on all datacards ("*.card.txt") in an input directory.
    Collect the limit, 1, and 2 sigma bands from the output, and store
    them together with the cv and ct values (extracted from the filename)
    in a .csv file.

    Note that you need to have 'combineCards.py' in your path. Try:
    cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -
    """
    parser = OptionParser(usage=usage)
    # parser.add_option("-o","--outdir", dest="outdir",
    #                   type="string", default="combined/")
    parser.add_option("-t","--tag", dest="tag",
                      type="string", default=None)
    (options, args) = parser.parse_args()

    sys.exit(main(args, options))
