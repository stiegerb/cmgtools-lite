#!/usr/bin/env python
"""
makeLepTnPFriends.py
"""

import sys, os, pickle
import ROOT

from ROOT import TEfficiency
import os.path as osp

from multiprocessing import Manager, Pool
from array import array

from EfficiencyPlot import EfficiencyPlot
from EfficiencyPlot import getEfficiencyRatio

from helpers import projectFromTree
from helpers import getHistoFromTree
from helpers import putPHPIndexInAllSubdirs

from fitting import getNSignalEvents

LUMI = 36.5 ## FIXME
WEIGHT = "puWeight"
PAIRSEL = ("((pdgId*tag_pdgId==-11*11||pdgId*tag_pdgId==-13*13)"
           "&&abs(mass-91.)<30.&&abs(mcMatchId)>0)")
SELECTIONS = {
    'inclusive':               PAIRSEL,
    # mcMatchId is never ==1 for MC but always for data
    # 'runs (<= 275125)':        PAIRSEL+"&&(mcMatchId==1&&run<=275125)",
    # 'runs (>275125 <=275783)': PAIRSEL+"&&(mcMatchId==1&&run>275125&&run<=275783)",
    # 'runs (>275783 <=276384)': PAIRSEL+"&&(mcMatchId==1&&run>275783&&run<=276384)",
    # 'runs (>276384 <=276811)': PAIRSEL+"&&(mcMatchId==1&&run>276384&&run<=276811)",
    # 'singleTriggers': PAIRSEL+"&&passSingle",
    # 'doubleTriggers': PAIRSEL+"&&passDouble",
    # 'ttbar': "( (pdgId*tag_pdgId==-11*13)||"
    #           "  ( (pdgId*tag_pdgId==-11*11||pdgId*tag_pdgId==-13*13)"
    #           "&&abs(mass-91.)>15.&&met_pt>30.) )"
    #           "&&passDouble&&nJet25>=2&&nBJetLoose25>=2"
    #           "&&tag_pt>30&&abs(tag_mcMatchId)>0",
    # 'ttH'  : "abs(mcMatchId)>0&&passDouble",
}

LEPSEL = [
    ('eb', 'abs(pdgId)==11&&abseta<1.479',
           'Electrons Barrel (#eta < 1.479)'),
    ('ee', 'abs(pdgId)==11&&abseta>=1.479',
           'Electrons Endcap (#eta #geq 1.479)'),
    ('mb', 'abs(pdgId)==13&&abseta<1.2',
           'Muons Barrel (#eta < 1.2)'),
    ('me', 'abs(pdgId)==13&&abseta>=1.2',
           'Muons Endcap (#eta #geq 1.2)'),
]
## Eta binning for 2d plots:
LEPSEL2D = []
ETABINS2D_EL = [0,0.74,1.479,2.0,2.5]
for n in range(len(ETABINS2D_EL)-1):
    LEPSEL2D.append(('e%d'%n,
                   'abs(pdgId)==11&&abseta>={elo}&&abseta<{ehi}'.format(
                       elo=ETABINS2D_EL[n], ehi=ETABINS2D_EL[n+1]),
                   'Electrons {elo} #leq |#eta| < {ehi}'.format(
                       elo=ETABINS2D_EL[n], ehi=ETABINS2D_EL[n+1]) ) )

ETABINS2D_MU = [0,0.4,0.8,1.2,1.8,2.5]
for n in range(len(ETABINS2D_MU)-1):
    LEPSEL2D.append(('m%d'%n,
                   'abs(pdgId)==13&&abseta>={elo}&&abseta<{ehi}'.format(
                       elo=ETABINS2D_MU[n], ehi=ETABINS2D_MU[n+1]),
                   'Muons {elo} #leq |#eta| < {ehi}'.format(
                       elo=ETABINS2D_MU[n], ehi=ETABINS2D_MU[n+1]) ) )
LEPSEL.extend(LEPSEL2D)

MASSBINS  = range(61,122,1)
PTBINS    = [10.,15.,20.,25.,30.,37.5,45.,60.,80.,100.]
ETABINS   = [0.,0.25,0.50,0.75,1.00,1.25,1.50,2.00,2.50]
NVERTBINS = [0,4,7,8,9,10,11,12,13,14,15,16,17,19,22,25,30]
NJETBINS  = [0,1,2,3,4,5,6]
NBJETBINS = [0,1,2,3]
BINNINGS = [
    ('pt',            PTBINS,    'p_{T} [GeV]'),
    ('nVert',         NVERTBINS, 'N_{vertices}'),
#    ('nJet25',        NJETBINS,  'N_{jets}'),
#    ('nBJetMedium25', NBJETBINS, 'N_{bjets, CSVM}'),
]

