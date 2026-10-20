"""ZKStrap 3.20.23: reliable handoff, startup diagnostics, installer preflight."""
from pathlib import Path
import ast
import os

p=Path(os.environ.get("ZK_SOURCE_DIR","."))/"ZKStrap_v3_18_0.py"
s=p.read_text(encoding="utf-8")

def replace_method(source,name,body):
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="ModernConfigApp")
    method=next((n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name),None)
    if method is None:raise RuntimeError("missing method "+name)
    lines=source.splitlines(True)
    start=sum(map(len,lines[:method.lineno-1]))
    end=sum(map(len,lines[:method.end_lineno]))
    return source[:start]+body.rstrip()+"\n"+source[end:]

s=replace_method(s,"_update_launch_installer",'''
    def _update_launch_installer(self, package, expected_sha, version):
        """Launch a detached updater; never report success before file replacement."""
        src=self._update_updater_source()
        if not src:
            self._update_download_failed("ZKUpdater.exe não foi encontrado ao lado do ZKStrap.exe.")
            return
        install=os.path.realpath(self._update_install_dir())
        if os.name=="nt":
            temp_root=os.path.normcase(os.path.realpath(tempfile.gettempdir()))
            target=os.path.normcase(install)
            if target==temp_root or target.startswith(temp_root+os.sep):
                self._update_download_failed("ZKStrap aberto de pasta temporária/ZIP. Extraia o aplicativo para uma pasta permanente e execute o ZKStrap.exe de lá.")
                messagebox.showwarning("ZKStrap Update Center",
                    "Você abriu o ZKStrap de uma pasta temporária, possivelmente dentro de um ZIP.\\n\\n"
                    "Extraia todos os arquivos para uma pasta permanente e inicie o ZKStrap.exe dessa pasta para que a atualização seja mantida.")
                return
        if not os.path.isfile(package):
            self._update_download_failed("Pacote de atualização não encontrado.")
            return
        if not messagebox.askyesno("ZKStrap Update Center",
                f"Atualização v{version} verificada.\\n\\n"
                f"Instalação atual:\\n{install}\\n\\n"
                "O aplicativo será fechado, a versão anterior será salva em backup e o ZKUpdater fará a substituição. Continuar?"):
            try:self.btn_update_install.configure(state="normal")
            except Exception:pass
            return
        try:
            working=tempfile.mkdtemp(prefix="ZKStrapUpdater_")
            ext=".exe" if src.lower().endswith(".exe") else ".py"
            updater=os.path.join(working,"ZKUpdater"+ext)
            shutil.copy2(src,updater)
            backup=os.path.join(self._update_base_dir(),"backups")
            exe_name=os.path.basename(sys.executable) if getattr(sys,"frozen",False) else "ZKStrap.exe"
            args=[updater,"--apply",os.path.realpath(package),
                  "--sha256",expected_sha,"--install-dir",install,
                  "--backup-dir",backup,"--wait-pid",str(os.getpid()),
                  "--relaunch",exe_name,"--from-version",APP_VERSION,
                  "--to-version",version]
            if ext==".py":
                args=[sys.executable]+args
            process=subprocess.Popen(args,cwd=working,close_fds=True)
            if process.poll() not in (None,):
                raise RuntimeError(f"O atualizador encerrou imediatamente (código {process.returncode}).")
            try:
                self._update_set_status("● INSTALANDO APÓS FECHAR O ZKSTRAP…")
                self.update_progress_label.configure(text="Aguardando o ZKUpdater concluir. A versão instalada será conferida na próxima abertura.")
            except Exception:pass
            self._owner_skip_shutdown_save=False
            self.after(350,self._shutdown_app)
        except Exception as exc:
            self._update_download_failed(f"Não foi possível iniciar ZKUpdater: {exc}")
''')

# Add a self-contained diagnostics method right before _update_latest_backup.
anchor="    def _update_latest_backup(self):"
if s.count(anchor)!=1:raise RuntimeError("startup diagnostics insertion point missing")
diagnostics='''    def _update_startup_health_check(self):
        """Surface updater failures and warn when another old EXE is launched."""
        if bool(getattr(self,"_update_health_reported",False)):
            return
        self._update_health_reported=True
        try:
            base=self._update_base_dir()
            failed=os.path.join(base,"last_error.txt")
            if os.path.isfile(failed):
                with open(failed,encoding="utf-8") as f:
                    msg=f.read().strip()
                try: os.remove(failed)
                except Exception: pass
                if msg:
                    self.after(100,lambda m=msg:messagebox.showerror(
                        "ZKStrap — atualização não instalada",
                        "O ZKUpdater encontrou um erro e a versão anterior foi mantida.\\n\\n"+
                        m[:700]+"\\n\\nDetalhes em %LOCALAPPDATA%\\\\ZKSTRAP\\\\updates\\\\updater.log"))
                return
            state_file=os.path.join(base,"last_update.json")
            if not os.path.isfile(state_file):
                return
            with open(state_file,encoding="utf-8") as f:
                state=json.load(f)
            expected=str(state.get("installed_version","") or "")
            if not expected or self._update_version_tuple(expected)<=self._update_version_tuple(APP_VERSION):
                return
            target=str(state.get("install_dir","") or "")
            current=os.path.normcase(os.path.realpath(self._update_install_dir()))
            if target and os.path.normcase(os.path.realpath(target))!=current:
                msg=(f"A atualização v{expected} foi instalada em outra pasta:\\n\\n"
                     f"{target}\\n\\n"
                     f"Você está abrindo a cópia antiga v{APP_VERSION}. Abra o ZKStrap.exe na pasta acima.")
            else:
                msg=(f"Há registro de instalação da v{expected}, mas esta cópia ainda está na v{APP_VERSION}.\\n"
                     "Verifique se o executável atualizado está em outra pasta.")
            self.after(100,lambda m=msg:messagebox.showwarning("ZKStrap — outra cópia detectada",m))
        except Exception as exc:
            try:self.log_output(f"[!] Update health check: {exc}")
            except Exception:pass

'''
s=s.replace(anchor,diagnostics+anchor,1)
trigger='        if getattr(self, "update_auto_check", True):'
if s.count(trigger)!=1:raise RuntimeError("init startup anchor not unique")
s=s.replace(trigger,'        self.after(2200, self._update_startup_health_check)\n'+trigger,1)
old='APP_VERSION = "3.20.22"'
if s.count(old)!=1:raise RuntimeError("version anchor missing")
s=s.replace(old,'APP_VERSION = "3.20.23"',1)
ast.parse(s)
compile(s,str(p),"exec")
p.write_text(s,encoding="utf-8")
print("ZKStrap v3.20.23 runtime diagnostic + updater fix OK")
