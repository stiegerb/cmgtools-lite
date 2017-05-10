#!/usr/bin/env python
import sys, os, re, shlex
from subprocess import Popen, PIPE

def runCombineCommand(combinecmd, card, verbose=False, queue=None, submitName=None):
    if queue:
        combinecmd = combinecmd.replace('combine', 'combineTool.py')
        combinecmd += ' --job-mode lxbatch --sub-opts="-q %s"' % queue
        combinecmd += ' --task-name tHq_%s' % submitName
        # combinecmd += ' --dry-run'
    if verbose: 
        print 40*'-'
        print "%s %s" % (combinecmd, card)
        print 40*'-'
    try:
        p = Popen(shlex.split(combinecmd) + [card] , stdout=PIPE, stderr=PIPE)
        comboutput = p.communicate()[0]
    except OSError:
        print "combine command not known. Try this: cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -"
        comboutput = None
    return comboutput

def parseName(card, printout=True):
    # Turn the tag into floats:
    tag = re.match(r'.*\_([\dpm]+\_[\dpm]+).*\.card\.(txt|root)', os.path.basename(card))
    if tag == None:
        print "Couldn't figure out this one: %s" % card
        return

    tag = tag.groups()[0]
    tagf = tag.replace('p', '.').replace('m','-')
    cv,ct = tuple(map(float, tagf.split('_')))
    if printout:
        print "%-40s CV=%5.2f, Ct=%5.2f : " % (os.path.basename(card), cv, ct),
    return cv, ct, tag

def setParamatersFreezeAll(ct,cv):
    addoptions = " --setPhysicsModelParameters kappa_t=%.2f,kappa_V=%.2f" % (ct,cv)
    addoptions += " --freezeNuisances kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam"
    addoptions += " --redefineSignalPOIs r"
    return addoptions

def getLimits(card, model='K6', unblind=False, printCommand=False):
    """
    Run combine on a single card, return a tuple of 
    (cv,ct,twosigdown,onesigdown,exp,onesigup,twosigup)
    """
    cv,ct,tag = parseName(card)
    if printCommand: print ""

    combinecmd =  "combine -M Asymptotic"
    if not unblind:
        combinecmd += " --run blind"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    if model in ['K4', 'K5', 'K6', 'K7']:
        if model == 'K6': # Rescale to cv = 1, we only care about the ct/cv ratio
            combinecmd += setParamatersFreezeAll(ct/cv,1.0)
        else:
            combinecmd += setParamatersFreezeAll(ct, cv)

    comboutput = runCombineCommand(combinecmd, card, verbose=printCommand)

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

def runSMExpectedLimits(card, ntoys=100, toysfile="higgsCombine_SMtoys.GenerateOnly.mH125.123456.root",
                        queue=None,
                        printCommand=False):
    """
    Run combine on a single card, return a tuple of 
    (cv,ct,twosigdown,onesigdown,exp,onesigup,twosigup)
    """
    cv,ct,tag = parseName(card)
    if printCommand: print ""

    if queue:
        print toysfile
    combinecmd =  "combine -M Asymptotic --run observed"
    combinecmd += " -m 125 --verbose 0 -n cvct%s_SM"%tag
    combinecmd += setParamatersFreezeAll(ct/cv,1.0)
    combinecmd += " -t %d" % ntoys
    combinecmd += " --toysFile %s" % toysfile

    comboutput = runCombineCommand(combinecmd, card, submitName=tag, queue=queue, verbose=printCommand)
    return comboutput

def getSMExpectedLimits(output, printCommand=False):
    liminfo = {}
    for line in output.split('\n'):
        try: header, body = line.split(':', 1)
        except ValueError: continue
        if header == 'median expected limit':
            liminfo['exp'] = float(body.rsplit('<', 1)[1].rsplit('@',1)[0].strip())
        if 'expected band' in header:
            down, up = body.split(' < r < ')
            if '68%' in header:
                liminfo['onesigup']   = float(up)
                liminfo['onesigdown'] = float(down)
            elif '95%' in header:
                liminfo['twosigup']   = float(up)
                liminfo['twosigdown'] = float(down)

    print "%5.2f, %5.2f, \033[92m%5.2f\033[0m, %5.2f, %5.2f" %(
        liminfo['twosigdown'], liminfo['onesigdown'], liminfo['exp'],
        liminfo['onesigup'], liminfo['twosigup'])
    return liminfo

