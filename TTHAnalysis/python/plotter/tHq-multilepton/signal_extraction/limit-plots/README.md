# tHq limit plotting

Use the workspaces produced in the previous step and the `extract_signal_scalings.py` script to produce the csv files with cross section and branching fraction scalings for each model (`br_scalings_K6.csv`, `xsbr_scalings_K6.csv`). The `process_xsec_scalings.py` script turns these into .csv files with actual cross sections.

The plotting is done in the `plotLimits.py` and `plotNLLScans.py` scripts, which take .json configuration files as input. Note that this requires `matplotlib`, `scipy`, `seaborn`, and `jupyter` libraries to be installed.


## Installation

1. Check out only this folder:

```
git init limit-plots
cd limit-plots
git remote add stiegerb git@github.com:stiegerb/cmgtools-lite.git
git config core.sparsecheckout true
echo "TTHAnalysis/python/plotter/tHq-multilepton/signal_extraction/limit-plots/" >> .git/info/sparse-checkout
git checkout -b 80X_M17_tHqJan30_bbcombination
git pull --depth=1 stiegerb 80X_M17_tHqJan30_bbcombination
cd TTHAnalysis/python/plotter/tHq-multilepton/signal_extraction/limit-plots/
```

2. Install necessary python packages (better with virtualenv):

Might need to upgrade pip and/or install virtualenv

```
[pip install --upgrade pip]
[pip install virtualenv]
virtualenv pyplot
source pyplot/bin/activate
pip install -r requirements.txt [--user]
```

One more caveat to run the plotting scripts, as matplotlib doesn't play well with virtual envs we need to run the framework installation of python to call them. Either call it by hand like so:

```
export PYTHONHOME=$VIRTUAL_ENV
/usr/local/bin/python2.7 plot_xs_limits.py
```

Or put a function `fwpython` in your .bashrc like so:

```bash
function fwpython {
    if [[ ! -z "$VIRTUAL_ENV" ]]; then
        PYTHONHOME=$VIRTUAL_ENV /usr/local/bin/python "$@"
    else
        /usr/local/bin/python "$@"
    fi
}
```

3. Running the plotting scripts

Once everything is set up, we only need to enter the virtual env and call the fw python:

```
source pyplot/bin/activate
fwpython plotLimits.py limits_K5b.json
fwpython plotNLLScans.py nll_scan_K5.json
```
