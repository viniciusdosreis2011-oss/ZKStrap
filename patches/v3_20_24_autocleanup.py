"""ZKStrap v3.20.24 automatic update storage cleanup."""
from pathlib import Path
import ast,os
src=Path(os.environ.get("ZK_SOURCE_DIR","."))/"ZKStrap_v3_18_0.py"
s=src.read_text(encoding="utf-8")
anchor="    def _update_latest_backup(self):"
if s.count(anchor)!=1:raise RuntimeError("cleanup insertion point missing")

method=r'''    def _update_autocleanup_storage(self):
        """Remove obsolete updater ZIPs while preserving the newest rollback.

        Does not touch Roblox caches or separate ZKSTRAP_OWNER backups.
        """
        if bool(getattr(self,"_update_download_busy",False)):
            return
        try:
            import re
            import zipfile
            import time
            root=os.path.realpath(self._update_base_dir())
            install=os.path.realpath(self._update_install_dir())
            version_file=os.path.join(install,"ZKStrap-version.txt")
            if not os.path.isfile(version_file):
                return
            with open(version_file,encoding="utf-8-sig") as f:
                if f.read().strip()!=APP_VERSION:
                    return
            backup_dir=os.path.join(root,"backups")
            download_dir=os.path.join(root,"downloads")
            backups_re=re.compile(r"^20[0-9]{6}_[0-9]{6}_v[A-Za-z0-9._-]+\.zip$",re.I)
            downloads_re=re.compile(r"^ZKStrap-v([0-9]+\.[0-9]+\.[0-9]+)\.zip$",re.I)
            def safe(folder,name):
                p=os.path.join(folder,name)
                return (os.path.isfile(p) and not os.path.islink(p)
                        and os.path.dirname(os.path.realpath(p))==os.path.realpath(folder))
            def vt(value):
                try:return tuple(map(int,value.split(".")[:3]))
                except (ValueError,TypeError):return (0,0,0)
            protected=set()
            state_file=os.path.join(root,"last_update.json")
            if os.path.isfile(state_file):
                try:
                    with open(state_file,encoding="utf-8") as f:
                        state=json.load(f)
                    backup=str(state.get("backup","") or "")
                    if backup and os.path.realpath(os.path.dirname(backup))==os.path.realpath(backup_dir):
                        protected.add(os.path.realpath(backup))
                except (OSError,ValueError,TypeError):
                    pass
            removed=0
            bytes_saved=0
            if os.path.isdir(backup_dir) and not os.path.islink(backup_dir):
                archives=[]
                for item in os.scandir(backup_dir):
                    if backups_re.fullmatch(item.name) and safe(backup_dir,item.name):
                        archives.append(item.path)
                archives.sort(key=lambda p:(os.path.getmtime(p),os.path.basename(p)),reverse=True)
                valid=False
                if archives:
                    try:
                        with zipfile.ZipFile(archives[0]) as z:
                            valid="ZKStrap.exe" in z.namelist() and z.testzip() is None
                    except (OSError,zipfile.BadZipFile,RuntimeError):
                        valid=False
                if valid:
                    protected.add(os.path.realpath(archives[0]))
                    for path in archives[1:]:
                        if os.path.realpath(path) in protected:
                            continue
                        try:
                            size=os.path.getsize(path)
                            os.remove(path);removed+=1;bytes_saved+=size
                        except OSError:
                            pass
            if os.path.isdir(download_dir) and not os.path.islink(download_dir):
                for item in os.scandir(download_dir):
                    match=downloads_re.fullmatch(item.name)
                    if not match or not safe(download_dir,item.name):
                        continue
                    if vt(match.group(1))>vt(APP_VERSION):
                        continue
                    try:
                        # Never delete a new download or active transfer.
                        if time.time()-item.stat().st_mtime<900:
                            continue
                        size=item.stat().st_size
                        os.remove(item.path);removed+=1;bytes_saved+=size
                    except OSError:
                        pass
            if removed:
                with open(os.path.join(root,"updater.log"),"a",encoding="utf-8") as log:
                    log.write(f"[ZKStrap v{APP_VERSION}] auto-cleanup: {removed} archives, {bytes_saved} bytes freed; latest rollback kept\\n")
        except Exception:
            # Cache cleanup is best-effort: never block ZKStrap startup.
            return

'''
s=s.replace(anchor,method+anchor,1)
trigger='        self.after(2200, self._update_startup_health_check)'
if s.count(trigger)!=1:raise RuntimeError("startup anchor missing")
s=s.replace(trigger,trigger+'\n        self.after(10500, lambda: threading.Thread(target=self._update_autocleanup_storage, daemon=True).start())',1)
if s.count('APP_VERSION = "3.20.23"')!=1:raise RuntimeError("incorrect base version")
s=s.replace('APP_VERSION = "3.20.23"','APP_VERSION = "3.20.24"',1)
ast.parse(s);compile(s,str(src),"exec")
src.write_text(s,encoding="utf-8")
print("v3.20.24 autostorage cleanup installed")
