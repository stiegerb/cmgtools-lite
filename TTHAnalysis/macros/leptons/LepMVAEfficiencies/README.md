## Produce lepton MVA efficiency maps

#### Content

- `lepTnPFriendTreeMaker.cc`: TTree::MakeClass based macro that processes trees produced with the `treeProducerSusyMultiLepton` analyzer. Selects dilepton events (see `SelectEvent` method) consistent with DY, then looks for tag leptons passing a given selection (see `SelectTagElectron`, `SelectTagMuon` methods). For each found tag lepton, looks for a probe lepton such that the pair passes a given selection (see `SelectPair`). The tree is then filled with a few properties of the tag lepton and the pair, and all necessary properties of the probe lepton to be flexible enough to calculate efficiencies.

- `runLepTnPFriendMaker.py`: Python script to steer the `lepTnPFriendTreeMaker` class and run it on all input files in a given directory (locally or on eos). Note that for remote files it will copy them to a local temp directory first (`/tmp/username/` by default) to speed up the process. When running on data, some of the MC-only branches are not found in the tree, so errors like `<TTree::SetBranchAddress>: unknown branch` are expected.

- `makeLepTnPFriends.py`: Python script to do the mass fit for each bin in pt, eta, nvertices, etc. and produce the efficiency plots and maps. Note that by default it expects a merged file for the data trees.

- `makeXSecWeights.py`: Use the sample definition file (by `default samples_13TeV_RunIISpring16MiniAODv2.py`) to find cross sections and the `SkimReport.pck` pickle files to find number of processed events, and generate sample weights. These are used to weight MC samples when running `makeLepTnPFriends.py`.

- `singleFit.py`: Just run a single fit (for testing).

------------

#### Instructions to run

First, compile the tree class: ```root -l -b -q -n lepTnPFriendTreeMaker.cc+```

Produce the tag and probe trees:

```
python runLepTnPFriendMaker.py /eos/cms/store/cmst3/group/tthlep/peruzzi/TREES_TTH_050218_Fall17_JECV1NoRes/ --frienddir /path/to/8_vtxWeight2017_v1/ -q 8nh
```

By default, this will process all files in that directory containing `2017` or `DYJetsToLL_M50_LO_part` strings. For debugging, you can use the `-f/--filter` option to restrict to individual samples and the `-m` option to process only a certain number of events. To run in parallel, use the `-j/--jobs` option. To submit to batch, use the `-q/--queue` option.

By default, the output is stored in a directory called `tnptrees/`. You can change this with the `-o/--outDir` option.

Note that samples are checked to be data or not depending on whether their file name contains the string `2017`.

Merge the data trees:

```
hadd tnptrees/Run2017.root tnptrees/*2017*.root
```

Generate the cross section weights (stored in `.xsecweights.pck` by default):

```
python makeXSecWeights.py treeDir/
```

(Note that without this, MC samples will just be used unweighted, so this is only necessary when mixing MC processes.)

Finally, run the fits and make the plots using `makeLepTnPFriends.py`. Modify the global variables at the top of the script to configure the binnings, pair selections, event selections, probe selections, and input files. Beware that the script caches the mass histograms and the passed and total histograms in pickle files (`masshistos.pck` and `tnppassedtotal.pck` by default) after the first run.

```
python makeLepTnPFriends.py tnptrees/ -j 8
```

Note: when running in parallel mode, a warning message (`*** Break *** write on a pipe with no one to read it`) is normal.

