#!/usr/bin/env python
import sys, os, re, glob
import numpy as np
import pandas as pd

from scipy.interpolate import splev, splrep

import matplotlib.pyplot as plt
import matplotlib as mpl

import seaborn as sns

sns.set(style="ticks")
sns.set_context("poster")

mpl.rcParams['text.latex.preamble'] = [
       r'\usepackage{siunitx}',   # i need upright \micro symbols, but you need...
       r'\sisetup{detect-all}',   # ...this to force siunitx to actually use your fonts
       r'\usepackage{helvet}',    # set the normal font here
       r'\usepackage{upgreek}',   # upright greek letters
       r'\usepackage{sansmath}',  # load up the sansmath so that math -> helvet
       r'\sansmath'               # <- tricky! -- gotta actually tell tex to use!
]

mpl.rc('text', usetex=True)
mpl.rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})

plt.rcParams["figure.figsize"] = [10.0, 9.0]

def readScaledXsecs(filename='xsbr_scalings_K4.csv'):
    sigscale = pd.DataFrame.from_csv(filename, sep=",", index_col=None)

    # Read the SM tHq and tHW cross sections from those files
    xsec_thq_th = pd.DataFrame.from_csv("xsecs.csv", sep=",", index_col=None)
    xsec_thq_SM = float(xsec_thq_th.loc[xsec_thq_th.cv == 1.0].loc[xsec_thq_th.cf == 1.0].xsec)

    xsec_thw_th = pd.DataFrame.from_csv("xsecs_tWH.csv", sep=",", index_col=None)
    xsec_thw_SM = float(xsec_thw_th.loc[xsec_thw_th.cv == 1.0].loc[xsec_thw_th.cf == 1.0].xsec)

    xsec_tth_SM = 0.5071
    SM_BR_zz = 0.026
    SM_BR_ww = 0.214
    SM_BR_tt = 0.063

    xsecs = pd.DataFrame()
    xsecs['cv'] = sigscale.cv
    xsecs['cf'] = sigscale.ct
    xsecs['tth'] = sigscale.ttHww*SM_BR_ww*xsec_tth_SM + sigscale.ttHzz*SM_BR_zz*xsec_tth_SM + sigscale.ttHtt*SM_BR_tt*xsec_tth_SM
    xsecs['thq'] = sigscale.tHqww*SM_BR_ww*xsec_thq_SM + sigscale.tHqzz*SM_BR_zz*xsec_thq_SM + sigscale.tHqtt*SM_BR_tt*xsec_thq_SM
    xsecs['thw'] = sigscale.tHWww*SM_BR_ww*xsec_thw_SM + sigscale.tHWzz*SM_BR_zz*xsec_thw_SM + sigscale.tHWtt*SM_BR_tt*xsec_thw_SM
    xsecs['tot'] = xsecs.tth + xsecs.thq + xsecs.thw

    return xsecs

def readXsecs():
    xsec_thq = pd.DataFrame.from_csv("xsecs.csv",     sep=",", index_col=None)
    xsec_thw = pd.DataFrame.from_csv("xsecs_tWH.csv", sep=",", index_col=None)

    xsec_tth = pd.DataFrame()
    xsec_tth['cf']   = xsec_thq.loc[xsec_thq.cv == 1.0].cf
    xsec_tth['xsec'] = xsec_tth.cf.apply(lambda x: x**2*0.5071)

    return xsec_thq, xsec_thw, xsec_tth

