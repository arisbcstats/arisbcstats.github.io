import json,sys,collections,urllib.request,concurrent.futures as cf
def get(u):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'curl/8.5.0','Accept':'application/json'}),timeout=40))
    except Exception: return None
ECG={'ARI':'Άρης','JER':'Χάποελ Ιερουσαλήμ','RIG':'Ρίγα','LEM':'Λε Μαν','BGS':'Μπούργος','TRT':'Ντερτόνα','RTK':'Ρόστοκ','LJU':'Τσεντεβίτα'}
GBN=[('Aris','Άρης'),('AEK','ΑΕΚ'),('ΒΙΚΟΣ','Βίκος Ιωαννίνων'),('Vikos','Βίκος Ιωαννίνων'),('Doxa','Δόξα Λευκάδας'),('DOXA','Δόξα Λευκάδας'),('Δόξα','Δόξα Λευκάδας'),('Iraklis','Ηρακλής'),('Karditsa','Καρδίτσα'),('Kolossos','Κολοσσός Ρόδου'),('Maroussi','Μαρούσι'),('Mykonos','Μύκονος'),('Olympiacos','Ολυμπιακός'),('PAOK','ΠΑΟΚ'),('Panathinaikos','Παναθηναϊκός'),('Peristeri','Περιστέρι'),('Promitheas','Προμηθέας Πατρών')]
def fin(K,g):
    out={}
    for n,k in K.items():
        c=k['gp']; fga=k['a2']+k['a3']; fgm=k['m2']+k['m3']
        poss=fga+.44*k['fa']-k['orb']+k['to']; oposs=k['ofga']+.44*k['ofa']-k['ooreb']+k['oto']
        out[n]=dict(gp=c,pts=round(k['pts']/c,1),pa=round(k['pa']/c,1),reb=round(k['reb']/c,1),orb=round(k['orb']/c,1),ast=round(k['ast']/c,1),stl=round(k['stl']/c,1),to=round(k['to']/c,1),blk=round(k['blk']/c,1),
          p2=round(100*k['m2']/max(1,k['a2']),1),p3=round(100*k['m3']/max(1,k['a3']),1),ft=round(100*k['fm']/max(1,k['fa']),1),ts=round(100*k['pts']/(2*(fga+.44*k['fa'])),1),pir=round(k['pir']/c,1),oto=round(k['oto']/c,1),
          orp=round(100*k['orb']/max(1,k['orb']+k['odrb']),1),drp=round(100*k['drb']/max(1,k['drb']+k['ooreb']),1),efg=round(100*(fgm+.5*k['m3'])/max(1,fga),1),
          ortg=round(100*k['pts']/max(1,poss),1),drtg=round(100*k['pa']/max(1,oposs),1))
    return out
d=json.load(open(sys.argv[1])); G=d.get('grp') if isinstance(d.get('grp'),dict) and 'EC' in d.get('grp',{}) else {}
# ---- EuroCup: group of Aris
ag=get('https://api-live.euroleague.net/v2/competitions/U/seasons/U2026/games?teamCode=ARI')
played=[g for g in (ag or {}).get('data',[]) if g.get('played')]
if played:
    grp=played[-1]['group']['name']; rounds=sorted({g['round'] for g in played if g['group']['name']==grp})
    codes=[c for r in rounds for c in range(16*(r-1)+1,16*r+1)]
    with cf.ThreadPoolExecutor(8) as ex: hdr=list(ex.map(lambda c:(c,get(f'https://api-live.euroleague.net/v2/competitions/U/seasons/U2026/games/{c}')),codes))
    allc=[c for c,h in hdr if h and h.get('played')]
    gc=[c for c in allc if dict(hdr)[c]['group']['name']==grp]
    with cf.ThreadPoolExecutor(6) as ex: sts=dict(zip(allc,ex.map(lambda c:get(f'https://api-live.euroleague.net/v3/competitions/U/seasons/U2026/games/{c}/stats'),allc)))
    H=dict(hdr); K=collections.defaultdict(collections.Counter); KA=collections.defaultdict(collections.Counter)
    for c in allc:
      s=sts[c]
      if not s: continue
      for KK in ((K,KA) if c in gc else (KA,)):
        for a,b in (('local','road'),('road','local')):
            code=H[c][a]['club']['code']; n=ECG.get(code,H[c][a]['club']['name']); t=s[a]['total']; o=s[b]['total']; k=KK[n]
            k['gp']+=1; k['pts']+=t['points']; k['pa']+=o['points']; k['reb']+=t['totalRebounds']; k['orb']+=t['offensiveRebounds']; k['ast']+=t['assistances']; k['stl']+=t['steals']; k['to']+=t['turnovers']; k['blk']+=t['blocksFavour']
            k['m2']+=t['fieldGoalsMade2']; k['a2']+=t['fieldGoalsAttempted2']; k['m3']+=t['fieldGoalsMade3']; k['a3']+=t['fieldGoalsAttempted3']; k['fm']+=t['freeThrowsMade']; k['fa']+=t['freeThrowsAttempted']; k['pir']+=t['valuation']; k['oto']+=o['turnovers']
            k['drb']+=t['defensiveRebounds']; k['odrb']+=o['defensiveRebounds']; k['ooreb']+=o['offensiveRebounds']; k['ofga']+=o['fieldGoalsAttempted2']+o['fieldGoalsAttempted3']; k['ofa']+=o['freeThrowsAttempted']
    rows={r[0]:r for r in d['standings']['ec']['rows']}
    bad=[n for n,k in K.items() if n in rows and (k['gp']!=rows[n][1]+rows[n][2] or k['pts']!=rows[n][3])]
    if bad or not K: print('EC ΠΡΟΒΛΗΜΑ',bad)
    else:
        G['EC']={'round':max(rounds),'teams':fin(K,None)}; print('EC OK round',max(rounds),len(K),'ομάδες')
        if len(KA)>len(K) and 'Άρης' in KA: G['ECALL']={'round':max(rounds),'teams':fin(KA,None)}; print('EC σύνολο OK',len(KA),'ομάδες',len(allc),'αγώνες')
