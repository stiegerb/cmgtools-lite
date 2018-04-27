#!/usr/bin/env python
import sys, os, re, glob
import numpy as np
import pandas as pd

from scipy.interpolate import splev, splrep

import matplotlib.pyplot as plt
import matplotlib as mpl

import seaborn as sns

from functools import partial

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

XSEC_THQ_SM = 0.07096
XSEC_THW_SM = 0.01561
XSEC_TTH_SM = 0.5071

SM_BR_WW = 0.214
SM_BR_ZZ = 0.026
SM_BR_TT = 0.063
SM_BR_bb = 0.583

def xsec_thq(ratio, kv):
    kt = ratio*kv
    return XSEC_THQ_SM*(2.633*kt**2 + 3.578*kv**2 - 5.211*kt*kv)

def xsec_thw(ratio, kv):
    kt = ratio*kv
    return XSEC_THW_SM*(2.909*kt**2 + 2.310*kv**2 - 4.220*kt*kv)

def xsec_tth(kt):
    return XSEC_TTH_SM*kt**2

def label_line(line, label, x, y, color='0.5', size=12):
    """Add a label to a line, at the proper angle.
    From here: http://stackoverflow.com/questions/18780198/how-to-rotate-matplotlib-annotation-to-match-a-line

    Arguments
    ---------
    line : matplotlib.lines.Line2D object,
    label : str
    x : float
        x-position to place center of text (in data coordinated
    y : float
        y-position to place center of text (in data coordinates)
    color : str
    size : float
    """
    xdata, ydata = line.get_data()
    x1 = xdata[0]
    x2 = xdata[-1]
    y1 = ydata[0]
    y2 = ydata[-1]

    ax = line.axes
    text = ax.annotate(label, xy=(x, y), xytext=(-10, 0),
                       textcoords='offset points',
                       size=size, color=color,
                       horizontalalignment='left',
                       verticalalignment='bottom')

    sp1 = ax.transData.transform_point((x1, y1))
    sp2 = ax.transData.transform_point((x2, y2))

    rise = (sp2[1] - sp1[1])
    run = (sp2[0] - sp1[0])

    slope_degrees = np.degrees(np.arctan2(rise, run))
    text.set_rotation(slope_degrees)
    return text

