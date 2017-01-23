#!/usr/bin/env python
import ROOT
from CMGTools.TTHAnalysis.plotter.mcAnalysis import addMCAnalysisOptions, MCAnalysis, CutsFile, mergePlots
from CMGTools.TTHAnalysis.plotter.tree2yield import mergePlots
import re, sys, os, os.path, math

def mkOneSpline():
    x_vec,y_vec = ROOT.std.vector('double')(), ROOT.std.vector('double')()
    for x in range(10):
        x_vec.push_back(100*x) 
        y_vec.push_back(1) 
    spline = ROOT.ROOT.Math.Interpolator(x_vec,y_vec);
    spline._x = x_vec
    spline._y = y_vec
    return spline

SPLINES = {
    'ttH' : mkOneSpline(),
    'hww' : mkOneSpline(),
    'hzz' : mkOneSpline(),
    'htt' : mkOneSpline(),
}
def getYieldScale(mass,process):
    if "ttH_" not in process: return 1.0
    scale = SPLINES['ttH'].Eval(mass)
    for dec in "hww","hzz","htt":
        if dec in process: 
            scale *= SPLINES[dec].Eval(mass)
            if 'efficiency_'+dec in SPLINES:
                scale *= SPLINES['efficiency_'+dec].Eval(mass)
            break
    return scale 

def rebin2Dto1D(h, funcstring):
    nbins,fname = funcstring.split(':',1)
    func = getattr(ROOT,fname)
    nbins = int(nbins)
    goodname = h.GetName()
    h.SetName(goodname+"_oldbinning")
    newh = ROOT.TH1D(goodname,h.GetTitle(),nbins,0.5,nbins+0.5)
    x = h.GetXaxis()
    y = h.GetYaxis()
    allowed = range(1,nbins+1)
    if 'TH2' not in h.ClassName(): raise RuntimeError, "Calling rebin2Dto1D on something that is not TH2"
    for i in xrange(x.GetNbins()):
        for j in xrange(y.GetNbins()):
            bin = int(func(x.GetBinCenter(i+1),y.GetBinCenter(j+1)))
            if bin not in allowed: raise RuntimeError, "Binning function gives not admissible result"
            newh.SetBinContent(bin,newh.GetBinContent(bin)+h.GetBinContent(i+1,j+1))
            newh.SetBinError(bin,math.hypot(newh.GetBinError(bin),h.GetBinError(i+1,j+1)))
    for bin in range(1,nbins+1):
        if newh.GetBinContent(bin)<0:
            print 'Warning: cropping to zero bin %d in %s (was %f)'%(bin,newh.GetName(),newh.GetBinContent(bin))
            newh.SetBinContent(bin,0)
    newh.SetLineWidth(h.GetLineWidth())
    newh.SetLineStyle(h.GetLineStyle())
    newh.SetLineColor(h.GetLineColor())
    return newh

class ShapeCardMaker:
    """docstring for ShapeCardMaker"""
    def __init__(self, mcafile, cutsfile, var, bins, systsfile, options):
        self.mcafile = mcafile
        self.cutsfile = cutsfile
        self.var = var
        self.bins = bins
        self.systfile = systfile
        self.options = options
    
        self.mca = MCAnalysis(mcafile, options)
        self.cuts = CutsFile(cutsfile, options)

        self.truebinname = options.outname or os.path.basename(cutsfile).replace(".txt","")
        self.binname = truebinname if truebinname[0] not in "234" else "ttH_"+truebinname

def produceReport(mca, variable, bins, cuts, outfilename, options):
    report = {}
    if options.infile != None:
        infile = ROOT.TFile(options.infile, "read")
        for proc in mca.listSignals(True) + mca.listBackgrounds(True) + ['data']:
            histo = infile.Get(proc)
            if histo: report[proc] = histo
    else:
        report = mca.getPlotsRaw("x", variable, bins, cuts.allCuts(), nodata=options.asimov)

    if options.savefile != None:
        savefile = ROOT.TFile(outfilename, "recreate")
        for n,h in report.iteritems():
            savefile.WriteTObject(h,n)
        savefile.Close()

    if options.asimov:
        tomerge = []
        for p in mca.listSignals() + mca.listBackgrounds():
            if p in report: tomerge.append(report[p])
        report['data_obs'] = mergePlots("x_data_obs", tomerge) 
    else:
        report['data_obs'] = report['data'].Clone("x_data_obs") 

    return report

