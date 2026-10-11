from pathlib import Path

# Compatibility entrypoint used by the release workflow.
# The first implementation was too strict about one generated-code anchor;
# keep the workflow path stable and delegate to the robust patch.
_fixed = Path(__file__).with_name("v3_20_5_fixed.py")
code = compile(_fixed.read_text(encoding="utf-8"), str(_fixed), "exec")
exec(code, globals(), globals())
