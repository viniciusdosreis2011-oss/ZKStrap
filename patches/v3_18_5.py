from pathlib import Path
import os
import re

root = Path(os.environ.get("ZK_SOURCE_DIR", "."))
path = root / "ZKStrap_v3_18_0.py"
s = path.read_text(encoding="utf-8")


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f"v3.18.5 patch: pattern not found: {label}")
    s = s.replace(old, new, 1)


# Version / public endpoints. The report endpoint itself is intentionally NOT shipped here.
rep('APP_VERSION = "3.18.4"', 'APP_VERSION = "3.18.5"', 'version')
rep('BUILD_TIMESTAMP = "Support Hub + GitHub Pages"', 'BUILD_TIMESTAMP = "Launch Polish + Safe Reports"', 'build timestamp')
rep(
    'SUPPORT_PAGE_URL = "https://viniciusdosreis2011-oss.github.io/ZKStrap/"\n',
    'SUPPORT_PAGE_URL = "https://viniciusdosreis2011-oss.github.io/ZKStrap/"\n'
    'FEEDBACK_CONFIG_URL = "https://viniciusdosreis2011-oss.github.io/ZKStrap/feedback.json"\n'
    'PUBLIC_YOUTUBE_URL = "https://www.youtube.com/@zkvez"\n'
    'PUBLIC_GITHUB_URL = "https://github.com/viniciusdosreis2011-oss/ZKStrap"\n'
    'PUBLIC_DISCORD_URL = ""  # preencher só quando houver um convite público oficial\n'
    '_SAFE_START_ACTIVE = False\n',
    'public urls'
)

# Safe-start state. It only resets UI/runtime preferences after repeated failed boots;
# combos, profile, creator data and Roblox flags are preserved.
insert_before = 'AUDIO_PACKS = {\n'
safe_code = r'''
def _safe_start_state_path():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "ZKSTRAP", "startup_state.json")


def _safe_start_write(data):
    try:
        path = _safe_start_state_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass


def _safe_start_prepare_config():
    try:
        cfg_path = _boot_config_path()
        if not os.path.isfile(cfg_path):
            return
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict):
            return
        backup = cfg_path + ".safe-start-backup"
        try:
            if not os.path.exists(backup):
                shutil.copy2(cfg_path, backup)
        except Exception:
            pass
        # UI-only recovery: do not touch modules, linked profile, combos or creator data.
        cfg["theme"] = "ZKStrap Core"
        cfg["compact_mode"] = False
        cfg["current_page"] = "home"
        cfg["sounds_enabled"] = False
        cfg["music_enabled"] = False
        cfg["update_auto_check"] = False
        cfg["theme_overrides"] = {}
        tmp = cfg_path + ".safe.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(tmp, cfg_path)
        _startup_log("SAFE START: UI preferences recovered after repeated boot failures")
    except Exception as exc:
        _startup_log("SAFE START: recovery failed " + repr(exc))


def _safe_start_begin():
    global _SAFE_START_ACTIVE
    failures = 0
    try:
        path = _safe_start_state_path()
        old = {}
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                old = json.load(f)
            if not isinstance(old, dict):
                old = {}
        failures = int(old.get("failures", 0) or 0)
        if bool(old.get("boot_pending", False)):
            failures += 1
    except Exception:
        failures = 0
    _SAFE_START_ACTIVE = failures >= 2
    if _SAFE_START_ACTIVE:
        _safe_start_prepare_config()
    _safe_start_write({"boot_pending": True, "failures": failures, "started_at": time.time(), "safe_start": _SAFE_START_ACTIVE})
    return _SAFE_START_ACTIVE


def _safe_start_mark_boot_ok():
    _safe_start_write({"boot_pending": False, "failures": 0, "boot_ok_at": time.time(), "safe_start": bool(_SAFE_START_ACTIVE)})


def _safe_start_mark_clean():
    _safe_start_write({"boot_pending": False, "failures": 0, "clean_shutdown_at": time.time(), "safe_start": False})


def _enable_windows_dpi_awareness():
    if os.name != "nt":
        return
    try:
        # PER_MONITOR_AWARE_V2. CustomTkinter still handles widget scaling;
        # this prevents Windows from bitmap-stretching the whole window on 125/150%.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


'''
if insert_before not in s:
    raise SystemExit('v3.18.5 patch: AUDIO_PACKS anchor missing')
