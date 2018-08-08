import sys
from ROOT import gROOT
from ROOT import gStyle
from ROOT import gDirectory
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TGraph
from ROOT import TLegend
from ROOT import TH2F
from ROOT import TLatex

gROOT.SetBatch(1)

def contourPlot(tree, pmin, pmax, bestFit=(10.194, 1.655)):
    n = tree.Draw("mu_XS_ttH:mu_XS_tH", "%f <= quantileExpected && quantileExpected <= %f && quantileExpected != 1" % (pmin,pmax), "")
    print "Drawing for %f <= quantileExpected && quantileExpected <= %f && quantileExpected != 1 yielded %d points" % (pmin, pmax, n)
    gr = gROOT.FindObject("Graph").Clone()

    xi = gr.GetX()
    yi = gr.GetY()
    npoints = gr.GetN()
    for i in range(npoints):
       xi[i] -= bestFit[0]
       yi[i] -= bestFit[1]

    def compArg(i, j):
        return 1 if TGraph.CompareArg(gr, i, j) else -1

    sorted_points = sorted(range(npoints), cmp=compArg)
    sorted_graph = TGraph(npoints+1)
    for n,i in enumerate(sorted_points):
        sorted_graph.SetPoint(n, xi[i], yi[i])
    sorted_graph.SetPoint(npoints, xi[sorted_points[0]],
                                   yi[sorted_points[0]])

    xi_sorted = sorted_graph.GetX()
    yi_sorted = sorted_graph.GetY()

    for i in range(npoints+1):
       xi_sorted[i] += bestFit[0]
       yi_sorted[i] += bestFit[1]

    return sorted_graph


tf = TFile.Open(sys.argv[1], "READ")
tree = tf.Get("limit")

tf2 = TFile.Open(sys.argv[2], "READ")
tree68 = tf2.Get("limit")

tf3 = TFile.Open(sys.argv[3], "READ")
tree95 = tf3.Get("limit")

try:
    print "%s tree loaded from %s" % (tree.GetName(), sys.argv[1])
    print "%s tree loaded from %s" % (tree68.GetName(), sys.argv[2])
    print "%s tree loaded from %s" % (tree95.GetName(), sys.argv[3])
except AttributeError:
    print "tree not found!"
    sys.exit(-1)

gStyle.SetOptStat(0)
gStyle.SetOptTitle(0)

gr68 = contourPlot(tree68, 0.310, 1.0)
gr68.SetLineWidth(1)
gr68.SetLineStyle(1)
gr68.SetLineColor(1)
gr68.SetFillStyle(1001)
gr68.SetFillColor(82)

gr95 = contourPlot(tree95, 0.049, 1.0)
gr95.SetLineWidth(1)
gr95.SetLineStyle(7)
gr95.SetLineColor(1)
gr95.SetFillStyle(1001)
gr95.SetFillColor(89)

canv = TCanvas("canv", "canv", 800, 600)
canv.SetBottomMargin(0.10)
canv.SetLeftMargin(0.08)
canv.SetRightMargin(0.12)

tree.Draw("2*deltaNLL:mu_XS_ttH:mu_XS_tH>>hist(50,-20,42,50,-1.2,5)","2*deltaNLL<10","prof colz")

hist = gDirectory.Get("hist")
hist.GetXaxis().SetTitleFont(43)
hist.GetYaxis().SetTitleFont(43)
hist.GetXaxis().SetTitleSize(28)
hist.GetYaxis().SetTitleSize(28)
hist.GetXaxis().SetTitleOffset(0.8)
hist.GetYaxis().SetTitleOffset(0.7)
hist.GetZaxis().SetTitleOffset(0.5)
hist.GetXaxis().SetTitle("#mu_{tH}")
hist.GetYaxis().SetTitle("#mu_{t#bar{t}H}")
hist.GetZaxis().SetTitleFont(43)
hist.GetZaxis().SetTitleSize(28)
hist.GetZaxis().SetTitle("-2#Delta lnL")

print "GetCorrelationFactor: %.3f" % hist.GetCorrelationFactor()

tree.Draw("mu_XS_ttH:mu_XS_tH","quantileExpected == -1","P same")
best_fit = gROOT.FindObject("Graph").Clone()
best_fit.SetMarkerSize(2)
best_fit.SetMarkerColor(0)
best_fit.SetMarkerStyle(34)
best_fit.Draw("p same")

bf_for_leg = best_fit.Clone()
bf_for_leg.SetMarkerStyle(28)
bf_for_leg.SetMarkerColor(1)

# bf_for_leg.Draw("p same")

sm_point = TGraph(1)
sm_point.SetPoint(0, 1, 1)
sm_point.SetMarkerSize(2)
sm_point.SetLineWidth(2)
sm_point.SetMarkerStyle(29)
sm_point.Draw("p same")

gr95.Draw("L SAME")
gr68.Draw("L SAME")

# hist.Draw("AXIS SAME")

lat = TLatex()
lat.SetNDC()
lat.SetTextFont(43)
lat.SetTextSize(32)
lat.DrawLatex(0.12, 0.92, "#bf{CMS} #it{Supplementary}")
lat.SetTextSize(26)
lat.DrawLatex(0.14, 0.84, "pp #rightarrow tH+t#bar{t}H, H #rightarrow WW*/ZZ*/#tau#tau/b#bar{b}/#gamma#gamma")

leg = TLegend(0.12, 0.15, .3, .3)
leg.SetFillColor(0)
leg.SetShadowColor(0)
leg.SetLineColor(0)
leg.SetTextFont(43)
leg.SetTextSize(18)
leg.AddEntry(bf_for_leg, "Best fit", 'P')
leg.AddEntry(sm_point, "SM expected", 'P')
leg.AddEntry(gr68, "68% C.I.", 'L')
leg.AddEntry(gr95, "95% C.I.", 'L')
leg.Draw()

canv.SaveAs("nllscan_tH-vs_ttH.pdf")
canv.SaveAs("nllscan_tH-vs_ttH.png")
canv.SaveAs("nllscan_tH-vs_ttH.C")
