# tHq signal extraction procedure

### Produce datacards:

```
python makeShapeCardsTHQ.py \
--savefile report_thq_3l.root \
tHq-multilepton/signal_extraction/mca-thq-3l-mcdata-frdata_limits.txt \
tHq-multilepton/cuts-thq-3l.txt \
thqMVA_ttv_3l:thqMVA_tt_3l 40,-1,1,40,-1,1 \
tHq-multilepton/signal_extraction/systsEnv.txt \
-P treedir/mixture_jecv6prompt_datafull_jul20/ \
-P treedir/tHq_production_Jan11/ \
--tree treeProducerSusyMultilepton \
--s2v -j 8 -l 12.9 -f \
--xp data --asimov \
-F sf/t treedir/tHq_eventvars_Jan18/evVarFriend_{cname}.root \
--Fs {P}/2_recleaner_v5_b1E2 \
--mcc ttH-multilepton/lepchoice-ttH-FO.txt \
--neg \
-o 3l \
--od tHq-multilepton/signal_extraction/cards \
-L tHq-multilepton/functionsTHQ.cc \
--2d-binning-function "10:tHq_MVAto1D_3l_10" \
-v 2
```

- Change from `--savefile report.root` to `--infile report.root` to rerun quickly with a different binning.
- Binning function in `tHq-multilepton/functionsTHQ.cc`. This turns the 2d histogram of mva1 vs mva2 into a 1d histogram for shape fitting in combine.
- Keep track of reporting of empty bins and adjust binning function accordingly.

This produces two files for each point: `..input.root` and `..card.txt`.

Note that the standard selection is hardcoded in `tHq-multilepton/makecards.sh`.

Check some of the datacards using `HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py`:

```
systematicsAnalyzer.py data.card.txt --all -f html > www/systanalysis.html
```

### Run single limit calculations:

You'll need to set your environment to a release area with `combine` available, e.g. like so:

```
cd ~stiegerb/combine707/; cmsenv ; cd -;
```

Run on a single datacard you can use combine directly:

```
combine -M AsymptoticLimits --run blind --rAbsAcc 0.0005 --rRelAcc 0.0005 ttH_3l.card.txt
```

or use `runAllLimits.py cards/ttH_3l.card.txt` to do everything in one go.

In case of several datacards, combine them first with `combineCards.py *card.txt > combined.txt`.

Then the "Expected 50.0%" is the number to be quoted.


### Combining several channels

Use `combineChannels.py` to consistently combine cards for several points from different channels. The script looks for matching card files (`*.card.txt`) in the input directories, then calls `combineCards.py` on them, and moves the input root files into the output directory.

Note that it assumes a certain order of the channels (2lss_mm, 2lss_em, 3l, bb_3m, bb_4m, bb_dilep) by default, and will name the output channels accordingly. Change this order with the `-c/--binnames` option.

Also assumes that cards are named in a certain scheme for the different kt/kV points. They need to match the `.*\_([\dpm]+\_[\dpm]+)\.card\.txt` regular expression, e.g. tHq_2lss_mm_1p5_m1p25.card.txt, etc.

Example command:

```
python combineChannels.py 2lss_mm/ 2lss_em/ 3l/ bb_3m/ bb_4m/ bb_dilep/ -o comb6
```

To rename the cards from the bb channel following a different naming scheme, use the `renamebbCards.py` script.

To change the outdated luminosity uncertainty from 1.026 to 1.025, rename btagging uncertainties, and change to the new autoMCStats feature in the multilepton cards, use the `fixNuisancesInMultilepCards.py` script.

Note: there's a little bug in combine (see [here](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/81x-root606/python/NuisanceModifier.py#L100) and [here](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/issues/467)), that causes trouble with the `nuisance edit rename ...` feature and overlapping nuisance names. If you get errors of histograms not found with btagging nuisances, hack that line in `NuisanceModifier.py` in your combine area.


### Running limits for several kt/kV points

Generate the workspaces from the cards, using `makeWorkspaces.py`, which calls `text2workspace.py`, e.g. for the K6 model:

```
makeWorkspaces.py K6 *.card.root -j 8
```

Then use `runAllLimits.py` to run on all the workspaces (cards) in one directory and produce a .csv file with the kt/kV points, the expected limit, and the one and two sigma bands.

