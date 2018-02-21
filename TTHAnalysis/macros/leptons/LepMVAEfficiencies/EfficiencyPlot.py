#!/usr/bin/env python
import ROOT
import os.path as osp

def getEfficiencyRatio(eff1, eff2, attributes_from_first=False):
    # This calculates eff1/eff2
    ratio = eff1.GetPassedHistogram().Clone("ratio")
    ratio.Sumw2()
    ratio.Divide(eff1.GetTotalHistogram())
    ratio.Multiply(eff2.GetTotalHistogram())
    ratio.Divide(eff2.GetPassedHistogram())
    # Pass on the attributes of the chosen argument
    for att in ['LineWidth', 'LineColor', 'MarkerStyle',
                'MarkerSize', 'MarkerColor']:
        if not attributes_from_first:
            getattr(ratio, 'Set%s' % att)(getattr(eff2, 'Get%s' % att)())
        else:
            getattr(ratio, 'Set%s' % att)(getattr(eff1, 'Get%s' % att)())
    return ratio


class EfficiencyPlot(object):
    """Simple class for making plots comparing TEfficiency objects"""
    def __init__(self, name):
        self.name = name
        self.effs = []
        self.effsforratio = []
        self.legentries = []
        self.plotformats = ['.pdf', '.png']
        self.xtitle = ''
        self.ytitle = 'MVA tight efficiency'
        self.tag = None
        self.tagpos = (0.92, 0.35)
        self.subtag = None
        self.subtagpos = (0.92, 0.29)

        self.colors = [ROOT.kBlack, ROOT.kAzure+1,
                       ROOT.kOrange+8, ROOT.kSpring-5]

        self.reference = None  # reference for ratios
        self.invertratio = False
        self.ratiorange = (0.75, 1.15)

    def add(self, eff, tag, includeInRatio=True):
        self.effs.append(eff)
        self.legentries.append(tag)
        if includeInRatio:
            self.effsforratio.append(eff)

    def show(self, outname, outdir):
        ROOT.gROOT.SetBatch(1)
        ROOT.gStyle.SetOptTitle(0)
        ROOT.gStyle.SetOptStat(0)

        canv = ROOT.TCanvas("canv_%s" % (self.name), "efficiencies", 800, 800)
        canv.SetRightMargin(0.05)
        canv.SetTopMargin(0.05)

        rangex = (self.effs[0].GetTotalHistogram().GetXaxis().GetXmin(),
                  self.effs[0].GetTotalHistogram().GetXaxis().GetXmax())

        axes = ROOT.TH2D("axes_%s" % (self.name), "axes",
                         1, rangex[0], rangex[1], 1, 0.0, 1.0)
        axes.GetXaxis().SetTitle(self.xtitle)
        axes.GetYaxis().SetTitleOffset(1.2)
        axes.GetYaxis().SetTitle(self.ytitle)
        axes.Draw("axis")

        leg = ROOT.TLegend(.65, .15, .89, .30+0.037*max(len(self.effs)-3, 0))

        leg.SetBorderSize(0)
        leg.SetFillColor(0)
        leg.SetFillStyle(0)
        leg.SetShadowColor(0)
        leg.SetTextFont(43)
        leg.SetTextSize(26)

        for eff, entry, color in zip(self.effs, self.legentries, self.colors):
            eff.SetLineColor(color)
            eff.SetLineWidth(2)
            eff.SetMarkerStyle(20)
            eff.SetMarkerSize(1.4)
            eff.SetMarkerColor(color)
            eff.Draw("PE same")
            leg.AddEntry(eff, entry, 'PL')
        leg.Draw()

        tlat = ROOT.TLatex()
        tlat.SetTextFont(43)
        tlat.SetNDC(1)
        tlat.SetTextAlign(33)  # right aligned
        if self.tag:
            if self.tagpos[0] < 0.50:
                # left aligned if on the left side
                tlat.SetTextAlign(13)
            tlat.SetTextSize(26)
            tlat.DrawLatex(self.tagpos[0], self.tagpos[1], self.tag)
        if self.subtag:
            tlat.SetTextAlign(33)  # right aligned
            if self.subtagpos[0] < 0.50:
                # left aligned if on the left side
                tlat.SetTextAlign(13)
            tlat.SetTextSize(22)
            tlat.DrawLatex(self.subtagpos[0], self.subtagpos[1], self.subtag)

        for ext in self.plotformats:
            canv.SaveAs(osp.join(outdir, "%s%s" % (outname, ext)))

    def show_with_ratio(self, outname, outdir):
        ROOT.gROOT.SetBatch(1)
        ROOT.gStyle.SetOptTitle(0)
        ROOT.gStyle.SetOptStat(0)

        canv = ROOT.TCanvas("canv_%s" % (self.name), "efficiencies", 600, 800)

        p2 = ROOT.TPad("pad2", "pad2", 0, 0, 1, 0.31)
        ROOT.SetOwnership(p2, False)
        p2.SetTopMargin(0)
        p2.SetBottomMargin(0.30)
        p2.SetLeftMargin(0.1)
        p2.SetRightMargin(0.03)
        p2.SetFillStyle(0)
        p2.Draw()

        p1 = ROOT.TPad("pad1", "pad1", 0, 0.31, 1, 1)
        ROOT.SetOwnership(p1, False)
        p1.SetBottomMargin(0)
        p1.SetLeftMargin(p2.GetLeftMargin())
        p1.SetRightMargin(p2.GetRightMargin())
        p1.Draw()

        # Main pad
        p1.cd()

        mainframe = self.effs[0].GetTotalHistogram().Clone('mainframe')
        mainframe.Reset('ICE')
        mainframe.GetXaxis().SetTitleFont(43)
        mainframe.GetXaxis().SetLabelFont(43)
        mainframe.GetYaxis().SetTitleFont(43)
        mainframe.GetYaxis().SetLabelFont(43)

        if not self.ytitle:
            mainframe.GetYaxis().SetTitle('Efficiency')
        else:
            mainframe.GetYaxis().SetTitle(self.ytitle)
        mainframe.GetYaxis().SetLabelSize(22)
        mainframe.GetYaxis().SetTitleSize(26)
        mainframe.GetYaxis().SetTitleOffset(1.5)

        mainframe.GetXaxis().SetTitle('')
        mainframe.GetXaxis().SetLabelSize(0)
        mainframe.GetXaxis().SetTitleSize(0)
        mainframe.GetYaxis().SetNoExponent()
        mainframe.Draw()

        # leg = ROOT.TLegend(.12,.15,.60,.30+0.037*max(len(self.effs)-3,0))
        leg = ROOT.TLegend(.35, .03, .85, .13+0.053*max(len(self.effs)-3, 0))

        leg.SetBorderSize(0)
        leg.SetFillColor(0)
        leg.SetFillStyle(0)
        leg.SetShadowColor(0)
        leg.SetTextFont(43)
        leg.SetTextSize(22)

        for eff, entry, color in zip(self.effs, self.legentries, self.colors):
            eff.SetLineColor(color)
            eff.SetLineWidth(2)
            eff.SetMarkerStyle(20)
            eff.SetMarkerSize(1.4)
            eff.SetMarkerColor(color)
            eff.Draw("PE same")
            leg.AddEntry(eff, entry, 'PL')
        leg.Draw()

        tlat = ROOT.TLatex()
        tlat.SetTextFont(43)
        tlat.SetNDC(1)
        tlat.SetTextAlign(33)  # right aligned
        if self.tag:
            if self.tagpos[0] < 0.50:
                # left aligned if on the left side
                tlat.SetTextAlign(13)
            tlat.SetTextSize(26)
            tlat.DrawLatex(self.tagpos[0], self.tagpos[1], self.tag)
        if self.subtag:
            tlat.SetTextAlign(33)  # right aligned
            if self.subtagpos[0] < 0.50:
                # left aligned if on the left side
                tlat.SetTextAlign(13)
            tlat.SetTextSize(22)
            tlat.DrawLatex(self.subtagpos[0], self.subtagpos[1], self.subtag)

        # Ratio pad
        p2.cd()

        if not self.reference:  # no reference given, take first
            self.reference = len(self.effsforratio) * [self.effs[0]]
        if len(self.reference) == 1:  # one reference (compare all to this):
            self.reference = len(self.effsforratio) * [self.reference[0]]
        assert(len(self.reference) == len(self.effsforratio))

        # Ratio axes
        ratioframe = mainframe.Clone('ratioframe')
        ratioframe.Reset('ICE')
        ratioframe.GetYaxis().SetRangeUser(0.80, 1.20)
        ratioframe.GetYaxis().SetTitle('Data/MC')
        ratioframe.GetXaxis().SetLabelSize(22)
        ratioframe.GetXaxis().SetTitleSize(32)  # 26
        ratioframe.GetYaxis().SetNdivisions(5)
        ratioframe.GetYaxis().SetNoExponent()
        ratioframe.GetYaxis().SetTitleOffset(
            mainframe.GetYaxis().GetTitleOffset())
        ratioframe.GetXaxis().SetTitleOffset(3.0)

        # Calculate ratios
        self.ratios = []
        for eff, ref in zip(self.effsforratio, self.reference):
            if self.invertratio:
                self.ratios.append(getEfficiencyRatio(ref, eff))
            else:
                self.ratios.append(getEfficiencyRatio(eff, ref, attributes_from_first=True))

        if not self.xtitle:
            ratioframe.GetXaxis().SetTitle(
                self.ratios[0].GetXaxis().GetTitle())
        else:
            ratioframe.GetXaxis().SetTitle(self.xtitle)

        if self.ratiorange:
            ratmin, ratmax = self.ratiorange
            for ratio in self.ratios:
                ratio.SetMinimum(ratmin)
                ratio.SetMaximum(ratmax)
            ratioframe.SetMinimum(ratmin)
            ratioframe.SetMaximum(ratmax)
            ratioframe.GetYaxis().SetRangeUser(ratmin, ratmax)

        ratioframe.Draw()

        line = ROOT.TLine(self.ratios[0].GetXaxis().GetXmin(), 1.0,
                          self.ratios[0].GetXaxis().GetXmax(), 1.0)
        line.SetLineColor(ROOT.kGray)
        line.Draw()

        line2 = line.Clone("grid")
        line2.SetLineStyle(3)
        line2.DrawLine(self.ratios[0].GetXaxis().GetXmin(), 1.1,
                       self.ratios[0].GetXaxis().GetXmax(), 1.1)

        line2.DrawLine(self.ratios[0].GetXaxis().GetXmin(), 0.9,
                       self.ratios[0].GetXaxis().GetXmax(), 0.9)

        for ratio in reversed(self.ratios):
            ratio.Draw("E1 same")

        for ext in self.plotformats:
            canv.SaveAs(osp.join(outdir, "%s%s" % (outname,ext)))