def makePlot(inputfile='limits_1.dat', outdir='plots/', logscale=True, smoothing=0.0):
    # reset()
    print "...reading limits from %s" % inputfile

    try:
        cvval = float(re.match(r'limits.*_cv_([01p5]{1,3})', os.path.basename(inputfile)).group(1).replace('p','.'))
    except ValueError:
        cvval = 1.0
    # print "...determined cV for this input file to be %3.1f" % cvval


    # Fill dataframes
    df = pd.DataFrame.from_csv(inputfile, sep=",", index_col=None)
    xsecs = readScaledXsecs(filename='xsbr_scalings_K5.csv')
    xsecs = xsecs.loc[xsecs.cv == cvval]

    # xsec_thq, xsec_thw, xsec_tth = readXsecs()
    # xsec_tot = xsec_thw.loc[xsec_thw.cv == cvval].xsec + xsec_thq.loc[xsec_thq.cv == cvval].xsec + xsec_tth.xsec
    # xsec_th  = xsec_thw.loc[xsec_thw.cv == cvval].xsec + xsec_thq.loc[xsec_thq.cv == cvval].xsec
    
    x = sorted(list(set(df.cf.values.tolist())))

    # Evaluate spline at more points
    x2 = np.linspace(-3,3,100)

    spline_xsec_tot = splrep(x, xsecs.tot, s=smoothing)
    spline_xsec_th  = splrep(x, xsecs.thq+xsecs.thw, s=smoothing)
    spline_xsec_tth = splrep(x, xsecs.tth, s=smoothing)
    # spline_xsec_tot = splrep(x, xsec_tot, s=smoothing)
    # spline_xsec_th  = splrep(x, xsec_th, s=smoothing)
    # spline_xsec_tth = splrep(x, xsec_tth.xsec, s=smoothing)

    y2_xsec_tot = splev(x2, spline_xsec_tot)
    y2_xsec_tth = splev(x2, spline_xsec_tth)
    y2_xsec_th  = splev(x2, spline_xsec_th)

    # calculate splines for cv=1
    if logscale:
        spline_twosigdown = splrep(x,np.log(df.twosigdown), s=smoothing, k=3)
        spline_onesigdown = splrep(x,np.log(df.onesigdown), s=smoothing, k=3)
        spline_exp        = splrep(x,np.log(df.exp), s=smoothing, k=3)
        spline_onesigup   = splrep(x,np.log(df.onesigup), s=smoothing, k=3)
        spline_twosigup   = splrep(x,np.log(df.twosigup), s=smoothing, k=3)
    else:
        spline_twosigdown = splrep(x,df.twosigdown, s=smoothing, k=3)
        spline_onesigdown = splrep(x,df.onesigdown, s=smoothing, k=3)
        spline_exp        = splrep(x,df.exp, s=smoothing, k=3)
        spline_onesigup   = splrep(x,df.onesigup, s=smoothing, k=3)
        spline_twosigup   = splrep(x,df.twosigup, s=smoothing, k=3)

    y_twosigdown      = splev(x2, spline_twosigdown  )
    y_onesigdown      = splev(x2, spline_onesigdown  )
    y_exp             = splev(x2, spline_exp  )
    y_onesigup        = splev(x2, spline_onesigup  )
    y_twosigup        = splev(x2, spline_twosigup  )

    fig, ax = plt.subplots(1)

    # Plot horizontal line at 1 corresponding to exclusion
    plt.axhline(y=1, xmin=-3, xmax=3, hold=None, color='indianred', linewidth=1.5)

    # Configure axes
    ax.get_xaxis().set_tick_params(which='both', direction='in')
    ax.get_yaxis().set_tick_params(which='both', direction='in')
    if logscale:
        ax.set_ylim(0.2, 2000)
        ax.set_yscale("log", nonposy='clip')
        ax.set_yticks([1, 10, 100,1000])
        ax.set_yticks([1, 10, 100,1000])
        ax.set_yticklabels(['1','10','100','1000'])
        ax.spines['left'].set_zorder(101)    
    else:
        ax.set_ylim(0., 10)
        ax.set_yscale("linear", nonposy='clip')

    ax2 = ax.twinx()
    ax2.set_ylim(0.008, 14)
    if logscale:
        ax2.set_yscale("log", nonposy='clip')
    else:
        ax2.set_yscale("linear", nonposy='clip')
    ax2.set_ylabel('$\sigma~(\mathrm{tHq+tWH+ttH})$ [pb]',fontsize=24,labelpad=20,rotation=270)
    ax2.get_yaxis().set_tick_params(which='both', direction='in')
    if logscale:
        ax2.set_yticks([0.01, 0.1, 1,10])
        ax2.set_yticklabels(['0.01','0.1','1','10'])

    # Plot limits with sigma error bands
    if logscale:
        ax.plot(x2, np.exp(y_exp), "--", lw=2, color='black',zorder=4)
        ax.fill_between(x2, np.exp(y_onesigdown), np.exp(y_onesigup), facecolor='chartreuse', alpha=0.8,zorder=0)
        ax.fill_between(x2, np.exp(y_twosigdown), np.exp(y_onesigdown), facecolor='yellow', alpha=0.8,zorder=0)
        ax.fill_between(x2, np.exp(y_twosigup), np.exp(y_onesigup), facecolor='yellow', alpha=0.8,zorder=0)
    else:
        ax.plot(x2, y_exp, "--", lw=2, color='black',zorder=4)
        ax.fill_between(x2, y_onesigdown, y_onesigup, facecolor='chartreuse', alpha=0.8,zorder=0)
        ax.fill_between(x2, y_twosigdown, y_onesigdown, facecolor='yellow', alpha=0.8,zorder=0)
        ax.fill_between(x2, y_twosigup, y_onesigup, facecolor='yellow', alpha=0.8,zorder=0)

    # Plot xsec line
    ax2.plot(x2, y2_xsec_tot, lw=1.5, label='dummy',color='black' ,linestyle='-.')
    if options.print_split_xsecs:
        ax2.plot(x2, y2_xsec_tth, lw=0.5, label='dummy',color='black', linestyle='dashed')
        ax2.plot(x2, y2_xsec_th,  lw=0.5, label='dummy',color='black', linestyle='dotted')

    # Set labels
    ax.set_xlabel('$\kappa_\mathrm{t}$',fontsize=24,labelpad=20)
    ax.set_ylabel('95\% C.L. exp. asymptotic limit on $\sigma/\sigma_{\mathrm{tH+ttH}}$',fontsize=24,labelpad=20)

    def print_text(x, y, text, fontsize=24):
        plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes)

    print_text(0.06, 1.02, "$\mathbf{CMS}$ {\\huge{\\textit{Preliminary}}", 28)
    print_text(0.67, 1.02, "%.1f\,$\mathrm{fb}^{-1}$ (13\,TeV)"% (35.9))
    print_text(0.06, 0.92, "$\mathrm{pp}\\to\mathrm{tH}$")
    print_text(0.06, 0.86, ("$\mathrm{H}\\to\mathrm{W}\mathrm{W}/\mathrm{Z}\mathrm{Z}"
                            "/\mathrm{\\tau}\mathrm{\\tau}$, "
                            "$\mathrm{t}\\to\mathrm{b}\\ell\\upnu$"))
    print_text(0.06, 0.80, '$\kappa_\mathrm{V}=%3.1f$' % cvval)


    # Cosmetics
    import matplotlib.patches as mpatches
    twosigpatch = mpatches.Patch(color='yellow', label='$\pm2$ std. dev.')
    onesigpatch = mpatches.Patch(color='chartreuse', label='$\pm1$ std. dev.')
    obsline = mpl.lines.Line2D([], [], color='black', linestyle='-',
                               label='observed limit', marker='.',
                               markersize=14, linewidth=1)
    expline = mpl.lines.Line2D([], [], color='black', linestyle='--',
                               label='med. expected limit', linewidth=1.5)
    xsline = mpl.lines.Line2D([], [], color='black', lw=1.5, linestyle='-.',
                                  label='$\sigma\\times \mathrm{BR}$ (tH+ttH)')
    if options.print_split_xsecs:
        tthxsline = mpl.lines.Line2D([], [], color='black', lw=1, linestyle='dashed',
                                  label='$\sigma\\times \mathrm{BR}$ (ttH)')
        thxsline = mpl.lines.Line2D([], [], color='black', lw=1, linestyle='dotted',
                                  label='$\sigma\\times \mathrm{BR}$ (tH)')

    # Legend
    legend=plt.legend(loc=(0.71,0.75)) # Legend: list, location, Title (in bold)
    if not options.print_split_xsecs:
        plt.legend(handles=[expline,onesigpatch,twosigpatch,xsline], fontsize=18)
    else:
        plt.legend(handles=[expline,onesigpatch,twosigpatch,xsline,tthxsline,thxsline], fontsize=18)

    # Set Figure parameter
    # fig_size = plt.rcParams["figure.figsize"]
    # fig_size[0] = 10
    # fig_size[1] = 9

    outfile = os.path.join(outdir, os.path.splitext(os.path.basename(inputfile))[0])
    plt.savefig("%s.pdf"%outfile, bbox_inches='tight')
    plt.savefig("%s.png"%outfile, bbox_inches='tight', dpi=300)
    print "...saved plots in %s.pdf/.png" % outfile

    return 0

if __name__ == '__main__':
    from optparse import OptionParser
    usage = """%prog limits.dat"""
    parser = OptionParser(usage=usage)
    parser.add_option("-o","--outdir", dest="outdir",
                      type="string", default="plots/")
    parser.add_option("-l","--lin", dest="lin", action="store_true",
                      help="Do linear scale")
    parser.add_option("--print_split_xsecs", dest="print_split_xsecs", action="store_true",
                      help="Print split xsections for ttH and tH")
    parser.add_option("-s", "--smoothing", dest="smoothing", type="float",
                      default=0.0, help="Amount of smoothing applied for splines")
    (options, args) = parser.parse_args()

    try:
        os.system('mkdir -p %s' % options.outdir)
    except ValueError:
        pass

    for ifile in args:
        if not os.path.exists(ifile): continue
        makePlot(ifile, outdir=options.outdir, logscale=(not options.lin), smoothing=options.smoothing)

    sys.exit(0)