DENOMINATOR = "passLoose" # or passFO?
NUMERATORS  = [
    ('2lss',"passTight&&passTCharge", 'same-sign 2 lepton definition'),
    # ('3l',  "passTight", '3 lepton definition'),
]

INPUTS = {
    'data':[
        "Run2017",
        ],
    'DY':[
        "DYJetsToLL_M50_LO_part1_treeProducerSusyMultilepton_tree",
        "DYJetsToLL_M50_LO_part2_treeProducerSusyMultilepton_tree",
        "DYJetsToLL_M50_LO_part3_treeProducerSusyMultilepton_tree",
        ],
    # 'ttbar':[
    #     "TTJets_DiLepton",
    #     "TTJets_SingleLeptonFromTbar_ext",
    #     "TTJets_SingleLeptonFromTbar",
    #     "TTJets_SingleLeptonFromT_ext",
    #     "TTJets_SingleLeptonFromT",
    #     ],
    # 'ttH':["TTHnobb"],
}

_PASSTOTALCACHE = "tnppassedtotal.pck"
_MASSHISTOCACHE = "masshistos.pck"

def getPassTotalHistosBinned((key, output,
                        tag, floc, pairsel,
                        probnum, probdenom, var, bins,
                        options)):
    totalsel  = '(%s)&&(%s)' % (pairsel, probdenom)
    passedsel = '(%s)&&(%s)' % (pairsel, probnum)

    bincut = "({var}>={binlo}&&{var}<{binhi})"
    binsels = []
    for nbin in xrange(len(bins)-1):
        binlo, binhi = bins[nbin], bins[nbin+1]
        binsels.append(bincut.format(var=var,binlo=binlo,binhi=binhi))

    treefile = ROOT.TFile(floc,"READ")
    tree = treefile.Get('fitter_tree')

    htemp = getHistoFromTree(tree,"0",bins,var,hname="htemp_%s"%(var))
    htemp.Reset("ICE")

    hpassed = htemp.Clone("%s_passed"%var)
    hpassed.SetDirectory(0)
    htotal = htemp.Clone("%s_total"%var)
    htotal.SetDirectory(0)

    plotDir = osp.join(options.outDir, 'tnpfits', *tuple(tag.split('_')))
    proc = tag.split('_',1)[0]
    dofit = [proc in ['data','DY']] and not options.cutNCount

    try:
        with open(_MASSHISTOCACHE, 'r') as cachefile:
            cache = pickle.load(cachefile)
            print " reading mass histos from cache"
    except Exception:
        cache = {}

    for n,binsel in enumerate(binsels):
        print "  ... processing %-36s" % binsel,

        totalbinsel = "%s&&%s" % (totalsel, binsel)
        htotalbin = cache.get((floc, totalbinsel), None)
        if not htotalbin:
            htotalbin = getHistoFromTree(tree,totalbinsel,MASSBINS,"mass",
                                         hname="%s_total_%d"%(var,n),
                                         weight=WEIGHT,
                                         titlex='Dilepton Mass [GeV]')
            with open(_MASSHISTOCACHE, 'w') as cachefile:
                cache[(floc, totalbinsel)] = htotalbin
                pickle.dump(cache, cachefile, pickle.HIGHEST_PROTOCOL)

        passedbinsel = "%s&&%s" % (passedsel, binsel)
        hpassedbin = cache.get((floc, passedbinsel), None)
        if not hpassedbin:
            hpassedbin = getHistoFromTree(tree,passedbinsel,MASSBINS,"mass",
                                          hname="%s_passed_%d"%(var,n),
                                          weight=WEIGHT,
                                          titlex='Dilepton Mass [GeV]')
            with open(_MASSHISTOCACHE, 'w') as cachefile:
                cache[(floc, passedbinsel)] = hpassedbin
                pickle.dump(cache, cachefile, pickle.HIGHEST_PROTOCOL)

        npass,passerr = getNSignalEvents(hpassedbin,
                                         dofit=dofit,
                                         odir=plotDir)
        ntot,toterr   = getNSignalEvents(htotalbin,
                                         dofit=dofit,
                                         odir=plotDir)
        print 'pass: %8.1f +- %5.1f' % (npass,passerr),
        print 'tot:  %8.1f +- %5.1f' % (ntot,toterr),

        # Some cheating (i.e. taking cut&count in some cases):
        #  npass > ntot (can only happen if the fit goes wrong)
        #  for the threshold bin containing pT of 50 GeV
        if npass > ntot or (50.>=bins[n] and 50.<bins[n+1]):
            print "CHEATING"
            npass,passerr = getNSignalEvents(hpassedbin,dofit=False)
            ntot,toterr   = getNSignalEvents(htotalbin, dofit=False)

        hpassed.SetBinContent(n+1, npass)
        hpassed.SetBinError(n+1, passerr)
        htotal.SetBinContent(n+1, ntot)
        htotal.SetBinError(n+1, toterr)
        print "DONE"

    output[key] = (hpassed, htotal)

