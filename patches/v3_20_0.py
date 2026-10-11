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
        raise SystemExit('v3.20.0: ModernConfigApp missing')
    return tree,cls


def replace_app_method(name,new_block):
    global s
    _,cls=app_class(s)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:
        raise SystemExit(f'v3.20.0: method missing: {name}')
    _,pos=line_offsets(s)
    start=pos[node.lineno-1]
    end=pos[node.end_lineno]
    s=s[:start]+new_block.rstrip()+"\n\n"+s[end:]


if 'APP_VERSION = "3.19.9"' not in s:
    raise SystemExit('v3.20.0: expected v3.19.9 base')
s=s.replace('APP_VERSION = "3.19.9"','APP_VERSION = "3.20.0"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "First Run Simulation Lab"',s,count=1)
if n!=1:
    raise SystemExit('v3.20.0: timestamp missing')

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
            "• Um snapshot de segurança será criado.\n"
            "• O perfil de teste será apagado e recriado 100% do zero.\n"
            "• Você verá idioma, onboarding, tutorial e valores padrão novamente.\n\n"
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
                lbl.configure(text="Criando snapshot e preparando perfil zerado...")
        except Exception:pass

        def worker():
            partial=""
            try:
                # 1) Snapshot of the real profile. The real profile itself is never moved/deleted.
                src=self._owner_main_profile_dir()
                os.makedirs(src,exist_ok=True)
                stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
                base=os.path.join(self._owner_backups_dir(),f"{stamp}_before_first_run_test")
                partial=base+".zip"
                archive=shutil.make_archive(base,"zip",root_dir=src)

                # 2) Recreate the isolated test profile from zero every single time.
                test=self._owner_test_profile_dir()
                if os.path.isdir(test):
                    shutil.rmtree(test,ignore_errors=False)
                os.makedirs(test,exist_ok=True)

                # 3) Persist mode only after both operations completed successfully.
                st=_owner_state_read_global() if self._owner_key_valid() else {}
                st["last_snapshot"]=archive
                st["test_profile"]=True
                if not _owner_state_write_global(st):
                    raise RuntimeError("não foi possível ativar o perfil de teste")
                self._owner_state=dict(st)
                self._owner_fresh_result=("ok",archive)
            except Exception as exc:
                try:
                    if partial and os.path.isfile(partial):
                        os.remove(partial)
                except Exception:pass
                self._owner_fresh_result=("error",f"{type(exc).__name__}: {exc}")

        threading.Thread(target=worker,name="ZKFirstRunLab",daemon=True).start()
        try:self.after(120,self._owner_fresh_poll)
        except Exception:
            self._owner_fresh_busy=False

    def _owner_fresh_poll(self):
        if not bool(getattr(self,"_owner_fresh_busy",False)):
            return
        result=getattr(self,"_owner_fresh_result",None)
        if result is None:
            try:self.after(120,self._owner_fresh_poll)
            except Exception:self._owner_fresh_busy=False
            return
        self._owner_fresh_result=None
        status,payload=result
        if status=="ok":
            self._owner_fresh_busy=False
            try:
                lbl=getattr(self,"_owner_fresh_status",None)
                if lbl is not None and lbl.winfo_exists():
                    lbl.configure(text="Perfil zerado pronto. Reiniciando no modo novo usuário...")
            except Exception:pass
            try:self.show_toast("FIRST RUN LAB","Perfil limpo pronto — reiniciando...",kind="success",duration=1800)
            except Exception:pass
            self.after(300,self._owner_restart)
        else:
            self._owner_fresh_failed(payload)

    def _owner_fresh_failed(self,message):
        self._owner_fresh_busy=False
        try:
            btn=getattr(self,"_owner_fresh_button",None)
            if btn is not None and btn.winfo_exists():
                btn.configure(state="normal",text="SIMULAR PRIMEIRA EXECUÇÃO")
        except Exception:pass
        try:
            lbl=getattr(self,"_owner_fresh_status",None)
            if lbl is not None and lbl.winfo_exists():
                lbl.configure(text="Falha ao preparar o perfil de teste. Seu perfil principal continua intacto.")
        except Exception:pass
        try:messagebox.showerror("FIRST RUN LAB",f"Não foi possível preparar a simulação:\n{message}",parent=self)
        except Exception:pass
