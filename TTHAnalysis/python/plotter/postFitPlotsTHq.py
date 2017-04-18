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

REBINMAP_3l = {7:9, 2:5, 9:7, 5:2}
REBINMAP_2l = {3:2, 2:4, 5:3, 4:8, 6:5, 9:6, 8:10, 10:9}

def doRatioHistsCustom(pspec, pmap, total, totalSyst, maxRange,
                       fixRange=False,
                       fitRatio=None,
                       errorsOnRef=True,
                       ratioNums="signal",
                       ratioDen="background",
                       ylabel="Data/pred.",
                       doWide=False,
                       showStatTotLegend=False):
    numkeys = [ "data" ]
    if "data" not in pmap: 
        if len(pmap) >= 4 and ratioDen in pmap:
            numkeys = []
            for p in pmap.iterkeys():
                for s in ratioNums.split(","):
                    if re.match(s,p): 
                        numkeys.append(p)
                        break
            if len(numkeys) == 0:
                return (None,None,None,None)
            # do this first
            total.GetXaxis().SetLabelOffset(999) ## send them away
            total.GetXaxis().SetTitleOffset(999) ## in outer space
            total.GetYaxis().SetTitleSize(0.06)
            total.GetYaxis().SetTitleOffset(0.75 if doWide else 1.48)
            total.GetYaxis().SetLabelSize(0.05)
            total.GetYaxis().SetLabelOffset(0.007)
            # then we can overwrite total with background
            numkey = 'signal'
            total     = pmap[ratioDen]
            totalSyst = pmap[ratioDen]
        else:    
            return (None,None,None,None)
    ratios = [] #None
    for numkey in numkeys:
        if hasattr(pmap[numkey], 'poissonGraph'):
            ratio = pmap[numkey].poissonGraph.Clone("data_div"); 
            for i in xrange(ratio.GetN()):
                x    = ratio.GetX()[i]
                div  = total.GetBinContent(total.GetXaxis().FindBin(x))
                ratio.SetPoint(i, x, ratio.GetY()[i]/div if div > 0 else 0)
                ratio.SetPointError(i, ratio.GetErrorXlow(i), ratio.GetErrorXhigh(i), 
                                       ratio.GetErrorYlow(i)/div  if div > 0 else 0, 
                                       ratio.GetErrorYhigh(i)/div if div > 0 else 0) 
        else:
            ratio = pmap[numkey].Clone("data_div"); 
            ratio.Divide(total)
        ratios.append(ratio)
    unity  = totalSyst.Clone("sim_div");
    unity0 = total.Clone("sim_div");
    rmin, rmax =  1,1
    for b in xrange(1,unity.GetNbinsX()+1):
        e,e0,n = unity.GetBinError(b), unity0.GetBinError(b), unity.GetBinContent(b)
        unity.SetBinContent(b, 1 if n > 0 else 0)
        unity0.SetBinContent(b,  1 if n > 0 else 0)
        if errorsOnRef:
            unity.SetBinError(b, e/n if n > 0 else 0)
            unity0.SetBinError(b, e0/n if n > 0 else 0)
        else:
            unity.SetBinError(b, 0)
            unity0.SetBinError(b, 0)
        rmin = min([ rmin, 1-2*e/n if n > 0 else 1])
        rmax = max([ rmax, 1+2*e/n if n > 0 else 1])
    for ratio in ratios:
        if ratio.ClassName() != "TGraphAsymmErrors":
            for b in xrange(1,unity.GetNbinsX()+1):
                if ratio.GetBinContent(b) == 0: continue
                rmin = min([ rmin, ratio.GetBinContent(b) - 2*ratio.GetBinError(b) ]) 
                rmax = max([ rmax, ratio.GetBinContent(b) + 2*ratio.GetBinError(b) ])  
        else:
            for i in xrange(ratio.GetN()):
                rmin = min([ rmin, ratio.GetY()[i] - 2*ratio.GetErrorYlow(i)  ]) 
                rmax = max([ rmax, ratio.GetY()[i] + 2*ratio.GetErrorYhigh(i) ])  
    if rmin < maxRange[0] or fixRange: rmin = maxRange[0]; 
    if rmax > maxRange[1] or fixRange: rmax = maxRange[1];
    if (rmax > 3 and rmax <= 3.4): rmax = 3.4
    if (rmax > 2 and rmax <= 2.4): rmax = 2.4
    unity.SetFillStyle(1001);
    unity.SetFillColor(ROOT.kCyan);
    unity.SetMarkerStyle(1);
    unity.SetMarkerColor(ROOT.kCyan);
    unity0.SetFillStyle(1001);
    unity0.SetFillColor(ROOT.kBlue-7);
    unity0.SetMarkerStyle(1);
    unity0.SetMarkerColor(ROOT.kBlue-7);
    ROOT.gStyle.SetErrorX(0.5);
    if errorsOnRef:
        unity.Draw("E2");
    else:
        unity.Draw("AXIS");
    if fitRatio != None and len(ratios) == 1:
        from CMGTools.TTHAnalysis.tools.plotDecorations import fitTGraph
        fitTGraph(ratio,order=fitRatio)
        unity.SetFillStyle(3013);
        unity0.SetFillStyle(3013);
        if errorsOnRef:
            unity.Draw("AXIS SAME");
            # unity0.Draw("E2 SAME");
    # else:
    #     if total != totalSyst and errorsOnRef:
    #         unity0.Draw("E2 SAME");
    rmin = float(pspec.getOption("RMin",rmin))
    rmax = float(pspec.getOption("RMax",rmax))
    unity.GetYaxis().SetRangeUser(rmin,rmax);
    unity.GetXaxis().SetTitleFont(42)
    unity.GetXaxis().SetTitleSize(0.14)
    unity.GetXaxis().SetTitleOffset(0.9)
    unity.GetXaxis().SetLabelFont(42)
    unity.GetXaxis().SetLabelSize(0.1)
    unity.GetXaxis().SetLabelOffset(0.007)
    unity.GetYaxis().SetNdivisions(505)
    unity.GetYaxis().SetTitleFont(42)
    unity.GetYaxis().SetTitleSize(0.14)
    offset = 0.32 if doWide else 0.62
    unity.GetYaxis().SetTitleOffset(offset)
    unity.GetYaxis().SetLabelFont(42)
    unity.GetYaxis().SetLabelSize(0.11)
    unity.GetYaxis().SetLabelOffset(0.007)
    unity.GetYaxis().SetDecimals(True) 
    unity.GetYaxis().SetTitle(ylabel)
    total.GetXaxis().SetLabelOffset(999) ## send them away
    total.GetXaxis().SetTitleOffset(999) ## in outer space
    total.GetYaxis().SetTitleSize(0.06)
    total.GetYaxis().SetTitleOffset(0.75 if doWide else 1.48)
    total.GetYaxis().SetLabelSize(0.05)
    total.GetYaxis().SetLabelOffset(0.007)
    binlabels = pspec.getOption("xBinLabels","")
    if binlabels != "" and len(binlabels.split(",")) == unity.GetNbinsX():
        blist = binlabels.split(",")
        for i in range(1,unity.GetNbinsX()+1): 
            unity.GetXaxis().SetBinLabel(i,blist[i-1]) 
        unity.GetXaxis().SetLabelSize(0.15)
    #ratio.SetMarkerSize(0.7*ratio.GetMarkerSize()) # no it is confusing
    binlabels = pspec.getOption("xBinLabels","")
    if binlabels != "" and len(binlabels.split(",")) == unity.GetNbinsX():
        blist = binlabels.split(",")
        for i in range(1,unity.GetNbinsX()+1): 
            unity.GetXaxis().SetBinLabel(i,blist[i-1]) 
    #$ROOT.gStyle.SetErrorX(0.0);
    line = ROOT.TLine(unity.GetXaxis().GetXmin(),1,unity.GetXaxis().GetXmax(),1)
    line.SetLineWidth(1);
    line.SetLineColor(1);
    line.Draw("L")
    for ratio in ratios:
        ratio.Draw("E SAME" if ratio.ClassName() != "TGraphAsymmErrors" else "PZ SAME");
    leg0 = ROOT.TLegend(0.12 if doWide else 0.2, 0.8, 0.25 if doWide else 0.45, 0.9)
    leg0.SetFillColor(0)
    leg0.SetShadowColor(0)
    leg0.SetLineColor(0)
    leg0.SetTextFont(42)
    leg0.SetTextSize(0.035*0.7/0.3)
    leg0.AddEntry(unity0, "stat. bkg. unc.", "F")
    if showStatTotLegend: leg0.Draw()
    leg1 = ROOT.TLegend(0.25 if doWide else 0.45, 0.8, 0.38 if doWide else 0.7, 0.9)
    leg1.SetFillColor(0)
    leg1.SetShadowColor(0)
    leg1.SetLineColor(0)
    leg1.SetTextFont(42)
    leg1.SetTextSize(0.035*0.7/0.3)
    leg1.AddEntry(unity, "total bkg. unc.", "F")
    if showStatTotLegend: leg1.Draw()
    global legendratio0_, legendratio1_
    legendratio0_ = leg0
    legendratio1_ = leg1
    return (ratios, unity, unity0, line)

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
    parser.add_option("--doRebinning", dest="doRebinning", action="store_true",
                      help="Remap the bins according to PR#18");
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
    rebinmap = REBINMAP_3l if '3l' in channel else REBINMAP_2l

    var = "finalBins_40"

    if args[4].rsplit('_',1)[0] not in args[2]: # channel not in filename is suspicious
        print "WARNING"

    infile = ROOT.TFile(args[2])
    datahistname = "_data"
    hdata  = infile.Get(var+datahistname)
    try:
        hdata.GetName()
    except ReferenceError:
        raise RuntimeError("Histo %s not found in %s" % (var+datahistname, args[2]))

    hdata_rebinned = hdata.Clone("%s_rebinned"%hdata.GetName())
    hdata_rebinned.Reset("ICE")
    for b in xrange(1, hdata.GetNbinsX()+1):
        hdata_rebinned.SetBinContent(rebinmap.get(b,b), hdata.GetBinContent(b))
        hdata_rebinned.SetBinError(rebinmap.get(b,b), hdata.GetBinError(b))
    hdata = hdata_rebinned

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
                hist.SetBinContent(rebinmap.get(b,b), h_postfit.GetBinContent(b))
                hist.SetBinError(rebinmap.get(b,b), h_postfit.GetBinError(b))

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
            htot.SetBinContent(rebinmap.get(b,b), htot_postfit.GetBinContent(b))
            htot.SetBinError(  rebinmap.get(b,b), htot_postfit.GetBinError(b))
            hbkg.SetBinContent(rebinmap.get(b,b), hbkg_postfit.GetBinContent(b))
            hbkg.SetBinError(  rebinmap.get(b,b), hbkg_postfit.GetBinError(b))

        for hist in plots.values() + [htot]:
            outfile.WriteTObject(hist)

        if not options.doLog:
            if MLD == 'prefit':
                ymax = 1.2*max(htot.GetMaximum(), hdata.GetMaximum())
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
        totalError = mcP.doShadedUncertainty(htot)

        hdata.poissonGraph.Draw("PZ")
        htot.Draw("AXIS SAME")

        ## Do the legend
        leg = None
        if options.doLog:
            leg = mcP.doLegend(plots, mca_merged,
                               textSize=0.042,
                               totalError=None,
                               cutoff=0.0,
                               legWidth=0.28,
                               corner='BL')
        else:
            leg = mcP.doLegend(plots, mca_merged,
                               textSize=0.042,
                               totalError=None,
                               cutoff=0.01,
                               legWidth=0.28)
        leg.AddEntry(totalError, "Total uncert.","F") 
        
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
        rdata,rnorm,rnorm2,rline = doRatioHistsCustom(PlotSpec(var,var,"",{}),
                                                      plots, htot, htot,
                                                      maxRange=options.maxRatioRange,
                                                      fixRange=options.fixRatioRange,
                                                      fitRatio=options.fitRatio,
                                                      errorsOnRef=options.errorBandOnRatio,
                                                      ratioNums=options.ratioNums,
                                                      ratioDen=options.ratioDen,
                                                      ylabel="Data/pred.",
                                                      doWide=options.wideplot,
                                                      showStatTotLegend=False)
        rnorm2.Delete()

        ## Save the plots
        c1.cd()
        for ext in ['.pdf',]:#'.png', '.C']
            outname = '%s_%s%s' % (channel,MLD,ext)
            if options.doLog:
                outname = '%s_%s_log%s' % (channel,MLD,ext)
            c1.Print(os.path.join(options.outDir, outname))
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
            pout = mergeMap.get(proc, proc)
            if pout not in pyields:
                pyields[pout] = (0,0)
            rvar = argset.find("%s/%s" % (channel,proc))
            if not rvar:
                print 'Did not find rvar for %s/%s' % (channel, proc)
                continue
            pyields[pout] = ( pyields[pout][0] + rvar.getVal(),
                              pyields[pout][1] + rvar.getError()**2 ) 
            if pout.startswith('tHq') or pout.startswith('tHW') or pout.startswith('ttH'):
                pyields["signal"] = ( pyields[pout][0] + rvar.getVal(),
                                      pyields[pout][1] + rvar.getError()**2 ) 
            else:
                pyields["background"] = ( pyields[pout][0] + rvar.getVal(),
                                          pyields[pout][1] + rvar.getError()**2 ) 

        for p in pyields.iterkeys():
            pyields[p] = (pyields[p][0], sqrt(pyields[p][1]))

        maxlen = max([len(mca_indivi.getProcessOption(p,'Label',p))
                      for p in mca_indivi.listSignals(allProcs=True) +
                               mca_indivi.listBackgrounds(allProcs=True)]+[7])
        fmt    = "%%-%ds %%6.2f \pm %%5.2f\n" % (maxlen+1)

        all_processes =  mca_indivi.listSignals(allProcs=True)
        all_processes += mca_indivi.listBackgrounds(allProcs=True)
        all_processes += ["background","signal","data"]

        for p in sorted(all_processes+list(set(mergeMap.values())), key=lambda x:rank.get(x,-1)):
            if p not in pyields: continue
            if p in ["background", "data"]:
                dump.write(("-"*(maxlen+45))+"\n");
            label = p.upper()
            try:
                label = mca_indivi.getProcessOption(p,'Label',p)
            except RuntimeError: pass
            dump.write(fmt % ( label, pyields[p][0], pyields[p][1]))

        dump.close()



