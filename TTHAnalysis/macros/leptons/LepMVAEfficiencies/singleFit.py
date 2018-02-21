#!/usr/bin/env python
"""
singleFit.py
"""

import os
import pickle
from ROOT import TFile
from helpers import getHistoFromTree
from helpers import putPHPIndex
from makeLepTnPFriends import getNSignalEvents
from makeLepTnPFriends import WEIGHT
from makeLepTnPFriends import MASSBINS

_CACHEFILENAME = "cache_singlefits.pck"


def getMassHisto(floc, selection, pairsel):
    cachekey = "%s:%s:%s" % (floc, selection, pairsel)

    try:
        with open(_CACHEFILENAME, 'r') as cachefile:
            cache = pickle.load(cachefile)
    except Exception:
        cache = {}

    masshisto = cache.get(cachekey, None)
    if masshisto:
        print ">>> Read mass histo from cache"

    else:
        print ">>> Histo not found in cache, producing from tree"
        treefile = TFile(floc, "READ")
        tree = treefile.Get('fitter_tree')

        print " >> selecting pairs with %s" % pairsel
        print " >> adding selection %s" % selection

        totalsel = '(%s)&&(%s)' % (pairsel, selection)

        masshisto = getHistoFromTree(tree, totalsel, MASSBINS, "mass",
                                     hname="h_total",
                                     weight=WEIGHT,
                                     titlex='Dilepton Mass [GeV]')
        print "  > %d entries" % masshisto.GetEntries()

        print ">>> Updating cache"
        with open(_CACHEFILENAME, 'w') as cachefile:
            cache[cachekey] = masshisto
            pickle.dump(cache, cachefile, pickle.HIGHEST_PROTOCOL)

    return masshisto


def doSingleFit(floc, selection, pairsel,
                outdir='plots', shush=True):
    os.system('mkdir -p %s' % outdir)
    if 'www' in outdir:
        putPHPIndex(outdir)

    masshisto = getMassHisto(floc, selection, pairsel)

    print '  > integral: %8.2f' % masshisto.Integral()
    ntot, toterr = getNSignalEvents(masshisto,
                                    dofit=True,
                                    odir=outdir)
    print '  > tot:  %8.1f +- %5.1f' % (ntot, toterr)


def main(args, options):
    doSingleFit(args[1], args[0],
                pairsel=options.pairsel,
                outdir=options.outDir)


if __name__ == '__main__':
    from optparse import OptionParser
    usage = "%prog [options] selection filename.root"
    parser = OptionParser(usage=usage)
    parser.add_option("--pairsel",
                      default=("((pdgId*tag_pdgId==-11*11||"
                               "pdgId*tag_pdgId==-13*13)"
                               "&&abs(mass-91.)<30.&&abs(mcMatchId)>0)"),
                      action="store", type="string", dest="pairsel",
                      help=("Pair selection "
                            "[default: %default/]"))
    parser.add_option("-o", "--outDir", default="singlefits",
                      action="store", type="string", dest="outDir",
                      help=("Output directory for single fits "
                            "[default: %default/]"))
    (options, args) = parser.parse_args()

    ws = main(args, options)
