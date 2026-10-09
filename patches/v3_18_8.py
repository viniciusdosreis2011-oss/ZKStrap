from pathlib import Path
import os

root = Path(os.environ.get("ZK_SOURCE_DIR", "."))
path = root / "ZKStrap_v3_18_0.py"
s = path.read_text(encoding="utf-8")

if 'APP_VERSION = "3.18.7"' not in s:
    raise SystemExit('v3.18.8 hotfix: expected v3.18.7 source')
s = s.replace('APP_VERSION = "3.18.7"', 'APP_VERSION = "3.18.8"', 1)

if 'BUILD_TIMESTAMP = "Scroll Router + Visual Depth"' in s:
    s = s.replace('BUILD_TIMESTAMP = "Scroll Router + Visual Depth"', 'BUILD_TIMESTAMP = "Support Callback Hotfix"', 1)

# v3.18.7 replaced the whole _module_switch -> build_right_tabview region.
# _open_support_page and _copy_support_link lived in that region and were
# unintentionally deleted. Restore them without touching the new scroll system.
if '    def _open_support_page(self):\n' not in s:
    anchor = '    def build_right_tabview(self):\n'
    if anchor not in s:
        raise SystemExit('v3.18.8 hotfix: build_right_tabview anchor missing')
    methods = '''    def _open_support_page(self):
        try:
            webbrowser.open(SUPPORT_PAGE_URL)
            self._play_ui_sound("confirm", .02)
        except Exception as exc:
            try:
                messagebox.showerror("ZKStrap", f"Não foi possível abrir a página de apoio.\\n\\n{exc}")
            except Exception:
                pass

    def _copy_support_link(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(SUPPORT_PAGE_URL)
            self.update_idletasks()
            self._play_ui_sound("confirm", .02)
            try:
                messagebox.showinfo("ZKStrap", "Link da página de apoio copiado.")
            except Exception:
                pass
        except Exception as exc:
            try:
                messagebox.showerror("ZKStrap", f"Não foi possível copiar o link.\\n\\n{exc}")
            except Exception:
                pass

'''
    s = s.replace(anchor, methods + anchor, 1)

# Hard fail if either callback is still missing.
for required in ('    def _open_support_page(self):\n', '    def _copy_support_link(self):\n'):
    if required not in s:
        raise SystemExit(f'v3.18.8 hotfix: missing callback {required.strip()}')

path.write_text(s, encoding='utf-8')
print('patched v3.18.8', path)
