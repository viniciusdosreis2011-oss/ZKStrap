#!/usr/bin/env python3
import argparse, hashlib, os, shutil, sys, time, zipfile, tempfile, json, traceback
from pathlib import Path
from datetime import datetime

UPDATER_VERSION = "1.1.0"

def local_data_dir():
    base=os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    p=os.path.join(base,"ZKSTRAP","updates")
    os.makedirs(p,exist_ok=True)
    return p

def log(msg):
    try:
        path=os.path.join(local_data_dir(),"updater.log")
        with open(path,"a",encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n")
    except Exception:
        pass

def notify(title, message, error=False):
    """Make updater status visible even when compiled with --windowed."""
    log(f"{title}: {message}")
    if os.name == "nt":
        try:
            import ctypes
            flags = 0x00000010 if error else 0x00000040
            ctypes.windll.user32.MessageBoxW(None,str(message),str(title),flags)
            return
        except Exception:
            pass
    print(f"{title}: {message}",file=sys.stderr if error else sys.stdout)

def ephemeral_install(path):
    """Do not install into WinRAR/7-Zip/Windows temporary extraction folders."""
    if os.name != "nt":
        return False
    target=os.path.normcase(os.path.realpath(path)).rstrip("\\\\/")
    tmp=os.path.normcase(os.path.realpath(tempfile.gettempdir())).rstrip("\\\\/")
    if target == tmp or target.startswith(tmp+os.sep):
        return True
    name=os.path.basename(target).lower()
    return name.startswith(("rar$","7zo","temp_","zkstrapupdater_"))

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest().lower()

def pid_alive(pid):
    try:
        pid=int(pid)
        if pid<=0:return False
        if os.name=="nt":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION=0x1000
            STILL_ACTIVE=259
            handle=ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,False,pid)
            if not handle:return False
            try:
                code=ctypes.c_ulong()
                ok=ctypes.windll.kernel32.GetExitCodeProcess(handle,ctypes.byref(code))
                return bool(ok and code.value==STILL_ACTIVE)
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        os.kill(pid,0);return True
    except Exception:return False

def wait_for_pid(pid, timeout=45):
    end=time.time()+timeout
    while time.time()<end:
        if not pid_alive(pid): return True
        time.sleep(.25)
    return not pid_alive(pid)

def safe_extract(zip_path,dest):
    root=os.path.realpath(dest)
    with zipfile.ZipFile(zip_path,"r") as z:
        for info in z.infolist():
            target=os.path.realpath(os.path.join(dest,info.filename))
            if target!=root and not target.startswith(root+os.sep):
                raise RuntimeError("Pacote contém caminho inseguro")
        z.extractall(dest)

