"""Hotfix de lançamento: onboarding único e indicador do tamanho do cursor."""
from __future__ import annotations
import ast
import os
from pathlib import Path

src = Path(os.environ.get("ZK_SOURCE_DIR", ".")) / "ZKStrap_v3_18_0.py"
data = src.read_text(encoding="utf-8")

def replace_method(source, method_name, replacement):
    tree = ast.parse(source)
    cls = next((node for node in tree.body if isinstance(node, ast.ClassDef)
                and node.name == "ModernConfigApp"), None)
    if cls is None:
        raise RuntimeError("ModernConfigApp nao encontrada")
    method = next((node for node in cls.body if isinstance(node, ast.FunctionDef)
                   and node.name == method_name), None)
    if method is None:
        raise RuntimeError("Metodo obrigatorio nao encontrado: " + method_name)
    lines = source.splitlines(keepends=True)
    begin = sum(map(len, lines[:method.lineno - 1]))
    finish = sum(map(len, lines[:method.end_lineno]))
    return source[:begin] + replacement.rstrip() + "\n" + source[finish:]

data = replace_method(data, "_maybe_show_first_run_tutorial", '''
    def _maybe_show_first_run_tutorial(self):
        """Mostrar automaticamente uma unica vez por usuario local.

        O tutorial continua disponivel manualmente no menu. Uma sentinela fora
        do diretorio da instalacao sobrevive a atualizacoes e novas builds.
        """
        if not bool(getattr(self, "language_selected", False)):
            self.after(300, self._maybe_show_first_run_tutorial)
            return
        if bool(getattr(self, "_sound_prompt_open", False)):
            self.after(350, self._maybe_show_first_run_tutorial)
            return
        if bool(getattr(self, "tutorial_completed", False)):
            return

        base = os.environ.get("LOCALAPPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Local"
        )
        marker = os.path.join(base, "ZKSTRAP", "tutorial_first_run_seen.flag")
        already_seen = os.path.isfile(marker)
        # Migracao: jogadores que ja passaram pelo perfil/onboarding nao
        # devem receber o tutorial novamente depois de atualizar.
        profile_done = bool(
            getattr(self, "config_data", {}).get("roblox_onboarding_completed", False)
        )
        if already_seen or profile_done:
            self.tutorial_completed = True
            try:
                self.salvar_config_app()
            except Exception:
                pass
            if not already_seen:
                try:
                    os.makedirs(os.path.dirname(marker), exist_ok=True)
                    with open(marker, "w", encoding="utf-8") as f:
                        f.write("1\\n")
                except OSError:
                    pass
            return

        self.abrir_tutorial(primeiro_acesso=True)
        # Marca apos criar a interface, nao antes; evita perder o tutorial
        # caso abrir_tutorial falhe antes de exibir a primeira tela.
        try:
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker, "w", encoding="utf-8") as f:
                f.write("1\\n")
        except OSError:
            pass
''')

# Mantem o comportamento original do slider e faz o indicador "30 px"
# acompanhar seu valor. O ajuste e aplicado ao cursor ao clicar em Aplicar.
tree = ast.parse(data)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ModernConfigApp")
method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "evento_cursor_tamanho")
lines = data.splitlines(keepends=True)
begin = sum(map(len, lines[:method.lineno - 1]))
finish = sum(map(len, lines[:method.end_lineno]))
original = data[begin:finish].rstrip("\n")
if "cursor_size_value.configure" not in original:
    original += '''
        try:
            label = getattr(self, "cursor_size_value", None)
            if label is not None and label.winfo_exists():
                label.configure(text=f"{int(self.cursor_visual_size)} px")
        except Exception:
            pass'''
data = data[:begin] + original + "\n" + data[finish:]

old = 'APP_VERSION = "3.20.20"'
if data.count(old) != 1:
    raise RuntimeError(f"Version anchor inesperado: {data.count(old)}")
data = data.replace(old, 'APP_VERSION = "3.20.21"', 1)
ast.parse(data)
compile(data, str(src), "exec")
assert 'tutorial_first_run_seen.flag' in data
assert 'label.configure(text=f"{int(self.cursor_visual_size)} px")' in data
src.write_text(data, encoding="utf-8")
print("HOTFIX v3.20.21 OK: tutorial one-time + cursor px label")
