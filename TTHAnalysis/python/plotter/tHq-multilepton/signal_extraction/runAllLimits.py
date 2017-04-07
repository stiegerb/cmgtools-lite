#!/usr/bin/env python
import sys, os, re, shlex
from subprocess import Popen, PIPE

def getLimits(card, model='K6', unblind=False):
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

    combinecmd =  "combine -M Asymptotic"
    if not unblind:
        combinecmd += " --run blind"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    if model in ['K4', 'K5', 'K6']:
        if model == 'K6':
            # Rescale to cv = 1, we only care about the ct/cv ratio
            combinecmd += " --setPhysicsModelParameters kappa_t=%.2f,kappa_V=%.2f" % (ct/cv, 1.0)
        else:
            combinecmd += " --setPhysicsModelParameters kappa_t=%.2f,kappa_V=%.2f" % (ct,cv)
        combinecmd += " --freezeNuisances kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam"
        combinecmd += " --redefineSignalPOIs r"
    try:
        p = Popen(shlex.split(combinecmd) + [card] , stdout=PIPE, stderr=PIPE)
        comboutput = p.communicate()[0]
    except OSError:
        print "combine command not known. Try this: cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -"
        return

    liminfo = {}
    for line in comboutput.split('\n'):
        if line.startswith('Observed Limit:'):
            liminfo['obs'] = float(line.rsplit('<', 1)[1].strip())
        if line.startswith('Expected'):
            value = float(line.rsplit('<', 1)[1].strip())
            if   'Expected  2.5%' in line: liminfo['twosigdown'] = value
            elif 'Expected 16.0%' in line: liminfo['onesigdown'] = value
            elif 'Expected 50.0%' in line: liminfo['exp']        = value
            elif 'Expected 84.0%' in line: liminfo['onesigup']   = value
            elif 'Expected 97.5%' in line: liminfo['twosigup']   = value

    print "%5.2f, %5.2f, \033[92m%5.2f\033[0m, %5.2f, %5.2f" %(
        liminfo['twosigdown'], liminfo['onesigdown'], liminfo['exp'],
        liminfo['onesigup'], liminfo['twosigup']),
    if 'obs' in liminfo: # Add observed limit to output, in case it's there
        print "\033[1m %5.2f \033[0m" % (liminfo['obs'])
    else:
        print ""
    return cv, ct, liminfo

def getFitValues(card, model='K6', unblind=False):
    """
    Run combine on a single card, return a tuple of fitvalues
    (cv,ct,median,downerror,uperror)
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

    combinecmd =  "combine -M MaxLikelihoodFit"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    if model in ['K4', 'K5', 'K6']:
        if model == 'K6':
            # Rescale to cv = 1, we only care about the ct/cv ratio
            combinecmd += " --setPhysicsModelParameters kappa_t=%.2f,kappa_V=%.2f" % (ct/cv, 1.0)
        else:
            combinecmd += " --setPhysicsModelParameters kappa_t=%.2f,kappa_V=%.2f" % (ct,cv)
        combinecmd += " --freezeNuisances kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam"
        combinecmd += " --redefineSignalPOIs r"
        if abs(ct/cv) > 3:        
            combinecmd += " --robustFit 1 --setPhysicsModelParameterRanges r=0,1"
        else:
            combinecmd += " --robustFit 1 --setPhysicsModelParameterRanges r=0,10"
    try:
        p = Popen(shlex.split(combinecmd) + [card] , stdout=PIPE, stderr=PIPE)
        comboutput = p.communicate()[0]
    except OSError:
        print "combine command not known. Try this: cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -"
        return

    fitinfo = {}
    for line in comboutput.split('\n'):
        if line.startswith('Best'):
            print(line)
            fitinfo['median'] = float((line.split(': ')[1]).split('  ')[0])
            fitinfo['downerror'] = float((line.split('  ')[1]).split('/')[0])
            fitinfo['uperror'] = float((line.split('+')[1]).split('  (')[0])

    print "\033[92m%5.2f\033[0m, %5.2f, %5.2f" %( fitinfo['median'], fitinfo['downerror'], fitinfo['uperror'])
    return cv, ct, fitinfo

def main(args, options, limit=False, fit=True):

    cards = []
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
        if len(tag): tag = '_'+tag
        cards = sorted([c for c in args if os.path.exists(c) and (c.endswith('card.txt') or c.endswith('card.root'))])

    print "Found %d cards to run" % len(cards)


    if limit:
        limdata = {} # (cv,ct) -> (2sd, 1sd, lim, 1su, 2su, [obs])
        for card in cards:
            cv, ct, liminfo = getLimits(card, model=options.model, unblind=options.unblind)
            limdata[(cv,ct)] = liminfo
    
        fnames = []
        for cv_ in [0.5, 1.0, 1.5]:
            if not cv_ in [v for v,_ in limdata.keys()]: continue
            csvfname = 'limits%s_cv_%s.csv' % (tag, str(cv_).replace('.','p'))
            with open(csvfname, 'w') as csvfile:
                if options.unblind:
                    csvfile.write('cv,cf,twosigdown,onesigdown,exp,onesigup,twosigup,obs\n')
                else:
                    csvfile.write('cv,cf,twosigdown,onesigdown,exp,onesigup,twosigup\n')
                for cv,ct in sorted(limdata.keys()):
                    if not cv == cv_: continue
                    values = [cv, ct]
                    values += [limdata[(cv,ct)][x] for x in ['twosigdown','onesigdown','exp','onesigup','twosigup']]
                    if options.unblind:
                        values += [limdata[(cv,ct)]['obs']]
                    csvfile.write(','.join(map(str, values)) + '\n')
            fnames.append(csvfname)
        print "All done. Wrote limits to: %s" % (" ".join(fnames))

    if fit:
        fitdata = {} # (cv,ct) -> (fit, down, up)
        for card in cards:
            cv, ct, fitinfo = getFitValues(card, model=options.model, unblind=options.unblind)
            fitdata[(cv,ct)] = fitinfo

        fnames = []
        for cv_ in [0.5, 1.0, 1.5]:
            if not cv_ in [v for v,_ in fitdata.keys()]: continue
            csvfname = 'fits%s_cv_%s.csv' % (tag, str(cv_).replace('.','p'))
            with open(csvfname, 'w') as csvfile:
                if options.unblind:
                    csvfile.write('cv,cf,median,downerror,uperror\n')
                else:
                    csvfile.write('cv,cf,median,downerror,uperror\n')
                for cv,ct in sorted(fitdata.keys()):
                    if not cv == cv_: continue
                    values = [cv, ct]
                    values += [fitdata[(cv,ct)][x] for x in ['median','downerror','uperror']]
                    csvfile.write(','.join(map(str, values)) + '\n')
            fnames.append(csvfname)
    
        print "Wrote limits to: %s" % (" ".join(fnames))
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
    parser.add_option("-m","--model", dest="model",
                      type="string", default="K6")
    parser.add_option("-u","--unblind", dest="unblind",
                      action='store_true')
    (options, args) = parser.parse_args()

    sys.exit(main(args, options))
