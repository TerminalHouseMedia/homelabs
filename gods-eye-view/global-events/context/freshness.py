"""Separate publication age from fetch age; never renew old data by reserializing it."""
import time
def sanitize(data,now=None):
 now=int(now or time.time());out=dict(data);rows=[];sources=data.get('sources',[])
 for x in data.get('items',[]):
  row=dict(x);kind=row.get('kind','news');published=row.get('published',0)
  limits={'repo':90*86400,'contract':30*86400};ttl=7200 if kind=='repo' else 3600
  checks=[s for s in sources if s.get('name')==row.get('source')]
  fetched=row.get('fetched') or max([s.get('checked',0) for s in checks] or [0])
  if not fetched or not published or now-fetched>ttl or now-published>limits.get(kind,7*86400) or published>now+3600:continue
  if any(not s.get('ok') for s in checks):row['stale']=True
  row['fetched']=fetched;rows.append(row)
 out['items']=rows;out['freshness']={'served':now,'expired_items':len(data.get('items',[]))-len(rows),'news_max_age_days':7,'fetch_ttl_seconds':3600,'repo_fetch_ttl_seconds':7200};return out
