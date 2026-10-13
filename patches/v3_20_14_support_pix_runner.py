from pathlib import Path
import ast
import re

src_path = Path(__file__).with_name("v3_20_14_support_pix.py")
src = src_path.read_text(encoding="utf-8")

# The clean-icons pass may format its pictogram method differently between
# reconstructed builds. The support page does not need to rewrite that method,
# so strip the fragile optional icon rewrite and apply only the page/QR changes.
start_marker = "# Give Support its own clean heart identity instead of sharing the generic info icon."
end_marker = "support_method = '''def _lazy_build_page_support(self):"
start = src.find(start_marker)
end = src.find(end_marker)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Could not prepare support-page patch runner")
src = src[:start] + src[end:]

# Keep the QR rendering self-contained at runtime instead of relying on global
# base64/BytesIO imports from older patch layers.
src = src.replace(
    '        from PIL import Image\n        raw=base64.b64decode(_ZK_SUPPORT_QR_B64)',
    '        from PIL import Image\n        import base64\n        from io import BytesIO\n        raw=base64.b64decode(_ZK_SUPPORT_QR_B64)',
    1,
)

# Avoid geometry-only padding options in the CTkLabel constructor. Use an
# explicit compact badge size so this stays compatible across CTk versions.
src = src.replace(
    'font=ctk.CTkFont(size=9,weight="bold"),padx=8,pady=3).pack(side="right")',
    'font=ctk.CTkFont(size=9,weight="bold"),width=92,height=24).pack(side="right")',
    1,
)

ns = {"__name__": "__main__", "__file__": str(src_path)}
exec(compile(src, str(src_path), "exec"), ns, ns)

# Force the generated app to contain exactly the QR payload from this patch.
# This also overrides any placeholder left by older Support Hub versions.
app_path = Path(ns["p"])
app = app_path.read_text(encoding="utf-8")
qr_b64 = ns["_ZK_SUPPORT_QR_B64"]
qr_line = f'_ZK_SUPPORT_QR_B64 = "{qr_b64}"'
pattern = r'(?m)^_ZK_SUPPORT_QR_B64\s*=.*$'
if re.search(pattern, app):
    app = re.sub(pattern, qr_line, app, count=1)
else:
    anchor = 'PUBLIC_DISCORD_URL = ""  # preencher só quando houver um convite público oficial\n'
    if anchor not in app:
        raise SystemExit("Could not place final embedded Pix QR")
    app = app.replace(anchor, anchor + qr_line + "\n", 1)
app_path.write_text(app, encoding="utf-8")
ast.parse(app)

print("v3.20.14 Pix support runner applied successfully with forced QR payload")
