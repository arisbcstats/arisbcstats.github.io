# usage: python3 adv2.py data.json -> adds g.src (πηγές πόντων), g.flow (ροή σκορ), g.opp_top (κορυφαίοι αντίπαλοι) όπου λείπουν
import json,sys,urllib.request
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'curl/8.5.0','Accept':'application/json'}),timeout=40))
def secs(t): m,s=t.split(':')[:2]; return int(m)*60+int(s)
def pir(s): return s['pts']+s['reb']+s['ast']+s['stl']+s['blk']+s['fd']-((s['a2']-s['m2'])+(s['a3']-s['m3'])+(s['fa']-s['fm'])+s['to']+s['ba']+s['pf'])
def title(n):
    if ',' in n: last,first=[x.strip() for x in n.split(',',1)]; n=first+' '+last
    return ' '.join(w.capitalize() if w.isupper() else w for w in n.replace(' - ','-').split())
def build(g):
    flow=[]; F=A=0; out={}
    if g['id'].startswith('U2026-'):
        code=g['id'].split('-')[1]
        st=get(f'https://api-live.euroleague.net/v3/competitions/U/seasons/U2026/games/{code}/stats')
        pts=get(f'https://live.euroleague.net/api/Points?gamecode={code}&seasoncode=U2026')['Rows']
        pbp=get(f'https://live.euroleague.net/api/PlayByPlay?gamecode={code}&seasoncode=U2026')
        aris='local' if 'ARIS' in (st['local']['players'][0]['player']['club']['name'].upper()) else 'road'; opp='road' if aris=='local' else 'local'
        src={}
        for side,code_is_aris in (('for',True),('against',False)):
            rows=[r for r in pts if (r['TEAM'].strip()=='ARI')==code_is_aris]
            made=[r for r in rows if r['ID_ACTION'] in('2FGM','3FGM','FTM')]
            S=lambda f:sum(r['POINTS'] for r in made if r[f]=='1')
            paint=sum(2 for r in rows if r['ID_ACTION']=='2FGM' and abs(r['COORD_X'])<=245 and r['COORD_Y']<=422)
            team=st[aris if code_is_aris else opp]
            bench=sum(p['stats']['points'] for p in team['players'] if not p['stats'].get('startFive'))
            src[side]={'tov':S('POINTS_OFF_TURNOVER'),'fb':S('FASTBREAK'),'sc':S('SECOND_CHANCE'),'paint':paint,'bench':int(bench)}
        isA=pbp['CodeTeamA'].strip()=='ARI'
        for pi,q in enumerate(('FirstQuarter','SecondQuarter','ThirdQuarter','ForthQuarter','ExtraTime')):
            for e in (pbp.get(q) or []):
                if not e['MARKERTIME'] or (e['POINTS_A'] is None and e['POINTS_B'] is None): continue
                per=pi+1; plen=600 if per<=4 else 300; T=600*min(per-1,4)+(plen-secs(e['MARKERTIME']))
                pa=e['POINTS_A'] if e['POINTS_A'] is not None else (F if isA else A); pb=e['POINTS_B'] if e['POINTS_B'] is not None else (A if isA else F)
                nF,nA=(pa,pb) if isA else (pb,pa)
                if (nF,nA)!=(F,A): F,A=nF,nA; flow.append([T,F,A])
        tops=[]
        for p in st[opp]['players']:
            s=p['stats']
            if not s['timePlayed']: continue
            r=dict(n=title(p['player']['person']['name']),sec=int(s['timePlayed']),pts=int(s['points']),m2=int(s['fieldGoalsMade2']),a2=int(s['fieldGoalsAttempted2']),m3=int(s['fieldGoalsMade3']),a3=int(s['fieldGoalsAttempted3']),fm=int(s['freeThrowsMade']),fa=int(s['freeThrowsAttempted']),reb=int(s['totalRebounds']),ast=int(s['assistances']),pir=int(s['valuation']))
            tops.append(r)
    else:
        mid=g['id'].split('-')[1]; f=get(f'https://fibalivestats.dcd.shared.geniussports.com/data/{mid}/data.json')
        tno=[k for k,t in f['tm'].items() if 'Aris' in t['name']][0]; ono='2' if tno=='1' else '1'
        src={}
        for side,k in (('for',tno),('against',ono)):
            t=f['tm'][k]; src[side]={'tov':t['tot_sPointsFromTurnovers'],'fb':t['tot_sPointsFastBreak'],'sc':t['tot_sPointsSecondChance'],'paint':t['tot_sPointsInThePaint'],'bench':t['tot_sBenchPoints']}
        evs=[]
        for e in f['pbp']:
            per=e['period']; reg=e['periodType']=='REGULAR'; plen=600 if reg else 300; base=600*(per-1) if reg else 2400+300*(per-1)
            c=e['clock'].split(':'); T=base+plen-(int(c[0])*60+int(c[1])+(1 if len(c)>2 and int(c[2])>0 else 0))
            s1,s2=int(e['s1'] or 0),int(e['s2'] or 0); evs.append((T,s1+s2,e['actionNumber'],s1,s2))
        for T,_,_,s1,s2 in sorted(evs):
            nF,nA=(s1,s2) if tno=='1' else (s2,s1)
            if nF>=F and nA>=A and (nF,nA)!=(F,A): F,A=nF,nA; flow.append([T,F,A])
        tops=[]
        for p in f['tm'][ono]['pl'].values():
            mm,ss=(p.get('sMinutes') or '0:00').split(':'); sec=int(mm)*60+int(ss)
            if not sec: continue
            import re as _re
            nm=(p.get('firstName','')[:1]+'. ' if p.get('firstName') else '')+_re.sub(r'σ\b','ς',p.get('familyName',''))
            tops.append(dict(n=nm,sec=sec,pts=p['sPoints'],m2=p['sTwoPointersMade'],a2=p['sTwoPointersAttempted'],m3=p['sThreePointersMade'],a3=p['sThreePointersAttempted'],fm=p['sFreeThrowsMade'],fa=p['sFreeThrowsAttempted'],reb=p['sReboundsTotal'],ast=p['sAssists'],pir=p['eff_5']))
    prob=[]
    if not flow or flow[-1][1:]!=[g['ptsFor'],g['ptsAgainst']]: prob.append(f"flow end {flow[-1] if flow else None}")
    if any(flow[i][0]<flow[i-1][0] for i in range(1,len(flow))): prob.append('flow time order')
    if sum(t['pts'] for t in tops)!=g['ptsAgainst']: prob.append('opp pts sum')
    for side,tot in (('for',g['ptsFor']),('against',g['ptsAgainst'])):
        if any(v<0 or v>tot for v in src[side].values()): prob.append('src range '+side)
    tops=sorted(tops,key=lambda t:(-t['pir'],-t['pts']))[:3]
    return src,flow,tops,prob
d=json.load(open(sys.argv[1]))
for g in d['games']:
    if all(k in g for k in ('src','flow','opp_top')): continue
    try: src,flow,tops,prob=build(g)
    except Exception as e: print(g['id'],'ΣΦΑΛΜΑ',repr(e)); continue
    if prob: print(g['id'],'ΠΡΟΒΛΗΜΑ',prob); continue
    g['src']=src; g['flow']=flow; g['opp_top']=tops
    print(g['id'],'OK src',src,'flow',len(flow),'top',[(t['n'],t['pts'],t['pir']) for t in tops])
json.dump(d,open(sys.argv[1],'w'),ensure_ascii=False,separators=(',',':'))
