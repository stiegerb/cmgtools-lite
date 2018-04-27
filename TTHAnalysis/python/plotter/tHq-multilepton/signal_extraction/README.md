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

Generate the workspaces from the cards, using `make_workspaces.sh`, which calls `text2workspace.py`, e.g. for the K6 model:

```
make_workspaces.sh K6 *.card.root
```

Then use `runAllLimits.py` to run on all the workspaces (cards) in one directory and produce a .csv file with the kt/kV points, the expected limit, and the one and two sigma bands.

```
python runAllLimits.py -t comb6 
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

<!-- Check that the fit result is `r=0` and that pulls for the background only fit are all 0.00.
Check that the fit result is `r=1` and that pulls for the signal+background fit are all 0.00.
 -->
### Limits using HCG models (scaling BRs with couplings)
Note that all of these assume that the input yields (the 'rate' line in the datacards) correspond to standard model cross sections!

A few possibilities:

- 'lambda_FV' in [LambdasReduced](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/74x-root6/python/LHCHCGModels.py#L626-L788) is basically our Ct/CV, 'kappa_VV' should correspond to CV^2.

- Could also use [KappaVKappaF](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/blob/74x-root6/python/LHCHCGModels.py#L522-L624) which directly has Ct and CV (as 'kappa_F', 'kappa_V').

- Currently using [KappaTKappaV](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit/pull/369), either with K4 (resolved) or K5 (non-resolved)

All of these need to have '13TeV' string in bin names. We can use `combineCards.py` for that, or just our `combineChannels.py`.

```
combineCards.py tHq_3l_1_m1_13TeV=tHq_3l_1_m1.card.txt &> tHq_3l_1_m1_13TeV.txt
```

To use the models, we need to use `text2workspace.py` to produce a RooWorkspace with all the scaling functions, etc. (e.g. for K5):

```
text2workspace.py tHq_1_m1.card.txt \
-P HiggsAnalysis.CombinedLimit.LHCHCGModels:K5 \
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
make_workspaces.sh K5 *.card.txt
python runAllLimits.py -t K5 *K5.card.root
```

### Limits ala Gritsan (no BR scaling)
If we assume the relative fractions of WW/ZZ/tautau are the same for constant kt/kV (which is true if ktau=kt), we can set cross section limits for 33 distinct points of kt/kV (or kt**2/(kt**2+kV**2)) which are then valid for all other possible kt and kV points with the same ratio. To do so, we now just have to let tHq and tHW float with the ttH scale for a given point.

Note that tHq and tHW are proportional to kt**2 (and therefore r_ttH) for fixed kt/kV ratios. The relative fractions then depend on the value of the ratio as follows (where a = kt/kV):

- r_tHq = (2.633 + 3.578/a**2 - 5.211/a) * r_ttH
- r_tHW = (2.909 + 2.310/a**2 - 4.220/a) * r_ttH
- r_ttH is left floating

We can make a workspace with these scaling by using the `HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel` with mapping commands. We just have to provide the kt/kV ratio (e.g. for a kt=-3, kV=1.5 point):

```
text2workspace.py tHq_1p5_m3.card.txt -o ws_tHq_1p5_m3_K6.card.root \
-P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel -m 125 \
--PO 'map=.*/ttH.*:r_ttH[1,-5,10]' \
--PO 'map=.*/tHq.*:r_tHq=expr::r_tHq("(2.633+3.578/(@1*@1)-5.211/(@1))*@0",r_ttH,-2.00)' \
--PO 'map=.*/tHW.*:r_tHW=expr::r_tHW("(2.909+2.310/(@1*@1)-4.220/(@1))*@0",r_ttH,-2.00)'
```

### Run the unblinded fit
To run the final fit on the unblinded data:

```
combine -M MaxLikelihoodFit \
--saveShapes --saveWithUncertainties \
--setPhysicsModelParameters kappa_t=-1.0,kappa_V=1.0 \
--freezeNuisances kappa_t,kappa_V,kappa_tau,kappa_mu,kappa_b,kappa_c,kappa_g,kappa_gam \
--redefineSignalPOIs r \
ws_tHq_1_m1_K6.card.root
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

