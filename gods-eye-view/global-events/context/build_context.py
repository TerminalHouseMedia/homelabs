import os
import freshness
"""Location-aware event briefs from cached public headlines; no guessed company HQs."""
import json,time,re,html,hashlib,urllib.request,xml.etree.ElementTree as ET,email.utils,datetime
from pathlib import Path
ROOT=Path(os.environ.get('THM_DASHBOARD_ROOT','/var/lib/thm-dashboard'));CACHE=Path(os.environ.get('THM_NEWS_CACHE','/var/lib/thm-news-cache'));OUT=ROOT/'global-context.json'
CUSTOM=[('Singapore',1.35,103.82),('Taipei',25.03,121.57),('Hsinchu',24.8,120.97),('Seoul',37.57,126.98),('Pyeongtaek',36.99,127.11),('Tokyo',35.68,139.69),('Kyiv',50.45,30.52),('Beijing',39.9,116.4),('Shanghai',31.23,121.47),('Shenzhen',22.54,114.06),('Hong Kong',22.32,114.17),('Suez',30.0,32.55),('Panama Canal',9.1,-79.68),('Strait of Hormuz',26.56,56.25),('Red Sea',20,38),('Strait of Malacca',3.5,100),('South China Sea',14,114),('Taiwan Strait',24.5,119.5),('Eindhoven',51.44,5.48),('Dresden',51.05,13.74),('Frankfurt',50.11,8.68),('Dublin',53.35,-6.26),('London',51.51,-.13),('Paris',48.86,2.35),('Berlin',52.52,13.4),('Warsaw',52.23,21.01),('Phoenix',33.45,-112.07),('Austin',30.27,-97.74),('Texas',31,-99),('Arizona',34.1,-111.1),('Virginia',37.5,-79),('South Carolina',34,-81),('Delaware',39,-75.5),('Seattle',47.61,-122.33),('New York',40.71,-74.01),('Washington DC',38.91,-77.04),('Mumbai',19.08,72.88),('Bengaluru',12.97,77.59),('Hanoi',21.03,105.83),('Ho Chi Minh City',10.82,106.63),('Dubai',25.2,55.27),('Abu Dhabi',24.45,54.38),('Riyadh',24.71,46.68),('Doha',25.29,51.53),('Toronto',43.65,-79.38),('Sao Paulo',-23.55,-46.63),('Europe',51,15),('Africa',1,20),('Middle East',29,44)]
RULES=[('Trade & policy',r'export.{0,15}(control|ban|restrict)|sanction|tariff|trade war|chip.{0,15}(ban|restrict)|US restrictions','access to {sector} and cross-border procurement','which products are covered, the effective date and any exemptions'),('Supply chain',r'semiconductor|chip|\bHBM\b|\bDRAM\b|\bNAND\b|foundry|wafer|memory|rare earth','{sector} availability, production capacity and hardware lead times','production schedules and supplier guidance; announcements are not available capacity'),('Infrastructure',r'\b(?:data.?cent(?:er|re)s?|power (?:grid|plant|supply|outage)|grid|energy|electricity|cables?|fiber|fibre|airports?|ports?|shipping|canal|pipeline|satellite|bridge|rail)\b','{sector} capacity, route resilience and operating costs','service notices, actual affected sites and restoration or commissioning dates'),('Geopolitics',r'\b(?:missiles?|military|war|strike|blockade|invasion|peace talks|drones?|defen[cs]e)\b','regional transport, technology access and infrastructure resilience','official updates on affected routes, trade measures and operating restrictions'),('Business investment',r'\b(?:funding|raises|raised|invests?|investment|investments|acquires?|acquisition|factory|plant|launch(?:es|ed)?|contracts?|expands?|expansion|recorded award)\b','{sector} supplier choices, capacity plans and capital spending','filings and delivery milestones; funding or an award does not establish profits'),('Cyber infrastructure',r'cyberattack|ransomware|breach|outage','service continuity and technology supplier risk','operator advisories, confirmed affected systems and remediation')]
EXCLUDE=re.compile(r'\b(coupon|discount|gaming deal|save \$|review:|best deals)\b',re.I)
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s or ''))).strip()
def stamp(s):
 try:return int(email.utils.parsedate_to_datetime(s).timestamp())
 except Exception:return 0
def matches(title,places):
 found=[]
 for p in places:
  for alias in p['aliases']:
   if alias in ('Georgia','Jordan','Chad','Guinea','Niger','Congo'):continue
   flags=0 if alias in ('US','UK','U.S.','DPRK','UAE') else re.I
   match=re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',title,flags)
   if match:
    specificity=2 if p['name'] in ('Europe','Africa','Middle East') else 1 if p['scale']=='Country reference' else 0
    found.append((specificity,match.start(),p,alias));break
 return sorted(found,key=lambda x:(x[0],x[1]))
def locate(title,places):
 found=matches(title,places)
 return (found[0][2],found[0][3]) if found else (None,None)

