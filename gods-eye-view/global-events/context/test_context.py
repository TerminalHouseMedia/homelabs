import importlib.util,json,time
from pathlib import Path
p=Path(__file__).with_name('build_context.py');spec=importlib.util.spec_from_file_location('context',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
places=json.loads(p.with_name('places.json').read_text());now=int(time.time())
def row(title,**extra):return {'title':title,'url':'https://example.com/'+title,'source':'Test reporting','published':now,**extra}
items=m.build([row("Micron's Taiwan union will launch a one-day strike threatening memory production"),row('Google resolves cloud outage affecting United Kingdom banks'),row('No order, no seat: Starbucks China rolls out new store policy'),row("Police investigate Married at First Sight Australia"),row('Celebrity shark refuses to leave South Korea canal'),row('Company raises funding without a named location'),row('Russia missile strike disrupts Ukraine power grid',published=now-8*86400)],places,now)
assert len(items)==2,[(x['title'],x['kind']) for x in items]
assert all(x['context'].startswith(x['country']) for x in items)
assert all('not a verified impact site' in x['locationBasis'] for x in items)
print('Passed: relevant tech events, explicit geography, no guessed HQ, stale exclusion and unrelated-news rejection.')
