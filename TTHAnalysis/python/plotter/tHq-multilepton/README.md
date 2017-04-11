# Specific instructions for the tHq analysis

### Add the remotes for Benjamin's repository and get the `80X_M17_tHqJan30` branch:

```
git remote add stiegerb https://github.com/stiegerb/cmgtools-lite.git -f -t 80X_M17_tHqJan30
git checkout -b 80X_M17_tHqJan30 stiegerb/80X_M17_tHqJan30
git push -u origin 80X_M17_tHqJan30
```

A current set of minitree outputs is at:
```
/afs/cern.ch/work/p/peruzzi/tthtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2/
```
You might have to ask Marco Peruzzi for access rights to it.

----------------

### Producing mini trees

It's advisable to put the version of the code used for a production on a separate branch on github. The branch used for the Moriond 2017 samples is on the `80X_M17` branch on [Marco's github](https://github.com/peruzzim/cmgtools-lite/tree/80X_M17/TTHAnalysis/cfg).

Set it up like so:

```
cd $CMSSW_BASE/src
git remote add peruzzim https://github.com/peruzzim/cmg-cmssw.git -t 80X_M17  -f
git checkout -b heppy_80X peruzzim/heppy_80X
# Clean and recompile
scram b clean
scram b -j 9
```

The samples are defined in files in `CMGTools/RootTools/python/samples/`, e.g. in `samples_13TeV_RunIISummer16MiniAODv2.py`. So to add or update a sample, define it in the appropriate file there.

The configuration file used to run the production is:
```
TTHAnalysis/cfg/run_ttH_cfg.py
```

To run on specific samples, edit the code around [these lines](https://github.com/peruzzim/cmgtools-lite/blob/80X_M17/TTHAnalysis/cfg/run_ttH_cfg.py#L217).

The command to test running on the first file of the first sample is then:
```
heppy myTest run_ttH_cfg.py -p 0 -o nofetch -j 1 -o test=1
```

Note that the first time running will take a while, as it submits DAS queries for all the samples and caches the results (in `~/.cmgdatasets/`). Note also that you need a valid grid certificate for the DAS queries to work (`voms-proxy-init -voms cms -rfc` to get a valid token; check [this TWiki](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookStartingGrid#ObtainingCert) on how to get a certificate).

Check that the output is ok before submitting jobs to the batch to run on the full samples. To submit to batch, you use these commands:

```
heppy_batch.py -r /store/user/<username>/remote_output -o local_directory --option analysis=susy run_ttH_cfg.py -b 'bsub -q 1nd -u <username> -o std_output.txt -J job_name < batchScript.sh'
```

The relevant options are: `-r remote_dir` to specify an output directory on eos (or don't specify to store locally); `-o dirname` for the local directory name; `-J job_name` to specify the name of the jobs.

Once the jobs are completed, check that they are all there, i.e. that you have an output directory for each chunk. Then you can check if each of the output directories is ok by using `heppy_check.py outputdir/`, and finally merge the chunks by running `heppy_hadd.py outputdir/` -c.

----------------

### Producing friend trees

Friend trees are trees containing additional information to the original trees. Each entry (i.e. event) in the original trees has a corresponding entry in the friend tree. For the tHq analysis we create friend trees with additional event variables related to forward jets, e.g. the eta of the most forward jet in each event.

The main python class calculating this information for is in the file `python/tools/tHqEventVariables.py`. The `__call__` method of that class is called once per event and returns a dictionary associating each branch name to the value for that particular event. Currently, the class only calculates and stores the highest eta of any jet with pT greater than 25 GeV (stored in a branch named "maxEtaJet25").

The class can be tested on a few events of a minitree by simply running `python tHqEventVariables.py tree.root`.

To produce the friend trees for many samples and events, a separate handler script is used, saved in `macros/prepareEventVariablesFriendTree.py`. It takes as first argument a directory with minitrees outputs, and as second argument a directory where it will store the output. To run it on a few events of a single sample, you can do this:
```
python prepareEventVariablesFriendTree.py -m tHqEventVariables -I CMGTools.TTHAnalysis.tools.tHqEventVariables -t treeProducerSusyMultilepton -N 10000 ra5trees/809_June9_ttH/ tHq_eventvars_Aug5 -d TTHnobb_mWCutfix_ext1 -c 1
```

Or, with a friend tree included:
```
python prepareEventVariablesFriendTree.py -m tHqEventVariables -I CMGTools.TTHAnalysis.tools.tHqEventVariables -t treeProducerSusyMultilepton -N 10000 ra5trees/809_June9_ttH/ tHq_eventvars_Oct21 -d TTHnobb_mWCutfix_ext1 -c 1 -F sf/t ra5trees/809_June9_ttH/2_recleaner_v5_b1E2/evVarFriend_{cname}.root
```

You should use this to figure out how fast your producer is running, and adjust the chunk size (`-N` option) to have jobs of reasonable run times. (200000 seems a reasonable choice for the current version.) Once this works, you can submit all the jobs for all samples to lxbatch, by running something like this:
```
python prepareEventVariablesFriendTree.py -m tHqEventVariables -I CMGTools.TTHAnalysis.tools.tHqEventVariables -t treeProducerSusyMultilepton -N 200000 ra5trees/809_June9_ttH/ tHq_eventvars_Aug11 -q 8nh
```

Note that the `-q` option specifies the queue to run on. The most common options would be `8nh` for jobs shorter than 8 hours, or `1nd` for jobs shorter than one day (24 hours). Keep an eye on the status of the jobs with the `bjobs` command, and look at the output of a running job with `bpeek <jobid>`. The STDOUT and STDERR log files of each job are stored in a directory named `LSFJOB_<jobid>`.

Once all the jobs have finished successfully, you can check the output files using the `friendChunkCheck.sh` script: cd to the output directory and run `friendChunkCheck.sh evVarFriend`. If there is no output from the script, all the chunks are present. To merge the junks, there is a similar script in `macros/leptons/friendChunkAdd.sh`. Run it with `. ../leptons/friendChunkAdd.sh evVarFriend`, inside the output directory.

If that went ok, you can remove all the chunk files and are left with only the friend tree files.

For producing the recleaner friends, selecting a few processes (example):

```
python prepareEventVariablesFriendTree.py -m leptonJetFastReCleanerTTH_step1 -m leptonJetFastReCleanerTTH_step2_mc -I CMGTools.TTHAnalysis.tools.functionsTHQ -t treeProducerSusyMultilepton -N 1000000 tthtrees/TREES_TTH_250117_Summer16_JECV3_noClean_qgV2/ 1_thq_recleaner_240217_full -D TTJets_.* -D DYJetsToLL_.*_LO -D WJetsToLNu_LO -D T_tch_powheg -D TToLeptons_sch -D WWTo2L2Nu -D TBar.* -D T_tWch_ext --tra2 -q 8nh
```

----------------

### Making basic plots using `mcPlots.py`

The main script for making basic plots in the framework is in `python/plotter/mcPlots.py`, which uses the classes in `mcAnalysis.py` (for handling the samples) and `tree2yield.py` (for getting yields/histograms from the trees). It accepts three text files as inputs, one specifying the data and MC samples to be included, one listing the selection to be applied, and one configuring the variables to be plotted. Examples for these there files are in the `python/plotter/tHq-multilepton/` directory (where this README is also), with some explanation on their format in comments inside the files.

A full example for making plots with all corrections is the following:

```
python mcPlots.py \
tHq-multilepton/mca-thq-3l-mcdata-frdata.txt \
tHq-multilepton/cuts-thq-3l.txt \
tHq-multilepton/plots-thq-3l-kinMVA.txt \
--s2v \
--tree treeProducerSusyMultilepton \
--showRatio --poisson \
-j 8 \
-f \
-P treedir/mixture_jecv6prompt_datafull_jul20/ \
-l 12.9 \
--pdir tHq-multilepton/plots_Sep9/ \
-F sf/t treedir/tHq_eventvars_Jan18/evVarFriend_{cname}.root \
--Fs {P}/2_recleaner_v5_b1E2 \
--mcc ttH-multilepton/lepchoice-ttH-FO.txt \
--mcc ttH-multilepton/ttH_2lss3l_triggerdefs.txt \
-W 'puw2016_nTrueInt_13fb(nVert)'
```

Note that this uses some symbolic links to the corresponding tree directories.

The important options are:

- `-P treedir/`: Input directory containing the minitree outputs. Can give multiple paths, the code will look through them in order.
- `--pdir plotdir/`: The output directory for the plots
- `-l 12.9`: Integrated luminosity to scale the MC to (in inverse femtobarn)
- `-j 8`: Number of processes to run in parallel
- `-f`: Only apply the full set of cuts at once. Without this, it will produce sequential plots for each line in the cut file.
- `-F sf/t directory/evVarFriend_{cname}.root`: Add the tree named `sf/t` in these files as a friend
- `--mcc textfile.txt`: Read this file defining new branches as shortcuts
- `-W 'weightexpression'`: Apply this event weight

If everything goes according to plan, this will produce an output directory with the plots in `.pdf` and `.png` format, a text file with the event yields, as well as a copy of the mca, cut, and plot files, the command string used, and a root file with the raw histograms.

Note that the main plots are now hardcoded in `makeplots.sh`. Run that by calling `./makeplots.sh outputdir selectplots` where `selectplots` is one of the tags specified in the script, e.g. `3l`, `2lss-mm-ttcontrol`, etc.

----------------

### Some tips

- It's useful to have a symbolic link to the directory containing the minitree outputs in your working directory. E.g. like this:

```
ln -s /afs/cern.ch/work/p/peruzzi/ra5trees/809_June9_ttH
```

- Often we store the minitree files on eos, and save only a text file (`tree.root.url` in place of `tree.root`) with the location (something like `root://eoscms.cern.ch//eos/cms/store/...`). You can open them in one go like this:

```
root `cat /afs/cern.ch/user/p/peruzzi/work/ra5trees/809_June9_ttH/TTHnobb_mWCutfix_ext1/treeProducerSusyMultilepton/tree.root.url`
```