def produceYields(mca, report):
    allyields = dict([(p,h.Integral()) for p,h in report.iteritems()])
    processes = []
    iproc = {}
    for i,s in enumerate(mca.listSignals()):
        if allyields[s] == 0: continue
        processes.append(s)
        iproc[s] = i-len(mca.listSignals())+1

    for i,b in enumerate(mca.listBackgrounds()):
        if allyields[b] == 0: continue
        processes.append(b)
        iproc[b] = i+1
    
    return allyields, processes, iproc

def parseSystsFile(filename, options):
    systs = {}
    systsEnv = {}
    with open(filename, 'r') as sysfile:
        for line in sysfile:
            if re.match("\s*#.*", line): continue
            line = re.sub("#.*","",line).strip()
            if len(line) == 0: continue

            field = [f.strip() for f in line.split(':')]
            if len(field) < 4:
                raise RuntimeError, "Malformed line %s in file %s"%(line.strip(),sysfile)

            # Pure normalization
            elif len(field) == 4 or field[4] == "lnN":
                (name, procmap, binmap, amount) = field[:4]
                if re.match(binmap+"$",truebinname) == None: continue
                if name not in systs: systs[name] = []
                systs[name].append( (re.compile(procmap+"$"), amount) )

            # Shape systematics
            elif field[4] in ["envelop","shapeOnly","templates",
                              "alternateShape","alternateShapeOnly"] or '2D' in field[4]:
                (name, procmap, binmap, amount) = field[:4]
                if re.match(binmap+"$",truebinname) == None: continue
                if name not in systs: systsEnv[name] = []
                systsEnv[name].append( (re.compile(procmap+"$"), amount, field[4]) )

            # Bin by bin statistics
            elif field[4] in ["stat_foreach_shape_bins"]:
                (name, procmap, binmap, amount) = field[:4]
                if re.match(binmap+"$",truebinname) == None: continue
                if name not in systsEnv: systsEnv[name] = []
                systsEnv[name].append( (re.compile(procmap+"$"), amount, field[4], field[5].split(',')) )

            else:
                raise RuntimeError, "Unknown systematic type %s" % field[4]

        if options.verbose:
            print "Loaded %d systematics" % len(systs)
            print "Loaded %d envelope systematics" % len(systsEnv)
    return systs, systsEnv

def parseSystsFiles(syst_filenames, processes, options):
    systs = {}
    systsEnv = {}

    # Parse files
    for sysfile in syst_filenames:
        parsed_systs, parsed_systsEnv = parseSystsFile(sysfile, options)
        systs.update(parsed_systs)
        systsEnv.update(parsed_systsEnv)

    return systs, systsEnv

def parseNormalizationSysts(systs, processes, mca):
    for name in systs.keys():
        effmap = {}
        for proc in processes:
            effect = "-"
            for (procmap,amount) in systs[name]:
                if re.match(procmap, proc):
                    effect = amount

            if mca._projection != None and effect not in ["-","0","1"]:
                if "/" in effect:
                    eff_up, eff_down = effect.split("/")
                    effect = "%.3f/%.3f" % (mca._projection.scaleSyst(name, float(eff_up)),
                                            mca._projection.scaleSyst(name, float(eff_down)))
                else:
                    effect = str(mca._projection.scaleSyst(name, float(effect)))

            effmap[proc] = effect
        systs[name] = effmap

    return systs