def plotBRScalings(outdir='plots/',
                   ymax=0.5,
                   smoothing=0.0,
                   alpha=False):

    # Fill dataframes 
    # df = pd.DataFrame()
    # if not alpha:
    #     df = df.append(pd.DataFrame({"ratio" : np.linspace(-6,6,101)}))
    # else:
    #     df = df.append(pd.DataFrame({"ratio" : np.linspace(-0.99,0.99,101)}))

    df = pd.DataFrame.from_csv('br_scalings_K6.csv', sep=",", index_col=None)
    df['cv'] = df.cv.round(3)
    df['ct'] = df.ct.round(3)
    df['ratio'] = df.ct/df.cv
    df['alpha'] = np.sign(df.ct)*df.ct**2/(df.ct**2+1.0)

    df['brhww'] = df.hww*SM_BR_WW
    df['brhzz'] = df.hzz*SM_BR_ZZ
    df['brhtt'] = df.htt*SM_BR_TT
    df['brhbb'] = df.hbb*SM_BR_bb

    x = sorted(list(set(df.ratio.loc[df.cv==1.0].values.tolist())))
    if alpha:
        x = sorted(list(set(df.alpha.loc[df.cv==1.0].values.tolist())))

    # Evaluate spline at more points
    x2 = np.linspace(-3, 3, 101)
    if alpha:
        x2 = np.linspace(-0.973, 0.973, 101)

    spline_BR_hww_0p5 = splev(x, splrep(x, df.brhww.loc[df.cv==0.5], s=smoothing))
    spline_BR_hww_1p0 = splev(x, splrep(x, df.brhww.loc[df.cv==1.0], s=smoothing))
    spline_BR_hww_1p5 = splev(x, splrep(x, df.brhww.loc[df.cv==1.5], s=smoothing))
    spline_BR_hzz_0p5 = splev(x, splrep(x, df.brhzz.loc[df.cv==0.5], s=smoothing))
    spline_BR_hzz_1p0 = splev(x, splrep(x, df.brhzz.loc[df.cv==1.0], s=smoothing))
    spline_BR_hzz_1p5 = splev(x, splrep(x, df.brhzz.loc[df.cv==1.5], s=smoothing))
    spline_BR_htt_0p5 = splev(x, splrep(x, df.brhtt.loc[df.cv==0.5], s=smoothing))
    spline_BR_htt_1p0 = splev(x, splrep(x, df.brhtt.loc[df.cv==1.0], s=smoothing))
    spline_BR_htt_1p5 = splev(x, splrep(x, df.brhtt.loc[df.cv==1.5], s=smoothing))
    spline_BR_hbb_0p5 = splev(x, splrep(x, df.brhbb.loc[df.cv==0.5], s=smoothing))
    spline_BR_hbb_1p0 = splev(x, splrep(x, df.brhbb.loc[df.cv==1.0], s=smoothing))
    spline_BR_hbb_1p5 = splev(x, splrep(x, df.brhbb.loc[df.cv==1.5], s=smoothing))

    fig, ax = plt.subplots(1)

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
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(0.1))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(0.025))

    # Plot xsec line(s)
    ax.plot(x, spline_BR_hww_0p5, lw=1.0, label='dummy', color='Black', linestyle='-.')
    ax.plot(x, spline_BR_hww_1p0, lw=2.0, label='dummy', color='Black', linestyle='-')
    ax.plot(x, spline_BR_hww_1p5, lw=1.0, label='dummy', color='Black', linestyle='--')
    ax.plot(x, spline_BR_hzz_0p5, lw=1.0, label='dummy', color='RoyalBlue', linestyle='-.')
    ax.plot(x, spline_BR_hzz_1p0, lw=2.0, label='dummy', color='RoyalBlue', linestyle='-')
    ax.plot(x, spline_BR_hzz_1p5, lw=1.0, label='dummy', color='RoyalBlue', linestyle='--')
    ax.plot(x, spline_BR_htt_0p5, lw=1.0, label='dummy', color='OrangeRed', linestyle='-.')
    ax.plot(x, spline_BR_htt_1p0, lw=2.0, label='dummy', color='OrangeRed', linestyle='-')
    ax.plot(x, spline_BR_htt_1p5, lw=1.0, label='dummy', color='OrangeRed', linestyle='--')
    ax.plot(x, spline_BR_hbb_0p5, lw=1.0, label='dummy', color='LimeGreen', linestyle='-.')
    ax.plot(x, spline_BR_hbb_1p0, lw=2.0, label='dummy', color='LimeGreen', linestyle='-')
    ax.plot(x, spline_BR_hbb_1p5, lw=1.0, label='dummy', color='LimeGreen', linestyle='--')

    # Set axis labels
    ax.set_xlabel('$\kappa_\mathrm{t}/\kappa_\mathrm{V}$',fontsize=24,labelpad=20)
    if alpha:
        ax.set_xlabel('$\pm\kappa_\mathrm{t}^2 / (\kappa_\mathrm{t}^2+\kappa_\mathrm{V}^2)$',fontsize=24,labelpad=20)
    ax.set_ylabel('Branching Ratio', fontsize=24, labelpad=20)

    def print_text(x, y, text, fontsize=24, addbackground=True):
        if addbackground:
            ptext = plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes, backgroundcolor='white')
            ptext.set_bbox(dict(alpha=0.8, color='white'))
        else:
            ptext = plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes)

    print_text(0.06, 0.92, "BR ($\mathrm{H}\\to \mathrm{WW^*}\,/\mathrm{ZZ^*}\,/\mathrm{\\tau\\tau}\,/\mathrm{b\overline{b}})$")
    print_text(0.06, 0.84, '$\kappa_\\tau=\kappa_{\mathrm{t}}$')

    line_0p5 = mpl.lines.Line2D([], [], color='black', linestyle='--', label='$\kappa_V=0.5$', linewidth=1.0)
    line_1p0 = mpl.lines.Line2D([], [], color='black', linestyle='-',  label='$\kappa_V=1.0$', linewidth=2.0)
    line_1p5 = mpl.lines.Line2D([], [], color='black', linestyle='-.', label='$\kappa_V=1.5$', linewidth=1.0)
    import matplotlib.patches as mpatches
    hwwpatch = mpatches.Patch(color='Black',    label='$\mathrm{H}\\to\mathrm{WW^*}$')
    hzzpatch = mpatches.Patch(color='RoyalBlue',label='$\mathrm{H}\\to\mathrm{ZZ^*}$')
    httpatch = mpatches.Patch(color='OrangeRed',label='$\mathrm{H}\\to\mathrm{\\tau\\tau}$')
    hbbpatch = mpatches.Patch(color='LimeGreen',label='$\mathrm{H}\\to\mathrm{b\overline{b}}$')

    legend = plt.legend(handles=[hwwpatch, hzzpatch, httpatch, hbbpatch, line_0p5, line_1p0, line_1p5],
                        fontsize=18, frameon=True, loc='upper right', framealpha=0.8)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_linewidth(0)

    # ax.text( 2.50, 1.30, "tHq ($\kappa_{\mathrm{V}}=1.5)$", ha='center', va='center', size=16, color='red', rotation=79)
    # ax.text( 2.65, 0.66, "tHq ($\kappa_{\mathrm{V}}=1.0)$", ha='center', va='center', size=16, color='red', rotation=67)
    # ax.text(-2.50, 0.64, "tHq ($\kappa_{\mathrm{V}}=0.5)$", ha='center', va='center', size=16, color='red', rotation=-52)

    # ax.text(-2.40, 1.10, "tHW ($\kappa_{\mathrm{V}}=1.5)$", ha='center', va='center', size=16, color='blue', rotation=-68)
    # ax.text( 2.50, 0.19, "tHW ($\kappa_{\mathrm{V}}=1.0)$", ha='center', va='center', size=16, color='blue', rotation=33)
    # ax.text(-2.30, 0.14, "tHW ($\kappa_{\mathrm{V}}=0.5)$", ha='center', va='center', size=16, color='blue', rotation=-17)

    # Save to pdf/png
    outfile = os.path.join(outdir, 'br_scaling')
    if alpha: outfile += '_alpha'
    plt.savefig("%s.pdf"%outfile, bbox_inches='tight')
    plt.savefig("%s.png"%outfile, bbox_inches='tight', dpi=300)
    print "...saved plots in %s.pdf/.png" % outfile

