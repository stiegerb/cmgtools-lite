#!/usr/bin/env python
import ROOT
ROOT.gROOT.SetBatch(True)

from math import sqrt
from os.path import dirname,basename
import os
import CMGTools.TTHAnalysis.plotter.mcPlots as mcP
from CMGTools.TTHAnalysis.plotter.mcAnalysis import MCAnalysis
from CMGTools.TTHAnalysis.plotter.tree2yield import PlotSpec

mergeMap = {
    "tHq_hww" : "tHq_hww",
    "tHq_htt" : "tHq_hww",
    "tHq_hzz" : "tHq_hww",
    "tHW_hww" : "tHW_hww",
    "tHW_htt" : "tHW_hww",
    "tHW_hzz" : "tHW_hww",
    "ttH_hww" : "ttH",
    "ttH_htt" : "ttH",
    "ttH_hzz" : "ttH",
}
RARES = ["ZZTo4L","WWW","WWZ","WZZ","ZZZ","TTTT","tZq_ll_ext_highstat","tWll"]
mergeMap.update({k:'tZq' for k in RARES})

PROC_TO_PLOTHIST = {
# processes defined for the fit, but not in the plot should take the
# colors etc. from these other processes
    'Rares'   : 'tZq',
    'tHq_htt' : 'tHq_hww',
    'tHq_hzz' : 'tHq_hww',
    'tHW_htt' : 'tHW_hww',
    'tHW_hzz' : 'tHW_hww',
    'ttH_hww' : 'ttH',
    'ttH_htt' : 'ttH',
    'ttH_hzz' : 'ttH',
}

rank = {
    'WWqq'       : 0,
    'VV'         : 0,
    'WZ'         : 1,
    'Others'     : 1,
    'ttGStar'    : 2,
    'ttG'        : 3,
    'ttZ'        : 4,
    'ttW'        : 5,
    'ttH'        : 6,
    'RareSM'     : 7,
    'QF_data'    : 8,
    'FR_data'    : 9,
    'Fakes'      : 9,
    'tHW_htt'    : 100,
    'tHW_hww'    : 101,
    'tHW_hzz'    : 102,
    'tHq_htt'    : 200,
    'tHq_hww'    : 201,
    'tHq_hzz'    : 202,
    'background' : 1001,
    'signal'     : 1002,
    'data'       : 1003
}

YAXIS_RANGE = {
    'tHq_3l_13TeV'      : (0.05, 80),
    'tHq_2lss_mm_13TeV' : (0.3, 100),
    'tHq_2lss_em_13TeV' : (0.5, 200),
    'tHq_2lss_ee_13TeV' : (0.5, 70),
}

def doTinyCmsPrelimCustom(textLeft="_default_",textRight="_default_",hasExpo=False,textSize=0.04,lumi=None, xoffs=0):
    from mcPlots import doSpam
    global options
    if textLeft  == "_default_": textLeft  = options.lspam
    if textRight == "_default_": textRight = options.rspam
    if lumi      == None       : lumi      = options.lumi
    if textLeft not in ['', None]:
        if textLeft.startswith('CMS Preliminary'):
            textLeftRight = textLeft[len('CMS Preliminary'):]
            ## new CMS Prelim style
            doSpam('CMS',         (.28 if hasExpo else .17)+xoffs,      .953, .60+xoffs,       .995, align=12, textSize=textSize, textFont=62)
            doSpam('Preliminary', (.28 if hasExpo else .17)+xoffs+0.071,.945, .60+xoffs+0.071, .995, align=12, textSize=textSize, textFont=52)
            # doSpam(textLeftRight, (.28 if hasExpo else .17)+xoffs+0.24, .953, .60+xoffs+0.28,  .995, align=12, textSize=textSize, textFont=42)
            doSpam(textLeftRight, .22, .85, .50, .89, align=12, textSize=0.05, textFont=42)
        else:
            doSpam(textLeft, (.28 if hasExpo else .17)+xoffs, .955, .60+xoffs, .995, align=12, textSize=textSize)
    if textRight not in ['', None]:
        if "%(lumi)" in textRight:
            textRight = textRight % { 'lumi':lumi }
        doSpam(textRight,.68+xoffs+0.015, .953, .99+xoffs+0.015, .995, align=32, textSize=textSize)