def parseShapeSysts1(systsEnv, mca, report):
    systsEnv1 = {}

    for name in systsEnv.keys():
        modes = [entry[2] for entry in systsEnv[name]]
        for _m in modes:
            if _m != modes[0]: raise RuntimeError, "Not supported"

        # do only this before rebinning
        if not (any([re.match(x+'.*', modes[0]) for x in ["envelop","shapeOnly"]])): continue
        effmap0  = {}
        effmap12 = {}
        for proc in processes:
            effect = "-"
            effect0  = "-"
            effect12 = "-"
            for entry in systsEnv[name]:
                procmap,amount,mode = entry[:3]
                if re.match(procmap, proc):
                    effect = amount
                    if mode not in ["templates", "alternateShape", "alternateShapeOnly"]:
                        effect = float(amount)

            if mca._projection != None and effect not in ["-","0","1",1.0,0.0] and type(effect) == type(1.0):
                effect = mca._projection.scaleSyst(name, effect)

            if effect == "-" or effect == "0": 
                effmap0[proc]  = "-" 
                effmap12[proc] = "-" 
                continue

            if any([re.match(x+'.*',mode) for x in ["envelop","shapeOnly"]]):
                nominal = report[proc]
                p0up = nominal.Clone(nominal.GetName()+"_"+name+"0Up"  ); p0up.Scale(effect)
                p0dn = nominal.Clone(nominal.GetName()+"_"+name+"0Down"); p0dn.Scale(1.0/effect)
                p1up = nominal.Clone(nominal.GetName()+"_"+name+"1Up"  );
                p1dn = nominal.Clone(nominal.GetName()+"_"+name+"1Down");
                p2up = nominal.Clone(nominal.GetName()+"_"+name+"2Up"  );
                p2dn = nominal.Clone(nominal.GetName()+"_"+name+"2Down");
                nbinx = nominal.GetNbinsX()
                xmin = nominal.GetXaxis().GetBinCenter(1)
                xmax = nominal.GetXaxis().GetBinCenter(nbinx)
                if '2D' in mode:
                    if 'TH2' not in nominal.ClassName():
                        raise RuntimeError, 'Trying to use 2D shape systs on a 1D histogram'
                    nbiny = nominal.GetNbinsY()
                    ymin = nominal.GetYaxis().GetBinCenter(1)
                    ymax = nominal.GetYaxis().GetBinCenter(nbiny)
                c1def = lambda x: 2*(x-0.5) # straight line from (0,-1) to (1,+1)
                c2def = lambda x: 1 - 8*(x-0.5)**2 # parabola through (0,-1), (0.5,~1), (1,-1)
                if '2D' not in mode:
                    if 'TH1' not in nominal.ClassName():
                        raise RuntimeError, 'Trying to use 1D shape systs on a 2D histogram'+nominal.ClassName()+" "+nominal.GetName()
                    for b in xrange(1,nbinx+1):
                        x = (nominal.GetBinCenter(bx)-xmin)/(xmax-xmin)
                        c1 = c1def(x)
                        c2 = c2def(x)
                        p1up.SetBinContent(b, p1up.GetBinContent(b) * pow(effect,+c1))
                        p1dn.SetBinContent(b, p1dn.GetBinContent(b) * pow(effect,-c1))
                        p2up.SetBinContent(b, p2up.GetBinContent(b) * pow(effect,+c2))
                        p2dn.SetBinContent(b, p2dn.GetBinContent(b) * pow(effect,-c2))
                else:
                    # e.g. shapeOnly2D_1.25X_0.83Y with effect == 1 will do an anti-correlated shape
                    # distortion of the x and y axes by 25% and -20% respectively
                    parsed = mode.split('_')
                    if len(parsed)!=3 or parsed[0]!="shapeOnly2D" or effect!=1:
                        raise RuntimeError, 'Incorrect option parsing for shapeOnly2D: %s %s'%(mode,effect)
                    effectX = float(parsed[1].strip('X'))
                    effectY = float(parsed[2].strip('Y'))
                    for bx in xrange(1,nbinx+1):
                        for by in xrange(1,nbiny+1):
                            x = (nominal.GetXaxis().GetBinCenter(bx)-xmin)/(xmax-xmin)
                            y = (nominal.GetYaxis().GetBinCenter(by)-ymin)/(ymax-ymin)
                            c1X = c1def(x)
                            c2X = c2def(x)
                            c1Y = c1def(y)
                            c2Y = c2def(y)
                            p1up.SetBinContent(bx,by, p1up.GetBinContent(bx,by) * pow(effectX,+c1X) * pow(effectY,+c1Y))
                            p1dn.SetBinContent(bx,by, p1dn.GetBinContent(bx,by) * pow(effectX,-c1X) * pow(effectY,-c1Y))
                            p2up.SetBinContent(bx,by, nominal.GetBinContent(bx,by))
                            p2dn.SetBinContent(bx,by, nominal.GetBinContent(bx,by))
                p1up.Scale(nominal.Integral()/p1up.Integral())
                p1dn.Scale(nominal.Integral()/p1dn.Integral())
                p2up.Scale(nominal.Integral()/p2up.Integral())
                p2dn.Scale(nominal.Integral()/p2dn.Integral())
                if "shapeOnly" not in mode:
                    report[proc+"_"+name+"0Up"]   = p0up
                    report[proc+"_"+name+"0Down"] = p0dn
                    effect0 = "1"
                report[proc+"_"+name+"1Up"]   = p1up
                report[proc+"_"+name+"1Down"] = p1dn
                effect12 = "1"
                # useful for plotting
                for h in p0up, p0dn, p1up, p1dn, p2up, p2dn: 
                    h.SetFillStyle(0); h.SetLineWidth(2)
                for h in p1up, p1dn: h.SetLineColor(4)
                for h in p2up, p2dn: h.SetLineColor(2)
            effmap0[proc]  = effect0 
            effmap12[proc] = effect12 
        systsEnv1[name] = (effmap0,effmap12,mode)

    return systsEnv1

