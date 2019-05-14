#!/usr/bin/env python
import os
import re
import sys
import shlex
import multiprocessing
import numpy as np

from runAllLimits import runCombineCommand
from runAllLimits import processInputs
from runNLLScan import getNLLFromRootFile
from runNLLScan import parseOutput

def parseName(card, printout=True):
    # Turn the tag into floats:
    tag = re.match(r'.*\_([\dpm]+).*\.card\.(txt|root)', os.path.basename(card))
    if tag == None:
        print "Couldn't figure out this one: %s" % card
        return

    tag = tag.groups()[0]
    tagf = tag.replace('p', '.').replace('m','-')
    cp = float(tagf)
    if printout:
        print "%-40s CP=%5.2f : " % (os.path.basename(card), cp),
    return cp, tag


def runNLLScan(card, verbose=False, toysFile=None):
    cp, tag = parseName(card, printout=False)
    printout = "%-40s CP=%5.2f" % (os.path.basename(card), cp)
    combinecmd = "combine -M MultiDimFit --algo fixed --fixedPointPOIs r=0"
    combinecmd += " --verbose 0 -m 125 -n _nll_scan_r1_%s" % (tag)
    combinecmd += " --setParameters r=1 --freezeParameters r"
    combinecmd += " --redefineSignalPOIs r"
    combinecmd += " --cminPreScan"

    if toysFile:
        assert(os.path.isfile(toysFile)), "file not found %s" % toysFile
        combinecmd += " -t -1 --toysFile %s" % toysFile

    comboutput = runCombineCommand(combinecmd, card, verbose=verbose)
    elapsed = parseOutput(comboutput)
    try:
        data = getNLLFromRootFile("higgsCombine_nll_scan_r1_%s.MultiDimFit.mH125.root" % tag)
        printout += " r=%5.2f, dNLL=%+7.3f " % (data[0][0], data[1][1])
    except AssertionError, IndexError:
        return np.nan, np.nan

    printout += "  \033[92mDone\033[0m in %.2f min" % elapsed
    print printout

    return (data[0][0], data[1][1])


def main(args, options):
    cards, runtag = processInputs(args, options)

    if options.toysFile:
        runtag += "_toys"
    csvfname = 'nll_scan%s.csv' % runtag
    pool = multiprocessing.Pool(processes=options.jobs)

    futures = []
    for card in cards:
        cp, tag = parseName(card, printout=False)
        future = pool.apply_async(runNLLScan, (card,
                                               options.printCommand,
                                               options.toysFile))
        futures.append((card, cp, future))

    with open(csvfname, 'w') as csvfile:
        csvfile.write('fname,cp,bestfitr,dnll\n')
        for card, cp, future in futures:
            cp_name, tag = parseName(card, printout=False)
            assert(cp == cp_name)
            bfr, dnll = future.get() # catch timeout?
            csvfile.write(','.join(map(str, [card, cp, bfr, dnll])) + '\n')

        csvfile.write('\n')

    print "...wrote results to %s" % csvfname

    return 0


if __name__ == '__main__':
    from optparse import OptionParser
    usage = """
    %prog [options] dir/
    %prog [options] card.txt
    %prog [options] workspace1.root workspace2.root

    Call combine on all datacards ("*.card.txt") in an input directory.
    Run MultiDimFit with --algo fixed and --fixedPointPOIs r=1 and r=0


    Note that you need to have 'combine' in your path. Try:
    cd /afs/cern.ch/user/s/stiegerb/combine707/ ; cmsenv ; cd -
    """
    parser = OptionParser(usage=usage)
    parser.add_option("-t","--tag", dest="tag", type="string", default=None,
                      help="Tag to put in name of output csv files")
    parser.add_option("-j","--jobs", dest="jobs", type="int", default=1,
                      help="Number of jobs to run in parallel")
    parser.add_option("--toysFile", dest="toysFile", type="string", default=None,
                      help="File from which to read toys for expected nll")
    parser.add_option("-p","--printCommand", dest="printCommand", action='store_true',
                      help="Print the combine command that is run")
    parser.add_option("--addValues", dest="addValues", action='store_true',
                      help="Add three steps between each point for interpolation")
    (options, args) = parser.parse_args()

    sys.exit(main(args, options))