def doTinyCmsCustom(textLeft="_default_",textRight="_default_",hasExpo=False,textSize=0.04,lumi=None, xoffs=0):
    from mcPlots import doSpam
    global options
    if textLeft  == "_default_": textLeft  = options.lspam
    if textRight == "_default_": textRight = options.rspam
    if lumi      == None       : lumi      = options.lumi
    if textLeft not in ['', None]:
        if textLeft.startswith('CMS'):
            textLeftRight = textLeft[len('CMS'):]
            ## new CMS Prelim style
            doSpam('CMS',         (.28 if hasExpo else .17)+xoffs,      .953, .60+xoffs,       .995, align=12, textSize=textSize, textFont=62)
            # doSpam(textLeftRight, (.28 if hasExpo else .17)+xoffs+0.24, .953, .60+xoffs+0.28,  .995, align=12, textSize=textSize, textFont=42)
            doSpam(textLeftRight, .22, .85, .50, .89, align=12, textSize=0.05, textFont=42)
        else:
            doSpam(textLeft, (.28 if hasExpo else .17)+xoffs, .955, .60+xoffs, .995, align=12, textSize=textSize)
    if textRight not in ['', None]:
        if "%(lumi)" in textRight:
            textRight = textRight % { 'lumi':lumi }
        doSpam(textRight,.68+xoffs+0.015, .953, .99+xoffs+0.015, .995, align=32, textSize=textSize)

AXISLABEL = 'BDT bin'