def getPassTotalHistosSimple((key, output,
                              tag, floc, pairsel,
                              probnum, probdenom, var, bins,
                              options)):
    totalsel  = '(%s)&&(%s)' % (pairsel, probdenom)
    passedsel = '(%s)&&(%s)' % (pairsel, probnum)

    treefile = ROOT.TFile(floc,"READ")
    tree = treefile.Get('fitter_tree')

    htotal = getHistoFromTree(tree,totalsel,bins,var,
                               hname="%s_total_simple_%s"%(var,tag),
                               weight=WEIGHT)
    hpassed = getHistoFromTree(tree,passedsel,bins,var,
                               hname="%s_passed_simple_%s"%(var,tag),
                               weight=WEIGHT)

    output[key] = (hpassed, htotal)

def makePassedFailed(proc,fnames,indir,
                     options, stump='.root'):

    try:
        with open('.xsecweights.pck', 'r') as cachefile:
            xsecweights = pickle.load(cachefile)
            print '>>> Read xsecweights from cache (.xsecweights.pck)'
    except IOError:
        print ("Please run makeXSecWeights.py first to apply "
               "cross section weights.")
        xsecweights = {}

    result = {}

    pool = None
    if options.jobs>1:
        pool = Pool(options.jobs)

    for pname in fnames:
        floc = osp.join(indir, "%s%s"%(pname,stump))
        if not osp.isfile(floc):
            print "Missing file: %s" % floc
            raw_input(" ... press key to continuing without")
            continue

        print '... processing', pname
        if proc != 'data':
            weight = LUMI*xsecweights.get(pname, 1.0/LUMI)
            print '    weighting histos by', weight
        else: weight = 1.0

        tasks = []    # do the fit for these
        tasks_cc = [] # do cut & count for these

        if pool:
            manager = Manager()
            result_dict = manager.dict()
        else:
            result_dict = {}

        for lep,lepsel,_ in LEPSEL:
            for sname,sel in SELECTIONS.iteritems():
                if sname == 'ttH' and proc != 'ttH': continue
                if sname.startswith('runs') and proc != 'data': continue
                finalsel = '(%s)&&(%s)' % (lepsel, sel)
                for nname,num,_ in NUMERATORS:
                    for var,bins,_ in BINNINGS:

                        # Some special cases:
                        # Skip eta binnings for non pt vars
                        if (not lep in ['eb','ee','mb','me'] and
                            var != 'pt'): continue

                        # Cut at pt>30 for njet and nbjet binnings
                        if 'Jet' in var: fsel = finalsel+'&&pt>30'
                        else: fsel = finalsel

                        tag = '_'.join([proc, lep, nname, var])
                        key = (lep,sname,nname,var)

                        task = (key, result_dict, tag, floc, fsel, num,
                                DENOMINATOR, var, bins, options)

                        if proc not in ['DY', 'data']:
                            tasks_cc.append(task)
                        else:
                            tasks.append(task)


        print 'Have %d tasks to process' % (len(tasks)+len(tasks_cc))

        if pool:
            pool.map(getPassTotalHistosBinned, tasks)
            pool.map(getPassTotalHistosSimple, tasks_cc)
        else:
            map(getPassTotalHistosBinned, tasks)
            map(getPassTotalHistosSimple, tasks_cc)

        for key in [t[0] for t in tasks+tasks_cc]:
            hpass, htot = result_dict[key]

            hpass.Scale(weight)
            htot.Scale(weight)

            if key in result:
                result[key][0].Add(hpass)
                result[key][1].Add(htot)
            else:
                result[key] = (hpass,htot)

        print '      %s done' % pname

    if pool:
        pool.close()
        pool.join()

    return result

