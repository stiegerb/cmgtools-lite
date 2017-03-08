import sys,ROOT


def getRatiosAndBins(filename, histname='maxEtaJet25'):
    tfile = ROOT.TFile.Open(filename,'READ')

    # Get the data histogram and read the bins
    h_data = tfile.Get("%s_data"%histname)
    binedges = [float("%.3f"%h_data.GetXaxis().GetBinLowEdge(n)) for n in range(1, h_data.GetNbinsX()+2)]
    bins = zip(binedges[:-1], binedges[1:])

    # Get the MC histograms and add them up
    h_mc = h_data.Clone("%s_totalmc"%histname); h_mc.Reset("ICE")
    for hist in tfile.Get("%s_stack"%histname).GetHists():
        h_mc.Add(hist)

    # Normalize both to unit integral
    h_data.Scale(1./h_data.Integral())
    h_mc.Scale(1./h_mc.Integral())

    # Make the ratio
    h_ratio = h_data.Clone("%s_ratio"%histname); h_ratio.Reset("ICE")
    h_ratio.Add(h_data)
    h_ratio.Divide(h_mc)

    # Write out the bins and ratios
    ratios = {}
    for n,(lo,hi) in enumerate(bins):
        # print "%5.3f,%5.3f,%5.4f"%(lo,hi,h_ratio.GetBinContent(n+1))
        ratios[(lo,hi)] = h_ratio.GetBinContent(n+1)

    return ratios

ratios1 = getRatiosAndBins(sys.argv[1]) # pt 25
ratios2 = getRatiosAndBins(sys.argv[2], histname="maxEtaJet25_30") # pt 30
ratios3 = getRatiosAndBins(sys.argv[3], histname="maxEtaJet25_40") # pt 40

print 'etalo, etahi, rat 25, rat 30, rat 40'
for (lo,hi) in sorted(ratios1.keys()):
    print '%5.3f, %5.3f, %5.4f, %5.4f, %5.4f' % (lo, hi, ratios1[(lo,hi)], ratios2[(lo,hi)], ratios3[(lo,hi)])