s = s.replace(insert_before, safe_code + insert_before, 1)

# Adaptive first window size for 100/125/150% display scaling.
rep(
    '        self.title(f"ZKStrap v{APP_VERSION}")\n'
    '        self.geometry("1440x860")\n'
    '        self.minsize(1040, 680)\n'
    '        self.resizable(True, True)\n',
    '        self.title(f"ZKStrap v{APP_VERSION}")\n'
    '        try:\n'
    '            sw, sh = int(self.winfo_screenwidth()), int(self.winfo_screenheight())\n'
    '            target_w = min(1440, max(900, sw - 70))\n'
    '            target_h = min(860, max(590, sh - 90))\n'
    '            min_w = min(1040, max(840, sw - 180))\n'
    '            min_h = min(680, max(540, sh - 180))\n'
    '            x = max(0, (sw - target_w) // 2); y = max(0, (sh - target_h) // 2)\n'
    '            self.geometry(f"{target_w}x{target_h}+{x}+{y}")\n'
    '            self.minsize(min_w, min_h)\n'
    '        except Exception:\n'
    '            self.geometry("1280x760"); self.minsize(900, 580)\n'
    '        self.resizable(True, True)\n',
    'adaptive window geometry'
)

# Update center gets a network/offline indicator.
rep(
    '        self.update_info_label.pack(fill="x",padx=16,pady=(2,8))\n',
    '        self.update_info_label.pack(fill="x",padx=16,pady=(2,4))\n'
    '        self.network_status_label=ctk.CTkLabel(hero_up,text="REDE: verificando…" if pt else "NETWORK: checking…",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w")\n'
    '        self.network_status_label.pack(fill="x",padx=16,pady=(0,8))\n',
    'network status label'
)

# Bug reports always attach diagnostics for bug-type reports; no bulky diagnostic text is shown while typing.
old_diag = '        self.switch_feedback_diag=ctk.CTkSwitch(form,text="INCLUIR DIAGNÓSTICO DO APP" if pt else "INCLUDE APP DIAGNOSTICS",progress_color=t["accent"],fg_color="#44484F",text_color=t["text"]); self.switch_feedback_diag.pack(anchor="w",padx=16,pady=(2,6)); self.switch_feedback_diag.select()\n'
new_diag = '        self.switch_feedback_diag=None\n        ctk.CTkLabel(form,text="Ao reportar um bug, o diagnóstico técnico do app é anexado automaticamente." if pt else "When reporting a bug, app diagnostics are attached automatically.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w",justify="left").pack(fill="x",padx=16,pady=(2,6))\n'
rep(old_diag, new_diag, 'feedback automatic diagnostics UI')

# Support hub is intentionally an "em breve" state until a payment provider is configured.
rep(
    '            "Uma forma opcional de fortalecer o projeto sem colocar dados de pagamento dentro do app." if pt else "An optional way to support the project without storing payment data inside the app."\n',
    '            "O apoio financeiro será ativado em breve. O ZKStrap continua gratuito." if pt else "Financial support is coming soon. ZKStrap remains free."\n',
    'support subtitle'
)
rep(
    '            "O ZKStrap continua gratuito. Se ele te ajuda e você quiser apoiar, a contribuição é totalmente opcional." if pt else "ZKStrap stays free. If it helps you and you want to support it, contributions are completely optional."\n',
    '            "A estrutura já está pronta, mas o recebimento ainda não foi ativado. Quando chegar, apoiar continuará sendo totalmente opcional." if pt else "The structure is ready, but payments are not enabled yet. Supporting will remain completely optional when it launches."\n',
    'support hero text'
)
rep(
    '                "O pagamento acontece em uma página externa. O ZKStrap não pede, recebe ou armazena senha bancária, cartão, CPF, chave Pix ou credenciais de pagamento."\n'
    '                if pt else\n'
    '                "Payment happens on an external page. ZKStrap does not request, receive or store bank passwords, card data, tax IDs, Pix keys or payment credentials."\n',
    '                "STATUS: EM BREVE  •  nenhuma forma de pagamento está ativa nesta versão."\n'
    '                if pt else\n'
    '                "STATUS: COMING SOON  •  no payment method is active in this version."\n',
    'support status text'
)
rep(
    '            text="ABRIR PÁGINA DE APOIO" if pt else "OPEN SUPPORT PAGE",\n'
    '            command=self._open_support_page,\n'
    '            fg_color="#1ED760",\n',
    '            text="APOIO FINANCEIRO — EM BREVE" if pt else "FINANCIAL SUPPORT — COMING SOON",\n'
    '            command=lambda: None,\n'
    '            state="disabled",\n'
    '            fg_color="#1ED760",\n',
    'support disabled payment button'
)
rep(
    '            text="COPIAR LINK" if pt else "COPY LINK",\n'
    '            command=self._copy_support_link,\n',
    '            text="ABRIR PÁGINA" if pt else "OPEN PAGE",\n'
    '            command=self._open_support_page,\n',
    'support info button'
)

