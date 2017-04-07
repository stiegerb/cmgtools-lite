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

def makePlot(inputfile='limits_1.dat',
             outdir='plots/',
             ymax=1.0,
             smoothing=0.0,
             split_xsecs=True,
             split_cv_xsecs=False,
             alpha=False,
             observed=False):
    print "...reading fits from %s" % inputfile
    if split_cv_xsecs: split_xsecs = False

    # Fill dataframes
    df    = pd.DataFrame.from_csv(inputfile, sep=",", index_col=None)
    xsecs = pd.DataFrame.from_csv('xsecs_tH_ttH_K6.csv', sep=",", index_col=None)
    xsecs['alpha'] = np.sign(xsecs.cf)*xsecs.cf**2/(xsecs.cf**2+1.0)

    x = sorted(list(set(df.ratio.values.tolist())))
    if alpha:
        x = sorted(list(set(df.alpha.values.tolist())))

    # Evaluate spline at more points
    x2 = np.linspace(-6,6,100)
    if alpha:
        x2 = np.linspace(-0.973,0.973,100)

    spline_xsec_tot = splrep(x, xsecs.loc[xsecs.cv==1.0].tot, s=smoothing)
    if split_cv_xsecs:
        spline_xsec_tot_0p5 = splrep(x, xsecs.loc[xsecs.cv==0.5].tot, s=smoothing)
        spline_xsec_tot_1p5 = splrep(x, xsecs.loc[xsecs.cv==1.5].tot, s=smoothing)
    spline_xsec_th  = splrep(x, xsecs.loc[xsecs.cv==1.0].thq+xsecs.loc[xsecs.cv==1.0].thw, s=smoothing)
    spline_xsec_tth = splrep(x, xsecs.loc[xsecs.cv==1.0].tth, s=smoothing)

    y2_xsec_tot = splev(x2, spline_xsec_tot)
    if split_cv_xsecs:
        y2_xsec_tot_0p5 = splev(x2, spline_xsec_tot_0p5)
        y2_xsec_tot_1p5 = splev(x2, spline_xsec_tot_1p5)
    y2_xsec_tth = splev(x2, spline_xsec_tth)
    y2_xsec_th  = splev(x2, spline_xsec_th)

    fig, ax = plt.subplots(1)

    # Make a spline at the upper and lower error edges
    spline_uperror = splrep(x, df.get('median')+df.get('uperror'), s=smoothing)
    spline_dnerror = splrep(x, df.get('median')+df.get('downerror'), s=smoothing)
    y2_uperror = splev(x2, spline_uperror)
    y2_dnerror = splev(x2, spline_dnerror)

    # Configure axes
    ax.get_xaxis().set_tick_params(which='both', direction='in')
    ax.get_xaxis().set_major_locator(mpl.ticker.MultipleLocator(1.0))
    ax.get_xaxis().set_minor_locator(mpl.ticker.MultipleLocator(0.25))
    ax.set_xlim(-3., 3)
    if alpha:
        ax.get_xaxis().set_major_locator(mpl.ticker.MultipleLocator(0.25))
        ax.get_xaxis().set_minor_locator(mpl.ticker.MultipleLocator(0.05))
        ax.set_xlim(-1.0, 1.0)

    ax.set_ylim(0., ymax)
    ax.set_yscale("linear", nonposy='clip')
    ax.get_yaxis().set_tick_params(which='both', direction='in')
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(0.2))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(0.05))

    # Plot limits with sigma error bands
    ax.fill_between(x2, y2_uperror, y2_dnerror, facecolor='lightgrey', alpha=0.8, zorder=0)

    if alpha:
        ax.plot(df.alpha, df.get('median'), lw=2.0, c='black')
        # ax.errorbar(df.alpha, df.get('median'),
        #             yerr=[-df.downerror, df.uperror],
        #             ecolor='grey',
        #             linewidth=0.0,
        #             elinewidth=0.5)
        ax.scatter(df.alpha, df.get('median'), marker='o', s=30, c='black', lw=2)
    else:
        ax.plot(df.ratio, df.get('median'), lw=2.0, c='black')
        # ax.errorbar(df.ratio, df.get('median'),
        #             yerr=[-df.downerror, df.uperror],
        #             ecolor='grey',
        #             linewidth=0.0,
        #             elinewidth=0.5)
        ax.scatter(df.ratio, df.get('median'), marker='o', s=30, c='black', lw=2)

    # # Plot vertical line at 1 corresponding to SM
    # hpos = 1.0 if not alpha else 0.5
    # plt.axvline(x=hpos, ymin=0.0, ymax=ymax, hold=None, color='indianred', linewidth=1.0)

    # Plot xsec line(s)
    if not split_cv_xsecs:
        ax.plot(x2, y2_xsec_tot, lw=1.5, label='dummy',color='black' ,linestyle='-.')
    if split_xsecs:
        ax.plot(x2, y2_xsec_tth, lw=0.5, label='dummy',color='black', linestyle='dashed')
        ax.plot(x2, y2_xsec_th,  lw=0.5, label='dummy',color='black', linestyle='dotted')
    if split_cv_xsecs:
        ax.plot(x2, y2_xsec_tot,     lw=1.0, label='dummy',color='black' ,linestyle='-.')
        ax.plot(x2, y2_xsec_tot_0p5, lw=1.0, label='dummy',color='black', linestyle='dashed')
        ax.plot(x2, y2_xsec_tot_1p5, lw=1.0, label='dummy',color='black', linestyle='dotted')

    # Set axis labels
    ax.set_xlabel('$\kappa_\mathrm{t}/\kappa_\mathrm{V}$',fontsize=24,labelpad=20)
    if alpha:
        ax.set_xlabel('$\pm\kappa_\mathrm{t}^2 / (\kappa_\mathrm{t}^2+\kappa_\mathrm{V}^2)$',fontsize=24,labelpad=20)
    # ax.set_ylabel('95\% C.L. limit on $\sigma_{\mathrm{tH+t\\bar{t}H}}\\times$ BR [pb]',fontsize=24,labelpad=20)
    ax.set_ylabel('$\sigma\\times$ BR [pb]',fontsize=24,labelpad=20)

    def print_text(x, y, text, fontsize=24, addbackground=True):
        if addbackground:
            ptext = plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes, backgroundcolor='white')
            ptext.set_bbox(dict(alpha=0.8, color='white'))
        else:
            ptext = plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes)

    print_text(0.03, 1.02, "$\mathbf{CMS}$ {\\huge{\\textit{Preliminary}}", 28, addbackground=False)
    print_text(0.65, 1.02, "%.1f\,$\mathrm{fb}^{-1}$ (13\,TeV)"% (35.9), addbackground=False)

    print_text(0.06, 0.92, "$\mathrm{pp}\\to\mathrm{tH}+\mathrm{t\\bar{t}H}$")
    print_text(0.06, 0.86, ("$\mathrm{H}\\to\mathrm{W}\mathrm{W}/\mathrm{Z}\mathrm{Z}"
                            "/\mathrm{\\tau}\mathrm{\\tau}$"))
    # print_text(0.06, 0.80,  "$\mathrm{t}\\to\mathrm{b}\\ell\\upnu$")
    print_text(0.06, 0.78, '$\kappa_\\tau=\kappa_{\mathrm{t}}$')


    # Cosmetics
    import matplotlib.patches as mpatches
    errorpatch = mpatches.Patch(color='lightgrey', label='$\pm1$ standard dev.')
    fitline = mpl.lines.Line2D([], [], color='black', linestyle='-',
                               label='Measured $\sigma_{\mathrm{tH+t\\bar{t}H}}$', marker='.',
                               markersize=14, linewidth=2)
    if not split_cv_xsecs:
        xsline = mpl.lines.Line2D([], [], color='black', lw=1.5, linestyle='-.',
                               label='$\sigma^\\text{theo.}_{\mathrm{tH+t\\bar{t}H}}\\times \mathrm{BR}$ ($\kappa_V=1.0$)')
    if split_xsecs:
        tthxsline = mpl.lines.Line2D([], [], color='black', lw=1, linestyle='dashed',
                               label='$\sigma^\\text{theo.}_{\mathrm{t\\bar{t}H}}\\times \mathrm{BR}$ ($\kappa_V=1.0$)')
        thxsline = mpl.lines.Line2D([], [], color='black', lw=1, linestyle='dotted',
                               label='$\sigma^\\text{theo.}_{\mathrm{tH}}\\times \mathrm{BR}$ ($\kappa_V=1.0$)')
    if split_cv_xsecs:
        xsline = mpl.lines.Line2D([], [], color='black', lw=1.0, linestyle='-.',
                               label='$\sigma^\\text{theo.}_{\mathrm{tH+t\\bar{t}H}}\\times \mathrm{BR}$ ($\kappa_V=1.0$)')
        tthxsline = mpl.lines.Line2D([], [], color='black', lw=1.0, linestyle='dashed',
                               label='$\sigma^\\text{theo.}_{\mathrm{tH+t\\bar{t}H}}\\times \mathrm{BR}$ ($\kappa_V=0.5$)')
        thxsline = mpl.lines.Line2D([], [], color='black', lw=1.0, linestyle='dotted',
                               label='$\sigma^\\text{theo.}_{\mathrm{tH+t\\bar{t}H}}\\times \mathrm{BR}$ ($\kappa_V=1.5$)')

    # Legend
    legentries = [fitline,errorpatch]
    if observed:
        legentries.insert(0, obsline)
    if not split_cv_xsecs:
        legentries += [xsline]
    if split_xsecs:
        legentries += [tthxsline, thxsline]
    if split_cv_xsecs:
        legentries += [tthxsline, xsline, thxsline]
    legend = plt.legend(handles=legentries, fontsize=18, frameon=True, loc='upper right', framealpha=0.8)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_linewidth(0)

    # Save to pdf/png
    outfile = os.path.join(outdir, os.path.splitext(os.path.basename(inputfile))[0])
    if alpha: outfile += '_alpha'
    if split_cv_xsecs: outfile += '_split_cv'
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
    parser.add_option("--alpha", dest="alpha", action="store_true",
                      help="Plot alpha on x-axis instead of ratio")
    parser.add_option("--split_xsecs", dest="split_xsecs", action="store_true",
                      help="Show split xsections for ttH and tH")
    parser.add_option("--split_cv_xsecs", dest="split_cv_xsecs", action="store_true",
                      help="Show split xsections for different values of cv")
    parser.add_option("-s", "--smoothing", dest="smoothing", type="float",
                      default=0.0, help="Amount of smoothing applied for splines")
    parser.add_option("--observed", dest="observed", action="store_true",
                      help="Plot also the observed limit")
    parser.add_option("--ymax", dest="ymax", type="float",
                      default=1.5, help="Y axis maximum")
    (options, args) = parser.parse_args()

    try:
        os.system('mkdir -p %s' % options.outdir)
    except ValueError:
        pass

    for ifile in args:
        if not os.path.exists(ifile): continue
        makePlot(ifile, outdir=options.outdir,
                        ymax=options.ymax,
                        smoothing=options.smoothing,
                        split_xsecs=options.split_xsecs,
                        split_cv_xsecs=options.split_cv_xsecs,
                        alpha=options.alpha,
                        observed=options.observed)

    sys.exit(0)
