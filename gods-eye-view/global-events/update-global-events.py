import os
import urllib.request,xml.etree.ElementTree as E,json,time,email.utils,re,math,html
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
GEV_ROOT=Path(os.environ.get('GEV_ROOT','/opt/gods-eye-view'));OUT=GEV_ROOT/'public/thm-events.json';NS={'g':'http://www.gdacs.org','geo':'http://www.georss.org/georss'}
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s or ''))).strip()
def stamp(s):
 try:return int(email.utils.parsedate_to_datetime(s).timestamp())
 except:return 0
def distance(a,b,c,d):
 rad=math.pi/180;x=(c-a)*rad;y=(d-b)*rad;v=math.sin(x/2)**2+math.cos(a*rad)*math.cos(c*rad)*math.sin(y/2)**2;return 12742*math.asin(min(1,math.sqrt(v)))
def sites():
 out=[]
 if not (GEV_ROOT/'src/data/local_data/datacenters/datacenters.geojsonl').exists():return out
 for l in (GEV_ROOT/'src/data/local_data/datacenters/datacenters.geojsonl').read_text().splitlines():
  try:
   d=json.loads(l);c=d['geometry']['coordinates']
   while isinstance(c[0],list):c=c[0]
   out.append((c[1],c[0],d['properties'].get('tags',{}).get('name','Unnamed mapped site')))
  except:pass
 return out

def hazards():
 req=urllib.request.Request('https://www.gdacs.org/xml/rss.xml',headers={'User-Agent':'THM-GlobalEvents/1.0'})
 with urllib.request.urlopen(req,timeout=25) as r:root=E.fromstring(r.read(4000000))
 now=int(time.time());records=[];dc=sites();seen=set()
 for x in root.findall('./channel/item'):
  def get(k):return clean(x.findtext('g:'+k,namespaces=NS))
  kind=get('eventtype');level=get('alertlevel');modified=stamp(get('datemodified')) or stamp(x.findtext('pubDate'));end=stamp(get('todate'));start=stamp(get('fromdate'))
  if kind not in ['TC','FL','WF','EQ','DR'] or modified<now-7*86400 or (end and end<now-3*86400):continue
  severity=x.find('g:severity',NS)
  try:value=float(severity.get('value','0'))
  except:value=0
  population=x.find('g:population',NS)
  try:pop=float(population.get('value','0'))
  except:pop=0
  if level not in ['Red','Orange'] and not (kind=='TC' and value>=100 and get('country')) and not(kind=='EQ' and value>=6) and not(kind=='WF' and value>=10000):continue
  point=x.findtext('geo:point',namespaces=NS)
  try:lat,lon=map(float,point.split());assert -90<=lat<=90 and -180<=lon<=180
  except:continue
  link=clean(x.findtext('link'))
  parsed=urlsplit(link)
  if parsed.scheme not in ('http','https') or parsed.hostname not in ('www.gdacs.org','gdacs.org') or parsed.username or parsed.password or parsed.port not in (None,80,443):continue
  link=urlunsplit(('https','www.gdacs.org',parsed.path,parsed.query,''))
  if link in seen:continue
  seen.add(link);near=[name for a,b,name in dc if distance(lat,lon,a,b)<=200]
  name={'TC':'Tropical cyclone','FL':'Flood','WF':'Wildfire','EQ':'Earthquake','DR':'Drought'}[kind];country=get('country') or 'Open ocean / location in source report'
  title=clean(x.findtext('title'))
  records.append({'id':get('eventid') or link,'title':title,'country':country,'kind':name,'severity':clean(severity.text if severity is not None else '') or level+' alert','level':level,'population':clean(population.text if population is not None else ''),'lat':lat,'lon':lon,'alt':3500000 if kind in ['TC','DR'] else 1600000,'updated':modified,'eventTime':start,'url':link,'source':'GDACS · UN / European Commission','description':clean(x.findtext('description')),'exposureCount':len(near),'exposureNames':list(dict.fromkeys(near))[:3],'rank':({'Red':3,'Orange':2}.get(level,1),min(len(near),50),modified)})
 return records

def main():
 now=int(time.time());old={}
 try:old=json.loads(OUT.read_text())
 except Exception:pass
 sources=[]
 try:weather=[dict(e,fetched=now) for e in hazards()];sources.append({'name':'GDACS','ok':True,'checked':now})
 except Exception:
  weather=[{**e,'stale':True} for e in old.get('events',[]) if e.get('eventClass')!='context' and now-e['updated']<7*86400 and now-e.get('fetched',0)<3600];sources.append({'name':'GDACS','ok':False,'checked':0})
 try:
  with urllib.request.urlopen(os.environ.get('THM_CONTEXT_URL',''),timeout=15) as r:context=json.load(r)
  if now-context.get('updated',0)>3600:raise ValueError('Context cache stale')
  reports=[dict(e,fetched=context['updated']) for e in context.get('events',[])];sources.append({'name':'Public event briefs','ok':context.get('ok',False),'checked':context['updated']})
 except Exception:
  reports=[{**e,'stale':True} for e in old.get('events',[]) if e.get('eventClass')=='context' and now-e['updated']<7*86400 and now-e.get('fetched',0)<3600];sources.append({'name':'Public event briefs','ok':False,'checked':0})
 weather.sort(key=lambda x:x.get('rank',[0,0,x['updated']]),reverse=True)
 buckets={}
 for e in reports:buckets.setdefault(e['kind'],[]).append(e)
 balanced=[]
 for i in range(max([len(v) for v in buckets.values()] or [0])):
  for rows in buckets.values():
   if i<len(rows):balanced.append(rows[i])
 events=[]
 for i in range(max(6,min(12,len(balanced)))):
  if i<len(balanced):events.append(balanced[i])
  if i<min(6,len(weather)):events.append(weather[i])
 data={'updated':now,'ok':any(s['ok'] for s in sources),'events':events,'sources':sources,'scope':'Selected geopolitical, business and natural-hazard reports; geography and potential impacts are qualified.'}
 temp=OUT.with_suffix('.tmp');temp.write_text(json.dumps(data));temp.replace(OUT);print('Global event watch:',len(events),'events;',len(balanced),'available context reports')
if __name__=='__main__':main()
