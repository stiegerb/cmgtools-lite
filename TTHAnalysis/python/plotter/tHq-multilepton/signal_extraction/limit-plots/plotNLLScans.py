#!/usr/bin/env python
import os
import re
import sys
import json
import numpy as np
import pandas as pd

from functools import partial
from collections import namedtuple
from scipy.interpolate import splev, splrep

import matplotlib.pyplot as plt
import matplotlib as mpl

import seaborn as sns
sns.set(style="ticks")
sns.set_context("poster")

from process_limits import scale_limits
from plotLimit import readConfig
from plotLimit import setUpMPL


def process(inputfile):
    df = pd.read_csv(inputfile, sep=",", index_col=None)
    # Calculate relative NLL
    df['dnll'] = 2*(df.nllr1 - df.nllr0)

    # Add in ratio column if it's not there
    if not 'ratio' in df.columns:
        try:
            df['ratio'] = df.cf/df.cv
            df['ratio'] = df.ratio.round(3)
        except AttributeError:
            print "Failed to build ratio column in dataframe... check input file"

    # Drop duplicates for equal ratios
    df.drop_duplicates(subset='ratio', inplace=True)
    df.sort_values(by='ratio', inplace=True)
    df.index = range(1,len(df)+1)

    # Shift dnll up by lowest value
    dnllmin = np.min(df.dnll)
    idxmin = df.dnll.idxmin()
    assert(df.loc[idxmin].dnll == dnllmin), "inconsistent minimum?"
    print '... shifting dnll values by %5.3f (at %4.2f) for %s' % (np.abs(dnllmin), df.loc[idxmin].ratio, inputfile)
    df['dnll'] = df.dnll + np.abs(dnllmin)
    return df


def plotNLLScans(config, outdir='plots/', tag='', nosplines=False):
    for entry in config['entries']:
        filename = entry['csv_file']
        if 'inputdir' in config:
            filename = os.path.join(config['inputdir'], entry['csv_file'])
        entry['df'] = process(filename)

    fig, ax = plt.subplots(1)

    x = sorted(list(set(config['entries'][0]['df'].ratio.values.tolist())))
    x2 = np.linspace(-6, 6, 100) # Evaluate spline at more points

    for entry in config['entries']:
        df = entry['df']
        if nosplines:
            ax.plot(df.loc[df.ratio<=config['xmax']].loc[df.ratio>=-config['xmax']].ratio,
                    df.loc[df.ratio<=config['xmax']].loc[df.ratio>=-config['xmax']].dnll,
                    lw=entry['line_width'], c=entry['color'], ls=entry['line_style'])
        else:
            spline = splev(x2, splrep(df.ratio, df.dnll, s=0.0, k=3))
            ax.plot(x2, spline, ls=entry['line_style'], lw=entry['line_width'], color=entry['color'],zorder=0)
        ax.scatter(df.loc[df.ratio<=config['xmax']].loc[df.ratio>=-config['xmax']].ratio,
                   df.loc[df.ratio<=config['xmax']].loc[df.ratio>=-config['xmax']].dnll,
                marker=entry['marker_style'], s=30, c=entry['color'], lw=entry['line_width'])

    # Configure axes
    ax.get_xaxis().set_tick_params(which='both', direction='in')
    ax.get_xaxis().set_major_locator(mpl.ticker.MultipleLocator(1.0))
    ax.get_xaxis().set_minor_locator(mpl.ticker.MultipleLocator(0.10))
    ax.set_xlim(-config['xmax'], config['xmax'])

    ax.axhline(1.0, lw=0.5, ls='--', color='gray')
    ax.axhline(4.0, lw=0.5, ls='--', color='gray')
    ax.axhline(9.0, lw=0.5, ls='--', color='gray')
    ax.axhline(16.0, lw=0.5, ls='--', color='gray')
    ax.axhline(25.0, lw=0.5, ls='--', color='gray')
    plt.text(-config['xmax'] + 0.02*config['xmax'], 1.15, "1$\\sigma$", fontsize=14, color='gray')
    plt.text(-config['xmax'] + 0.02*config['xmax'], 4.15, "2$\\sigma$", fontsize=14, color='gray')
    plt.text(-config['xmax'] + 0.02*config['xmax'], 9.15, "3$\\sigma$", fontsize=14, color='gray')
    plt.text(-config['xmax'] + 0.02*config['xmax'], 16.15, "4$\\sigma$", fontsize=14, color='gray')
    plt.text(-config['xmax'] + 0.02*config['xmax'], 25.15, "5$\\sigma$", fontsize=14, color='gray')

    ax.set_ylim(0., config['ymax'])
    ax.set_yscale("linear", nonposy='clip')
    ax.get_yaxis().set_tick_params(which='both', direction='in')
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(config['y_major_ticks']))
    ax.get_yaxis().set_minor_locator(mpl.ticker.MultipleLocator(config['y_minor_ticks']))

    # Set axis labels
    ax.set_xlabel(config['x_axis_label'], fontsize=24, labelpad=20)
    ax.set_ylabel(config['y_axis_label'], fontsize=24, labelpad=20)

    def print_text(x, y, text, fontsize=24, addbackground=True, bgalpha=0.8):
        if addbackground:
            ptext = plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes, backgroundcolor='white')
            ptext.set_bbox(dict(alpha=bgalpha, color='white'))
        else:
            ptext = plt.text(x, y, text, fontsize=fontsize, transform=ax.transAxes)

    # Print stuff
    print_text(0.03, 1.02, config["header_left"], 28, addbackground=False)
    print_text(0.65, 1.02, config["header_right"], addbackground=False)
    print_text(0.06, 0.92, config["tag1"], bgalpha=config["text_bg_alpha"])
    print_text(0.06, 0.86, config["tag2"], bgalpha=config["text_bg_alpha"])
    print_text(0.06, 0.78, config["tag3"], bgalpha=config["text_bg_alpha"])

    # Cosmetics
    import matplotlib.patches as mpatches
    legentries = []
    for entry in config['entries']:
        legentries.append(mpl.lines.Line2D([], [],
                          color=entry['color'], linestyle=entry['line_style'],
                          label=entry['label'], marker=entry['marker_style'], markersize=14, linewidth=2))

    # Legend
    legend = plt.legend(handles=legentries, fontsize=18, loc='upper right', 
                        frameon=True, framealpha=config["text_bg_alpha"])
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_linewidth(0)

    # Save to pdf/png
    outfile = os.path.join(outdir, config['name'])
    # outfile = os.path.join(outdir, os.path.splitext(os.path.basename(config['entries'][0]['csv_file']))[0])
    if tag:
        outfile += '_%s' % tag
    plt.savefig("%s.pdf"%outfile, bbox_inches='tight')
    plt.savefig("%s.png"%outfile, bbox_inches='tight', dpi=300)
    print "...saved plot in %s.pdf" % outfile

    return 0

