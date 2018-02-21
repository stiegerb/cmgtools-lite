#!/usr/bin/env python
import os
import ROOT

from helpers import putPHPIndex


def shushRooFit():
    "Make RooFit shut up"
    msgSI = ROOT.RooMsgService.instance()
    msgSI.setSilentMode(True)
    for s in [0, 1]:
        for t in ['Eval',
                  'NumIntegration',
                  'DataHandling',
                  'ObjectHandling',
                  'Minimization',
                  'Fitting',
                  'Plotting',
                  'InputArguments',
                  'Caching']:
            msgSI.getStream(s).removeTopic(getattr(ROOT.RooFit, t))


def shapeCBBreitWigner(ws):
    ws.factory("RooBreitWigner::bw(mass, mZ0[91.188], gammaZ0[2.4952])")
    ws.factory("RooCBShape::cb_pdf(mass, cbb[0.07, -3.00, 3.0]," # bias
                                        "cbw[1.00,  0.00, 5.0]," # width
                                        "cba[1.20,  0.03, 4.0]," # alpha
                                        "cbn[5])")               # power

    ws.factory("RooFFTConvPdf::sig(mass, bw, cb_pdf)")


def shapeExpBackgr(ws):
    ws.factory("RooExponential::bg(mass,tau[-0.05,-40.,-0.01])")


def shapeRooCMSShape(ws):
    ws.factory("RooCMSShape::bg(mass, alpha[40.,20.,160.], "
                                     "beta[ 0.050, 0., 2.0], "
                                     "gamma[0.020, 0., 0.1], "
                                     "peak[91.2])")


def getNSignalEvents(histo, dofit=True, odir='tnpfits/'):
    if not dofit:
        # Return cut&count values
        binlo = histo.GetXaxis().FindBin(71.)
        binhi = histo.GetXaxis().FindBin(101.)
        err = ROOT.Double(0.0)
        nev = histo.IntegralAndError(binlo, binhi, err)
        return nev, err

    os.system('mkdir -p %s' % odir)

    ROOT.gROOT.SetBatch(1)
    shushRooFit()

    ws = ROOT.RooWorkspace()
    mass = ws.factory('mass[61,121]')
    data = ROOT.RooDataHist(histo.GetName(),
                            histo.GetTitle(),
                            ROOT.RooArgList(mass),
                            histo)
    getattr(ws, 'import')(data)

    # Define the pdfs:
    shapeCBBreitWigner(ws)
    shapeRooCMSShape(ws)
    # shapeExpBackgr(ws)

    # Define the fit model:
    nev = histo.Integral()
    nsig  = ws.factory('nsig[%.1f,%.1f,%.0f]' % (0.9*nev, 0.2*nev, 1.5*nev))
    nbkg  = ws.factory('nbkg[%.1f,0,%.0f]' % (0.1*nev, 1.5*nev))
    shape = ws.factory('SUM::model(nsig*sig, nbkg*bg)')
    getattr(ws, 'import')(shape)

    # Do the fit
    fitResult = shape.fitTo(data, ROOT.RooFit.Save())
    getattr(ws, 'import')(fitResult)

    # Plot the result
    canv = ROOT.TCanvas('canv_%s' % histo.GetName(), 'canvas', 800, 800)
    frame = mass.frame()
    data.plotOn(frame)
    shape.plotOn(frame,
                 ROOT.RooFit.Name('total'),
                 ROOT.RooFit.ProjWData(data),
                 ROOT.RooFit.LineColor(ROOT.kBlue),
                 ROOT.RooFit.LineWidth(2),
                 ROOT.RooFit.MoveToBack())
    shape.plotOn(frame,
                 ROOT.RooFit.Name('bkg'),
                 ROOT.RooFit.ProjWData(data),
                 ROOT.RooFit.Components('*bg*'),
                 ROOT.RooFit.FillColor(ROOT.kGray),
                 ROOT.RooFit.LineColor(ROOT.kGray),
                 ROOT.RooFit.LineWidth(1),
                 ROOT.RooFit.DrawOption('f'),
                 ROOT.RooFit.FillStyle(1001),
                 ROOT.RooFit.MoveToBack())
    frame.Draw()

    tlat = ROOT.TLatex()
    tlat.SetTextFont(83)
    tlat.SetNDC(1)
    tlat.SetTextSize(22)
    fitparms = ['cbb', 'cbw', 'cba', 'beta', 'gamma', 'alpha']
    for v in fitparms:
        val = ws.var(v).getVal()
        # if abs(val - ws.var(v).getMax()) < 1e-5:
        #     print ('########## %s is hitting maximum: %f (%f)' %
        #                   (v, val, ws.var(v).getMax()))
        # if abs(val - ws.var(v).getMin()) < 1e-5:
        #     print ('########## %s is hitting minimum: %f (%f)' %
        #                   (v, val, ws.var(v).getMin()))

        tlat.DrawLatex(0.14, 0.80-0.03*fitparms.index(v), '%-5s: %6.3f' % (v, val))
    tlat.DrawLatex(0.14, 0.86, 'Nsig : %8.1f' % (nsig.getVal()))
    tlat.DrawLatex(0.14, 0.83, 'Nbkg : %8.1f' % (nbkg.getVal()))

    chi2 = frame.chiSquare()
    tlat.DrawLatex(0.65, 0.86, "#chi^{2}/ndof = %3.2f" % chi2)
    if chi2 > 1000:
        print "$$$ Warning, bad fit? chi2/ndof = %3.2f $$$" % chi2

    canv.SaveAs(os.path.join(odir, "massfit_%s.pdf" % (histo.GetName())))
    canv.SaveAs(os.path.join(odir, "massfit_%s.png" % (histo.GetName())))
    if 'www' in odir:
        putPHPIndex(odir)

    return nsig.getVal(), nsig.getError()