options = None
if __name__ == "__main__":
    from optparse import OptionParser
    usage="%prog [options] mcaplot.txt mcafit.txt infile.root mlfile.root channel"
    parser = OptionParser(usage=usage)
    mcP.addPlotMakerOptions(parser)
    parser.add_option("--outDir", dest="outDir", type="string",
                      default="postFitPlots/",
                      help="Output directory for postfit plots");
    parser.add_option("--doLog", dest="doLog", action="store_true",
                      help="Do logarithmic scale plots");
    (options, args) = parser.parse_args()
    options.path = ["thqtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2_tHqsoup_v2/"]
    options.lumi = 35.9
    options.poisson = True

    # options.lspam = 'CMS'

    try: os.makedirs(options.outDir)
    except OSError: pass

    os.system("cp /afs/cern.ch/user/s/stiegerb/www/index.php "+os.path.dirname(options.outDir))

    mca_merged = MCAnalysis(args[0], options) # for the merged processes (plots)
    mca_indivi = MCAnalysis(args[1], options) # for the individual processes (fit)
    channel = {'3l': 'tHq_3l_13TeV', '2lss_mm':'tHq_2lss_mm_13TeV', '2lss_em':'tHq_2lss_em_13TeV'}[args[4]]

    var = "finalBins_40"

    if args[4] not in args[2]: # channel not in filename is suspicious
        print "WARNING"

    infile = ROOT.TFile(args[2])
    datahistname = "_data"
    hdata  = infile.Get(var+datahistname)
    try:
        hdata.GetName()
    except ReferenceError:
        raise RuntimeError("Histo %s not found in %s" % (var+datahistname, args[2]))

    ## Cosmetics
    hdata.SetMarkerSize(1.3)

    mlfile  = ROOT.TFile(args[3])

    ROOT.gROOT.ProcessLine(".x /afs/cern.ch/user/g/gpetrucc/cpp/tdrstyle.cc(0)")
    ROOT.gROOT.ForceStyle(False)
    ROOT.gStyle.SetErrorX(0.5)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetPaperSize(20.,25.)

    ymax = -1
    for MLD in ["prefit", "fit_b", "fit_s"]:
        plots  = {'data' : hdata}
        mldir  = mlfile.GetDirectory("shapes_"+MLD);
        try:
            mldirname = mldir.GetName()
        except ReferenceError:
            print "Could not find directory shapes_%s in %s" %(MLD, args[3])
            exit(-1)

        outfile = ROOT.TFile(os.path.join(options.outDir, "%s_%s.root" % (MLD, channel)), "RECREATE")

        # `processes` should be all the ones defined in the fit (i.e. the second mca)
        processes = list(reversed(mca_indivi.listBackgrounds()))
        processes += ['tHq_hww', 'tHq_htt', 'tHq_hzz',
                      'tHW_hww', 'tHW_htt', 'tHW_hzz',
                      'ttH_hww', 'ttH_htt', 'ttH_hzz']

        ## HACK
        if '2lss_mm' in channel:
            processes.remove('Convs')
            processes.remove('data_flips')

        stack = ROOT.THStack("%s_stack_%s"%(var,MLD),"")

        if options.poisson:
            pdata = mcP.getDataPoissonErrors(hdata, True, True)
            hdata.poissonGraph = pdata ## attach it so it doesn't get deleted

        for process in processes:
            # Get the pre-fit histogram (just for the color etc.)
            hist = infile.Get("%s_%s" % (var, PROC_TO_PLOTHIST.get(process, process)))
            if not hist:
                raise RuntimeError("Missing %s_%s for %s" % (var, process, process))

            hist = hist.Clone(var+"_"+process)
            hist.Reset("ICE")
            hist.SetDirectory(0)

            # Get the post-fit shape
            h_postfit = mldir.Get("%s/%s" % (channel, process))
            if not h_postfit:
                # if process not in mergeMap:
                raise RuntimeError("Could not find shape for %s/%s in dir %s of file %s" % (channel, process, mldir.GetName(), args[3]))

            # Set the bin-content and error from the post-fit
            for b in xrange(1, hist.GetNbinsX()+1):
                hist.SetBinContent(b, h_postfit.GetBinContent(b))
                hist.SetBinError(b, h_postfit.GetBinError(b))

            # Add them up to reflect the plotting mca
            pout = mergeMap.get(process, process)
            if pout in plots:
                plots[pout].Add(hist)
            else:
                plots[pout] = hist
                hist.SetName(var+"_"+pout)
                stack.Add(hist) # only add them once to the stack

        htot         = hdata.Clone(var+"_total")
        htot_postfit = mldir.Get(channel+"/total")
        hbkg         = hdata.Clone(var+"_total_background")
        hbkg_postfit = mldir.Get(channel+"/total_background")

        for b in xrange(1, hdata.GetNbinsX()+1):
            htot.SetBinContent(b, htot_postfit.GetBinContent(b))
            htot.SetBinError(  b, htot_postfit.GetBinError(b))
            hbkg.SetBinContent(b, hbkg_postfit.GetBinContent(b))
            hbkg.SetBinError(  b, hbkg_postfit.GetBinError(b))

        for hist in plots.values() + [htot]:
            outfile.WriteTObject(hist)

        if not options.doLog:
            if MLD == 'prefit':
                ymax = 1.8*max(htot.GetMaximum(), hdata.GetMaximum())
            htot.GetYaxis().SetRangeUser(0, ymax)
        else:
            htot.GetYaxis().SetRangeUser(YAXIS_RANGE.get(channel, (0.5, 100))[0],
                                         YAXIS_RANGE.get(channel, (0.5, 100))[1])


        ## Cosmetics
        htot.GetXaxis().SetTitle(AXISLABEL)
        htot.GetXaxis().SetNdivisions(510)
        htot.GetYaxis().SetNdivisions(510)
        htot.GetXaxis().SetTitleOffset(1.0)
        htot.GetYaxis().SetTitle('Events/Bin')
        htot.GetYaxis().SetTitleOffset(0.8)
        htot.GetYaxis().SetTitleSize(0.06)

        ## Prepare split screen
        c1 = ROOT.TCanvas("c1%s"%MLD, "c1", 600, 750); c1.Draw()
        c1.SetWindowSize(600 + (600 - c1.GetWw()), (750 + (750 - c1.GetWh())));
        p1 = ROOT.TPad("pad1","pad1",0,0.29,1,0.99);
        p1.SetTopMargin(0.06);
        p1.SetBottomMargin(0.06);
        p1.Draw();
        p2 = ROOT.TPad("pad2","pad2",0,0,1,0.31);
        p2.SetTopMargin(0.0);
        p2.SetBottomMargin(0.3);
        p2.SetFillStyle(0);
        p2.Draw();
        p1.cd();

        ## Draw absolute prediction in top frame
        htot.Draw("HIST")
        stack.Draw("HIST F SAME")

        hdata.poissonGraph.Draw("PZ")
        htot.Draw("AXIS SAME")

        ## Do the legend
        if options.doLog:
            mcP.doLegend(plots, mca_merged, textSize=0.042, cutoff=0.0, legWidth=0.28, corner='BL')
        else:
            mcP.doLegend(plots, mca_merged, textSize=0.042, cutoff=0.01, legWidth=0.28)

        lspam = options.lspam
        if channel == 'em':
            lspam += r"e^{#pm}#mu^{#pm} channel"
        if channel == 'mm':
            lspam += r"#mu^{#pm}#mu^{#pm} channel"
        if channel == '3l':
            lspam += "3-lepton channel"

        mcP.doTinyCmsPrelim(hasExpo = False,
                            textSize=(0.055), xoffs=-0.03,
                            textLeft = lspam, textRight = options.rspam,
                            lumi = options.lumi)

        if options.doLog:
            p1.SetLogy(True)

        ## Do the ratio plot
        ## Draw relative prediction in the bottom frame
        p2.cd()
        rdata,rnorm,rnorm2,rline = mcP.doRatioHists(PlotSpec(var,var,"",{}),plots,
                                                    htot, htot,
                                                    maxRange=options.maxRatioRange,
                                                    fitRatio=options.fitRatio,
                                                    errorsOnRef=options.errorBandOnRatio,
                                                    ratioNums=options.ratioNums,
                                                    ratioDen=options.ratioDen,
                                                    ylabel="Data/pred.",
                                                    doWide=options.wideplot,
                                                    showStatTotLegend=False)

        ## Save the plots
        c1.cd()
        for ext in ['.pdf',]:#'.png', '.C']
            c1.Print(os.path.join(options.outDir, '%s_%s%s' % (channel,MLD,ext)))
        del c1

        outfile.Close()
        ## PLOTTING DONE
        ################

        ## Save the postfit yields also
        dump = open("%s/%s_%s.txt" % (options.outDir,channel,MLD), "w")
        pyields = {
            "background" : [0,0],
            "signal"     : [0,0],
            "data"       : [plots["data"].Integral(), plots["data"].Integral()]
        }
        argset =  mlfile.Get("norm_"+MLD)

        for proc in processes:
            # pout = mergeMap[proc] if proc in mergeMap else proc
            pout = proc
            if pout not in pyields:
                pyields[pout] = [0,0]
            rvar = argset.find("%s/%s" % (channel,proc))
            if not rvar:
                print 'Did not find rvar for %s/%s' % (channel, proc)
                continue
            pyields[pout][0] += rvar.getVal()
            pyields[pout][1] += rvar.getError()**2
            if pout.startswith('tHq') or pout.startswith('tHW') or pout.startswith('ttH'):
                pyields["signal"][0] += rvar.getVal()
                pyields["signal"][1] += rvar.getError()**2
            else:
                pyields["background"][0] += rvar.getVal()
                pyields["background"][1] += rvar.getError()**2

        for p in pyields.iterkeys():
            pyields[p][1] = sqrt(pyields[p][1])

        maxlen = max([len(mca_indivi.getProcessOption(p,'Label',p))
                      for p in mca_indivi.listSignals(allProcs=True) +
                               mca_indivi.listBackgrounds(allProcs=True)]+[7])
        fmt    = "%%-%ds %%6.2f \pm %%5.2f\n" % (maxlen+1)

        all_processes =  mca_indivi.listSignals(allProcs=True)
        all_processes += mca_indivi.listBackgrounds(allProcs=True)
        all_processes += ["background","signal","data"]

        for p in sorted(all_processes, key=lambda x:rank.get(x,-1)):
            if p not in pyields: continue
            if p in ["background","data"]:
                dump.write(("-"*(maxlen+45))+"\n");
            dump.write(fmt % ( mca_indivi.getProcessOption(p,'Label',p)
                                 if p not in ["background","signal","data"] else p.upper(),
                               pyields[p][0],
                               pyields[p][1]))

        dump.close()