# Add official links/tools to About. Discord is only rendered once a public invite is explicitly configured.
about_anchor = '        self.yt_link.bind("<Button-1>",lambda e:webbrowser.open("https://www.youtube.com/@zkvez"))\n'
about_insert = about_anchor + r'''        links=self._section_card(body,"LINKS & SUPORTE" if pt else "LINKS & SUPPORT","Atalhos oficiais do projeto e suporte." if pt else "Official project and support shortcuts.")
        lr=ctk.CTkFrame(links,fg_color="transparent"); lr.pack(fill="x",padx=14,pady=(5,6))
        ctk.CTkButton(lr,text="YOUTUBE",command=lambda:webbrowser.open(PUBLIC_YOUTUBE_URL),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(lr,text="GITHUB",command=lambda:webbrowser.open(PUBLIC_GITHUB_URL),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",expand=True,fill="x",padx=4)
        if PUBLIC_DISCORD_URL:
            ctk.CTkButton(lr,text="DISCORD",command=lambda:webbrowser.open(PUBLIC_DISCORD_URL),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",expand=True,fill="x",padx=(4,0))
        lr2=ctk.CTkFrame(links,fg_color="transparent"); lr2.pack(fill="x",padx=14,pady=(0,14))
        ctk.CTkButton(lr2,text="REPORTAR BUG" if pt else "REPORT BUG",command=lambda:self.show_page("feedback"),fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=38).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(lr2,text="VERIFICAR ATUALIZAÇÃO" if pt else "CHECK UPDATE",command=lambda:(self.show_page("updates"),self.after(120,lambda:self._update_check_async(silent=False))),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",expand=True,fill="x",padx=(4,0))
'''
rep(about_anchor, about_insert, 'about links')

# Trigger the network probe after the pages exist.
rep(
    '        try: self.aplicar_fonte_widgets(self)\n        except Exception: pass\n\n    # ------------------------------------------------------------------\n',
    '        try: self.aplicar_fonte_widgets(self)\n        except Exception: pass\n        try: self.after(350,self._network_probe_async)\n        except Exception: pass\n\n    # ------------------------------------------------------------------\n',
    'network probe schedule'
)

# Replace legacy direct-Discord submission with proxy-ready, threaded, sanitized reporting.
pattern = re.compile(r'    def enviar_sugestao\(self\):\n.*?\n    def _snapshot_sistema\(self\):\n', re.S)
match = pattern.search(s)
if not match:
    raise SystemExit('v3.18.5 patch: enviar_sugestao block not found')
