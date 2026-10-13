from pathlib import Path
import ast
import base64
import re
import runpy

src_path = Path(__file__).with_name("v3_20_14_support_pix.py")
src = src_path.read_text(encoding="utf-8")

# Exact PNG generated from the user's no-fixed-value Pix BR Code payload.
# Kept here as the canonical copy so a typo in the earlier patch cannot affect
# the QR shown to users.
VALID_PIX_QR_B64 = "iVBORw0KGgoAAAANSUhEUgAAAhIAAAISAQAAAACxRhsSAAAE1klEQVR4nO2dUY7bOgxFL2sD+bSBLmCWYu+gSyq6pO7AXsosoID8GUAG+yFKovIy0wc09ssLrj6COHEOZICgyCtSEcXfjvXLXyMAMsgggwwyyCCDDDLIqAyx0UNmADJv9gGAXbCOgMi4i8jov5X5wfMgg4wPhqqqYlJV1dApMES4yyl06Z2qRthLusw/W57lWch4fcZm3lEXdKo/RkDmIUKX4Vr8aee0ARHpj5gHGWTcG/3NtUwBkOm9j4rtaxSgU5l0F0xLueXn4+dBBhmfjVs7VWDvgeEqiiECKT6VTmUdA+SweZBBxr9hDKq6AAC2i71bpU+RKjBcBVPYJYWlC5Ai1QPmQQYZnzBWkZzMA5B5u6h8DwCw9cD0flFgu6jMWw+ZsRc14MHzIIOMuyOt+y5BWscOad23d7F8AQGGCG3uf9A8yCDj02ECUwDSer4kw+xyGADAjHWIUA0wXWop+hV1KTIOZyQ7Na1UYwlIIzAFAECXZVKYnJpvsV/STsk4nmH+FMWLmrPUJOzfKP71UpeBOj8ZpzGKP7Ul32f0wWIBTBqRw4DqT8vNz/IsZLwuw8Wn9qLq/KnZbv427VYlV5o3T2mnZBzPyP5US6akZoTAUNxmALJ15l8sjE/JOI/R5FG5DsWHpjWtqgYMS7pop2ScxMh5FLIDTUl/AMyf5tzqRggwhYp2SsYpDJ9HFV3UcqY7FX4LzESZR5FxJsMHpGllT9mTFveqefNpiP+Q+GmnZJzD8Pk+UNxma6L12xqaLmC+T8ZpDJfv14w+K1R+U8rs2d3XUecn4yyGU5nyJ9VjllEVqlLNx3yfjPMZReJPXjSNsvhPYRdMoVOZ637UdlGZHz0PMsi4O1Jdn1WSbl8j1vFXj3UMilTZb59BV+kisI35vreYy/ue5VnIeHWGl/MDoMsmAtNUI3IsehWsY9dWUz12HmSQ8cHI+VGVn2oylRtMU7qEptvE7aA+y7OQ8boMV8+v67dfvQJ7r9i6KFa7D2AVAFN63ylSI+qgkNSD+izPQsbLM1YRSb1QdWVPl9Kj6fKzBlVdNhH77MmehYwXZPi+k1ahSgX8aeStKKdGKfVTMs5jlDqUsm8PmMRfWvhSDV8pPbXNU9BOyTiN0Rac5v1Q64VCTv+HUqpSdYGcftFOyTieUVZ7LzWpHXfmy/e8EAXW9ZFxLqOp69PYqFGhsdilJFNTtWzaKRmnMJw/zfFpG4YOdRu1VklFJ7vSTsk4nuGz/KmecKq+Q9++CEBtl2K9FBlnMkpdX20hbQ+bqAfzBsCZMtd9Mk5kuIb95jyU3DNVG/eQbvFBAvMoMk5ilECzyfdrJTQA1yRlR6MDcN1TtFMyDme4db9GpTdHS7nO09qQQv2UjNMZ9f9OML33wPqmfpMf2MVk//fef/boeZBBxqeMKYuoMJvcRTXsUg9Iw/p2zZfJgPO508/2LGS8IKM9X6o0PYe21jR37/k+Kvbvk/HfMWTeLpqK+9YRZrE/pKz2W5+7+7eLfsB4xDzIIKMZN/7U75beetH2H894Xh8Z5zMGE1F1QafmVOWiMqd0ySJVkberpH88W8dD5kEGGXeHqVFpdFl+QlfkfH9Amp0+NbSV1c/yLGS8LkP0z/f8YazP8ixkkEEGGWSQQQYZZPz/Gb8BDwxHMSMHqtsAAAAASUVORK5CYII="
raw_qr = base64.b64decode(VALID_PIX_QR_B64, validate=True)
if not raw_qr.startswith(b"\x89PNG\r\n\x1a\n") or len(raw_qr) != 1295:
    raise SystemExit("Canonical Pix QR PNG validation failed")

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

# Force the generated app to contain exactly the validated QR PNG above. This
# overrides the malformed first embedded copy and any older placeholder.
app_path = Path(ns["p"])
app = app_path.read_text(encoding="utf-8")
qr_line = f'_ZK_SUPPORT_QR_B64 = "{VALID_PIX_QR_B64}"'
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

# The release runner owns the final additive admin patch too, so the existing
# v3.20.14 build workflow always compiles the safe cleanup panel together with
# the support page without changing the normal app routes.
admin_patch = Path(__file__).with_name("v3_20_14_admin_cleanup.py")
if not admin_patch.is_file():
    raise SystemExit("Admin cleanup patch missing")
runpy.run_path(str(admin_patch), run_name="__main__")

final_source = app_path.read_text(encoding="utf-8")
final_tree = ast.parse(final_source)
app_cls = next(n for n in final_tree.body if isinstance(n, ast.ClassDef) and n.name == "ModernConfigApp")
method_names = {n.name for n in app_cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
for required in ("_owner_cleanup_specs","_owner_cleanup_scan","_owner_cleanup_delete_selected","_owner_cleanup_finish_delete"):
    if required not in method_names:
        raise SystemExit(f"Admin cleanup method missing after patch: {required}")
for required_text in ("LIMPEZA SEGURA // DISCO","MEMORY.DMP","DXCache","WinSxS","Windows\\\\Installer"):
    if required_text not in final_source:
        raise SystemExit(f"Admin cleanup safety marker missing: {required_text}")

print("v3.20.14 Pix support + admin safe disk cleanup applied successfully")
