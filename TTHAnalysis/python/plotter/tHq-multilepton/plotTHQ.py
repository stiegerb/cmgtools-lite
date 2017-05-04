#!/usr/bin/env python
import sys
import os
import re
from os.path import dirname,basename

from CMGTools.TTHAnalysis.plotter.tree2yield import PlotSpec
from CMGTools.TTHAnalysis.plotter.mcAnalysis import MCAnalysis
from CMGTools.TTHAnalysis.plotter.mcPlots import PlotMaker
from CMGTools.TTHAnalysis.plotter.mcPlots import PlotFile

import CMGTools.TTHAnalysis.plotter.mcPlots as mcP

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine(".x /afs/cern.ch/user/g/gpetrucc/cpp/tdrstyle.cc(0)")
ROOT.gROOT.ForceStyle(False)
ROOT.gStyle.SetErrorX(0.5)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPaperSize(20.,25.)

def doRatioHists(pspec,pmap,total,totalSyst,maxRange,fixRange=False,fitRatio=None,errorsOnRef=True,ratioNums="signal",ratioDen="background",ylabel="Data/pred.",doWide=False,showStatTotLegend=False):
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
            unity0.Draw("E2 SAME");
    else:
        if total != totalSyst and errorsOnRef:
            unity0.Draw("E2 SAME");
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
    line.SetLineWidth(2);
    line.SetLineColor(58);
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

legend_ = None
def doLegend(pmap, mca,
             corner="TR",
             textSize=0.035,
             cutoff=1e-2,
             cutoffSignals=True,
             mcStyle="F",
             legWidth=0.18,
             legBorder=True,
             signalPlotScale=None,
             totalError=None,
             header="",
             doWide=False,
             nColumns=1):
        if (corner == None): return
        total = sum([x.Integral() for x in pmap.itervalues()])
        sigEntries = []; bgEntries = []
        for p in mca.listSignals(allProcs=True):
            if mca.getProcessOption(p,'HideInLegend',False): continue
            if p in pmap and pmap[p].Integral() > (cutoff*total if cutoffSignals else 0): 
                lbl = mca.getProcessOption(p,'Label',p)
                if signalPlotScale and signalPlotScale!=1: 
                    lbl=lbl+" x "+("%d"%signalPlotScale if floor(signalPlotScale)==signalPlotScale else "%.2f"%signalPlotScale)
                myStyle = mcStyle if type(mcStyle) == str else mcStyle[0]
                sigEntries.append( (pmap[p],lbl,myStyle) )
        backgrounds = mca.listBackgrounds(allProcs=True)
        for p in backgrounds:
            if mca.getProcessOption(p,'HideInLegend',False): continue
            if p in pmap and pmap[p].Integral() >= cutoff*total: 
                lbl = mca.getProcessOption(p,'Label',p)
                myStyle = mcStyle if type(mcStyle) == str else mcStyle[1]
                bgEntries.append( (pmap[p],lbl,myStyle) )
        nentries = len(sigEntries) + len(bgEntries) + ('data' in pmap)

        nentries = nentries/nColumns

        (x1,y1,x2,y2) = (0.97-legWidth if doWide else .90-legWidth, .7 - textSize*max(nentries-3,0), .90, .91)
        if corner == "TR":
            (x1,y1,x2,y2) = (0.97-legWidth if doWide else .90-legWidth, .7 - textSize*max(nentries-3,0), .90, .91)
        elif corner == "TC":
            (x1,y1,x2,y2) = (.5, .70 - textSize*max(nentries-3,0), .5+legWidth, .91)
        elif corner == "TL":
            (x1,y1,x2,y2) = (.2, .70 - textSize*max(nentries-3,0), .2+legWidth, .91)
        elif corner == "BR":
            (x1,y1,x2,y2) = (.85-legWidth, .33 + textSize*max(nentries-3,0), .90, .15)
        elif corner == "BC":
            (x1,y1,x2,y2) = (.5, .33 + textSize*max(nentries-3,0), .5+legWidth, .15)
        elif corner == "BL":
            (x1,y1,x2,y2) = (.2, .33 + textSize*max(nentries-3,0), .2+legWidth, .15)

        leg = ROOT.TLegend(x1,y1,x2,y2)
        leg.SetNColumns(nColumns)
        if header: leg.SetHeader(header.replace("\#", "#"))
        leg.SetFillColor(0)
        leg.SetShadowColor(0)
        if header: leg.SetHeader(header.replace("\#", "#"))       
        if not legBorder:
            leg.SetLineColor(0)
        leg.SetTextFont(42)
        leg.SetTextSize(textSize)
        if 'data' in pmap: 
            leg.AddEntry(pmap['data'], mca.getProcessOption('data','Label','Data', noThrow=True), 'LPE')
        total = sum([x.Integral() for x in pmap.itervalues()])
        for (plot,label,style) in sigEntries: leg.AddEntry(plot,label,style)
        for (plot,label,style) in  bgEntries: leg.AddEntry(plot,label,style)
        if totalError: leg.AddEntry(totalError,"total bkg. unc.","F") 
        leg.Draw()
        ## assign it to a global variable so it's not deleted
        global legend_
        legend_ = leg 
        return leg