replacement = r'''    def _sanitize_diag_text(self, value):
        text=str(value or "")
        try:
            user=os.environ.get("USERNAME","")
            profile=os.environ.get("USERPROFILE","")
            local=os.environ.get("LOCALAPPDATA","")
            if profile: text=text.replace(profile,"%USERPROFILE%")
            if local: text=text.replace(local,"%LOCALAPPDATA%")
            if user and len(user)>2: text=re.sub(re.escape(user),"<user>",text,flags=re.I)
            text=re.sub(r"https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/[^\s]+","[webhook-redacted]",text,flags=re.I)
            text=re.sub(r"(?i)(authorization|cookie|token|password|senha)\s*[:=]\s*[^\s,;]+",r"\1=[redacted]",text)
        except Exception:
            pass
        return text[:1200]

    def _collect_bug_diagnostics(self):
        snap=self._snapshot_sistema()
        try:
            if os.name=="nt":
                wv=sys.getwindowsversion(); win=f"Windows {wv.major}.{wv.minor} build {wv.build}"
            else:
                win=sys.platform
        except Exception:
            win=sys.platform
        try: scaling=round(float(self.tk.call("tk","scaling")),2)
        except Exception: scaling=0.0
        try: screen=f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}"
        except Exception: screen="unknown"
        roblox_folder=os.path.basename(str(getattr(self,"pasta_roblox_salva","") or ""))
        current=getattr(self,"_spotify_current",{}) if isinstance(getattr(self,"_spotify_current",{}),dict) else {}
        diag={
            "app_version":APP_VERSION,
            "build":BUILD_TIMESTAMP,
            "os":win,
            "theme":str(getattr(self,"tema_atual","")),
            "page":str(getattr(self,"current_page_key","")),
            "update_channel":str(getattr(self,"update_channel","stable")),
            "roblox_running":bool(snap.get("roblox_count",0)),
            "roblox_version_folder":roblox_folder,
            "cpu_percent":round(float(snap.get("cpu",0.0)),1),
            "ram_percent":round(float(snap.get("ram_pct",0.0)),1),
            "screen":screen,
            "tk_scaling":scaling,
            "spotify_detected":bool(current),
            "safe_start":bool(_SAFE_START_ACTIVE),
        }
        logs=[]
        for line in list(getattr(self,"_log_history",[]))[-14:]:
            clean=self._sanitize_diag_text(line)
            if clean: logs.append(clean)
        return diag,logs

    def _feedback_endpoint(self):
        try:
            r=requests.get(FEEDBACK_CONFIG_URL,timeout=4,headers={"User-Agent":f"ZKStrap/{APP_VERSION}"})
            if not r.ok: return ""
            cfg=r.json()
            if not isinstance(cfg,dict) or not bool(cfg.get("enabled",False)): return ""
            endpoint=str(cfg.get("endpoint","") or "").strip()
            # The client only accepts an HTTPS proxy. A raw Discord webhook is explicitly rejected.
            if not endpoint.startswith("https://"): return ""
            if "discord.com/api/webhooks" in endpoint.lower() or "discordapp.com/api/webhooks" in endpoint.lower(): return ""
            return endpoint
        except Exception:
            return ""

    def _copy_feedback_fallback(self,payload):
        try:
            diag=payload.get("diagnostics") or {}
            lines=[f"[{payload.get('type','Feedback')}] {payload.get('title','')}",str(payload.get("message","")).strip()]
            if diag:
                lines.append("")
                lines.append("--- diagnóstico técnico ---")
                for k,v in diag.items(): lines.append(f"{k}: {v}")
            self.clipboard_clear(); self.clipboard_append("\n".join(lines).strip()); self.update_idletasks()
            return True
        except Exception:
            return False

    def _network_probe_async(self):
        if bool(getattr(self,"_network_probe_busy",False)): return
        self._network_probe_busy=True
        def worker():
            online=False
            try:
                r=requests.get(UPDATE_MANIFEST_URLS.get("stable"),timeout=3,headers={"User-Agent":f"ZKStrap/{APP_VERSION}"})
                online=bool(r.ok)
            except Exception:
                online=False
            def finish():
                self._network_probe_busy=False; self._network_online=online
                lbl=getattr(self,"network_status_label",None)
                if lbl is not None:
                    try:
                        t=TEMAS[self.tema_atual]
                        if online:
                            lbl.configure(text="REDE: ONLINE  •  serviços online disponíveis" if self.idioma=="pt" else "NETWORK: ONLINE  •  online services available",text_color=t["accent"])
                        else:
                            lbl.configure(text="MODO OFFLINE  •  ferramentas locais continuam funcionando" if self.idioma=="pt" else "OFFLINE MODE  •  local tools keep working",text_color="#D79A36")
                    except Exception: pass
            try:self.after(0,finish)
            except Exception:pass
        threading.Thread(target=worker,daemon=True).start()

    def enviar_sugestao(self):
        msg=self.txt_sug.get("0.0","end").strip()
        try: title=self.entry_sug_title.get().strip()
        except Exception: title=""
        if len(msg)<5:
            messagebox.showwarning(self.tr[self.idioma]['msg_warning'],self.tr[self.idioma]['short_message_warning']); return
        tipo=getattr(self,"sug_tipo",self.tr[self.idioma]['sug_type_vals'][0])
        is_bug="bug" in str(tipo).lower()
        diag,logs=({},[])
        if is_bug:
            try: diag,logs=self._collect_bug_diagnostics()
            except Exception: diag,logs=({},[])
        payload={
            "source":"zkstrap-client",
            "type":str(tipo),
            "title":self._sanitize_diag_text(title)[:140],
            "message":str(msg)[:3500],
            "app_version":APP_VERSION,
            "diagnostics":diag,
            "recent_logs":logs,
        }
        try:self.btn_enviar_sug.configure(state="disabled",text="ENVIANDO…" if self.idioma=="pt" else "SENDING…")
        except Exception:pass
        def worker():
            sent=False; copied=False; reason=""
            endpoint=self._feedback_endpoint()
            if endpoint:
                try:
                    r=requests.post(endpoint,json=payload,timeout=8,headers={"User-Agent":f"ZKStrap/{APP_VERSION}"})
                    sent=r.status_code in (200,201,202,204)
                    if not sent: reason=f"HTTP {r.status_code}"
                except Exception as exc:
                    reason=self._sanitize_diag_text(exc)
            else:
                reason="endpoint indisponível"
            if not sent:
                copied=self._copy_feedback_fallback(payload)
            def finish():
                try:self.btn_enviar_sug.configure(state="normal",text="ENVIAR FEEDBACK" if self.idioma=="pt" else "SEND FEEDBACK")
                except Exception:pass
                if sent:
                    try:self.show_toast("FEEDBACK ENVIADO" if self.idioma=="pt" else "FEEDBACK SENT","Relatório recebido pela central de suporte." if self.idioma=="pt" else "Report received by the support service.",kind="success",duration=3000)
                    except Exception:self._legacy_info("ZKStrap","Feedback enviado.")
                    try:self.txt_sug.delete("0.0","end"); self.entry_sug_title.delete(0,"end"); self._update_sug_counter()
                    except Exception:pass
                    self.log_output(f"[*] {tipo} enviado pelo endpoint seguro.")
                else:
                    msg2=("Sem conexão/endpoint de suporte. O relatório foi copiado para a área de transferência." if copied else "Sem conexão/endpoint de suporte. O relatório não pôde ser enviado.")
                    try:self.show_toast("MODO OFFLINE",msg2,kind="warning",duration=4200)
                    except Exception:messagebox.showwarning("ZKStrap",msg2)
                    self.log_output(f"[!] Feedback não enviado: {reason}")
                    self._network_probe_async()
            try:self.after(0,finish)
            except Exception:pass
        threading.Thread(target=worker,daemon=True).start()

    def _snapshot_sistema(self):
'''
s = s[:match.start()] + replacement + s[match.end():]

