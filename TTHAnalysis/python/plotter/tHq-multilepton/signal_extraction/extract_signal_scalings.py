import ROOT
import sys

"""
Open a workspace and print out scalings of cross section times BR as well
as BR only, for different values of kappa_t and kappa_V.
Also print the actual BR values.

Scalings are stored in a csv file to use in plotting.

Use as python extract_signal_scalings.py workspace.root
"""

cts = [-3, -2, -1.5, -1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.50, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]

ws = None
try:
    ws = ROOT.TFile.Open(sys.argv[1], "read").Get('w')
    _ = ws.GetName()
except IndexError:
    print "please provide an input file"
    sys.exit(-1)
except ValueError:
    print "workspace not found in file"
    sys.exit(-2)

ws.var("kappa_t").setRange(-4,4)

def setKappaV(workspace, cv):
    try:
        workspace.var("kappa_W").setVal(cv)
        workspace.var("kappa_Z").setVal(cv)
    except ReferenceError:
        workspace.var("kappa_V").setVal(cv)

# for coupl in ["W", "Z", "tau", "mu", "t", "b", "g", "gam"]:
#     print "kappa_%s"%coupl, ws.var("kappa_%s"%coupl).getVal()

print "\n\n XS x BF scalings"

xsbrs = ["c7_XSBRscal_ttH_hww_13TeV", "c7_XSBRscal_ttH_hzz_13TeV", "c7_XSBRscal_ttH_htt_13TeV",
         "c7_XSBRscal_tHq_hww_13TeV", "c7_XSBRscal_tHq_hzz_13TeV", "c7_XSBRscal_tHq_htt_13TeV",
         "c7_XSBRscal_tHW_hww_13TeV", "c7_XSBRscal_tHW_hzz_13TeV", "c7_XSBRscal_tHW_htt_13TeV"]
xsbrscalings = {} # (cv,ct) -> scalings
for cv in [1.0, 0.5, 1.5]:
    print "--------------------------------------------------------------------"
    print " CV = {:.1f}".format(cv)
    print "  Ct   ttHww  ttHzz  ttHtt  tHqww  tHqzz  tHqtt  tHWww  tHWzz  tHWtt"
    setKappaV(ws, cv)
    for ct in cts:
        ws.var("kappa_t").setVal(ct)
        scaling = tuple([ws.function(fn).getVal() for fn in xsbrs])
        linepat = "{:5.2f} "+len(xsbrs)*"{:6.3f} "
        print linepat.format(ct, *scaling)
        xsbrscalings[(cv,ct)] = scaling

with open('xsbr_scalings.csv', 'w') as csvfile:
    csvfile.write("cv,ct,ttHww,ttHzz,ttHtt,tHqww,tHqzz,tHqtt,tHWww,tHWzz,tHWtt\n")
    for (cv,ct),scaling in sorted(xsbrscalings.iteritems()):
        sscaling = ["{:.4f}".format(s) for s in scaling]
        csvfile.write(','.join(map(str, [cv,ct]+list(sscaling))))
        csvfile.write('\n')
print "--------------------------------------------------------------------"

print "\n\n Branching fraction scalings"
brs = [ "c7_BRscal_hww", "c7_BRscal_hzz", "c7_BRscal_htt",
        "c7_BRscal_hmm", "c7_BRscal_hbb", "c7_BRscal_hcc",
        "c7_BRscal_hgg", "c7_BRscal_hzg", "c7_BRscal_hgluglu", "c7_BRscal_hinv"]
brscalings = {} # (cv,ct) -> scalings
for cv in [1.0, 0.5, 1.5]:
    print "--------------------------------------------------------------------"
    print " CV = {:.1f}".format(cv)
    print "  Ct    Hww    Hzz    Htt    Hmm    Hbb    Hcc    Hgg    Hzg   Hglgl   Hinv"
    setKappaV(ws, cv)
    for ct in cts:
        ws.var("kappa_t").setVal(ct)
        scaling = tuple([ws.function(fn).getVal() for fn in brs])
        linepat = "{:5.2f} "+len(brs)*"{:6.3f} "
        print linepat.format(ct, *scaling)
        brscalings[(cv,ct)] = scaling

with open('br_scalings.csv', 'w') as csvfile:
    csvfile.write("cv,ct,hww,hzz,htt,hmm,hbb,hcc,hgg,hzg,hgluglu,hinv\n")
    for (cv,ct),scaling in sorted(brscalings.iteritems()):
        sscaling = ["{:.4f}".format(s) for s in scaling]
        csvfile.write(','.join(map(str, [cv,ct]+list(sscaling))))
        csvfile.write('\n')
print "--------------------------------------------------------------------"


print "\n\n c7_Gscal_tot scalings"


scals = ["c7_Gscal_tot", "c7_Gscal_Z", "c7_Gscal_W", "c7_Gscal_tau",
         "c7_Gscal_top", "c7_Gscal_bottom", "c7_Gscal_gluon",
         "c7_Gscal_gamma", "c7_SMBRs", "BRinv"]
for cv in [1.0, 0.5, 1.5]:
    print "--------------------------------------------------------------------"
    print " CV = {:.1f}".format(cv)
    print "  Ct    tot     Z      W     tau    top    bot    glu    gam   SMBR   BRinv"
    setKappaV(ws, cv)
    for ct in cts:
        ws.var("kappa_t").setVal(ct)
        scaling = tuple([ws.function(fn).getVal() for fn in scals])
        linepat = "{:5.2f} "+len(scals)*"{:6.3f} "
        print linepat.format(ct, *scaling)
print "--------------------------------------------------------------------"


