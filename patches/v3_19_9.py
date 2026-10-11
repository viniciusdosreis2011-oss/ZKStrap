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
        raise SystemExit('v3.19.9: ModernConfigApp missing')
    return tree,cls


def replace_app_method(name,new_block):
    global s
    _,cls=app_class(s)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None:
        raise SystemExit(f'v3.19.9: method missing: {name}')
    _,pos=line_offsets(s)
    start=pos[node.lineno-1]
    end=pos[node.end_lineno]
    s=s[:start]+new_block.rstrip()+"\n\n"+s[end:]


if 'APP_VERSION = "3.19.8"' not in s:
    raise SystemExit('v3.19.9: expected v3.19.8 base')
s=s.replace('APP_VERSION = "3.19.8"','APP_VERSION = "3.19.9"',1)
s,n=re.subn(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Owner Snapshot Background Worker"',s,count=1)
if n!=1:
    raise SystemExit('v3.19.9: timestamp missing')

# Manual Owner Lab snapshots used to run shutil.make_archive on Tk's main thread.
# On a non-trivial profile that blocks repaint/input long enough for Windows to
# show a blank/white window. Keep destructive-operation safety snapshots
# synchronous, but move the MANUAL button to a worker and poll results on Tk.
manual_snapshot=r'''    def _owner_backup_now(self):
        if not self._owner_key_valid():
            return
        if bool(getattr(self,"_owner_snapshot_busy",False)):
            try:self.show_toast("OWNER SNAPSHOT","Já existe um snapshot sendo criado.",kind="info",duration=2600)
            except Exception:pass
            return

        self._owner_snapshot_busy=True
        self._owner_snapshot_result=None
        try:
            btn=getattr(self,"_owner_snapshot_button",None)
            if btn is not None and btn.winfo_exists():
                btn.configure(state="disabled",text="CRIANDO SNAPSHOT...")
        except Exception:pass
        try:
            lbl=getattr(self,"_owner_snapshot_label",None)
            if lbl is not None and lbl.winfo_exists():
                lbl.configure(text="Criando snapshot em segundo plano...")
        except Exception:pass

        def worker():
            partial=""
            try:
                src=self._owner_main_profile_dir()
                os.makedirs(src,exist_ok=True)
                stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
                base=os.path.join(self._owner_backups_dir(),f"{stamp}_manual")
                partial=base+".zip"
                archive=shutil.make_archive(base,"zip",root_dir=src)
                st=_owner_state_read_global() if self._owner_key_valid() else {}
                st["last_snapshot"]=archive
                if not _owner_state_write_global(st):
                    raise RuntimeError("não foi possível salvar o estado do Owner Lab")
                self._owner_state=dict(st)
                self._owner_snapshot_result=("ok",archive)
            except Exception as exc:
                try:
                    if partial and os.path.isfile(partial):
                        os.remove(partial)
                except Exception:pass
                self._owner_snapshot_result=("error",f"{type(exc).__name__}: {exc}")

        threading.Thread(target=worker,name="ZKOwnerSnapshot",daemon=True).start()
        try:self.after(120,self._owner_snapshot_poll)
        except Exception:
            self._owner_snapshot_busy=False

    def _owner_snapshot_poll(self):
        if not bool(getattr(self,"_owner_snapshot_busy",False)):
            return
        result=getattr(self,"_owner_snapshot_result",None)
        if result is None:
            try:self.after(120,self._owner_snapshot_poll)
            except Exception:self._owner_snapshot_busy=False
            return
        self._owner_snapshot_result=None
        status,payload=result
        if status=="ok":
            self._owner_backup_done(payload)
        else:
            self._owner_backup_failed(payload)

    def _owner_backup_done(self,path):
        self._owner_snapshot_busy=False
        try:
            btn=getattr(self,"_owner_snapshot_button",None)
            if btn is not None and btn.winfo_exists():
                btn.configure(state="normal",text="CRIAR SNAPSHOT")
        except Exception:pass
        try:self._owner_refresh_panel_status()
        except Exception:pass
        try:self.show_toast("OWNER SNAPSHOT",os.path.basename(path),kind="success",duration=4200)
        except Exception:pass

    def _owner_backup_failed(self,message):
        self._owner_snapshot_busy=False
        try:
            btn=getattr(self,"_owner_snapshot_button",None)
            if btn is not None and btn.winfo_exists():
                btn.configure(state="normal",text="CRIAR SNAPSHOT")
        except Exception:pass
        try:
            lbl=getattr(self,"_owner_snapshot_label",None)
            if lbl is not None and lbl.winfo_exists():
                lbl.configure(text="Snapshot falhou — tente novamente.")
        except Exception:pass
        try:messagebox.showerror("ZK OWNER LAB",f"Falha no snapshot:\n{message}",parent=self)
        except Exception:pass
'''
replace_app_method('_owner_backup_now',manual_snapshot)

# Keep a reference to the manual snapshot button so its busy state is visible.
old='ctk.CTkButton(drow,text="CRIAR SNAPSHOT",command=self._owner_backup_now,fg_color=t["accent"],text_color="#050505").pack(side="left",expand=True,fill="x",padx=(0,4))'
new='self._owner_snapshot_button=ctk.CTkButton(drow,text="CRIAR SNAPSHOT",command=self._owner_backup_now,fg_color=t["accent"],text_color="#050505");self._owner_snapshot_button.pack(side="left",expand=True,fill="x",padx=(0,4))'
if old not in s:
    raise SystemExit('v3.19.9: Owner snapshot button anchor missing')
s=s.replace(old,new,1)

# Structural validation.
for needle in (
    'APP_VERSION = "3.19.9"',
    'threading.Thread(target=worker,name="ZKOwnerSnapshot",daemon=True).start()',
    'def _owner_snapshot_poll(self):',
    'def _owner_backup_done(self,path):',
    'def _owner_backup_failed(self,message):',
    'self._owner_snapshot_button=ctk.CTkButton',
    'CRIANDO SNAPSHOT...',
):
    if needle not in s:
        raise SystemExit('v3.19.9: missing '+needle)
if 'def _owner_backup_now(self):\n        path=self._owner_make_snapshot("manual")' in s:
    raise SystemExit('v3.19.9: blocking manual snapshot implementation still present')
if 'RedrawWindow(' in s:
    raise SystemExit('v3.19.9: unsafe repaint returned')

ast.parse(s)
path.write_text(s,encoding='utf-8')
print('Applied ZKStrap v3.19.9 Owner Lab background snapshot patch')