if __name__ == '__main__':
    from optparse import OptionParser
    usage = """%prog config.json"""
    parser = OptionParser(usage=usage)
    parser.add_option("-o","--outdir", dest="outdir",
                      type="string", default="plots/")
    parser.add_option("-t","--tag", dest="tag",
                      type="string", default="")
    parser.add_option("--nosplines", dest="nosplines",
                      action="store_true", default=False)
    parser.add_option("--defaultOptions", dest="defaultOptions",
                      type="string", default="defaults_nllscan.json",
                      help="Config file for default options")

    parser.add_option("--ymax", dest="ymax", type='float',
                      default=None, help="Y axis maximum")
    parser.add_option("--xmax", dest="xmax", type='float',
                      default=None, help="X axis maximum/minimum")
    parser.add_option("--y_major_ticks", dest="y_major_ticks", type='float',
                      default=None, help="Major ticks on y axis")
    parser.add_option("--y_minor_ticks", dest="y_minor_ticks", type='float',
                      default=None, help="Minor ticks on y axis")
    (options, args) = parser.parse_args()

    try:
        os.system('mkdir -p %s' % options.outdir)
    except ValueError:
        pass

    setUpMPL()
    for ifile in args:
        if not os.path.exists(ifile):
            print "Ignoring %s" % ifile
            continue

        plotConfig = readConfig(options.defaultOptions, options=options)
        plotConfig.update(readConfig(ifile))

        # Do fixes here
        for attr in ['xmax', 'ymax', 'y_major_ticks', 'y_minor_ticks']:
            if getattr(options, attr, None) is not None:
                plotConfig[attr] = float(getattr(options, attr, plotConfig[attr]))
        
        plotNLLScans(plotConfig, outdir=options.outdir, tag=options.tag, nosplines=options.nosplines)

    sys.exit(0)
