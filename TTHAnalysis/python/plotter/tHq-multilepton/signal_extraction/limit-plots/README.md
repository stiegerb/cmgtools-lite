# tHq limit plotting

Use the workspaces produced in the previous step and the `extract_signal_scalings.py` script to produce the csv files with cross section and branching fraction scalings for each model (`br_scalings_K6.csv`, `xsbr_scalings_K6.csv`). The `signal_scalings.ipynb` jupyter notebook then multiplies the scale factors with the SM cross sections and BR's to produce csv files with the actual cross sections. These, together with the limit files, are used in the `limits.ipynb` notebook to produce a final csv file containing the cross section times BR limits used in the plot.

The plotting is done in the `plot_xs_limits.py` script. Note that this requires `matplotlib`, `scipy`, `seaborn`, and `jupyter` libraries to be installed.
