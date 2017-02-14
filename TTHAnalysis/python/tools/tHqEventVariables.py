#!/usr/bin/env python
import os.path, types
import ROOT

from array import array
from math import log, exp

from CMGTools.TTHAnalysis.treeReAnalyzer import Collection
from itertools import combinations
from PhysicsTools.HeppyCore.utils.deltar import deltaPhi, deltaR


BTAGWP = 0.5426 # 0.8484 is for medium tags
# BTAGWP = 0.460 # 0.80 is for medium tags

class MVAVar:
    def __init__(self,name, form=None):
        self.name = name
        self.var  = array('f', [0.])
        self.form = form

    def set(self, event, ret={}):
        if self.name in ret:
            self.var[0] = ret[self.name]
        elif self.form:
            self.var[0] = event.eval(self.form)
        else:
            self.var[0] = event.eval(self.name)

def getCorrectedJetPt(jet, jec_syst=""):
    return {
        ""         : jet.pt,
        "_jecUp"   : jet.pt * jet.corr_JECUp/jet.corr,
        "_jecDown" : jet.pt * jet.corr_JECDown/jet.corr,
    }[jec_syst]

class tHqEventVariableFriend:
    def __init__(self):
        self.jecsysts = ["", "_jecUp", "_jecDown"] # Not sure we actually need these (only eta dependence)
        self.branches = [] # (branchname, default value)
        self.branches.append(("dPhiHighestPtSSPair", -99.9)) # delta phi highest pt same sign lepton pair
        self.branches.append(("minDRll", -99.9)) # minimum deltaR between all leptons
        for jecsyst in self.jecsysts:
            self.branches.append(("maxEtaJet25"+jecsyst, -99.9)) # max eta of any non-tagged jet
            self.branches.append(("fwdJetPt25"+jecsyst, -99.9)) # pt of the non-tagged jet with max eta
            self.branches.append(("nJetEta1"+jecsyst, -99.9)) # number of jets with |eta|>1.0
            self.branches.append(("dEtaFwdJetBJet"+jecsyst, -99.9)) # delta eta: max fwd jet and hardest bjet
            self.branches.append(("dEtaFwdJetClosestLep"+jecsyst,-99.9)) # delta eta: max fwd jet and closest lepton
            self.branches.append(("maxEtaBJet"+jecsyst, -99.9)) # max eta of the hardest Bjet
            self.branches.append(("maxEta2BJet"+jecsyst, -99.9)) # max Eta of the second hardest Bjet
            self.branches.append(("dEtaFwdJet2BJet"+jecsyst, -99.9)) # delta eta: max fwd jet and second hardest bjet
            self.branches.append(("dEtaBJet2BJet"+jecsyst, -99.9)) # delta eta: hardest bjet and second hardest bjet

        # Signal MVA
        self.mvavars = {}
        for jecsyst in self.jecsysts:
            self.mvavars['3l'+jecsyst] = [
                MVAVar(name="nJet25%s_Recl"%jecsyst),
                MVAVar(name="nJetEta1"+jecsyst),
                MVAVar(name="maxEtaJet25"+jecsyst),
                MVAVar(name="dEtaFwdJetBJet"+jecsyst),
                MVAVar(name="dEtaFwdJetClosestLep"+jecsyst),
                MVAVar(name="dPhiHighestPtSSPair"),
                MVAVar(name="LepGood_conePt[iLepFO_Recl[2]]"),
                MVAVar(name="minDRll"),
                MVAVar(name="LepGood_charge[iLepFO_Recl[0]]+LepGood_charge[iLepFO_Recl[1]]+LepGood_charge[iLepFO_Recl[2]]"),
                MVAVar(name="dEtaFwdJet2BJet"+jecsyst),
            ]
            self.mvavars['2lss'+jecsyst] = [
                MVAVar(name="nJet25%s_Recl"%jecsyst),
                MVAVar(name="nJetEta1"+jecsyst),
                MVAVar(name="maxEtaJet25"+jecsyst),
                MVAVar(name="dEtaFwdJetBJet"+jecsyst),
                MVAVar(name="dEtaFwdJetClosestLep"+jecsyst),
                MVAVar(name="dPhiHighestPtSSPair"),
                MVAVar(name="LepGood_conePt[iLepFO_Recl[1]]"),
                MVAVar(name="minDRll"),
                MVAVar(name="LepGood_charge[iLepFO_Recl[0]]+LepGood_charge[iLepFO_Recl[1]]"),
                MVAVar(name="dEtaFwdJet2BJet"+jecsyst),
            ]

        self.mvaspectators = [
            MVAVar(name="iLepFO_Recl[0]"),
            MVAVar(name="iLepFO_Recl[1]"),
            MVAVar(name="iLepFO_Recl[2]"),
        ]

        self.tmvaReaders = {}
        for channel in ['2lss', '3l']:
            self.tmvaReaders[channel] = ROOT.TMVA.Reader("Silent")
            self.tmvaReaders[channel].SetVerbose(True)
            for mvavar in self.mvavars[channel]:
                self.tmvaReaders[channel].AddVariable(mvavar.name, mvavar.var)
            for mvaspec in self.mvaspectators:
                self.tmvaReaders[channel].AddSpectator(mvaspec.name, mvaspec.var)

            for backgr in ['tt', 'ttv']:
                wfile = os.path.join(os.environ['CMSSW_BASE'],
                                     "src/CMGTools/TTHAnalysis/data/kinMVA/thq/",
                                     "thq_vs_%s_%s_BDTG.weights.xml"%(backgr,channel))
                self.tmvaReaders[channel].BookMVA("BDTG_"+backgr, wfile)
                for jecsyst in self.jecsysts:
                    self.branches.append(("thqMVA_%s_%s%s"%(backgr,channel,jecsyst), -99.9))

    def listBranches(self):
        """Return a list of branch names that are added"""
        return [bn for bn,_ in self.branches]

    def getJetCollection(self, event, jec_syst="", coll="JetSel", ptcut=25.):
        """Get a jet collection, either default or systematic variations"""
        if not hasattr(event, "n%s_Recl"%(coll)):
            raise RuntimeError("n%s_Recl not found" % (coll))
        jets = [j for j in Collection(event, "%s_Recl" % (coll), "n%s_Recl"%(coll))]

        # Apply JEC and re-apply the pt cut
        return filter(lambda j: getCorrectedJetPt(j, jec_syst) > ptcut, jets)

    def getLeptonCollection(self, event, label='LepGood', lenlabel='nLepFO_Recl'):
        """Get a lepton collection, either default or recleaned"""
        leptons = [l for l in Collection(event, label, 'n'+label)]

        try:
            _ileps_list = list(getattr(event, "iLepFO_Recl"))
            maxlen = int(getattr(event, lenlabel))
            _ileps_list = _ileps_list[:maxlen]
            return [leptons[il] for il in _ileps_list]

        except AttributeError:
            return leptons

    def __call__(self, event):
        # Set up dictionary with default values
        ret = {k:v for k,v in self.branches}

        # Get leptons
        leptons = self.getLeptonCollection(event, label="LepGood")

        sspairs = [(l1, l2) for l1, l2 in combinations(leptons, 2) if l1.pdgId*l2.pdgId > 0]
        if len(sspairs):
            lep1,lep2 = sorted(sspairs, key=lambda x:x[1],reverse=True)[0] # highest pt pair
            ret['dPhiHighestPtSSPair'] = abs(deltaPhi(lep1.phi,lep2.phi))

        else: # Fill this with the OS pair if there is no SS pair (for charge flip estimate)
            ospairs = [(l1, l2) for l1, l2 in combinations(leptons, 2) if l1.pdgId*l2.pdgId < 0]
            if len(ospairs):
                lep1,lep2 = sorted(ospairs, key=lambda x:x[1],reverse=True)[0] # highest pt pair
                ret['dPhiHighestPtSSPair'] = abs(deltaPhi(lep1.phi,lep2.phi))

        lepdrs = [deltaR(l1.eta, l1.phi, l2.eta, l2.phi) for l1, l2 in combinations(leptons, 2)]
        if len(lepdrs):
            ret['minDRll'] = min(lepdrs)

        for jecsyst in self.jecsysts:
            # Get jet collections
            jets  = self.getJetCollection(event, jec_syst=jecsyst)
            fjets = self.getJetCollection(event, jec_syst=jecsyst, coll="JetFwdSel")
            bjets = [j for j in jets if j.btagCSV > BTAGWP]
            bjets.sort(key=lambda x:x.pt, reverse=True)

            # All non-btagged jets with pt > 25 GeV
            light_jets =  [j for j in jets  if j.btagCSV < BTAGWP]
            light_jets += [j for j in fjets if j.btagCSV < BTAGWP]
            # Note that some fwd jets have btag values > 0 up to eta 3.05 or so
            light_jets.sort(key=lambda x:x.pt, reverse=True)

            # Get the most forward of these save its value
            if len(light_jets):
                maxjet = sorted(light_jets, key=lambda x:abs(x.eta), reverse=True)[0]
                ret['maxEtaJet25'+jecsyst] = abs(maxjet.eta)
                ret['fwdJetPt25'+jecsyst] = maxjet.pt
                if len(bjets):
                    ret['dEtaFwdJetBJet'+jecsyst] = abs(maxjet.eta - bjets[0].eta)

                if len(bjets)>1:
                    ret['dEtaFwdJet2BJet'+jecsyst] = abs(maxjet.eta - bjets[1].eta)
                    
                else: 
                    ret['dEtaFwdJet2BJet'+jecsyst] = -1.0

                if len(leptons):
                    detas = [abs(lep.eta - maxjet.eta) for lep in leptons]
                    ret['dEtaFwdJetClosestLep'+jecsyst] = sorted(detas)[0]

            ret['nJetEta1'+jecsyst] = len([j for j in light_jets if abs(j.eta) > 1.0])

            if(bjets):
                ret['maxEtaBJet'+jecsyst] = abs(bjets[0].eta)
                            
                if len(bjets)>1:
                    ret['maxEta2BJet'+jecsyst] = abs(bjets[1].eta)
                    ret['dEtaBJet2BJet'+jecsyst] = abs(bjets[0].eta - bjets[1].eta)

                else:
                    ret['maxEta2BJet'+jecsyst] = -1.0
                    ret['dEtaBJet2BJet'+jecsyst] = -1.0

        # Fix total charge for non-same sign events (for charge flips)
        br_lepcharge = "LepGood_charge[iLepFO_Recl[0]]+LepGood_charge[iLepFO_Recl[1]]" 
        if event.eval(br_lepcharge) == 0:
            ret[br_lepcharge] = event.eval("LepGood_charge[iLepFO_Recl[0]]")
            # Now mvavar.set should read this instead

        # Signal MVA
        for channel in ['2lss', '3l']:
            for mvavar in self.mvavars[channel]:
                mvavar.set(event, ret)

            for backgr in ['tt', 'ttv']:
                ret["thqMVA_%s_%s"%(backgr,channel)] = self.tmvaReaders[channel].EvaluateMVA("BDTG_"+backgr)

                # Systematics
                for jecsyst in self.jecsysts[1:]:
                    inputVec = ROOT.vector('double')()
                    for mvavar in self.mvavars[channel+jecsyst]:
                        mvavar.set(event, ret)
                        inputVec.push_back(mvavar.var[0])
    
                    ret["thqMVA_%s_%s%s"%(backgr,channel,jecsyst)] = self.tmvaReaders[channel].EvaluateMVA(inputVec,"BDTG_"+backgr)
                        
                        # print ret["thqMVA_%s_%s"%(backgr,channel)]
                        # print self.tmvaReaders[channel].EvaluateMVA(inputVec, "BDTG_"+backgr)

            # Need to remove br_lepcharge from ret again?
            ret.pop(br_lepcharge, None)

        return ret

