from pathlib import Path
import ast
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')

if 'APP_VERSION = "3.19.7"' not in s:
    raise SystemExit('v3.19.8: expected v3.19.7 base')
s=s.replace('APP_VERSION = "3.19.7"','APP_VERSION = "3.19.8"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Replay Language Picker"',s,count=1)
if n!=1:
    raise SystemExit('v3.19.8: timestamp missing')

# Replay the redesigned language onboarding once for users who already confirmed
# revision 3 in earlier betas. After the user chooses a language, revision 4 is
# persisted and the picker returns to normal one-time behavior.
s,n_gate=re.subn(r'picker_rev\s*>=\s*3\b','picker_rev>=4',s,count=1)
if n_gate!=1:
    raise SystemExit(f'v3.19.8: language picker gate not found ({n_gate})')

s,n_rev=re.subn(r'(\["language_picker_revision"\]\s*=\s*)3\b',r'\g<1>4',s)
if n_rev<2:
    raise SystemExit(f'v3.19.8: expected at least 2 language revision writes, found {n_rev}')

# Structural safety checks.
if 'picker_rev>=4' not in s:
    raise SystemExit('v3.19.8: revision 4 picker gate missing')
if s.count('["language_picker_revision"]=4') < 2:
    raise SystemExit('v3.19.8: revision 4 persistence missing')
if 'APP_VERSION = "3.19.8"' not in s:
    raise SystemExit('v3.19.8: version bump missing')
if 'RedrawWindow(' in s:
    raise SystemExit('v3.19.8: unsafe repaint returned')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print(f'Applied ZKStrap v3.19.8 language picker replay patch; revision writes={n_rev}')