def plotXsecs(outdir='plots/',
             ymax=1.0,
             smoothing=0.0,
             alpha=False):
    xsecs = pd.DataFrame()
    if not alpha:
        xsecs = xsecs.append(pd.DataFrame({"ratio" : np.linspace(-6,6,101)}))
    else:
        xsecs = xsecs.append(pd.DataFrame({"ratio" : np.linspace(-0.99,0.99,101)}))

    x = sorted(list(set(xsecs.ratio.values.tolist())))
    if alpha:
        x = sorted(list(set(xsecs.alpha.values.tolist())))

    for cv in  [0.5, 1.0, 1.5]:
        xsecs['thq_%s'%str(cv).replace('.','p')] = np.vectorize(partial(xsec_thq, kv=cv))(xsecs.ratio)
        xsecs['thw_%s'%str(cv).replace('.','p')] = np.vectorize(partial(xsec_thw, kv=cv))(xsecs.ratio)
    xsecs['tth'] = np.vectorize(xsec_tth)(xsecs.ratio)

    spline_xsec_thq_0p5 = splev(x, splrep(x, xsecs.thq_0p5, s=smoothing))
    spline_xsec_thq_1p0 = splev(x, splrep(x, xsecs.thq_1p0, s=smoothing))
    spline_xsec_thq_1p5 = splev(x, splrep(x, xsecs.thq_1p5, s=smoothing))
    spline_xsec_thw_0p5 = splev(x, splrep(x, xsecs.thw_0p5, s=smoothing))
    spline_xsec_thw_1p0 = splev(x, splrep(x, xsecs.thw_1p0, s=smoothing))
    spline_xsec_thw_1p5 = splev(x, splrep(x, xsecs.thw_1p5, s=smoothing))
    spline_xsec_tth     = splev(x, splrep(x, xsecs.tth,     s=smoothing)) # independent of cv

    fig, ax = plt.subplots(1)

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

    # Plot xsec line(s)
    ax.plot(x, spline_xsec_thq_0p5, lw=1.0, label='dummy', color='red',   linestyle='-.')
    ax.plot(x, spline_xsec_thq_1p0, lw=2.0, label='dummy', color='red',   linestyle='-')
    ax.plot(x, spline_xsec_thq_1p5, lw=1.0, label='dummy', color='red',   linestyle='--')
    ax.plot(x, spline_xsec_thw_0p5, lw=1.0, label='dummy', color='blue',  linestyle='-.')
    ax.plot(x, spline_xsec_thw_1p0, lw=2.0, label='dummy', color='blue',  linestyle='-')
    ax.plot(x, spline_xsec_thw_1p5, lw=1.0, label='dummy', color='blue',  linestyle='--')
    ax.plot(x, spline_xsec_tth,     lw=2.0, label='dummy', color='black', linestyle='-')

    # Set axis labels
    ax.set_xlabel('$\kappa_\mathrm{t}/\kappa_\mathrm{V}$',fontsize=24,labelpad=20)
    if alpha:
        ax.set_xlabel('$\pm\kappa_\mathrm{t}^2 / (\kappa_\mathrm{t}^2+\kappa_\mathrm{V}^2)$',fontsize=24,labelpad=20)
    ax.set_ylabel('$\sigma$ [pb]',fontsize=24,labelpad=20)

    def print_text(x, y, text, fontsize=24, addbackground=True):
        if addbackground:
            ptext = plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes, backgroundcolor='white')
            ptext.set_bbox(dict(alpha=0.8, color='white'))
        else:
            ptext = plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes)

    print_text(0.06, 0.92, "$\mathrm{pp}\\to\mathrm{tH}, \mathrm{t\\bar{t}H}$ (13 TeV)")

    ax.text( 2.50, 1.30, "tHq ($\kappa_{\mathrm{V}}=1.5)$", ha='center', va='center', size=16, color='red', rotation=79)
    ax.text( 2.65, 0.66, "tHq ($\kappa_{\mathrm{V}}=1.0)$", ha='center', va='center', size=16, color='red', rotation=67)
    ax.text(-2.50, 0.64, "tHq ($\kappa_{\mathrm{V}}=0.5)$", ha='center', va='center', size=16, color='red', rotation=-52)

    ax.text(-2.40, 1.10, "tHW ($\kappa_{\mathrm{V}}=1.5)$", ha='center', va='center', size=16, color='blue', rotation=-68)
    ax.text( 2.50, 0.19, "tHW ($\kappa_{\mathrm{V}}=1.0)$", ha='center', va='center', size=16, color='blue', rotation=33)
    ax.text(-2.30, 0.14, "tHW ($\kappa_{\mathrm{V}}=0.5)$", ha='center', va='center', size=16, color='blue', rotation=-17)
    
    ax.text(1.50, 1.40, "$\mathrm{t\\bar{t}H}$", ha='center', va='center', size=20, color='black', rotation=81)

    # Save to pdf/png
    outfile = os.path.join(outdir, 'xs_scaling')
    if alpha: outfile += '_alpha'
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
    parser.add_option("--smexp", dest="smexp", action="store_true",
                      help="Plot the SM expected limit")
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

    # plotXsecs(outdir=options.outdir,
    #          ymax=options.ymax,
    #          smoothing=options.smoothing,
    #          alpha=options.alpha)
    plotBRScalings(outdir=options.outdir,
                   smoothing=options.smoothing,
                   ymax=options.ymax,
                   alpha=options.alpha)
    sys.exit(0)