```
python runAllLimits.py -t comb6 ws_tHq_*_K7.root -j 8
```

Run it with `-u/--unblind` to run the limits unblinded and add a column for the observed limit in the csv file.


### Making impact and pull plots

Note that you'll need the `combineTool.py` for this. See [here](https://twiki.cern.ch/twiki/bin/view/CMS/SWGuideHiggsAnalysisCombinedLimit) for instructions.

Generate the workspace:

```
text2workspace.py -o tHq_cards.root comb3/tHq_1_m1.card.txt
```

```
combineTool.py -M Impacts -d tHq_1_1.card.root -m 125 --robustFit 1 --rMin -5 --rMax 10 --doInitialFit --setParameters kappa_t=1.0,kappa_V=1.0 --freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam --redefineSignalPOIs r

combineTool.py -M Impacts -d tHq_1_1.card.root -m 125 --robustFit 1 --rMin -5 --rMax 10 --doFits --parallel 12 --setParameters kappa_t=1.0,kappa_V=1.0 --freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam --redefineSignalPOIs r

combineTool.py -M Impacts -d tHq_1_1.card.root -m 125 -o impacts.json  --setParameters kappa_t=1.0,kappa_V=1.0 --freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam --redefineSignalPOIs r

plotImpacts.py -i impacts.json -o impacts --per-page 20
```

These additional fit options may be necessary to make it converge:
```
--robustFit 1 --rMin=0 --rMax=20
--X-rtd ADDNLL_RECURSIVE=0
--setCrossingTolerance 1E-6
--cminDefaultMinimizerStrategy 0
--cminDefaultMinimizerTolerance 0.01
--cminPreScan.
```

Note that this may require the renaming of root files:
```
for f in *123456.root; do mv $f ${f%.123456.root}.root; done
```

### Fit Diagnostics

