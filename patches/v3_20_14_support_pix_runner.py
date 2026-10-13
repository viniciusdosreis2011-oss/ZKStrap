from pathlib import Path

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

# Keep the support page self-contained at runtime instead of relying on global
# base64/BytesIO imports from older patch layers.
src = src.replace(
    '        from PIL import Image\n        raw=base64.b64decode(_ZK_SUPPORT_QR_B64)',
    '        from PIL import Image\n        import base64\n        from io import BytesIO\n        raw=base64.b64decode(_ZK_SUPPORT_QR_B64)',
    1,
)

ns = {"__name__": "__main__", "__file__": str(src_path)}
exec(compile(src, str(src_path), "exec"), ns, ns)
print("v3.20.14 Pix support runner applied successfully")
