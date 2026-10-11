from pathlib import Path
import ast
import os
import re

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
path=root/'ZKStrap_v3_18_0.py'
s=path.read_text(encoding='utf-8')


def line_offsets(text):
    lines=text.splitlines(True)
    pos=[0]
    total=0
    for line in lines:
        total+=len(line)
        pos.append(total)
    return lines,pos


def app_class(text):
    tree=ast.parse(text)
    cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp'),None)
    if cls is None:
        raise SystemExit('v3.20.1: ModernConfigApp missing')
    return tree,cls


def replace_app_method(name,new_block):
    global s
    _,cls=app_class(s)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:
        raise SystemExit(f'v3.20.1: method missing: {name}')
    _,pos=line_offsets(s)
    start=pos[node.lineno-1]
    end=pos[node.end_lineno]
    s=s[:start]+new_block.rstrip()+"\n\n"+s[end:]


if 'APP_VERSION = "3.20.0"' not in s:
    raise SystemExit('v3.20.1: expected v3.20.0 base')
s=s.replace('APP_VERSION = "3.20.0"','APP_VERSION = "3.20.1"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Instant First Run Lab"',s,count=1)
if n!=1:
    raise SystemExit('v3.20.1: timestamp missing')

fresh_flow=r'''    def _owner_enter_fresh_test(self):
        if not self._owner_key_valid():
            return
        if bool(getattr(self,"_owner_fresh_busy",False)):
            try:self.show_toast("FIRST RUN LAB","A simulação já está sendo preparada.",kind="info",duration=2400)
            except Exception:pass
            return
        if not messagebox.askyesno(
            "SIMULAR PRIMEIRA EXECUÇÃO",
            "Abrir o ZKStrap como se tivesse acabado de ser instalado?\n\n"
            "• Seu perfil principal NÃO será alterado.\n"
            "• Somente o perfil isolado de TESTE será apagado e recriado do zero.\n"
            "• Você verá idioma, onboarding, tutorial e valores padrão novamente.\n"
            "• Não é necessário criar snapshot para este teste.\n\n"
            "Depois, use VOLTAR AO MEU PERFIL para retornar.",
            parent=self
        ):
            return

        self._owner_fresh_busy=True
        self._owner_fresh_result=None
        try:
            btn=getattr(self,"_owner_fresh_button",None)
            if btn is not None and btn.winfo_exists():
                btn.configure(state="disabled",text="PREPARANDO PRIMEIRA EXECUÇÃO...")
        except Exception:pass
        try:
            lbl=getattr(self,"_owner_fresh_status",None)
            if lbl is not None and lbl.winfo_exists():
                lbl.configure(text="Zerando apenas o perfil isolado de teste...")
        except Exception:pass

        def worker():
            try:
                # The real profile is intentionally untouched. A safety snapshot is
                # unnecessary here because the simulation only destroys TEST_PROFILE.
                test=self._owner_test_profile_dir()
                if os.path.isdir(test):
                    shutil.rmtree(test,ignore_errors=False)
                os.makedirs(test,exist_ok=True)

                st=_owner_state_read_global() if self._owner_key_valid() else {}
                st["test_profile"]=True
                if not _owner_state_write_global(st):
                    raise RuntimeError("não foi possível ativar o perfil de teste")
                self._owner_state=dict(st)
                self._owner_fresh_result=("ok",test)
            except Exception as exc:
                self._owner_fresh_result=("error",f"{type(exc).__name__}: {exc}")

        threading.Thread(target=worker,name="ZKFirstRunLab",daemon=True).start()
        try:self.after(80,self._owner_fresh_poll)
        except Exception:
            self._owner_fresh_busy=False
'''
replace_app_method('_owner_enter_fresh_test',fresh_flow)

# Update the explanatory copy: snapshot belongs to Backup Lab, not First Run Lab.
s=s.replace(
    'Teste o ZKStrap exatamente como um usuário que acabou de baixar: idioma, onboarding, tutorial, valores padrão e desbloqueios iniciais. Seu perfil principal fica intacto em outra pasta.',
    'Teste o ZKStrap exatamente como um usuário que acabou de baixar: idioma, onboarding, tutorial, valores padrão e desbloqueios iniciais. Só o perfil isolado de teste é zerado; seu perfil principal não é tocado.'
)
s=s.replace('Criando snapshot e preparando perfil zerado...','Zerando apenas o perfil isolado de teste...')

# Remove stale v3.20.0 before-first-run archives opportunistically when entering
# Owner Lab backup directory next time. These were only safety copies and can be
# huge if the previous simulation was interrupted; manual snapshots are preserved.
old='''    def _owner_backups_dir(self):
        p=os.path.join(_owner_vault_dir(),"BACKUPS")
        os.makedirs(p,exist_ok=True)
        return p'''
new='''    def _owner_backups_dir(self):
        p=os.path.join(_owner_vault_dir(),"BACKUPS")
        os.makedirs(p,exist_ok=True)
        try:
            for name in os.listdir(p):
                if name.endswith("_before_first_run_test.zip"):
                    fp=os.path.join(p,name)
                    try:os.remove(fp)
                    except Exception:pass
        except Exception:pass
        return p'''
if old in s:
    s=s.replace(old,new,1)

for needle in (
    'APP_VERSION = "3.20.1"',
    'Não é necessário criar snapshot para este teste.',
    'Zerando apenas o perfil isolado de teste...',
    'self._owner_fresh_result=("ok",test)',
    'threading.Thread(target=worker,name="ZKFirstRunLab",daemon=True).start()',
):
    if needle not in s:
        raise SystemExit('v3.20.1: missing '+needle)

# First Run Lab must no longer archive the real profile.
tree,cls=app_class(s)
node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_owner_enter_fresh_test')
_,pos=line_offsets(s)
method_src=s[pos[node.lineno-1]:pos[node.end_lineno]]
for forbidden in ('shutil.make_archive','_owner_backups_dir()','last_snapshot','before_first_run_test'):
    if forbidden in method_src:
        raise SystemExit('v3.20.1: First Run Lab still contains '+forbidden)
if 'RedrawWindow(' in s:
    raise SystemExit('v3.20.1: unsafe repaint returned')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.20.1 instant First Run Lab patch')
