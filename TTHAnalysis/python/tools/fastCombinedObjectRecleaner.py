from CMGTools.TTHAnalysis.treeReAnalyzer import Collection, deltaR
from CMGTools.TTHAnalysis.tools.collectionSkimmer import CollectionSkimmer
import ROOT, os

class fastCombinedObjectRecleaner:

    def __init__(self,label,inlabel,cleanTausWithLooseLeptons,cleanJetsWithFOTaus,doVetoZ,doVetoLMf,doVetoLMt,jetPts,btagL_thr,btagM_thr):

        self.label = "" if (label in ["",None]) else ("_"+label)
        self.inlabel = inlabel

        self.vars = ["pt","eta","phi","mass"]
        self.vars_leptons = ["pdgId"]
        self.vars_taus = ["idMVAdR03"]
        self.vars_jets = ["btagCSV","qgl","corr","corr_JECUp","corr_JECDown"]
        self.vars_jets_nooutput = []

        self.cleanTausWithLooseLeptons = cleanTausWithLooseLeptons
        self.cleanJetsWithFOTaus = cleanJetsWithFOTaus
        self.jetPts = jetPts

        self.systsJEC = {0:"", 1:"_jecUp", -1:"_jecDown"}

        self.outmasses=['mZ1','minMllAFAS','minMllAFOS','minMllAFSS','minMllSFOS']
        self._outjetvars = ['htJet%dj','mhtJet%d','nBJetLoose%d','nBJetMedium%d','nJet%d']
        self.outjetvars=[]
        self.outfwdjetvars=[]
        for jetPt in self.jetPts:
            self.outjetvars.extend([(x%jetPt+y,'I' if ('nBJet' in x or 'nJet' in x) else 'F') for x in self._outjetvars for y in self.systsJEC.values()])
            self.outfwdjetvars.extend([("nJetFwd%d"%jetPt+y, 'I') for y in self.systsJEC.values()])

        self.branches = [var+self.label for var in self.outmasses]
        self.branches.extend([(var+self.label,_type) for var,_type in self.outjetvars+self.outfwdjetvars])
        self.branches += [("LepGood_conePt","F",20,"nLepGood")]

        self._helper_lepsF = CollectionSkimmer("LepFO"+self.label, "LepGood", floats=[], maxSize=20, saveSelectedIndices=True,padSelectedIndicesWith=0)
        self._helper_lepsT = CollectionSkimmer("LepTight"+self.label, "LepGood", floats=[], maxSize=20, saveTagForAll=True)
        self._helper_taus = CollectionSkimmer("TauSel"+self.label, "TauGood", floats=self.vars, ints=self.vars_taus, maxSize=20)
        self._helper_jets = CollectionSkimmer("JetSel"+self.label, "Jet", floats=self.vars+self.vars_jets, maxSize=20)
        self._helper_fwdjets = CollectionSkimmer("JetFwdSel"+self.label, "JetFwd", floats=self.vars+self.vars_jets, maxSize=20)
        self._helpers = [self._helper_lepsF,self._helper_lepsT,self._helper_taus,self._helper_jets,self._helper_fwdjets]

        if "/fastCombinedObjectRecleanerHelper_cxx.so" not in ROOT.gSystem.GetLibraries():
            print "Load C++ recleaner worker module"
            ROOT.gROOT.ProcessLine(".L %s/src/CMGTools/TTHAnalysis/python/tools/fastCombinedObjectRecleanerHelper.cxx+O" % os.environ['CMSSW_BASE'])
        self._worker = ROOT.fastCombinedObjectRecleanerHelper(self._helper_taus.cppImpl(),
                                                              self._helper_jets.cppImpl(),
                                                              self._helper_fwdjets.cppImpl(),
                                                              self.cleanJetsWithFOTaus,
                                                              btagL_thr, btagM_thr)
        for x in self.jetPts: self._worker.addJetPt(x)

        if "/fastCombinedObjectRecleanerMassVetoCalculator_cxx.so" not in ROOT.gSystem.GetLibraries():
            print "Load C++ recleaner mass and veto calculator module"
            ROOT.gROOT.ProcessLine(".L %s/src/CMGTools/TTHAnalysis/python/tools/fastCombinedObjectRecleanerMassVetoCalculator.cxx+O" % os.environ['CMSSW_BASE'])
        self._workerMV = ROOT.fastCombinedObjectRecleanerMassVetoCalculator(self._helper_lepsF.cppImpl(),self._helper_lepsT.cppImpl(),doVetoZ,doVetoLMf,doVetoLMt)

    def init(self,tree):
        self._ttreereaderversion = tree._ttreereaderversion
        for x in self._helpers:
            x.initInputTree(tree)
        self.initReaders(tree)
        self.initWorkers()

    def setOutputTree(self,pytree):
        for x in self._helpers: x.initOutputTree(pytree);

    def initReaders(self,tree):
        for coll in ["LepGood","TauGood","Jet","JetFwd"]:
            setattr(self,'n'+coll,tree.valueReader('n'+coll))
            _vars = self.vars[:]
            if coll=='LepGood': _vars.extend(self.vars_leptons)
            if coll=='TauGood': _vars.extend(self.vars_taus)
            if coll=='Jet':    _vars.extend(self.vars_jets+self.vars_jets_nooutput)
            if coll=='JetFwd': _vars.extend(self.vars_jets+self.vars_jets_nooutput)
            for B in _vars:
                setattr(self,"%s_%s"%(coll,B), tree.arrayReader("%s_%s"%(coll,B)))

    def initWorkers(self):
        self._worker.setLeptons(self.nLepGood, self.LepGood_pt, self.LepGood_eta, self.LepGood_phi)
        self._worker.setTaus(self.nTauGood, self.TauGood_pt, self.TauGood_eta, self.TauGood_phi)
        self._worker.setJets(self.nJet, self.Jet_pt, self.Jet_eta, self.Jet_phi, 
                             self.Jet_btagCSV, self.Jet_corr, self.Jet_corr_JECUp, self.Jet_corr_JECDown)
        self._worker.setFwdJets(self.nJetFwd, self.JetFwd_pt, self.JetFwd_eta, self.JetFwd_phi, 
                                self.JetFwd_btagCSV, self.JetFwd_corr, self.JetFwd_corr_JECUp, self.JetFwd_corr_JECDown)
        self._workerMV.setLeptons(self.nLepGood, self.LepGood_pt, self.LepGood_eta, self.LepGood_phi, self.LepGood_mass, self.LepGood_pdgId)

    def listBranches(self):
        return self.branches

    def __call__(self,event):
        ## Init
        if any([x.initEvent(event) for x in self._helpers]):
            self.initReaders(event._tree)
            self.initWorkers()

        tags = getattr(event,'_CombinedTagsForCleaning%s'%self.inlabel)
        ret = {}
        ret['LepGood_conePt'] = [tags.leps_conept[i] for i in xrange(self.nLepGood.Get()[0])]

        self._worker.clear()
        self._worker.loadTags(tags,self.cleanTausWithLooseLeptons)
        self._worker.run()

        for delta,varname in self.systsJEC.iteritems():
            for x in self._worker.GetJetSums(delta):
                for var in self._outjetvars: ret[var%x.thr+varname+self.label]=getattr(x,var.replace('%d',''))

        self._workerMV.clear()
        self._workerMV.loadTags(tags)
        self._workerMV.run()

        masses = self._workerMV.GetPairMasses()
        for var in self.outmasses: ret[var+self.label] = getattr(masses,var)
        return ret

MODULES=[]