'''
replace_app_method('_owner_enter_fresh_test',fresh_flow)

# Make the Profile Lab describe the actual workflow instead of making Snapshot
# sound like something the owner must manually orchestrate.
old_intro='ctk.CTkLabel(tab_profile,text="FRESH USER LAB",text_color=t["accent"],font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=16,pady=(16,4))\n        ctk.CTkLabel(tab_profile,text="O perfil de teste fica em uma pasta separada. Seu perfil real permanece intacto e volta com um clique.",text_color=t.get("muted","gray"),wraplength=850,justify="left").pack(anchor="w",padx=16,pady=(0,12))\n        for txt,cmd,fg in [\n            ("ENTRAR EM FRESH USER TEST",self._owner_enter_fresh_test,t["accent"]),\n            ("VOLTAR AO PERFIL PRINCIPAL",self._owner_return_main,t["card_active"]),\n            ("RESETAR PERFIL DE TESTE",self._owner_reset_test_profile,t["card_active"]),\n            ("FACTORY RESET DO PERFIL ATUAL",self._owner_factory_reset_current,"#8C2837")]:\n            ctk.CTkButton(tab_profile,text=txt,command=cmd,fg_color=fg,hover_color=t["hover"],text_color="#050505" if fg==t["accent"] else t["text"],height=42).pack(fill="x",padx=16,pady=5)'
new_intro='ctk.CTkLabel(tab_profile,text="FIRST RUN LAB",text_color=t["accent"],font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=16,pady=(16,4))\n        ctk.CTkLabel(tab_profile,text="Teste o ZKStrap exatamente como um usuário que acabou de baixar: idioma, onboarding, tutorial, valores padrão e desbloqueios iniciais. Seu perfil principal fica intacto em outra pasta.",text_color=t.get("muted","gray"),wraplength=850,justify="left").pack(anchor="w",padx=16,pady=(0,6))\n        self._owner_fresh_status=ctk.CTkLabel(tab_profile,text=("Você está no PERFIL DE TESTE." if _owner_test_profile_enabled() else "Você está no seu PERFIL PRINCIPAL."),text_color=t["accent"],anchor="w",font=ctk.CTkFont(size=10,weight="bold"));self._owner_fresh_status.pack(fill="x",padx=16,pady=(0,12))\n        self._owner_fresh_button=ctk.CTkButton(tab_profile,text="SIMULAR PRIMEIRA EXECUÇÃO",command=self._owner_enter_fresh_test,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=44);self._owner_fresh_button.pack(fill="x",padx=16,pady=5)\n        ctk.CTkButton(tab_profile,text="VOLTAR AO MEU PERFIL",command=self._owner_return_main,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],height=42).pack(fill="x",padx=16,pady=5)\n        ctk.CTkButton(tab_profile,text="ZERAR NOVAMENTE O PERFIL DE TESTE",command=self._owner_reset_test_profile,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],height=42).pack(fill="x",padx=16,pady=5)\n        ctk.CTkButton(tab_profile,text="FACTORY RESET DO PERFIL ATUAL",command=self._owner_factory_reset_current,fg_color="#8C2837",hover_color=t["hover"],text_color=t["text"],height=42).pack(fill="x",padx=16,pady=5)'
if old_intro not in s:
    raise SystemExit('v3.20.0: Profile Lab UI anchor missing')
s=s.replace(old_intro,new_intro,1)

for needle in (
    'APP_VERSION = "3.20.0"',
    'def _owner_fresh_poll(self):',
    'def _owner_fresh_failed(self,message):',
    'threading.Thread(target=worker,name="ZKFirstRunLab",daemon=True).start()',
    'SIMULAR PRIMEIRA EXECUÇÃO',
    'VOLTAR AO MEU PERFIL',
    'FIRST RUN LAB',
    'st["test_profile"]=True',
):
    if needle not in s:
        raise SystemExit('v3.20.0: missing '+needle)
if 'self._owner_make_snapshot("before_fresh_test")' in s:
    raise SystemExit('v3.20.0: blocking before_fresh_test snapshot still present')
if 'RedrawWindow(' in s:
    raise SystemExit('v3.20.0: unsafe repaint returned')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.20.0 First Run Lab patch')