def makeEfficiencies(passedtotal):
    result = {}

    # Calculate raw efficiencies
    for proc, histos in passedtotal.iteritems():
        proc_effs = {}
        for key,(p,f) in histos.iteritems():
            eff = TEfficiency(p, f)
            proc_effs[key] = eff
        result[proc] = proc_effs

    # # Calculate background corrected efficiencies
    # # I.e. subtract ttbar MC from data
    # for key in passedtotal.values()[0].keys():
    #     print '... processing', key
    #     passdata,totdata = passedtotal['data'][key]
    #     passtt,  tottt   = passedtotal['ttbar'][key]

    #     pcorr = passdata.Clone("pass_corrected")
    #     fcorr = totdata.Clone("tot_corrected")
    #     pcorr.Add(passtt, -1.0)
    #     fcorr.Add(tottt, -1.0)
    #     result.setdefault('data_corr', {})[key] = TEfficiency(pcorr, fcorr)

    return result

def makePlots(efficiencies, options):
    for lep,_,lname in LEPSEL:
        for nname,_,ntitle in NUMERATORS:
            for var,bins,xtitle in BINNINGS:

                if not lep in ['ee','eb','mb','me']: continue

                # Compare data/MC for each binning
                plot = EfficiencyPlot('%s_%s_%s'%(lep,nname,var))
                plot.xtitle = xtitle
                plot.tag = '%s'%(lname)
                plot.subtag = '%s'%(ntitle)
                plot.colors = [ROOT.kBlack,
                               ROOT.kAzure+1,
                               ROOT.kGreen+3,
                               ROOT.kGreen-2,
                               ROOT.kGreen-6,
                               ROOT.kGreen-9
                               ]
                # plot.colors = [ROOT.kBlack,  ROOT.kAzure+1,
                #                ROOT.kGray+1, ROOT.kSpring-8,
                #                ROOT.kPink+9]

                plot.tagpos = (0.92,0.35+0.1)
                plot.subtagpos = (0.92,0.29+0.1)
                if lep == 'ee':
                    plot.tagpos = (0.92,0.85)
                    plot.subtagpos = (0.92,0.79)


                if 'Jet' in var:
                    plot.subtag = '%s, p_{T} > 30 GeV' % ntitle

                plot.reference = [efficiencies['DY'][(lep,'inclusive',nname,var)]]

                fitlabel = 'Z mass fit' if not options.cutNCount else 'cut & count'

                plot.add(efficiencies['data'][(lep,'inclusive',nname,var)],
                         'Data (%.2f fb^{-1}), %s' % (LUMI, fitlabel),
                         includeInRatio=True)
                plot.add(efficiencies['DY'][(lep,'inclusive',nname,var)],
                         'DY MC, %s' % fitlabel,
                         includeInRatio=False)

                for selname in SELECTIONS.keys():
                    if selname == 'inclusive': continue
                    plot.add(efficiencies['data'][(lep, selname, nname, var)],
                         'Data %s'%selname, includeInRatio=True)

                # plot.add(efficiencies['data'][(lep,'ttbar',nname,var)],
                #          'Data, t#bar{t} dilepton, cut & count',
                #          includeInRatio=False)
                # plot.add(efficiencies['ttbar'][(lep,'ttbar',nname,var)],
                #          't#bar{t} MC, t#bar{t} dilepton, cut & count',
                #          includeInRatio=True)
                # plot.add(efficiencies['ttH'][(lep,'ttH',nname,var)],
                #          't#bar{t}H MC, inclusive',
                #          includeInRatio=False)

                # plot.reference = [plot.effs[0], plot.effs[1]]
                # plot.reference = [plot.effs[0], plot.effs[2]]

                plot.show_with_ratio('tnp_eff_%s'%(plot.name),
                                      options.outDir)