# Clean shutdown clears boot-failure state.
rep(
    '        try: self.quit()\n        except Exception: pass\n',
    '        try: _safe_start_mark_clean()\n        except Exception: pass\n        try: self.quit()\n        except Exception: pass\n',
    'safe-start clean shutdown'
)

# Activate DPI + boot guard before any root window/splash is created.
rep(
    'if __name__ == "__main__":\n    if "--zk-audio-helper" in sys.argv:\n',
    'if __name__ == "__main__":\n    _enable_windows_dpi_awareness()\n    if "--zk-audio-helper" in sys.argv:\n',
    'dpi awareness main'
)
rep(
    '    _splash_handle = _launch_detached_splash()\n',
    '    _safe_start_active = _safe_start_begin()\n    _splash_handle = _launch_detached_splash()\n',
    'safe-start begin'
)

# Mark boot healthy only once we are about to enter the normal event loop.
if '        app.mainloop()\n' not in s:
    raise SystemExit('v3.18.5 patch: app.mainloop anchor missing')
s=s.replace(
    '        app.mainloop()\n',
    '        try:\n            _safe_start_mark_boot_ok()\n            if _safe_start_active:\n                app.log_output("[SAFE START] Inicialização recuperada com preferências visuais seguras.")\n                app.after(900,lambda:app.show_toast("SAFE START","O ZKStrap recuperou preferências visuais após falhas de inicialização.",kind="warning",duration=5200))\n        except Exception: pass\n        app.mainloop()\n',
    1
)

# Ensure the legacy Discord webhook no longer exists anywhere in the public source.
if re.search(r'https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/', s, re.I):
    raise SystemExit('v3.18.5 patch: a Discord webhook URL is still embedded in source')

path.write_text(s,encoding="utf-8")
print("v3.18.5 launch polish patch applied", path, len(s))
