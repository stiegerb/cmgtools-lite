#!/usr/bin/env python
import sys
import os
import re
import multiprocessing
import numpy as np

from ROOT import TFile

from runAllLimits import runCombineCommand
from runAllLimits import parseName
from runAllLimits import setParamatersFreezeAll
from runAllLimits import processInputs


def parseOutput(comboutput):
    for line in comboutput.split('\n'):
        if "WARNING: MultiDimFit failed" in line:
            print "\033[91mFailed\033[0m"
        m = re.match(r'Done in [\d\.]+ min \(cpu\), ([\d\.]*) min \(real\)', line)
        if not m:
            continue

        return float(m.group(1))

    print "\033[91mFailed\033[0m"
    return None


def getNLLFromRootFile(rfilename):
    tf = TFile.Open(rfilename, 'read')
    tree = tf.Get("limit")
    if not tree:
        raise RunTimeError("Unable to read limit tree from file %s" % rfilename)

    data = [(float(e.r), float(e.deltaNLL)) for e in tree]
    tf.Close()

    assert(len(data) == 2 and len(data[0]) == 2 and len(data[1]) == 2), "something wrong? %s" % rfilename
    return data


def runNLLScan(card, verbose=False, toysFile=None):
    cv, ct, tag = parseName(card, printout=False)
    printout = "%-40s CV=%5.2f, Ct=%5.2f : " % (os.path.basename(card), cv, ct)
    combinecmd = "combine -M MultiDimFit --algo fixed --fixedPointPOIs r=1"
    combinecmd += " --rMin=0 --rMax=20 --X-rtd ADDNLL_RECURSIVE=0"
    combinecmd += " --cminDefaultMinimizerStrategy 0"
    combinecmd += " -m 125 --verbose 0 -n _nll_scan_r1_%s" % tag
    combinecmd += setParamatersFreezeAll(ct / cv, 1.0)

    if toysFile:
        assert(os.path.isfile(toysFile)), "file not found %s" % toysFile
        combinecmd += " -t -1 --toysFile %s" % toysFile

    comboutput = runCombineCommand(combinecmd, card, verbose=verbose)
    elapsed = parseOutput(comboutput)
    try:
        data1 = getNLLFromRootFile("higgsCombine_nll_scan_r1_%s.MultiDimFit.mH125.root" % tag)
        printout += "r=%5.2f, dNLL_r1=%5.2f " % (data1[0][0], data1[1][1])
    except AssertionError, IndexError:
        return np.nan, np.nan, np.nan

    combinecmd = combinecmd.replace("--fixedPointPOIs r=1", "--fixedPointPOIs r=0")
    combinecmd = combinecmd.replace("-n _nll_scan_r1_", "-n _nll_scan_r0_")
    comboutput = runCombineCommand(combinecmd, card, verbose=verbose)
    elapsed += parseOutput(comboutput)

    try:
        data0 = getNLLFromRootFile("higgsCombine_nll_scan_r0_%s.MultiDimFit.mH125.root" % tag)
        printout += "dNLL_r0=%5.2f" % data0[1][1]
    except AssertionError, IndexError:
        return np.nan, np.nan, np.nan

    # floating fit has to be identical and perfect
    assert(data1[0] == data0[0]), "r=1 and r=0 fits give different results"
    assert(data1[0][1] == 0.0), "dNLL for floating r not equal to 0"

    printout += "  \033[92mDone\033[0m in %.2f min" % elapsed
    print printout

    return (data1[0][0], data1[1][1], data0[1][1])

def main(args, options):
    cards, runtag = processInputs(args, options)

    if options.toysFile:
        runtag += "_toys"
    csvfname = 'nll_scan%s.csv' % runtag
    pool = multiprocessing.Pool(processes=options.jobs)

    futures = []
    for card in cards:
        future = pool.apply_async(runNLLScan, (card,
                                               options.printCommand,
                                               options.toysFile))
        futures.append((card, future))


    with open(csvfname, 'w') as csvfile:
        csvfile.write('fname,cv,cf,bestfitr,nllr1,nllr0\n')
        for card, future in futures:
            cv, ct, tag = parseName(card, printout=False)
            bfr, nllr1, nllr0 = future.get() # catch timeout?
            csvfile.write(','.join(map(str, [card, cv, ct, bfr, nllr1, nllr0])) + '\n')

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
    (options, args) = parser.parse_args()

    sys.exit(main(args, options))