def getFitValues(card, model='K6', unblind=False, printCommand=False):
    """
    Run combine on a single card, return a tuple of fitvalues
    (cv,ct,median,downerror,uperror)
    """
    cv,ct,tag = parseName(card)
    if printCommand: print ""

    combinecmd =  "combine -M MaxLikelihoodFit"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    if model in ['K4', 'K5', 'K6', 'K7']:
        if model == 'K6': # Rescale to cv = 1, we only care about the ct/cv ratio
            combinecmd += setParamatersFreezeAll(ct/cv,1.0)
        else:
            combinecmd += setParamatersFreezeAll(ct, cv)

        if abs(ct/cv) > 3:        
            combinecmd += " --robustFit 1 --setPhysicsModelParameterRanges r=0,1"
        else:
            # Note that these ranges don't work well for some points
            # e.g.: -3.0/1.0, -1.5/0.5, -1.25/0.5
            combinecmd += " --robustFit 1 --setPhysicsModelParameterRanges r=-5,10"
    comboutput = runCombineCommand(combinecmd, card, verbose=printCommand)

    fitinfo = {}
    for line in comboutput.split('\n'):
        if line.startswith('Best'):
            fitinfo['median'] = float((line.split(': ')[1]).split('  ')[0])
            fitinfo['downerror'] = float((line.split('  ')[1]).split('/')[0])
            fitinfo['uperror'] = float((line.split('+')[1]).split('  (')[0])

    print "\033[92m%5.2f\033[0m, %5.2f, %5.2f" %( fitinfo['median'], fitinfo['downerror'], fitinfo['uperror'])
    return cv, ct, fitinfo

def getSignificance(card, model='K6', unblind=False, printCommand=False):
    """
    Run combine on a single card, return significance
    """
    cv,ct,tag = parseName(card)
    if printCommand: print ""

    combinecmd =  "combine -M ProfileLikelihood --signif"
    combinecmd += " -m 125 --verbose 0 -n cvct%s"%tag
    if model in ['K4', 'K5', 'K6', 'K7']:
        if model == 'K6': # Rescale to cv = 1, we only care about the ct/cv ratio
            combinecmd += setParamatersFreezeAll(ct/cv,1.0)
        else:
            combinecmd += setParamatersFreezeAll(ct, cv)
    comboutput = runCombineCommand(combinecmd, card, verbose=printCommand)

    significance = {}
    for line in comboutput.split('\n'):
        if line.startswith('Significance'):
            print(line)
            significance['value'] = float(line.rsplit(':', 1)[1].strip())

    print "\033[92m%5.2f\033[0m" %( significance['value'])
    return cv, ct, significance

