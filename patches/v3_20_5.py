from pathlib import Path

_fixed = Path(__file__).with_name("v3_20_5_fixed2.py")
code = compile(_fixed.read_text(encoding="utf-8"), str(_fixed), "exec")
exec(code, globals(), globals())