def doRebinning(binfunction, report, mca):
    newhistos = {}

    # THIS:
    _to_be_rebinned = {}
    for n,h in report.iteritems():
        _to_be_rebinned[h.GetName()] = h
    for n,h in _to_be_rebinned.iteritems():
        thisname = h.GetName()
        newhistos[thisname] = rebin2Dto1D(h, options.binfunction)
    # REPLACED BY: ?
    # for histo in report.values():
    #     newhistos[histo.GetName()] = rebin2Dto1D(histo, options.binfunction)

    for n,h in report.iteritems():
        report[n] = newhistos[h.GetName().replace('_oldbinning','')]

def parseShapeSysts2(systsEnv, mca, report, processes, options):
    systsEnv2={}
    for name in systsEnv.keys():
        modes = [entry[2] for entry in systsEnv[name]]
        for _m in modes:
            if _m != modes[0]: raise RuntimeError, "Not supported"

        # do only this before rebinning
        if (any([re.match(x+'.*', modes[0]) for x in ["envelop","shapeOnly"]])): continue

        effmap0  = {}
        effmap12 = {}
        for proc in processes:
            effect = "-"
            effect0  = "-"
            effect12 = "-"
            for entry in systsEnv[name]:
                procmap,amount,mode = entry[:3]
                if re.match(procmap, proc):
                    effect = amount
                    if mode not in ["templates","alternateShape", "alternateShapeOnly"]:
                        effect = float(amount)
                    morefields = entry[3:]

            if mca._projection != None and effect not in ["-","0","1",1.0,0.0] and type(effect) == type(1.0):
                effect = mca._projection.scaleSyst(name, effect)

            if effect == "-" or effect == "0": 
                effmap0[proc]  = "-" 
                effmap12[proc] = "-" 
                continue

            if mode in ["stat_foreach_shape_bins"]:
                if mca._projection != None:
                    raise RuntimeError,'mca._projection.scaleSystTemplate not implemented in the case of stat_foreach_shape_bins'

                nominal = report[proc]
                if 'TH1' in nominal.ClassName():
                    for bin in xrange(1,nominal.GetNbinsX()+1):
                        for binmatch in morefields[0]:
                            if re.match(binmatch+"$",'%d'%bin):
                                if nominal.GetBinContent(bin) == 0 or nominal.GetBinError(bin) == 0:
                                    if nominal.Integral() != 0: 
                                        print "WARNING: for process %s in truebinname %s, bin %d has zero yield or zero error." % (proc,truebinname,bin)
                                    break

                                if (effect*nominal.GetBinError(bin)<0.1*math.sqrt(nominal.GetBinContent(bin)+0.04)):
                                    if options.verbose: print 'skipping stat_foreach_shape_bins %s %d because it is irrelevant'%(proc,bin)
                                    break

                                p0Up = nominal.Clone("%s_%s_%s_%s_bin%dUp"% (nominal.GetName(),name,truebinname,proc,bin))
                                p0Dn = nominal.Clone("%s_%s_%s_%s_bin%dDown"% (nominal.GetName(),name,truebinname,proc,bin))
                                p0Up.SetBinContent(bin,nominal.GetBinContent(bin)+effect*nominal.GetBinError(bin))
                                p0Dn.SetBinContent(bin,nominal.GetBinContent(bin)**2/p0Up.GetBinContent(bin))
                                report[str(p0Up.GetName())[2:]] = p0Up
                                report[str(p0Dn.GetName())[2:]] = p0Dn
                                systsEnv2["%s_%s_%s_bin%d"%(name,truebinname,proc,bin)] = (dict([(_p,"1" if _p==proc else "-") for _p in processes]),
                                                                                           dict([(_p,"1" if _p==proc else "-") for _p in processes]),
                                                                                           "templates")
                                break # otherwise you apply more than once to the same bin if more regexps match

                elif 'TH2' in nominal.ClassName():
                    for binx in xrange(1,nominal.GetNbinsX()+1):
                        for biny in xrange(1,nominal.GetNbinsY()+1):
                            for binmatch in morefields[0]:
                                if re.match(binmatch+"$",'%d,%d'%(binx,biny)):
                                    if nominal.GetBinContent(binx,biny) == 0 or nominal.GetBinError(binx,biny) == 0:
                                        if nominal.Integral() != 0: 
                                            print "WARNING: for process %s in truebinname %s, bin %d,%d has zero yield or zero error." % (proc,truebinname,binx,biny)
                                        break
                                    if (effect*nominal.GetBinError(binx,biny)<0.1*math.sqrt(nominal.GetBinContent(binx,biny)+0.04)):
                                        if options.verbose: print 'skipping stat_foreach_shape_bins %s %d,%d because it is irrelevant'%(proc,binx,biny)
                                        break
                                    p0Up = nominal.Clone("%s_%s_%s_%s_bin%d_%dUp"% (nominal.GetName(),name,truebinname,proc,binx,biny))
                                    p0Dn = nominal.Clone("%s_%s_%s_%s_bin%d_%dDown"% (nominal.GetName(),name,truebinname,proc,binx,biny))
                                    p0Up.SetBinContent(binx,biny,nominal.GetBinContent(binx,biny)+effect*nominal.GetBinError(binx,biny))
                                    p0Dn.SetBinContent(binx,biny,nominal.GetBinContent(binx,biny)**2/p0Up.GetBinContent(binx,biny))
                                    report[str(p0Up.GetName())[2:]] = p0Up
                                    report[str(p0Dn.GetName())[2:]] = p0Dn
                                    systsEnv2["%s_%s_%s_bin%d_%d"%(name,truebinname,proc,binx,biny)] = (dict([(_p,"1" if _p==proc else "-") for _p in processes]),
                                                                                                        dict([(_p,"1" if _p==proc else "-") for _p in processes]),
                                                                                                        "templates")
                                    break # otherwise you apply more than once to the same bin if more regexps match

            elif mode in ["templates"]:
                nominal = report[proc]
                p0Up = report["%s_%s_Up" % (proc, effect)]
                p0Dn = report["%s_%s_Dn" % (proc, effect)]
                if not p0Up or not p0Dn: 
                    raise RuntimeError, "Missing templates %s_%s_(Up,Dn) for %s" % (proc,effect,name)
                p0Up.SetName("%s_%sUp"   % (nominal.GetName(),name))
                p0Dn.SetName("%s_%sDown" % (nominal.GetName(),name))
                if p0Up.Integral()<=0 or p0Dn.Integral()<=0:
                    if p0Up.Integral()<=0 and p0Dn.Integral()<=0:
                        raise RuntimeError('ERROR: both template variations have negative or zero integral: '
                                           '%s, Nominal %f, Up %f, Down %f' % (proc, nominal.Integral(),
                                                                               p0Up.Integral(), p0Dn.Integral()))
                    print ('Warning: I am going to fix a template prediction that would have '
                           'negative or zero integral: %s, Nominal %f, Up %f, Down %f' % (proc,nominal.Integral(),
                                                                               p0Up.Integral(),p0Dn.Integral()))
                    for b in xrange(1,nominal.GetNbinsX()+1):
                        y0 = nominal.GetBinContent(b)
                        yA = p0Up.GetBinContent(b) if p0Up.Integral()>0 else p0Dn.GetBinContent(b)
                        yM = y0
                        if (y0 > 0 and yA > 0):
                            yM = y0*y0/yA
                        elif yA == 0:
                            yM = 2*y0
                        if p0Up.Integral()>0: p0Dn.SetBinContent(b, yM)
                        else: p0Up.SetBinContent(b, yM)
                    print 'The integral is now: %s, Nominal %f, Up %f, Down %f'%(proc,nominal.Integral(),p0Up.Integral(),p0Dn.Integral())
                report[str(p0Up.GetName())[2:]] = p0Up
                report[str(p0Dn.GetName())[2:]] = p0Dn
                effect0  = "1"
                effect12 = "-"
                if mca._projection != None:
                    mca._projection.scaleSystTemplate(name,nominal,p0Up)
                    mca._projection.scaleSystTemplate(name,nominal,p0Dn)
            elif mode in ["alternateShape", "alternateShapeOnly"]:
                nominal = report[proc]
                alternate = report[effect]
                if mca._projection != None:
                    mca._projection.scaleSystTemplate(name,nominal,alternate)
                alternate.SetName("%s_%sUp" % (nominal.GetName(),name))
                if mode == "alternateShapeOnly":
                    alternate.Scale(nominal.Integral()/alternate.Integral())
                mirror = nominal.Clone("%s_%sDown" % (nominal.GetName(),name))
                for b in xrange(1,nominal.GetNbinsX()+1):
                    y0 = nominal.GetBinContent(b)
                    yA = alternate.GetBinContent(b)
                    yM = y0
                    if (y0 > 0 and yA > 0):
                        yM = y0*y0/yA
                    elif yA == 0:
                        yM = 2*y0
                    mirror.SetBinContent(b, yM)
                if mode == "alternateShapeOnly":
                    # keep same normalization
                    mirror.Scale(nominal.Integral()/mirror.Integral())
                else:
                    # mirror normalization
                    mnorm = (nominal.Integral()**2)/alternate.Integral()
                    mirror.Scale(mnorm/alternate.Integral())
                report[alternate.GetName()] = alternate
                report[mirror.GetName()] = mirror
                effect0  = "1"
                effect12 = "-"
            effmap0[proc]  = effect0 
            effmap12[proc] = effect12 
        if mode not in ["stat_foreach_shape_bins"]: systsEnv2[name] = (effmap0,effmap12,mode)

    return systsEnv2

