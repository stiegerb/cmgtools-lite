#!/usr/bin/env python
import sys, os, re, glob
import numpy as np

from scipy.interpolate import splev, splrep

import matplotlib.pyplot as plt
import matplotlib as mpl

import seaborn as sns

# def reset():
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

def makePlot(inputfile='limits_1.dat', outdir='plots/'):
    # reset()
    print "...reading limits from %s" % inputfile

    try:
        cvval = float(re.match(r'limits_.*_cv_([01p5]{1,3})', os.path.basename(inputfile)).group(1).replace('p','.'))
    except ValueError:
        cvval = 1.0
    print "...determined cV for this input file to be %3.1f" % cvval


    # Fill dataframes
    import pandas as pd
    df       = pd.DataFrame.from_csv(inputfile,       sep=",", index_col=None)
    xsec_thq = pd.DataFrame.from_csv("xsecs.csv",     sep=",", index_col=None)
    xsec_thw = pd.DataFrame.from_csv("xsecs_tWH.csv", sep=",", index_col=None)

    x = sorted(list(set(df.cf.values.tolist())))

    # Evaluate spline at more points
    x2 = np.linspace(-3,3,100)

    spline_xsec = splrep(x, (xsec_thw.loc[xsec_thw.cv == cvval].xsec +
                             xsec_thq.loc[xsec_thq.cv == cvval].xsec), s=11)

    y2_xsec = splev(x2, spline_xsec)

    # calculate splines for cv=1
    spline_twosigdown = splrep(x,np.log(df.twosigdown), s=0.01, k=3)
    spline_onesigdown = splrep(x,np.log(df.onesigdown), s=0.01, k=3)
    spline_exp        = splrep(x,np.log(df.exp), s=0.01, k=3)
    spline_onesigup   = splrep(x,np.log(df.onesigup), s=0.01, k=3)
    spline_twosigup   = splrep(x,np.log(df.twosigup), s=0.01, k=3)

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
    ax.set_ylim(0.2, 2000)
    ax.set_yscale("log", nonposy='clip')
    ax.set_yticks([1, 10, 100,1000])
    ax.set_yticklabels(['1','10','100','1000'])
    ax.spines['left'].set_zorder(101)

    ax2 = ax.twinx()
    ax2.set_ylim(0.008, 14)
    ax2.set_yscale("log", nonposy='clip')
    ax2.set_ylabel('$\sigma~(\mathrm{tHq+tWH})$ [pb]',fontsize=24,labelpad=20,rotation=270)
    ax2.get_yaxis().set_tick_params(which='both', direction='in')
    ax2.set_yticks([0.01, 0.1, 1,10])
    ax2.set_yticklabels(['0.01','0.1','1','10'])

    # Plot limits with sigma error bands
    ax.plot(x2, np.exp(y_exp), "--", lw=2, color='black',zorder=4)
    ax.fill_between(x2, np.exp(y_onesigdown), np.exp(y_onesigup), facecolor='chartreuse', alpha=0.8,zorder=0)
    ax.fill_between(x2, np.exp(y_twosigdown), np.exp(y_onesigdown), facecolor='yellow', alpha=0.8,zorder=0)
    ax.fill_between(x2, np.exp(y_twosigup), np.exp(y_onesigup), facecolor='yellow', alpha=0.8,zorder=0)

    # Plot xsec line
    ax2.plot(x2, y2_xsec, lw=1, label='dummy',color='steelblue' ,linestyle='-.')

    # Set labels
    ax.set_xlabel('$C_\mathrm{t}$',fontsize=24,labelpad=20)
    ax.set_ylabel('95\% C.L. exp. asymptotic limit on $\sigma/\sigma_{\mathrm{theor.}}$',fontsize=24,labelpad=20)

    def print_text(x, y, text, fontsize=24):
        plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes)

    print_text(0.06, 1.02, "$\mathbf{CMS}$ {\\huge{\\textit{Preliminary}}", 28)
    print_text(0.67, 1.02, "%.1f\,$\mathrm{fb}^{-1}$ (13\,TeV)"% (36.5))
    print_text(0.06, 0.92, "$\mathrm{pp}\\to\mathrm{tH}$")
    print_text(0.06, 0.86, ("$\mathrm{H}\\to\mathrm{W}\mathrm{W}/\mathrm{Z}\mathrm{Z}"
                            "/\mathrm{\\tau}\mathrm{\\tau}$, "
                            "$\mathrm{t}\\to\mathrm{b}\\ell\\upnu$"))
    print_text(0.06, 0.80, '$C_\mathrm{V}=%3.1f$' % cvval)


    # Cosmetics
    import matplotlib.patches as mpatches
    twosigpatch = mpatches.Patch(color='yellow', label='$\pm2$ std. dev.')
    onesigpatch = mpatches.Patch(color='chartreuse', label='$\pm1$ std. dev.')
    obsline = mpl.lines.Line2D([], [], color='black', linestyle='-',
                               label='observed limit', marker='.',
                               markersize=14, linewidth=1)
    expline = mpl.lines.Line2D([], [], color='black', linestyle='--',
                               label='med. expected limit', linewidth=1.5)
    xsline = mpl.lines.Line2D([], [], color='steelblue', linestyle='-.',
                              label='tH cross section')

    # Legend
    legend=plt.legend(loc=(0.71,0.75)) # Legend: list, location, Title (in bold)
    plt.legend(handles=[expline,onesigpatch,twosigpatch,xsline], fontsize=18)

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
    (options, args) = parser.parse_args()

    try:
        os.system('mkdir -p %s' % options.outdir)
    except ValueError:
        pass

    for ifile in args:
        if not os.path.exists(ifile): continue
        makePlot(ifile, outdir=options.outdir)

    sys.exit(0)