def build(rows,places,now):
 result=[];seen=set()
 for item in rows:
  title=clean(item.get('title',''));url=item.get('url','');pub=item.get('published',0)
  if not pub or now-pub>7*86400 or pub>now+3600 or item.get('stale') or not url.startswith(('http://','https://')) or url in seen or EXCLUDE.search(title):continue
  rule=next((r for r in RULES if re.search(r[1],title,re.I)),None)
  if not rule:continue
  if rule[0]=='Infrastructure' and re.search(r'celebrity|shark|pasteuri',title,re.I):continue
  if rule[0]=='Geopolitics' and not re.search(r'Ukraine|Russia|China|Taiwan|North Korea|DPRK|missile|drone|defen[cs]e|navy|industrial|chip|nuclear|shipping|sanction|cyber|satellite|space',title,re.I):continue
  place,matched=locate(title,places)
  if not place:continue
  category,_,why,watch=rule;sector=next((label for pat,label in [(r'\bHBM\b|\bDRAM\b|\bNAND\b|memory','memory hardware'),(r'GPU|NVIDIA|AMD|AI chip','AI accelerators'),(r'DeepSeek|OpenAI|Anthropic|AI model','AI services'),(r'data.?cent','data-center'),(r'power|grid|electric|energy','power'),(r'\b(?:airports?|ports?)\b|shipping|canal|bridge|\brail\b','transport'),(r'cable|fiber|fibre|satellite','connectivity'),(r'chip|semiconductor|foundry|wafer','semiconductor'),(r'cyber|breach|outage','IT service') ] if re.search(pat,title,re.I)),'technology')
  context=place['name']+' is named in this '+sector+' report. Potential relevance: '+why.format(sector=sector)+'.'
  amount=re.search(r'\$[\d,.]+\s*(?:billion|million|[BM]\b)?',title,re.I)
  if amount:context+=' Reported '+amount.group().strip()+'; verify the original terms.'
  result.append({'id':'news-'+hashlib.sha256(url.encode()).hexdigest()[:14],'title':title,'country':place['name'],'kind':category,'level':'Report','severity':title,'population':'','lat':place['lat'],'lon':place['lon'],'alt':3500000 if place['scale']=='Country reference' else 1800000,'updated':pub,'eventTime':pub,'url':url,'source':item['source'],'description':title,'context':context,'watch':'Watch: '+watch+'.','locationBasis':place['scale']+' · place named in headline; not a verified impact site','matchedPlace':matched,'regions':list(dict.fromkeys(x[2]['name'] for x in matches(title,places)))[:6],'category':'Global events · '+category,'published':pub,'exposureCount':0,'exposureNames':[],'eventClass':'context'});seen.add(url)
 return sorted(result,key=lambda x:x['updated'],reverse=True)

def rss(url,name):
 req=urllib.request.Request(url,headers={'User-Agent':'TerminalHouseMedia-GlobalContext/1.0'})
 with urllib.request.urlopen(req,timeout=12) as r:root=ET.fromstring(r.read(3000000))
 return [{'title':clean(x.findtext('title')),'url':x.findtext('link') or '', 'published':stamp(x.findtext('pubDate') or ''),'source':name} for x in root.findall('./channel/item')[:60]]
def main():
 now=int(time.time());rows=[];sources=[]
 for name in ['intel.json','news.json']:
  try:
   d=json.loads((CACHE/name).read_text());groups=d.values() if name=='intel.json' else [d]
   for g in groups:
    if now-g.get('updated',0)>3600:continue
    failed={s['name'] for s in g.get('sources',[]) if not s.get('ok')}
    rows.extend(x for x in freshness.sanitize(g,now)['items'] if x.get('kind')!='repo' and x.get('source') not in failed)
  except Exception:pass
 for url,name in [('https://feeds.bbci.co.uk/news/world/rss.xml','BBC World · reporting'),('https://feeds.bbci.co.uk/news/business/rss.xml','BBC Business · reporting')]:
  try:rows.extend(rss(url,name));sources.append({'name':name,'ok':True,'checked':now})
  except Exception:sources.append({'name':name,'ok':False,'checked':now})
 places=[{'name':n,'lat':a,'lon':b,'aliases':[n],'scale':'Regional reference'} for n,a,b in CUSTOM]+json.loads((ROOT/'global-places.json').read_text())
 for p in places:
  if p['name']=='United States of America' or p['name']=='United States':p['aliases']+=['United States','U.S.','US']
  if p['name']=='United Kingdom':p['aliases']+=['Britain','UK']
  if p['name']=='North Korea':p['aliases']+=['DPRK','North Korean']
  if p['name']=='South Korea':p['aliases']+=['South Korean']
 data={'updated':now,'events':build(rows,places,now)[:36],'sources':sources,'ok':bool(rows),'scope':'Selected public reports with explicit headline geography; location and relevance are qualified.'}
 tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(data));tmp.replace(OUT);print('Context events:',len(data['events']))
if __name__=='__main__':main()
