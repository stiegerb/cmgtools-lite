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


ADD_RATIO_VALS = {
    -6.000 : [-5.5, -5.0, -4.5],
    -4.000 : [-3.75, -3.5, -3.25, -5.5, -5.0, -4.5],
    -3.000 : [-2.875, -2.75, -2.625, -3.75, -3.5, -3.25],
    -2.500 : [-2.375, -2.25, -2.125, -2.875, -2.75, -2.625],
    -2.000 : [-1.875, -1.75, -1.625, -2.375, -2.25, -2.125],
    -1.500 : [-1.4582, -1.4165, -1.3748, -1.875, -1.75, -1.625],
    -1.333 : [-1.3122, -1.2915, -1.2708, -1.4582, -1.4165, -1.3748],
    -1.250 : [-1.1875, -1.125, -1.0625, -1.3122, -1.2915, -1.2708],
    -1.000 : [-0.9582, -0.9165, -0.8748, -1.1875, -1.125, -1.0625],
    -0.833 : [-0.8122, -0.7915, -0.7708, -0.9582, -0.9165, -0.8748],
    -0.750 : [-0.7292, -0.7085, -0.6878, -0.8122, -0.7915, -0.7708],
    -0.667 : [-0.6253, -0.5835, -0.5417, -0.7292, -0.7085, -0.6878],
    -0.500 : [-0.4582, -0.4165, -0.3748, -0.6253, -0.5835, -0.5417],
    -0.333 : [-0.3123, -0.2915, -0.2708, -0.4582, -0.4165, -0.3748],
    -0.250 : [-0.2292, -0.2085, -0.1878, -0.3123, -0.2915, -0.2708],
    -0.167 : [-0.1252, -0.0835, -0.0418, -0.2292, -0.2085, -0.1878],
    -0.000 : [0.0418, 0.0835, 0.1252, -0.1252, -0.0835, -0.0418],
     0.167 : [0.1878, 0.2085, 0.2292, 0.0418, 0.0835, 0.1252],
     0.250 : [0.2708, 0.2915, 0.3123, 0.1878, 0.2085, 0.2292],
     0.333 : [0.3748, 0.4165, 0.4582, 0.2708, 0.2915, 0.3123],
     0.500 : [0.5417, 0.5835, 0.6253, 0.3748, 0.4165, 0.4582],
     0.667 : [0.6878, 0.7085, 0.7292, 0.5417, 0.5835, 0.6253],
     0.750 : [0.7708, 0.7915, 0.8122, 0.6878, 0.7085, 0.7292],
     0.833 : [0.8748, 0.9165, 0.9582, 0.7708, 0.7915, 0.8122],
     1.000 : [1.0625, 1.125, 1.1875, 0.8748, 0.9165, 0.9582],
     1.250 : [1.2708, 1.2915, 1.3122, 1.0625, 1.125, 1.1875],
     1.333 : [1.3748, 1.4165, 1.4582, 1.2708, 1.2915, 1.3122],
     1.500 : [1.625, 1.75, 1.875, 1.3748, 1.4165, 1.4582],
     2.000 : [2.125, 2.25, 2.375, 1.625, 1.75, 1.875],
     2.500 : [2.625, 2.75, 2.875, 2.125, 2.25, 2.375],
     3.000 : [3.25, 3.5, 3.75, 2.625, 2.75, 2.875],
     4.000 : [4.5, 5.0, 5.5, 3.25, 3.5, 3.75],
     6.000 : [4.5, 5.0, 5.5],
}


def parseOutput(comboutput):
    for line in comboutput.split('\n'):
        if "WARNING: MultiDimFit failed" in line:
            print "\033[91mFit Failed\033[0m"
        m = re.match(r'Done in [\d\.]+ min \(cpu\), ([\d\.]*) min \(real\)', line)
        if not m:
            continue

        return float(m.group(1))

    print "\033[91mFailed to parse output\033[0m"
    return None


def getNLLFromRootFile(rfilename):
    tf = TFile.Open(rfilename, 'read')
    tree = tf.Get("limit")
    if not tree:
        raise RuntimeError("Unable to read limit tree from file %s" % rfilename)

    data = [(float(e.r), float(e.deltaNLL)) for e in tree]
    tf.Close()

    assert(len(data) == 2 and len(data[0]) == 2 and len(data[1]) == 2), "something wrong? %s" % rfilename
    return data


def runNLLScan(card, setratio=None, verbose=False, toysFile=None):
    cv, ct, tag = parseName(card, printout=False)
    printout = "%-40s CV=%5.2f, Ct=%5.2f" % (os.path.basename(card), cv, ct)
    combinecmd = "combine -M MultiDimFit --algo fixed --fixedPointPOIs r=0,r_others=0"
    combinecmd += " --rMin=0 --rMax=20 --X-rtd ADDNLL_RECURSIVE=0"
    combinecmd += " --cminDefaultMinimizerStrategy 0" # default is 1
    combinecmd += " --cminDefaultMinimizerTolerance 0.01" # default is 0.1
    combinecmd += " --cminPreScan" # default is off
    # combinecmd += " --X-rtd MINIMIZER_analytic" # trying out for aa toys

    ratio = setratio or round(ct/cv, 3)
    filetag = "%s_%s" % (tag, str(ratio))
    printout += ", Ratio=%7.4f: " % setratio
    combinecmd += " -m 125 --verbose 0 -n _nll_scan_r1_%s" % (filetag)
    combinecmd += " --setParameters kappa_t=%.2f,kappa_V=1.0,r=1,r_others=1" % ratio
    combinecmd += " --freezeParameters r,r_others,kappa_t,kappa_V,"
    combinecmd += "kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam,"
    combinecmd += "pdfindex_TTHHadronicTag_13TeV,pdfindex_TTHLeptonicTag_13TeV"
    combinecmd += " --redefineSignalPOIs r"

    if toysFile:
        assert(os.path.isfile(toysFile)), "file not found %s" % toysFile
        combinecmd += " -t -1 --toysFile %s" % toysFile

    comboutput = runCombineCommand(combinecmd, card, verbose=verbose)
    elapsed = parseOutput(comboutput)
    try:
        data = getNLLFromRootFile("higgsCombine_nll_scan_r1_%s.MultiDimFit.mH125.root" % filetag)
        printout += "r=%5.2f, dNLL=%+7.3f " % (data[0][0], data[1][1])
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
        cv, ct, tag = parseName(card, printout=False)
        ratio = round(ct/cv, 3)
        future = pool.apply_async(runNLLScan, (card,
                                               ratio,
                                               options.printCommand,
                                               options.toysFile))
        futures.append((card, ratio, future))

        if options.addValues:
            for added_val in ADD_RATIO_VALS.get(ratio):
                future = pool.apply_async(runNLLScan, (card,
                                                       added_val,
                                                       options.printCommand,
                                                       options.toysFile))
                futures.append((card, added_val, future))

    with open(csvfname, 'w') as csvfile:
        csvfile.write('fname,cv,cf,ratio,bestfitr,dnll\n')
        for card, ratio, future in futures:
            cv, ct, tag = parseName(card, printout=False)
            bfr, dnll = future.get() # catch timeout?
            csvfile.write(','.join(map(str, [card, cv, ct, ratio, bfr, dnll])) + '\n')

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
