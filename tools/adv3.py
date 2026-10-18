# usage: python3 adv3.py data.json -> adds g.ast (ποιος πασάρει σε ποιον) και g.st (αρχική πεντάδα) όπου λείπουν
import json,sys,collections,urllib.request
ECN={'ANTETOKOUNMPO, KOSTAS':'Κ. Αντετοκούνμπο','ANTETOKOUNMPO, THANASIS':'Θ. Αντετοκούνμπο','BIRCH, KHEM':'Μπιρτς','CHARALAMPOPOULOS, VASILIS':'Χαραλαμπόπουλος','DIMITRIJEVIC, NENO':'Ντιμιτρίεβιτς','LIDDELL, E.J':'Λίντελ','MITROU - LONG, ELIJAH':'Μήτρου-Λονγκ','MOKOKA, ADAM':'Μοκόκα','MORGAN, MATTHEW':'Μόργκαν','ROBINSON - EARL, JEREMIAH':'Ρόμπινσον-Ερλ','TOLIOPOULOS, VASSILIS':'Τολιόπουλος','BOCHORIDIS, ELEFTHERIOS':'Μποχωρίδης','CHATZILAMPROU, CHRYSOSTOMOS':'Χατζηλάμπρου'}
FBN={'8':'Μήτρου-Λονγκ','15':'Ρόμπινσον-Ερλ','4':'Τολιόπουλος','12':'Ντιμιτρίεβιτς','3':'Μποχωρίδης','13':'Μόργκαν','16':'Λίντελ','1':'Χαραλαμπόπουλος','10':'Κ. Αντετοκούνμπο','6':'Θ. Αντετοκούνμπο','5':'Μπιρτς','14':'Μοκόκα','11':'Χατζηλάμπρου'}
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'curl/8.5.0','Accept':'application/json'}),timeout=40))
def build(g):
    pairs=collections.Counter(); st=[]
    if g['id'].startswith('U2026-'):
        code=g['id'].split('-')[1]
        b=get(f'https://live.euroleague.net/api/PlayByPlay?gamecode={code}&seasoncode=U2026')
        rows=[e for q in ('FirstQuarter','SecondQuarter','ThirdQuarter','ForthQuarter','ExtraTime') for e in (b.get(q) or [])]
        for i,e in enumerate(rows):
            if e['PLAYTYPE']=='AS' and e['CODETEAM'].strip()=='ARI':
                p=rows[i-1]
                if p['PLAYTYPE'] not in('2FGM','3FGM','FTM') or p['CODETEAM'].strip()!='ARI': raise ValueError('unlinked assist '+str(e['MARKERTIME']))
                pairs[(ECN[e['PLAYER']],ECN[p['PLAYER']],{'2FGM':2,'3FGM':3,'FTM':1}[p['PLAYTYPE']])]+=1
        s=get(f'https://api-live.euroleague.net/v3/competitions/U/seasons/U2026/games/{code}/stats')
        for side in ('local','road'):
            for p in s[side]['players']:
                if p['stats'].get('startFive') and p['player']['person']['name'] in ECN: st.append(ECN[p['player']['person']['name']])
    else:
        mid=g['id'].split('-')[1]; f=get(f'https://fibalivestats.dcd.shared.geniussports.com/data/{mid}/data.json')
        tno=[k for k,t in f['tm'].items() if 'Aris' in t['name']][0]; A={e['actionNumber']:e for e in f['pbp']}
        for e in f['pbp']:
            if e['actionType']=='assist' and str(e['tno'])==tno:
                p=A.get(e.get('previousAction'))
                if not p or str(p['tno'])!=tno or not p.get('success'): raise ValueError('unlinked assist '+str(e['actionNumber']))
                k={'2pt':2,'3pt':3,'freethrow':1}[p['actionType']]
                pairs[(FBN[str(e['pno'])],FBN[str(p['pno'])],k)]+=1
        st=[FBN[k] for k,pl in f['tm'][tno]['pl'].items() if pl.get('starter')]
    prob=[]; box={p['name']:p for p in g['players']}
    for n,p in box.items():
        a=sum(v for (x,y,k),v in pairs.items() if x==n)
        if a!=p['ast']: prob.append(f'ast {n} {a}/{p["ast"]}')
        for k,fld in ((2,'m2'),(3,'m3')):
            r=sum(v for (x,y,kk),v in pairs.items() if y==n and kk==k)
            if r>p[fld]: prob.append(f'assisted {n} {k}pt {r}>{p[fld]}')
    if len(st)!=5 or any(n not in box for n in st): prob.append(f'starters {st}')
    agg={}
    for (x,y,k),v in pairs.items(): agg.setdefault((x,y),[0,0,0])[{2:0,3:1,1:2}[k]]+=v
    return [[x,y,*v] for (x,y),v in sorted(agg.items())],st,prob
d=json.load(open(sys.argv[1]))
for g in d['games']:
    if 'ast' in g and 'st' in g: continue
    try: ast,st,prob=build(g)
    except KeyError as e: print(g['id'],'ΑΓΝΩΣΤΟ ΟΝΟΜΑ',e); continue
    except Exception as e: print(g['id'],'ΣΦΑΛΜΑ',repr(e)); continue
    if prob: print(g['id'],'ΠΡΟΒΛΗΜΑ',prob); continue
    g['ast']=ast; g['st']=st
    print(g['id'],'OK pairs',len(ast),'assists',sum(a[2]+a[3]+a[4] for a in ast),'starters',st)
json.dump(d,open(sys.argv[1],'w'),ensure_ascii=False,separators=(',',':'))