def writeDataCard(myout, allyields, systs, systsEnv, binname, cutsfile, processes):
    myyields = dict([(k,v) for (k,v) in allyields.iteritems()]) # doesn't this just copy the dict?
    if not os.path.exists(myout):
        os.mkdir(myout)

    with open(os.path.join(myout, binname+".card.txt"), 'w') as datacard:
        datacard.write("## Datacard for cut file %s\n" % cutsfile)
        datacard.write("shapes *        * %s.input.root x_$PROCESS x_$PROCESS_$SYSTEMATIC\n" % binname)
        datacard.write('##----------------------------------\n')
        datacard.write('bin         %s\n' % binname)
        datacard.write('observation %s\n' % myyields['data_obs'])
        datacard.write('##----------------------------------\n')
        
        klen = max([7, len(binname)]+[len(p) for p in processes])
        kpatt = " %%%ds " % klen
        fpatt = " %%%d.%df " % (klen,3)
        datacard.write('##----------------------------------\n')
        datacard.write('bin             '+(" ".join([kpatt % binname  for p in processes]))+"\n")
        datacard.write('process         '+(" ".join([kpatt % p        for p in processes]))+"\n")
        datacard.write('process         '+(" ".join([kpatt % iproc[p] for p in processes]))+"\n")
        datacard.write('rate            '+(" ".join([fpatt % myyields[p] for p in processes]))+"\n")
        datacard.write('##----------------------------------\n')

        for name, effmap in systs.iteritems():
            datacard.write(('%-12s lnN' % name) + " ".join([kpatt % effmap[p] for p in processes]) +"\n")

        for name, (effmap0,effmap12,mode) in systsEnv.iteritems():
            if mode == "templates":
                datacard.write('%-10s shape' % name)
                datacard.write(" ".join([kpatt % effmap0[p] for p in processes]))
                datacard.write("\n")

            if re.match('envelop.*',mode):
                datacard.write('%-10s shape' % (name+"0"))
                datacard.write(" ".join([kpatt % effmap0[p] for p in processes]))
                datacard.write("\n")

            if any([re.match(x+'.*',mode) for x in ["envelop", "shapeOnly"]]):
                datacard.write('%-10s shape' % (name+"1"))
                datacard.write(" ".join([kpatt % effmap12[p] for p in processes]))
                datacard.write("\n")
                if "shapeOnly2D" not in mode:
                    datacard.write('%-10s shape' % (name+"2"))
                    datacard.write(" ".join([kpatt % effmap12[p] for p in processes]))
                    datacard.write("\n")
        datacard.write("\n")