def main(args, options):

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

        cards = [os.path.join(inputdir, c) for c in os.listdir(inputdir)]

    elif os.path.exists(args[0]):
        tag = options.tag or ""
        if len(tag): tag = '_'+tag
        cards = [c for c in args if os.path.exists(c)]

    cards = [c for c in cards if any([c.endswith(ext) for ext in ['card.txt', 'card.root', '.log']])]
    cards = sorted(cards)
    print "Found %d cards to run" % len(cards)

    if options.runmode.lower() == 'limits':
        limdata = {} # (cv,ct) -> (2sd, 1sd, lim, 1su, 2su, [obs])
        for card in cards:
            cv, ct, liminfo = getLimits(card, model=options.model,
                                        unblind=options.unblind,
                                        printCommand=options.printCommand)
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

    if options.runmode.lower() == 'smexpected':
        if options.queue: # produce the limits on the batch system
            # pair each card with a file containing 100 toys
            # in the directory given by options.toysDir
            # assert(len(cards) <= len(os.listdir(options.toysDir)))
            # for card, tname in zip(cards, os.listdir(options.toysDir)):
            for card in cards:
                # toysfile = os.path.join(options.toysDir, tname)
                runSMExpectedLimits(card, ntoys=options.ntoys,
                                          toysfile=options.toysDir,
                                          # toysfile=toysfile,
                                          queue=options.queue,
                                          printCommand=options.printCommand) 
            return 0

        limdata = {} # (cv,ct) -> (2sd, 1sd, lim, 1su, 2su, [obs])
        for logfile in cards: # process the logfiles from the batch jobs
            # Recover the point first
            match = re.match(r'.*\_([\dpm]+\_[\dpm]+)\_0_[0-9]{8}\.log', os.path.basename(logfile))
            if match == None:
                raise RuntimeError("Error parsing filename %s" % logfile)

            match = match.groups()[0]
            matchf = match.replace('p', '.').replace('m','-')
            cv,ct = tuple(map(float, matchf.split('_')))

            print "%-40s CV=%5.2f, Ct=%5.2f : " % (os.path.basename(logfile), cv, ct),
            with open(logfile, 'r') as output:
                limdata[(cv,ct)] = getSMExpectedLimits(output.read())

        fnames = []
        for cv_ in [0.5, 1.0, 1.5]:
            if not cv_ in [v for v,_ in limdata.keys()]: continue
            csvfname = 'limits%s_cv_%s.csv' % (tag, str(cv_).replace('.','p'))
            with open(csvfname, 'w') as csvfile:
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

    if options.runmode.lower() == 'fit':
        fitdata = {} # (cv,ct) -> (fit, down, up)
        for card in cards:
            cv, ct, fitinfo = getFitValues(card, model=options.model,
                                           unblind=options.unblind,
                                           printCommand=options.printCommand)
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

    if options.runmode.lower() == 'sig':
        sigdata = {}
        for card in cards:
            cv, ct, significance = getSignificance(card, model=options.model,
                                                   unblind=options.unblind,
                                                   printCommand=options.printCommand)
            sigdata[(cv,ct)] = significance

        fnames = []
        for cv_ in [0.5, 1.0, 1.5]:
            if not cv_ in [v for v,_ in sigdata.keys()]: continue
            csvfname = 'significance%s_cv_%s.csv' % (tag, str(cv_).replace('.','p'))
            with open(csvfname, 'w') as csvfile:
                csvfile.write('cv,cf,significance\n')
                for cv,ct in sorted(sigdata.keys()):
                    if not cv == cv_: continue
                    values = [cv, ct]
                    values += [sigdata[(cv,ct)][x] for x in ['value']]
                    csvfile.write(','.join(map(str, values)) + '\n')
            fnames.append(csvfname)

        print "Wrote significance to: %s" % (" ".join(fnames))

    return 0

if __name__ == '__main__':
    from optparse import OptionParser
    usage = """
    %prog [options] dir/]

    Call combine on all datacards ("*.card.txt") in an input directory.
    Collect the limit, 1, and 2 sigma bands from the output, and store
    them together with the cv and ct values (extracted from the filename)
    in a .csv file.

    Note that you need to have 'combine' in your path. Try:
    cd /afs/cern.ch/user/s/stiegerb/combine/ ; cmsenv ; cd -
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-r","--run", dest="runmode", type="string", default="limit",
                      help="What to run (limits|fit|sig|smexpected)")
    parser.add_option("--toysDir", dest="toysDir",
                      type="string", default="SMlike_toys",
                      help="For smexpected mode: input directory for toys")
    parser.add_option("--ntoys", dest="ntoys", type="int", default=100,
                      help="For smexpected mode: number of toys to read")
    parser.add_option("-t","--tag", dest="tag", type="string", default=None,
                      help="Tag to put in name of output csv files")
    parser.add_option("-m","--model", dest="model", type="string", default="K6",
                      help="Toggle to configure combine commands")
    parser.add_option("-u","--unblind", dest="unblind", action='store_true',
                      help="For limits mode: add the observed limit")
    parser.add_option("-p","--printCommand", dest="printCommand", action='store_true',
                      help="Print the combine command that is run")
    parser.add_option("-q","--queue", dest="queue", type="string", default=None,
                      help="For smexpected mode: submit jobs to this queue")
    (options, args) = parser.parse_args()

    sys.exit(main(args, options))
