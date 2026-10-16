from pathlib import Path
import os

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')

old='''        intense_days=max(0,(today-intensive_start_dt.date()).days); project_days=max(0,(today-project_start).days)\n        intense_hours=max(0,int((now_dt-intensive_start_dt).total_seconds()//3600))'''
new='''        # Final post: the intensive development phase ended on day 33.\n        # Keep the overall project counter dynamic, but freeze this completed phase.\n        intense_days=33; project_days=max(0,(today-project_start).days)\n        intense_hours=792'''

if old not in s:
    raise SystemExit('v3.20.20 FINAL POST: intensive counter anchor missing')
s=s.replace(old,new,1)

# Guard against accidental regressions before packaging.
if 'intense_days=33' not in s or 'intense_hours=792' not in s:
    raise SystemExit('v3.20.20 FINAL POST: frozen counter validation failed')

p.write_text(s,encoding='utf-8')
print('v3.20.20 FINAL POST: intensive phase frozen at 33 days / 792 h')