if __name__ == '__main__':
    systs = {}

    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] mc.txt cuts.txt var bins systs.txt ")
    addMCAnalysisOptions(parser)
    parser.add_option("-o", "--out", dest="outname", type="string",
                      default=None, help="output name") 
    parser.add_option("--od", "--outdir", dest="outdir", type="string",
                      default="shapecards/", help="output name") 
    parser.add_option("-v", "--verbose", dest="verbose", type="int",
                      default=0, help="Verbosity level (0 = quiet, 1 = verbose, 2+ = more)")
    parser.add_option("--asimov", dest="asimov", action="store_true", help="Asimov")
    parser.add_option("--2d-binning-function", dest="binfunction", type="string",
                      default=None,
                      help=("Function used to bin the 2D histogram: "
                            "nbins:func, where func(x,y) = bin in [1,nbins]"))
    parser.add_option("--infile", dest="infile", type="string",
                      default=None, help="File to read histos from")
    parser.add_option("--savefile", dest="savefile", type="string",
                      default=None, help="File to save histos to")

    (options, args) = parser.parse_args()
    options.weight = True
    options.final  = True
    options.allProcesses = True

    if not os.path.isdir(options.outdir):
        os.mkdir(options.outdir)

    if "/functions_cc.so" not in ROOT.gSystem.GetLibraries(): 
        ROOT.gROOT.ProcessLine(".L %s/src/CMGTools/TTHAnalysis/python/plotter/functions.cc+" % os.environ['CMSSW_BASE']);

    mca  = MCAnalysis(args[0],options)
    cuts = CutsFile(args[1],options)

    truebinname = os.path.basename(args[1]).replace(".txt","") if options.outname == None else options.outname
    binname = truebinname if truebinname[0] not in "234" else "ttH_"+truebinname
    print binname

    myout = options.outdir
    report = produceReport(mca, args[2], args[3], cuts,
                           outfilename=os.path.join(myout, binname+".bare.root"),
                           options=options)

    allyields, processes, iproc = produceYields(mca, report)
    systs, systsEnv = parseSystsFiles(args[4:], processes, options)
    systs = parseNormalizationSysts(systs, processes, mca)
    systsEnv1 = parseShapeSysts1(systsEnv, mca, report)

    if options.binfunction:
        doRebinning(options.binfunction, report, mca)
        allyields, processes, iproc = produceYields(mca, report)

    systsEnv2 = parseShapeSysts2(systsEnv, mca, report, processes, options)

    systsEnv = {}
    systsEnv.update(systsEnv1)
    systsEnv.update(systsEnv2)

    writeDataCard(options.outdir, allyields, systs, systsEnv, binname, args[1], processes)

    myout = options.outdir
    workspace = ROOT.TFile.Open(os.path.join(myout,binname+".input.root"), "RECREATE")
    for n,h in report.iteritems():
        if options.verbose:
            print "\t%s (%8.3f events)" % (h.GetName(),h.Integral())
        workspace.WriteTObject(h,h.GetName())
    workspace.Close()

    print "Wrote to ", os.path.join(myout,binname+".input.root")

    sys.exit(0)
