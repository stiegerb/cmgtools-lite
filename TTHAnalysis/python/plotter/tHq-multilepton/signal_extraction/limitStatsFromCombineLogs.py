#!/usr/bin/env python
import os
import re
import sys
import numpy as np
from math import floor, ceil

EXPANDPRECISION = {
    -1.33 : -1.333,
    -0.83 : -0.833,
    -0.67 : -0.667,
    -0.33 : -0.333,
    -0.17 : -0.167,
    0.17 : 0.167,
    0.33 : 0.333,
    0.67 : 0.667,
    0.83 : 0.833,
    1.33 : 1.333,
}

def getLimitVals(logfile):
    values = []
    kappa_t, kappa_V = None, None
    with open(logfile, "r") as lfile:
        for line in lfile:
            if line.startswith("Observed Limit:"):
                limitval = float(line.split("r < ")[1])
                values.append(limitval)

            if 'Set Default Value of Parameter kappa_t To' in line:
                kappa_t = float(line.split(":")[1])
            if 'Set Default Value of Parameter kappa_V To' in line:
                kappa_V = float(line.split(":")[1])

    if kappa_t is None or kappa_V is None:
        print "failed to determine kappas for", logfile

    ktdivkV = float("%.3f" % (kappa_t / kappa_V))
    ktdivkV = EXPANDPRECISION.get(ktdivkV, ktdivkV)

    return values, ktdivkV


def calculateMeanMedIntervals(values):
    values = sorted(values)
    mean, median = np.mean(values), np.median(values)

    hi68 = values[min(len(values) - 1, int(ceil(0.84 * len(values))))]
    lo68 = values[min(len(values) - 1, int(floor(0.16 * len(values))))]
    hi95 = values[min(len(values) - 1, int(ceil(0.975 * len(values))))]
    lo95 = values[min(len(values) - 1, int(floor(0.025 * len(values))))]

    print "mean %.4f, median %.4f" % (mean, median),
    print "(%.4f (%.4f < r < %.4f ) %.4f)" % (lo95, lo68, hi68, hi95)

    return mean, median, lo68, hi68, lo95, hi95


if __name__ == '__main__':
    """
    Usage: limitStatsFromCombineLogs.py *.log

    Gather statistics from combine output logs (when submitting to batch).
    Looks for lines with 'Observed Limit:' and collects the values. Attempts
    to determine kappa_t and kappa_V from the log file. Then store those limit
    values grouped by kappa_t/kappa_V and calculate mean, median, and 68%/95%
    bands.
    Saves the result in a combineLogStats.csv file
    """
    data = {}
    nfiles = 0
    for filename in sys.argv[1:]:
        if not (os.path.isfile(filename) and filename.endswith('.log')):
            print "... ignoring", filename
            continue

        values, ktdivkV = getLimitVals(filename)
        if len(values) < 100:
            print "WARNING, found only %d limits in %s" % (len(values), filename)

        nfiles += 1

        basename = os.path.basename(filename)
        match = re.match(r'job\_tHq\_([\dpm]+\_[\dpm]+)\_([\d])+\_[\d]*\.log', basename)
        if not match:
            print "WARNING, couldn't match filename to pattern"
            tag, split = None, None
        else:
            tag = match.group(1)
            split = match.group(2)

        # Gather up toys by kt/kV and split, but NOT by tag
        # Toys with different tags but equal split and kt/kV are identical!
        data.setdefault(ktdivkV, {})[split] = values

    # Add up the split toy results
    aggdata = {}
    for ktdivkV, splitvalues in data.items():
        for values in splitvalues.values():
            aggdata.setdefault(ktdivkV, []).extend(values)

    print "Processed %d log files for %d different kt/kV values" % (nfiles, len(data.keys()))

    csvfilename = 'combineLogStats.csv'
    assert(not os.path.isfile(csvfilename)), 'file exists: %s' % csvfilename
    with open(csvfilename, 'w') as csvfile:
        csvfile.write('ratio,twosigdown,onesigdown,exp,onesigup,twosigup,ntoys\n')

        for ktdivkV, values in sorted(aggdata.items()):
            print " %4d toys for %+.3f" % (len(values), ktdivkV),
            mean,median,lo68,hi68,lo95,hi95 = calculateMeanMedIntervals(values)
            csvfile.write(','.join(map(str, [ktdivkV,lo95,lo68,median,hi68,hi95,len(values)])))
            csvfile.write('\n')
