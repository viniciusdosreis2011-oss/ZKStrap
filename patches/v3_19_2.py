from pathlib import Path

parts_dir = Path(__file__).with_name("v3_19_2_parts")
parts = sorted(parts_dir.glob("part*.txt"))
if len(parts) != 7:
    raise SystemExit(f"v3.19.2 loader: expected 7 parts, found {len(parts)}")
code = "".join(p.read_text(encoding="utf-8") for p in parts)
exec(compile(code, "v3_19_2_full.py", "exec"), globals(), globals())