See also [here](https://twiki.cern.ch/twiki/bin/view/CMS/HiggsWG/HiggsPAGPreapprovalChecks) and [here](https://cms-hcomb.gitbooks.io/combine/content/part3/nonstandard.html#fitting-diagnostics) for instructions.

```
combine -M FitDiagnostics --setParameters kappa_t=1.0,kappa_V=1.0 --freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam --redefineSignalPOIs r tHq_1_m1.card.txt
python diffNuisances.py fitDiagnostics.root
```

### Limits using HCG models (scaling BRs with couplings)
Note that all of these assume that the input yields (the 'rate' line in the datacards) correspond to standard model cross sections!

All of these need to have '13TeV' string in bin names. We can use `combineCards.py` for that, or just our `combineChannels.py`.

```
combineCards.py tHq_3l_1_m1_13TeV=tHq_3l_1_m1.card.txt &> tHq_3l_1_m1_13TeV.txt
```

To use the models, we need to use `text2workspace.py` to produce a RooWorkspace with all the scaling functions, etc. (e.g. for K7):

```
text2workspace.py tHq_1_m1.card.txt \
-P HiggsAnalysis.CombinedLimit.LHCHCGModels:K7 \
--PO verbose \
--PO BRU=0 \
-m 125
```

This workspace now contains the proper scaling functions of the higgs processes. 

To run the limit for a given point, we need to specify the kappa values at that point and redefine the parameter of interest as the signal strength. We freeze all the other nuisances.

```
combine -M AsymptoticLimits \
--run blind \
--rAbsAcc 0.0005 --rRelAcc 0.0005 \
--setParameters kappa_t=-1.0,kappa_V=1.0 \
--freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam \
--redefineSignalPOIs r \
tHq_1_m1.root
```

Can also redefine the range of a parameter, in case it's necessary, using `--setParameterRanges kappa_t=-4,4`.
See also `runAllLimits.py` for the combine commands to use.

Use -m 125 in text2workspace.py or combine in case you get `<ROOT::Math::GSLInterpolator::Eval>: input domain error` messages.

Recipe with shortcut scripts:

```
python combineChannels -o comb3 2lss_mm/ 2lss_em/ 3l/
makeWorkspaces.py K5 *.card.txt -j 8
runAllLimits.py -t K5 *K5.card.root -j 8
```

### Limits on tHq/tHW only
Using either the `multisignalModel` or the `LHCHCGModels:A1` signal strengths model, we can produce a limit on just tH production (or on ttH production):

```
text2workspace.py tHq_1_1.card.txt -o ws_tHq_1_1_A1.root -P HiggsAnalysis.CombinedLimit.LHCHCGModels:A1 -m 125
combine -M AsymptoticLimits --redefineSignalPOIs mu_XS_tH ws_tHq_1_1_A1.root -m 125
```

or equivalently:

```
text2workspace.py tHq_1_1.card.txt -o ws_tHq_1_1_MSM_tHonly.root -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -m 125  --PO 'map=.*/tH[qW].*:r_tH[1,-5,10]'
combine -M AsymptoticLimits --redefineSignalPOIs r_tH ws_tHq_1_1_MSM_tHonly.root
```

Note that we need to be on the `comb2017` branch of combine for the A1 model to work with this.

### Run the unblinded fit
To run the final fit on the unblinded data:

```
combine -M FitDiagnostics \
--saveShapes --saveWithUncertainties \
--setParameters kappa_t=-1.0,kappa_V=1.0 \
--freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam \
--redefineSignalPOIs r \
ws_tHq_1_m1_K6.card.root
```

Again we might need additional fit options to have it converge:

```
--robustFit 1 --rMin=0 --rMax=20
--X-rtd ADDNLL_RECURSIVE=0
--setCrossingTolerance 1E-6
--cminDefaultMinimizerStrategy 0.
```

This will produce the `mlfit.root` file needed to produce post-fit plots (using `postFitPlotsTHQ.py`).


### Produce expected numbers with SM-like Asimov data
Instead of producing expected limits using a background-only (i.e. non-Higgs) dataset, we want to show limits and significances with a dataset containing also the SM-like tH and ttH processes.

We already have a datacard/workspace for the SM point, and we can use it to generate toys with a signal strength of 1, e.g. like so:

```
combine -M GenerateOnly -m 125 --verbose 3 -n _SMtoys \
--setParameters kappa_t=1.0,kappa_V=1.0 \
--freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam --redefineSignalPOIs r \
--expectSignal=1 \
-t 100 -s 123456 --saveToys \
ws_tHq_1_1_K6.card.root
```

This produces a file `higgsCombine_SMtoys.GenerateOnly.mH125.123456.root` that can now be read when running the Asymptotic limits:

```
combine -M AsymptoticLimits --run observed  -m 125 --verbose 0 \
--setParameters kappa_t=-1.0,kappa_V=1.0 \
--freezeParameters kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam --redefineSignalPOIs r \
-t 100 --toysFile higgsCombine_SMtoys.GenerateOnly.mH125.123456.root \
workspacesK6/ws_tHq_1_m1_K6.card.root
```

Which in turn will use the observed limits from those Asimov toys to generate the median and the 68%/95% bands.

Note that there is an (as yet) undocumented feature of `combineTools.py` that allows to split the jobs by calling the seed option with `-s 1:100:1` when generating, and again when running the limit by using the same seed range option and putting a `%(SEED)s` placeholder in the `--toysFile` option.


All of this is automatized in `runSMExpectedLimits.py`.

1. Generate 10 times 100 toys with different seeds, from a single workspace:

```
runSMExpectedLimits.py workspaces/ws_tHq_1_1_K6.card.root --generate --ntoys 100 --split 10 --queue 8nh --printCommand
```

2. Calculate the limits for the models in a bunch of workspaces for each of these 1000 toys, running on lxbatch:

```
runSMExpectedLimits.py workspaces/ws_*.root --ntoys 100 --split 10 --queue 2nd --printCommand --toysfile "smexp/higgsCombine_SMtoys_100_cvct_1_1.GenerateOnly.mH125.%(SEED)s.root"
```

3. Gather the statistics from the log files of these jobs, calculate mean, median, and 68%/95% bands, and store in a .csv file ordered by kt/kV ratio:

```
python limitStatsFromCombineLogs.py *.log
```

### Produce NLL scans

To produce a likelihood scan, we can run combine with the `MultiDimFit` option and `--algo fixed --fixedPointPOIs`, once with r=1 and once with r=0. This first runs the nominal fit with floating signal strength, then repeats the fit with fixed signal strength, and reports the difference in log likelihood values. By always running one fit with r=0 (which is identical in each point), we can use that likelihood value as the reference and subtract it from the r=1 difference, to get comparable numbers for the likelihood outputs of the nominal fits.

The exact fit options are:
```
combine -M MultiDimFit --algo fixed --fixedPointPOIs r=1 \
 --rMin=0 --rMax=20 --X-rtd ADDNLL_RECURSIVE=0 \
 --cminDefaultMinimizerStrategy 0 \
 -m 125 --verbose 0 -n _nll_scan_r1_tag
 --setParameters kappa_t=<ct>/<cv>,kappa_V=1.0 \
 --freezeParameters kappa_t,kappa_V,kappa_mu,kappa_b, \
kappa_c,kappa_g,kappa_gam,r_others \
--redefineSignalPOIs r \
workspace.root
```

(and then repeated with `--fixedPointPOIs r=0`).

This produces the scan for the fit to observed data. To produce the expected likelihood scan, we repeat the procedure, but use toy data produced for the SM point. Generated with:

```
combine -M GenerateOnly -t -1 -m 125 \
--setParameters r=1.0,kappa_t=1.0,kappaV=1.0 \
--freezeParameters kappa_t,kappa_V,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam,r_others \
--saveToys \
workspace_SM.root
```

and passed to the scanning options above with `-t -1 --toysFile toy.root`.

The resulting series of likelihood values are adjusted such that the lowest value is at zero (by simply subtracting the lowest value from each point).


### Fit tH and ttH simultaneously

To assess the correlation between tH and ttH signal strengths, we can run a multidimensional fit floating both simultaneously and then investigate the 2-dimensional likelihood scan. We use the `A1` model from above, which includes the relevant POIs `mu_XS_tH`, `mu_XS_ttH`, and `mu_XS_ttHtH`.

To just float both and get the minimum point, we can use `-M MultiDimFit --algo singles`:
```
combine -M MultiDimFit --algo singles ws_tHq_1_1_A1.root \
--redefineSignalPOIs mu_XS_tH,mu_XS_ttH --autoBoundsPOIs=* \
-m 125 --verbose 0 -n testing \
--X-rtd ADDNLL_RECURSIVE=0 --X-rtd MINIMIZER_analytic \
--cminDefaultMinimizerTolerance 0.01 --cminDefaultMinimizerStrategy 0 --cminPreScan
```

To produce a grid of likelihood points in a certain range, we use `--algo grid --points N`. The `--fastScan` option skips the profiling of nuisances and speeds up by a factor 10-100.

```
combine -M MultiDimFit --algo grid --points 10000 ws_tHq_1_1_A1.root  \ 
--redefineSignalPOIs mu_XS_ttH,mu_XS_tH \
--setParameterRanges mu_XS_tH=-5,20:mu_XS_ttH=0.0,5.0 \ 
--fastScan \
-m 125 --verbose 0 -n testing \
--X-rtd ADDNLL_RECURSIVE=0 --X-rtd MINIMIZER_analytic \
--cminDefaultMinimizerTolerance 0.01 --cminDefaultMinimizerStrategy 0 --cminPreScan
```

To run the full scan (without `--fastScan`), we submit jobs to lxbatch:

```
combineTool.py -d ws_tHq_1_1_A1.root -M MultiDimFit  --algo grid --points 10000 \
--redefineSignalPOIs mu_XS_ttH,mu_XS_tH  \
--setParameterRanges mu_XS_tH=-5,20:mu_XS_ttH=0.0,5.0  \
--job-mode lxbatch  \
--split-points 100 --sub-opts='-q 8nh' --task-name tHttH_grid \
-m 125 --verbose 0 -n grid_tH_ttH_comb7 \
--X-rtd ADDNLL_RECURSIVE=0 --X-rtd MINIMIZER_analytic \
--cminDefaultMinimizerTolerance 0.01 --cminDefaultMinimizerStrategy 0 --cminPreScan \
```

See also the relevant sections in the combine help for additional info:
https://cms-hcomb.gitbooks.io/combine/content/part3/commonstatsmethods.html#likelihood-fits-and-scans
https://cms-hcomb.gitbooks.io/combine/content/part3/runningthetool.html#submission-to-lsf-batch