def zip_dir(source, out_zip):
    os.makedirs(os.path.dirname(out_zip),exist_ok=True)
    with zipfile.ZipFile(out_zip,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for root,dirs,files in os.walk(source):
            dirs[:] = [d for d in dirs if d not in {"__pycache__"}]
            for fn in files:
                full=os.path.join(root,fn)
                arc=os.path.relpath(full,source)
                try:z.write(full,arc)
                except PermissionError as exc:raise RuntimeError(f"Não foi possível criar backup de {full}: {exc}")

def latest_backup_name(from_version="unknown"):
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    safe="".join(c for c in str(from_version) if c.isalnum() or c in ".-_") or "unknown"
    return f"{stamp}_v{safe}.zip"

def clear_install_dir(install_dir):
    for name in os.listdir(install_dir):
        p=os.path.join(install_dir,name)
        try:
            if os.path.isdir(p) and not os.path.islink(p): shutil.rmtree(p)
            else: os.remove(p)
        except FileNotFoundError: pass

def copy_tree_contents(src,dst):
    os.makedirs(dst,exist_ok=True)
    for name in os.listdir(src):
        s=os.path.join(src,name); d=os.path.join(dst,name)
        if os.path.isdir(s) and not os.path.islink(s): shutil.copytree(s,d,dirs_exist_ok=True)
        else: shutil.copy2(s,d)

def relaunch(install_dir, exe_name):
    if not exe_name:return
    path=os.path.join(install_dir,exe_name)
    if os.path.isfile(path):
        import subprocess
        subprocess.Popen([path],cwd=install_dir,close_fds=True)

def apply_update(args):
    pkg=os.path.abspath(args.apply); install=os.path.abspath(args.install_dir); backups=os.path.abspath(args.backup_dir)
    if ephemeral_install(install):
        raise RuntimeError("ZKStrap aberto de pasta temporária/ZIP. Extraia o ZIP em uma pasta permanente e abra o ZKStrap.exe de lá antes de atualizar.")
    os.makedirs(install,exist_ok=True); os.makedirs(backups,exist_ok=True)
    log(f"apply requested {args.from_version} -> {args.to_version}; package={pkg}")
    if args.sha256 and sha256_file(pkg)!=args.sha256.lower(): raise RuntimeError("SHA-256 do pacote não confere")
    if not wait_for_pid(args.wait_pid): raise RuntimeError("ZKStrap não encerrou a tempo")
    backup=os.path.join(backups,latest_backup_name(args.from_version))
    zip_dir(install,backup); log(f"backup created: {backup}")
    stage=tempfile.mkdtemp(prefix="zkstrap_update_")
    try:
        safe_extract(pkg,stage)
        if not os.path.isfile(os.path.join(stage,"ZKStrap.exe")) or not os.path.isfile(os.path.join(stage,"ZKUpdater.exe")):
            raise RuntimeError("Pacote inválido: ZKStrap.exe ou ZKUpdater.exe não está na raiz")
        version_file=os.path.join(stage,"ZKStrap-version.txt")
        if os.path.isfile(version_file):
            with open(version_file,encoding="utf-8-sig") as f:
                packaged=f.read().strip()
            if args.to_version!="unknown" and packaged!=args.to_version:
                raise RuntimeError(f"Pacote v{packaged} não corresponde à versão esperada v{args.to_version}")
        try:
            clear_install_dir(install); copy_tree_contents(stage,install)
        except Exception:
            log("install failed; attempting automatic rollback")
            restore=tempfile.mkdtemp(prefix="zkstrap_rollback_")
            try:
                safe_extract(backup,restore); clear_install_dir(install); copy_tree_contents(restore,install)
            finally: shutil.rmtree(restore,ignore_errors=True)
            raise
        if not os.path.isfile(os.path.join(install,"ZKStrap.exe")):
            raise RuntimeError("ZKStrap.exe ausente após instalação")
        state={"installed_version":args.to_version,"previous_version":args.from_version,"backup":backup,"installed_at":datetime.now().isoformat(timespec="seconds"),"install_dir":install}
        with open(os.path.join(local_data_dir(),"last_update.json"),"w",encoding="utf-8") as f: json.dump(state,f,indent=2,ensure_ascii=False)
        try:
            os.remove(os.path.join(local_data_dir(),"last_error.txt"))
        except FileNotFoundError:
            pass
        log(f"update installed successfully in {install}")
    finally:
        shutil.rmtree(stage,ignore_errors=True)
    relaunch(install,args.relaunch)

def restore_backup(args):
    backup=os.path.abspath(args.restore); install=os.path.abspath(args.install_dir)
    if ephemeral_install(install):
        raise RuntimeError("Instalação em pasta temporária não pode ser restaurada com segurança.")
    if not os.path.isfile(backup): raise RuntimeError("Backup não encontrado")
    if not wait_for_pid(args.wait_pid): raise RuntimeError("ZKStrap não encerrou a tempo")
    # Safety backup of the version being replaced.
    bdir=os.path.join(local_data_dir(),"backups"); os.makedirs(bdir,exist_ok=True)
    safety=os.path.join(bdir,latest_backup_name("before-restore")); zip_dir(install,safety)
    stage=tempfile.mkdtemp(prefix="zkstrap_restore_")
    try:
        safe_extract(backup,stage)
        if not os.path.isfile(os.path.join(stage,"ZKStrap.exe")): raise RuntimeError("Backup inválido")
        clear_install_dir(install); copy_tree_contents(stage,install)
        log(f"restored backup: {backup}")
    finally: shutil.rmtree(stage,ignore_errors=True)
    relaunch(install,args.relaunch)

def main():
    # A standalone double-click is not an update operation.
    if len(sys.argv)==1:
        notify("ZKUpdater 1.1", "Este programa é o instalador auxiliar do ZKStrap.\n\nAbra o ZKStrap, vá em Atualizações e escolha Atualizar Agora.\n\nPara diagnosticar falhas, veja %LOCALAPPDATA%\\ZKSTRAP\\updates\\updater.log.")
        return 0
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply"); g.add_argument("--restore")
    ap.add_argument("--sha256",default=""); ap.add_argument("--install-dir",required=True); ap.add_argument("--backup-dir",default=os.path.join(local_data_dir(),"backups"))
    ap.add_argument("--wait-pid",type=int,default=0); ap.add_argument("--relaunch",default="ZKStrap.exe"); ap.add_argument("--from-version",default="unknown"); ap.add_argument("--to-version",default="unknown")
    args=ap.parse_args()
    try:
        if args.apply: apply_update(args)
        else: restore_backup(args)
        return 0
    except Exception as e:
        log("ERROR: "+str(e)+"\n"+traceback.format_exc())
        notify("Falha na atualização do ZKStrap", str(e)+"\n\nO erro foi salvo em %LOCALAPPDATA%\\ZKSTRAP\\updates\\updater.log",error=True)
        # Write a simple marker so the main app can explain the last failure next start.
        try:
            with open(os.path.join(local_data_dir(),"last_error.txt"),"w",encoding="utf-8") as f:f.write(str(e))
        except Exception:pass
        return 2

if __name__=="__main__":
    raise SystemExit(main())
