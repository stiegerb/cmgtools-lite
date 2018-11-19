## Producing parton friend trees

Test on a handful of events (from `TTHAnalysis/python/tools/`):

```
python matchJetsToPartons.py tree.root recleaner.root
```

Produce the entire friend tree (from `TTHAnalysis/macros`)
```
python prepareEventVariablesFriendTree.py -m matchJetsToPartons -I CMGTools.TTHAnalysis.tools.matchJetsToPartons -t treeProducerSusyMultilepton -N 100000 ttWgen_production_Nov1/ x_matchedJets_Nov1 -d TTWToLNu_fxfx -F sf/t ttWgen_production_Nov1/1_recleaner_011118/evVarFriend_{cname}.root -j 0 --tra2 -q 8nh
```

Run with `-c 0 -N 10000 -j 0` and without `-q 8nh` to test locally on a few thousand events first.

## Make plots

Run `ttH-multileptons/ttWGenPlots/makettWplots.sh outputdir`


