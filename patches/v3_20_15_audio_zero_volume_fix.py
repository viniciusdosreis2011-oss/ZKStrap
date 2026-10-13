from pathlib import Path
import ast, os

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')
old_music='mgr.music_volume=float(getattr(self,"music_volume",.22) or .22)'
new_music='mgr.music_volume=float(getattr(self,"music_volume",.22))'
old_sfx='mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0) or 1.0)'
new_sfx='mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0))'
if old_music not in s:raise SystemExit('v3.20.15 music zero-volume recovery anchor missing')
if old_sfx not in s:raise SystemExit('v3.20.15 SFX zero-volume recovery anchor missing')
s=s.replace(old_music,new_music,1).replace(old_sfx,new_sfx,1)
ast.parse(s)
p.write_text(s,encoding='utf-8')
print('Applied v3.20.15 zero-volume preservation fix')
