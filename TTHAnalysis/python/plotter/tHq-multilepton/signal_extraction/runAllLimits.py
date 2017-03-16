#!/usr/bin/env python
import sys, os, re, shlex
from subprocess import Popen, PIPE

def getLimits(card):
    """
    Run combine on a single card, return a tuple of 
    (cv,ct,twosigdown,onesigdown,exp,onesigup,twosigup)
    """
    # Turn the tag into floats:
    tag = re.match(r'.*\_([\dpm]+\_[\dpm]+).*\.card\.(txt|root)', os.path.basename(card))
    if tag == None:
        print "Couldn't figure out this one: %s" % card
        return

    tag = tag.groups()[0]
    tagf = tag.replace('p', '.').replace('m','-')
    cv,ct = tuple(map(float, tagf.split('_')))
    print "%-40s CV=%5.2f, Ct=%5.2f : " % (os.path.basename(card), cv, ct),

    combinecmd =  "combine -M Asymptotic --run blind --rAbsAcc 0.0005 --rRelAcc 0.0005"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    combinecmd += " --setPhysicsModelParameters kappa_t=%.2f,kappa_V=%.2f" % (ct,cv)
    # combinecmd += " --setPhysicsModelParameters kappa_t=%.2f,kappa_W=%.2f,kappa_Z=%.2f" % (ct,cv,cv)
    # combinecmd += " --setPhysicsModelParameters kappa_F=%.2f,kappa_V=%.2f" % (ct,cv)
    combinecmd += " --setPhysicsModelParameterRanges kappa_t=-4,4"
    combinecmd += " --freezeNuisances kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam"
    # combinecmd += " --freezeNuisances kappa_t,kappa_W,kappa_Z,kappa_tau,kappa_mu,kappa_b,kappa_c"
    # combinecmd += " --freezeNuisances kappa_F,kappa_V --redefineSignalPOIs r"
    combinecmd += " --redefineSignalPOIs r"
    # combinecmd += " --setPhysicsModelParameterRanges kappa_F=-4,4"
    # combinecmd = "combine -M Asymptotic --run blind --rAbsAcc 0.0005 --rRelAcc 0.0005 --setPhysicsModelParameterRanges lambda_FV=-10,10 --setPhysicsModelParameters lambda_FV=-1.0 --freezeNuisances kappa_VV,lambda_du,lambda_Vu,kappa_uu,lambda_lq,lambda_Vq,kappa_qq,lambda_FV --redefineSignalPOIs r"
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

    if os.path.isdir(args[0]):
        inputdir = args[0]

        if options.tag != None:
            tag = "_"+options.tag
        elif options.tag == "":
            tag = ""
        else:
            # Try to get the tag from the input directory
            if inputdir.endswith('/'): inputdir = inputdir[:-1]
            tag = "_"+os.path.basename(inputdir)
            assert( '/' not in tag )

        cards = sorted([os.path.join(inputdir, c) for c in
                    os.listdir(inputdir) if c.endswith('card.txt') or c.endswith('card.root')])

    elif os.path.exists(args[0]):
        tag = options.tag or ""
        cards = sorted([c for c in args if os.path.exists(c) and (c.endswith('card.txt') or c.endswith('card.root'))])

    print "Found %d cards to run" % len(cards)

    limdata = {} # (cv,ct) -> (2sd, 1sd, lim, 1su, 2su)
    for card in cards:
        cv, ct, liminfo = getLimits(card)
        limdata[(cv,ct)] = liminfo

    fnames = []
    for cv_ in [0.5, 1.0, 1.5]:
        if not cv_ in [v for v,_ in limdata.keys()]: continue
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
