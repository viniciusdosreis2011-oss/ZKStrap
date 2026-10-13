from pathlib import Path
import ast, os

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')
old='''        mgr.music_volume=float(getattr(self,"music_volume",.22) or .22)\n        mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0) or 1.0)'''
new='''        mgr.music_volume=float(getattr(self,"music_volume",.22))\n        mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0))'''
if old not in s:raise SystemExit('v3.20.15 zero-volume recovery anchor missing')
s=s.replace(old,new,1)
ast.parse(s)
p.write_text(s,encoding='utf-8')
print('Applied v3.20.15 zero-volume preservation fix')
