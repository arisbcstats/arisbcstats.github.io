# usage: python3 adv.py data.json  -> adds g.shots and g.lu to games missing them (validated), prints report
import json,sys,math,collections,urllib.request
ECN={'ANTETOKOUNMPO, KOSTAS':'Κ. Αντετοκούνμπο','ANTETOKOUNMPO, THANASIS':'Θ. Αντετοκούνμπο','BIRCH, KHEM':'Μπιρτς','CHARALAMPOPOULOS, VASILIS':'Χαραλαμπόπουλος','DIMITRIJEVIC, NENO':'Ντιμιτρίεβιτς','LIDDELL, E.J':'Λίντελ','MITROU - LONG, ELIJAH':'Μήτρου-Λονγκ','MOKOKA, ADAM':'Μοκόκα','MORGAN, MATTHEW':'Μόργκαν','ROBINSON - EARL, JEREMIAH':'Ρόμπινσον-Ερλ','TOLIOPOULOS, VASSILIS':'Τολιόπουλος','BOCHORIDIS, ELEFTHERIOS':'Μποχωρίδης','CHATZILAMPROU, CHRYSOSTOMOS':'Χατζηλάμπρου'}
FBN={'8':'Μήτρου-Λονγκ','15':'Ρόμπινσον-Ερλ','4':'Τολιόπουλος','12':'Ντιμιτρίεβιτς','3':'Μποχωρίδης','13':'Μόργκαν','16':'Λίντελ','1':'Χαραλαμπόπουλος','10':'Κ. Αντετοκούνμπο','6':'Θ. Αντετοκούνμπο','5':'Μπιρτς','14':'Μοκόκα','11':'Χατζηλάμπρου'}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'curl/8.5.0','Accept':'application/json'}),timeout=40))
def secs(t): m,s=t.split(':')[:2]; return int(m)*60+int(s)
def build(g):
    box=g['players']; idx={p['name']:i for i,p in enumerate(box)}; shots=[]; ev=[]; F=A=0; firstsub={}; prob=[]
    nper=max(4,len((g.get('q') or {}).get('for',[0]*4)))
    if g['id'].startswith('U2026-'):
        code=g['id'].split('-')[1]
        for r in get(f'https://live.euroleague.net/api/Points?gamecode={code}&seasoncode=U2026')['Rows']:
            if r['TEAM'].strip()=='ARI' and r['ID_ACTION'] in('2FGM','2FGA','3FGM','3FGA'):
                shots.append([idx[ECN[r['PLAYER']]],r['COORD_X'],r['COORD_Y'],int(r['ID_ACTION'].endswith('M')),int(r['ID_ACTION'][0])])
        b=get(f'https://live.euroleague.net/api/PlayByPlay?gamecode={code}&seasoncode=U2026'); isA=b['CodeTeamA'].strip()=='ARI'
        for pi,q in enumerate(('FirstQuarter','SecondQuarter','ThirdQuarter','ForthQuarter','ExtraTime')):
            for e in (b.get(q) or []):
                if not e['MARKERTIME']: continue
                per=pi+1; plen=600 if per<=4 else 300; T=600*min(per-1,4)+(plen-secs(e['MARKERTIME']))
                if e['POINTS_A'] is not None or e['POINTS_B'] is not None:
                    pa=e['POINTS_A'] if e['POINTS_A'] is not None else (F if isA else A); pb=e['POINTS_B'] if e['POINTS_B'] is not None else (A if isA else F)
                    F,A=(pa,pb) if isA else (pb,pa); ev.append((T,'S',None,F,A))
                if e['PLAYTYPE'] in('IN','OUT') and e['CODETEAM'].strip()=='ARI':
                    n=ECN[e['PLAYER']]; firstsub.setdefault(n,e['PLAYTYPE']); ev.append((T,e['PLAYTYPE'],n,F,A))
        starters=[p['name'] for p in box if p['sec'] and firstsub.get(p['name'],'OUT')=='OUT']
    else:
        mid=g['id'].split('-')[1]; f=get(f'https://fibalivestats.dcd.shared.geniussports.com/data/{mid}/data.json')
        tno=[k for k,t in f['tm'].items() if 'Aris' in t['name']][0]
        for s in f['tm'][tno]['shot']:
            x,y=s['x'],s['y']
            if x>50: x,y=100-x,100-y
            shots.append([idx[FBN[str(s['pno'])]],round(y*15-750),round(x*28-157.5),s['r'],3 if s['actionType']=='3pt' else 2])
        for e in sorted(f['pbp'],key=lambda e:e['actionNumber']):
            per=e['period']; reg=e['periodType']=='REGULAR'; plen=600 if reg else 300; base=600*(per-1) if reg else 2400+300*(per-1)
            c=e['clock'].split(':'); T=base+plen-(int(c[0])*60+int(c[1])+(1 if len(c)>2 and int(c[2])>0 else 0))
            s1,s2=int(e['s1'] or 0),int(e['s2'] or 0); nF,nA=(s1,s2) if tno=='1' else (s2,s1)
            if (nF,nA)!=(F,A): F,A=nF,nA; ev.append((T,'S',None,F,A))
            if e['actionType']=='substitution' and str(e['tno'])==tno:
                k='IN' if e['subType']=='in' else 'OUT'; ev.append((T,k,FBN[str(e['pno'])],F,A))
        starters=[FBN[k] for k,pl in f['tm'][tno]['pl'].items() if pl.get('starter')]
    c=collections.Counter()
    for pi,x,y,m,t in shots: c[(pi,t)]+=1; c[(pi,t,'m')]+=m
    for i,p in enumerate(box):
        if (c[(i,2,'m')],c[(i,2)],c[(i,3,'m')],c[(i,3)])!=(p['m2'],p['a2'],p['m3'],p['a3']): prob.append('shots '+p['name'])
    ev.sort(key=lambda e:e[0]); on=set(starters); last=[0,0,0]; agg={}; ps=collections.Counter(); pm=collections.Counter()
    def flush(T,F,A):
        if T>last[0] or F!=last[1] or A!=last[2]:
            if len(on)!=5: prob.append(f'on-court {len(on)} at {T}')
            o=agg.setdefault(tuple(sorted(on)),[0,0,0]); o[0]+=T-last[0]; o[1]+=F-last[1]; o[2]+=A-last[2]
            for n in on: ps[n]+=T-last[0]; pm[n]+=(F-last[1])-(A-last[2])
        last[:]=[T,F,A]
    for T,k,n,F,A in ev:
        flush(T,F,A)
        if k=='IN': on.add(n)
        elif k=='OUT': on.discard(n)
    flush(max(2400+300*(nper-4),ev[-1][0]),ev[-1][3],ev[-1][4])
    for p in box:
        if p['sec'] and (abs(ps[p['name']]-p['sec'])>3 or pm[p['name']]!=p['pm']): prob.append(f"lineup {p['name']} {ps[p['name']]}s/{p['sec']}s pm {pm[p['name']]}/{p['pm']}")
    return shots,[[list(k),*v] for k,v in agg.items()],prob
d=json.load(open(sys.argv[1]))
for g in d['games']:
    if 'shots' in g and 'lu' in g: continue
    try: shots,lu,prob=build(g)
    except KeyError as e: print(g['id'],'ΑΓΝΩΣΤΟ ΟΝΟΜΑ',e,'— πρόσθεσέ το στα ECN/FBN και ξανατρέξε'); continue
    except Exception as e: print(g['id'],'ΣΦΑΛΜΑ',repr(e)); continue
    sp=[x for x in prob if x.startswith('shots')]; lp=[x for x in prob if not x.startswith('shots')]
    if not sp: g['shots']=shots
    if not lp: g['lu']=lu
    print(g['id'],'shots',len(shots),'OK' if not sp else sp,'| lineups',len(lu),'OK' if not lp else lp)
json.dump(d,open(sys.argv[1],'w'),ensure_ascii=False,separators=(',',':'))