def make2DMap(efficiencies, options):
    outdir = osp.join(options.outDir, 'map')
    os.system('mkdir -p %s'%outdir)

    sfhistos = {}

    for nname,_,ntitle in NUMERATORS:
        for lepton in ['e', 'm']:
            # Make data/MC plots
            for lep,_,lname in LEPSEL2D:
                if not lep.startswith(lepton): continue

                plot = EfficiencyPlot('%s_%s_%s'%(lep,nname,'pt'))
                plot.xtitle = 'p_{T} [GeV]'
                plot.tag = '%s'%(lname)
                plot.subtag = '%s'%(ntitle)

                plot.add(efficiencies['data'][(lep,'inclusive',nname,'pt')],
                         'Data, Z mass fit', includeInRatio=False)
                plot.add(efficiencies['DY'][(lep,'inclusive',nname,'pt')],
                         'DY MC, Z mass fit', includeInRatio=True)

                plot.reference = [plot.effs[0]]

                plot.show_with_ratio('tnp_eff_%s'%(plot.name),outdir)

            ## Make the 2D histograms
            etabins = {'e': ETABINS2D_EL, 'm': ETABINS2D_MU}[lepton]
            sfhisto_2d = ROOT.TH2F("sf_%s"%lepton,
                                   "mva tight data/mc scale factors",
                                   len(PTBINS)-1, array('d', PTBINS),
                                   len(etabins)-1, array('d', etabins))
            sfhisto_2d.SetName('%s_%s'%(lepton, nname))
            sfhisto_2d.SetDirectory(0)

            for ny in range(len(etabins)-1):
                lep = '%s%d' % (lepton, ny)

                # each of these is binned in pt:
                sfhisto = getEfficiencyRatio(
                    efficiencies['data'][(lep,'inclusive',nname,'pt')],
                    efficiencies['DY']  [(lep,'inclusive',nname,'pt')])

                for nx in range(len(PTBINS)):
                    sfhisto_2d.SetBinContent(nx+1, ny+1,
                                             sfhisto.GetBinContent(nx+1))
                    sfhisto_2d.SetBinError(nx+1, ny+1,
                                             sfhisto.GetBinError(nx+1))

            sfhistos[(lepton,nname)] = sfhisto_2d

    for (lepton,nname),histo in sfhistos.iteritems():
        fname = 'lepMVAEffSF_%s_%s.root' % (lepton, nname)
        floc = osp.join(options.outDir,fname)
        ofile = ROOT.TFile(floc, 'RECREATE')
        ofile.cd()
        histo.Write('sf')
        ofile.Write()
        ofile.Close()
        print " wrote %s" % floc

def main(args, options):
    try:
        if not osp.exists(args[0]):
            print "Input directory does not exists: %s" % args[0]
            sys.exit(-1)
    except IndexError:
        parser.print_usage()
        sys.exit(-1)

    # Gather all the passed/total histograms
    if not osp.isfile(_PASSTOTALCACHE):
        passedtotal = {}
        for proc,fnames in INPUTS.iteritems():
            passedtotal[proc] = makePassedFailed(proc,fnames,args[0],options,stump='.root')

        print "#"*30
        print "ALL DONE"
        print "#"*30

        with open(_PASSTOTALCACHE, 'w') as cachefile:
            pickle.dump(passedtotal, cachefile, pickle.HIGHEST_PROTOCOL)
            print ('>>> Wrote tnp passed total histograms to cache (%s)' %
                                                        _PASSTOTALCACHE)
    else:
        with open(_PASSTOTALCACHE, 'r') as cachefile:
            passedtotal = pickle.load(cachefile)
            print ('>>> Read tnp passed total histograms from cache (%s)' %
                                                        _PASSTOTALCACHE)

    os.system('mkdir -p %s'%options.outDir)
    if 'www' in options.outDir:
        putPHPIndexInAllSubdirs(options.outDir)

    # Calculate efficiencies
    efficiencies = makeEfficiencies(passedtotal)

    # Make plots
    makePlots(efficiencies, options)
    make2DMap(efficiencies, options)


if __name__ == '__main__':
    from optparse import OptionParser
    usage = "%prog [options] tnptrees/"
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--outDir", default="tnp_effs",
                      action="store", type="string", dest="outDir",
                      help=("Output directory for eff plots "
                            "[default: %default/]"))
    parser.add_option('-c', '--cutNCount', dest='cutNCount',
                      action="store_true",
                      help='Do cut & count instead of fitting mass shape')
    parser.add_option('-j', '--jobs', dest='jobs', action="store",
                      type='int', default=1,
                      help=('Number of jobs to run in parallel '
                        '[default: single]'))
    (options, args) = parser.parse_args()

    main(args, options)