# ---- GBL: scan FIBA LiveStats ids
ids=[int(g['id'].split('-')[1]) for g in d['games'] if g['id'].startswith('FIBA-')]
lo,hi=min(ids+[2902681])-10,max(ids)+60
with cf.ThreadPoolExecutor(8) as ex: fs=list(ex.map(lambda m:get(f'https://fibalivestats.dcd.shared.geniussports.com/data/{m}/data.json'),range(lo,hi)))
K=collections.defaultdict(collections.Counter); ok=0
def gname(x):
    for a,b in GBN:
        if a in x: return b
for f in fs:
    if not f or 'tm' not in f: continue
    if not str(f.get('clock','')).startswith('00:00') or not (f.get('period',0)>=4 or f.get('periodType')=='OVERTIME'): continue
    n1,n2=gname(f['tm']['1']['name']),gname(f['tm']['2']['name'])
    if not n1 or not n2: continue
    ok+=1
    for a,b in (('1','2'),('2','1')):
        t,o=f['tm'][a],f['tm'][b]; k=K[gname(t['name'])]
        k['gp']+=1; k['pts']+=t['tot_sPoints']; k['pa']+=o['tot_sPoints']; k['reb']+=t['tot_sReboundsTotal']; k['orb']+=t['tot_sReboundsOffensive']; k['ast']+=t['tot_sAssists']; k['stl']+=t['tot_sSteals']; k['to']+=t['tot_sTurnovers']; k['blk']+=t['tot_sBlocks']
        k['m2']+=t['tot_sTwoPointersMade']; k['a2']+=t['tot_sTwoPointersAttempted']; k['m3']+=t['tot_sThreePointersMade']; k['a3']+=t['tot_sThreePointersAttempted']; k['fm']+=t['tot_sFreeThrowsMade']; k['fa']+=t['tot_sFreeThrowsAttempted']; k['pir']+=t.get('tot_eff_5',0); k['oto']+=o['tot_sTurnovers']
        k['drb']+=t['tot_sReboundsDefensive']; k['odrb']+=o['tot_sReboundsDefensive']; k['ooreb']+=o['tot_sReboundsOffensive']; k['ofga']+=o['tot_sTwoPointersAttempted']+o['tot_sThreePointersAttempted']; k['ofa']+=o['tot_sFreeThrowsAttempted']
R=d['standings']['gbl']['results']; P=collections.Counter(); N=collections.Counter()
for r,h,a,hs,as_ in R: P[h]+=hs; P[a]+=as_; N[h]+=1; N[a]+=1
bad=[n for n,k in K.items() if (k['gp'],k['pts'])!=(N[n],P[n])]
if bad or not K: print('GBL ΠΡΟΒΛΗΜΑ (τα αγωνιστικά του FIBA δεν ταιριάζουν με standings.gbl.results)',bad)
else: G['GBL']={'round':max(r[0] for r in R),'teams':fin(K,None)}; print('GBL OK',ok,'αγώνες',len(K),'ομάδες')
d['grp']=G
json.dump(d,open(sys.argv[1],'w'),ensure_ascii=False,separators=(',',':'))
