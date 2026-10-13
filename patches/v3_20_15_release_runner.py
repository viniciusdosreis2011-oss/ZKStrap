from pathlib import Path
import ast
import runpy

here=Path(__file__).resolve().parent
support=here/'v3_20_14_support_pix_runner.py'
runtime=here/'v3_20_15_runtime_fixes.py'
zero_volume=here/'v3_20_15_audio_zero_volume_fix.py'
if not support.is_file(): raise SystemExit('support/admin runner missing')
if not runtime.is_file(): raise SystemExit('v3.20.15 runtime patch missing')
if not zero_volume.is_file(): raise SystemExit('v3.20.15 zero-volume patch missing')
runpy.run_path(str(support),run_name='__main__')
runpy.run_path(str(runtime),run_name='__main__')
runpy.run_path(str(zero_volume),run_name='__main__')

root=Path(__import__('os').environ.get('ZK_SOURCE_DIR','.'))
app=root/'ZKStrap_v3_18_0.py'
s=app.read_text(encoding='utf-8')
t=ast.parse(s)
cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')
methods={n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
for req in ('_audio_restore_runtime_state','_persist_profile_avatar_bytes','_combo_local_icon_path','_owner_secret_theme_unlocked'):
    if req not in methods: raise SystemExit('missing v3.20.15 method: '+req)
for marker in ('APP_VERSION = "3.20.15"','APOIE O ZKSTRAP','LIMPEZA SEGURA // DISCO','for ext in ("png","webp")','"unlocked_secret_themes":[]','mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0))'):
    if marker not in s: raise SystemExit('missing v3.20.15 marker: '+marker)
print('v3.20.15 release runner applied: Pix + admin cleanup + runtime fixes')
