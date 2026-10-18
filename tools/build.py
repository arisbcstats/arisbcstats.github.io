# usage: python3 tools/build.py <σελίδα από το artifact .html> -> γράφει index.html (ίδια σελίδα + ρυθμίσεις εφαρμογής)
import sys,re
s=open(sys.argv[1],encoding='utf-8').read()
assert 'id="aris-data"' in s and s.lstrip().lower().startswith('<!doctype html>'), 'δεν μοιάζει με τη σελίδα ARIS BC Statistics'
HEAD='''<meta name="theme-color" content="#16150f"><link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png"><link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="Aris BC Stats">
<meta name="description" content="Στατιστικά, PIR, πρόγραμμα και βαθμολογίες του Άρη στο μπάσκετ, από τα επίσημα box score.">
<script>/* εκτός Claude: αποθήκευση εικόνων με απλό download */
if(!window.claude){window.claude={use:async n=>n==='downloads'?{save:async({filename,data})=>{const u=URL.createObjectURL(data instanceof Blob?data:new Blob([data]));const a=document.createElement('a');a.href=u;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),4000);return{status:'saved'};}}:null};}
</script>'''
GC='<script>(function(){var app=matchMedia("(display-mode: standalone)").matches||navigator.standalone===true;window.goatcounter={path:function(p){return app?"/app-open":p;}};addEventListener("appinstalled",function(){var t=setInterval(function(){if(window.goatcounter&&window.goatcounter.count){clearInterval(t);window.goatcounter.count({path:"install",title:"Εγκατάσταση εφαρμογής",event:true});}},500);});})();</script><script data-goatcounter="https://arisbcstats.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
TAIL='<script>if("serviceWorker" in navigator) addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));</script>'
s=re.sub(r'<!doctype html><html>','<!doctype html><html lang="el">',s,count=1,flags=re.I)
s=s.replace('<head>','<head>'+HEAD,1)
s=s.rstrip()
s=s[:-len('</html>')]+GC+TAIL+'</html>' if s.lower().endswith('</html>') else s+GC+TAIL
open('index.html','w',encoding='utf-8').write(s)
print('index.html OK',len(s))