MODULES = [('tHqEventVariables', tHqEventVariableFriend())]

##################################################
# Test this friend producer like so:
# >> python tHqEventVariables.py tree.root
# or so:
# >> python tHqEventVariables.py tree.root friend_tree.root

if __name__ == '__main__':
    from sys import argv
    treefile = ROOT.TFile.Open(argv[1])
    tree = treefile.Get("tree")
    tree.vectorTree = True
    print "... processing %s" % argv[1]

    try:
        friendfile = ROOT.TFile.Open(argv[2])
        friendtree = friendfile.Get("sf/t")
        tree.AddFriend(friendtree)
        print "... adding friend tree from %s" % argv[2]
    except IndexError:
        pass

    from CMGTools.TTHAnalysis.treeReAnalyzer import EventLoop, Module

    class Tester(Module):
        def __init__(self, name):
            Module.__init__(self,name,None)
            self.thqf = tHqEventVariableFriend()
            print "Adding these branches:", self.thqf.listBranches()

        def analyze(self,ev):
            print ("\nrun %6d lumi %4d event %d: jets %d, fwdJets %d, leps %d, isdata=%d" %
                      (ev.run, ev.lumi, ev.evt, ev.nJet25, ev.nJetFwd, ev.nLepGood, int(ev.isData)))
            ret = self.thqf(ev)

            print 'maxEtaJet25:', ret['maxEtaJet25'], ret['maxEtaJet25_jecUp']
            print 'nJet1:', ret['nJetEta1'], ret['nJetEta1_jecUp']
            print 'dEtaFwdJetBJet',ret['dEtaFwdJetBJet'],ret['dEtaFwdJetBJet_jecUp']
            print 'dEtaFwdJetClosestLep',ret['dEtaFwdJetClosestLep'],ret['dEtaFwdJetClosestLep_jecUp']
            print 'dPhiHighestPtSSPair', ret['dPhiHighestPtSSPair']
            print 'minDRll', ret['minDRll']
            print 'thqMVA_ttv_2lss      ', ret['thqMVA_ttv_2lss']
            print 'thqMVA_ttv_2lss_jecUp', ret['thqMVA_ttv_2lss_jecUp']
            # print 'thqMVA_tt_2lss', ret['thqMVA_tt_2lss']
            # print 'thqMVA_ttv_3l', ret['thqMVA_ttv_3l']
            # print 'thqMVA_tt_3l', ret['thqMVA_tt_3l']


            # print 'maxEtaBJet:', ret['maxEtaBJet']
            # print 'maxEta2BJet:', ret['maxEta2BJet']
            # print 'dEtaFwdJet2BJet',ret['dEtaFwdJet2BJet']
            # print 'dEtaBJet2BJet',ret['dEtaBJet2BJet']


            # add additional printout here to make sure everything is consistent

        def done(self):
            pass

    T = Tester("tester")
    el = EventLoop([ T ])
    el.loop([tree], maxEvents = 20)
    T.done()