if __name__ == "__main__":
    from optparse import OptionParser
    usage="%prog [options] mca.txt plots.txt infile.root"
    parser = OptionParser(usage=usage)
    mcP.addPlotMakerOptions(parser)

    parser.add_option("--outDir", dest="outDir", type="string",
                      default="postFitPlots/",
                      help="Output directory for postfit plots");
    parser.add_option("--doLog", dest="doLog", action="store_true",
                      help="Do logarithmic scale plots");
    parser.add_option("--bkgSub", dest="bkgSub", action="store_true",
                      help="Subtract backgrounds");
    parser.add_option("--doRebinning", dest="doRebinning", action="store_true",
                      help="Remap the bins according to PR#18");
    (options, args) = parser.parse_args()
    # options.path = ["thqtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2_tHqsoup_v2/"]
    # options.lumi = 35.9
    # options.poisson = True

    try: os.makedirs(options.outDir)
    except OSError: pass

    os.system("cp /afs/cern.ch/user/s/stiegerb/www/index.php "+options.outDir)

    options.allProcesses = True # To include SkipMe=True ones

    mca = MCAnalysis(args[0], options)
    plots = PlotFile(args[1], options)
    infile = ROOT.TFile.Open(args[2], 'READ')
    print "Reading histograms from %s" % infile.GetName()

    channel = '3l'
    if '2lss_mm' in args[2] or '2lss-mm' in args[2]:
        channel = 'mm'
    if '2lss_em' in args[2] or '2lss-em' in args[2]:
        channel = 'em'

    for pspec in plots.plots():
        hists = {} # pname -> histogram
        # Check that all histos are there
        for process in mca.listProcesses(allProcs=True):
            h = infile.Get("%s_%s"%(pspec.name, process))
            if not h:
                print "ERROR: missing %s_%s in %s" % (pspec.name, process, infile.GetName())

            if process in mca.listProcesses():
                h.SetDirectory(0)
                hists[process] = h

        stack = ROOT.THStack("%s_stack_SM"%(pspec.name),"")
        for process in list(reversed(mca.listBackgrounds())) + list(reversed(mca.listSignals())):
            h = infile.Get("%s_%s"%(pspec.name, process))
            stack.Add(h)

        hbkg = infile.Get("%s_background" % pspec.name)
        htot = hbkg.Clone("%s_htot" % pspec.name)

        for process in mca.listSignals():
            hsig = infile.Get("%s_%s"%(pspec.name, process))
            htot.Add(hsig)

        # Make adjustments to histograms

        # Make canvas/pads
        c1 = ROOT.TCanvas("c1_%s"%pspec.name, "c1", 600, 750)
        c1.Draw()
        c1.SetWindowSize(600 + (600 - c1.GetWw()), (750 + (750 - c1.GetWh())))
        p1 = ROOT.TPad("pad1","pad1",0,0.29,1,0.99)
        p1.SetTopMargin(0.06)
        p1.SetBottomMargin(0.06)
        p1.Draw()
        p2 = ROOT.TPad("pad2","pad2",0,0,1,0.31)
        p2.SetTopMargin(0.06)
        p2.SetBottomMargin(0.3)
        p2.SetFillStyle(0)
        p2.Draw()
        p1.cd()

        # # Set axis ranges
        # ymax = max([hists['data'].GetBinContent(b)+hists['data'].GetBinErrorUp(b)  for b in xrange(1,hists['data'].GetNbinsX())])
        # ymin = min([hists['data'].GetBinContent(b)-hists['data'].GetBinErrorLow(b) for b in xrange(1,hists['data'].GetNbinsX())])

        # if pspec.hasOption('Logy'):
        #     htot.GetYaxis().SetRangeUser(0.01, 4*ymax)
        # else:
        #     htot.GetYaxis().SetRangeUser(0, 1.5*ymax)


        # Draw histograms
        htot.Draw("HIST")
        stack.Draw("HIST F SAME")
        totalError = mcP.doShadedUncertainty(htot)

        if options.poisson:
            pdata = mcP.getDataPoissonErrors(hists['data'], True, True)
            pdata.Draw("PZ SAME")
            hists['data'].poissonGraph = pdata ## attach it so it doesn't get deleted
        else:
            hists['data'].Draw("E SAME")
        mcP.reMax(htot, hists['data'], pspec.hasOption('Logy'), doWide=False)
        htot.Draw("AXIS SAME")

        # Do the legend
        leg = doLegend(hists, mca,
                       corner=pspec.getOption('Legend','TR'),
                       legBorder=options.legendBorder,
                       textSize=0.042,
                       totalError=None,
                       cutoff=0.01,
                       cutoffSignals=True,
                       legWidth=0.40,
                       # legWidth=0.28,
                       nColumns=2)
        leg.AddEntry(totalError, "Total uncert.","F") 

        # if channel == 'em':
        #     lspam += r"e^{#pm}#mu^{#pm} channel"
        # if channel == 'mm':
        #     lspam += r"#mu^{#pm}#mu^{#pm} channel"
        # if channel == '3l':
        #     lspam += "3-lepton channel"

        mcP.doTinyCmsPrelim(hasExpo = False,
                            textSize=(0.055), xoffs=-0.03,
                            textLeft = "#bf{CMS} #it{Preliminary}",
                            textRight = "%(lumi) (13 TeV)",
                            lumi = options.lumi)

        if pspec.hasOption('Logy'):
            p1.SetLogy(True)

        # Make the ratios
        p2.cd()
        rdata,rnorm,rnorm2,rline = doRatioHists(pspec, hists, htot, htot,
                                                maxRange=options.maxRatioRange,
                                                fixRange=options.fixRatioRange,
                                                fitRatio=options.fitRatio,
                                                errorsOnRef=options.errorBandOnRatio,
                                                ratioNums=options.ratioNums,
                                                ratioDen=options.ratioDen,
                                                ylabel="Data/Pred.",
                                                doWide=options.wideplot,
                                                showStatTotLegend=False)

        rnorm2.Delete()

        # Save the plots
        c1.cd()
        for ext in ['.pdf', '.png']:#, '.C']:
            outname = '%s_%s' % (pspec.name, channel)
            if options.doLog: outname += '_log'
            c1.Print(os.path.join(options.outDir, outname+ext))
        del c1


