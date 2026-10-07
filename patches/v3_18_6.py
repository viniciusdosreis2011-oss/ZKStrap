from pathlib import Path
import os
import re

root = Path(os.environ.get("ZK_SOURCE_DIR", "."))
path = root / "ZKStrap_v3_18_0.py"
s = path.read_text(encoding="utf-8")


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit(f"v3.18.6 patch: pattern not found: {label}")
    s = s.replace(old, new, count)


def regex_rep(pattern, replacement, label, flags=re.S):
    global s
    ns, n = re.subn(pattern, replacement, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"v3.18.6 patch: regex pattern not found/ambiguous: {label} ({n})")
    s = ns


# Version
rep('APP_VERSION = "3.18.5"', 'APP_VERSION = "3.18.6"', 'version')
rep('BUILD_TIMESTAMP = "Launch Polish + Safe Reports"', 'BUILD_TIMESTAMP = "Input Polish + Spotify Volume + Visual Icons"', 'build timestamp')

# Support: Coming Soon should look disabled, not like a neon call-to-action.
rep(
    '            fg_color="#1ED760",\n'
    '            hover_color="#18B953",\n'
    '            text_color="#06150B",\n',
    '            fg_color="#10291C",\n'
    '            hover_color="#10291C",\n'
    '            text_color="#79E9A2",\n'
    '            border_width=1,\n'
    '            border_color="#1E7A48",\n',
    'support coming-soon colors'
)

# One scroll queue for BOTH the page canvas and inner widgets.
scroll_block = r'''    def _mark_fast_scroll(self):
        self._scroll_active_until=time.monotonic()+0.22

    def _queue_scroll_step(self, scrollable, step):
        """Throttle all wheel input through one queue per scrollable page."""
        try:
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None or not step:
                return "break"
            state=getattr(scrollable,"_zk_scroll_state",None)
            if not isinstance(state,dict):
                state={"pending":0,"job":None,"settle":None}
                setattr(scrollable,"_zk_scroll_state",state)

            state["pending"]=max(-10,min(10,int(state.get("pending",0))+int(step)))
            self._mark_fast_scroll()

            def settle():
                state["settle"]=None
                try:
                    if canvas.winfo_exists():
                        canvas.update_idletasks()
                except Exception:
                    pass

            def tick():
                state["job"]=None
                pending=int(state.get("pending",0))
                if not pending:
                    try:
                        if state.get("settle") is not None:self.after_cancel(state["settle"])
                    except Exception:
                        pass
                    try:state["settle"]=self.after(55,settle)
                    except Exception:pass
                    return
                move=1 if pending>0 else -1
                if abs(pending)>=6:
                    move*=2
                state["pending"]=pending-move
                try:
                    if canvas.winfo_exists():
                        canvas.yview_scroll(move,"units")
                except Exception:
                    state["pending"]=0
                    return
                self._mark_fast_scroll()
                try:state["job"]=self.after(22,tick)
                except Exception:state["job"]=None

            if state.get("job") is None:
                try:state["job"]=self.after(8,tick)
                except Exception:tick()
            return "break"
        except Exception:
            return "break"

    def _install_smooth_scroll(self, scrollable, units=1):
        """Install the same throttled wheel path on the CTk scroll canvas."""
        try:
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None:return
            def wheel(event):
                delta=getattr(event,"delta",0)
                if not delta:return "break"
                magnitude=max(1,min(3,int(abs(delta)/120) if abs(delta)>=120 else 1))
                direction=-1 if delta>0 else 1
                return self._queue_scroll_step(scrollable,direction*magnitude*max(1,int(units)))
            canvas.bind("<MouseWheel>",wheel,add=False)
            canvas.bind("<Button-4>",lambda e:self._queue_scroll_step(scrollable,-1),add=False)
            canvas.bind("<Button-5>",lambda e:self._queue_scroll_step(scrollable,1),add=False)
        except Exception:
            pass

    def _bind_outer_scroll(self, widget, page_key):
        """Inner widgets share the page scroll queue instead of scrolling directly."""
        try:
            target=getattr(widget,"_textbox",widget)
            def on_wheel(event):
                body=getattr(self,"page_scrolls",{}).get(page_key)
                if body is None or not self._widget_alive(body):return "break"
                delta=getattr(event,"delta",0)
                if not delta:return "break"
                magnitude=max(1,min(3,int(abs(delta)/120) if abs(delta)>=120 else 1))
                return self._queue_scroll_step(body,(-1 if delta>0 else 1)*magnitude)
            target.bind("<MouseWheel>",on_wheel,add=False)
            target.bind("<Button-4>",lambda e:self._queue_scroll_step(getattr(self,"page_scrolls",{}).get(page_key),-1) if getattr(self,"page_scrolls",{}).get(page_key) else "break",add=False)
            target.bind("<Button-5>",lambda e:self._queue_scroll_step(getattr(self,"page_scrolls",{}).get(page_key),1) if getattr(self,"page_scrolls",{}).get(page_key) else "break",add=False)
        except Exception:
            pass

'''
regex_rep(
    r'    def _mark_fast_scroll\(self\):\n.*?(?=    def _page_shell\(self, key, title, subtitle=""\):\n)',
    scroll_block,
    'unified scroll queue'
)

# Visual polish: generic section cards gain a compact icon tile based on context.
section_helper = r'''    def _section_icon_for_title(self, title):
        text=str(title or "").upper()
        rules=(
            (("SPOTIFY","MÚSICA","MUSIC","ÁUDIO","AUDIO"),"♫"),
            (("FPS","DESEMPENHO","PERFORMANCE","BENCHMARK","OTIMIZA"),"⚡"),
            (("CURSOR",),"✣"),
            (("FONTE","FONT"),"Aa"),
            (("PING","LATÊNCIA","LATENCY","REDE","NETWORK"),"⌁"),
            (("UPDATE","ATUALIZA"),"↻"),
            (("RECUPERA","RECOVERY","SAFE"),"↶"),
            (("APOIO","SUPPORT"),"♥"),
            (("BUG","SUGEST","FEEDBACK"),"!"),
            (("TEMA","THEME","PERSONAL","CUSTOM"),"✦"),
            (("BLOX","COMBO","BUILD"),"◆"),
            (("ROBLOX",),"R"),
        )
        for keys,icon in rules:
            if any(k in text for k in keys):
                return icon
        return "◇"

'''
anchor='    def _section_card(self, parent, title, description=""):\n'
if anchor not in s:
    raise SystemExit("v3.18.6 patch: section_card anchor missing")
s=s.replace(anchor,section_helper+anchor,1)

rep(
    '        ctk.CTkLabel(head,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold"),anchor="w").pack(side="left")\n',
    '        icon_chip=ctk.CTkFrame(head,width=34,height=34,corner_radius=10,fg_color=t.get("icon_bg",t["card_active"]),border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.38)); icon_chip.pack(side="left",padx=(0,10)); icon_chip.pack_propagate(False)\n'
    '        ctk.CTkLabel(icon_chip,text=self._section_icon_for_title(title),text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI Symbol",size=14,weight="bold")).pack(fill="both",expand=True)\n'
    '        ctk.CTkLabel(head,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold"),anchor="w").pack(side="left")\n',
    'section card icon chip'
)

# Add symbols to common actions, without changing the layout.
s=s.replace('text="APLICAR CONFIGURAÇÕES" if pt else "APPLY SETTINGS"', 'text="✓  APLICAR CONFIGURAÇÕES" if pt else "✓  APPLY SETTINGS"')
s=s.replace('text="COMPARAR CONFIGURAÇÕES" if pt else "COMPARE SETTINGS"', 'text="≋  COMPARAR CONFIGURAÇÕES" if pt else "≋  COMPARE SETTINGS"')
s=s.replace('text="MODO COMPACTO" if pt else "COMPACT MODE"', 'text="▣  MODO COMPACTO" if pt else "▣  COMPACT MODE"')
s=s.replace('text="REPORTAR BUG" if pt else "REPORT BUG"', 'text="!  REPORTAR BUG" if pt else "!  REPORT BUG"')
s=s.replace('text="VERIFICAR ATUALIZAÇÃO" if pt else "CHECK UPDATE"', 'text="↻  VERIFICAR ATUALIZAÇÃO" if pt else "↻  CHECK UPDATE"')

# Spotify Web volume: trust the already-proven WinRT media source after explicit opt-in.
new_volume_worker = r'''    def _spotify_audio_volume_worker(self, action="read", value=None):
        """Read/change Spotify audio via Windows Core Audio.

        Desktop Spotify is isolated by process name. For Spotify Web, browser
        volume is touched ONLY after the explicit Web-volume opt-in. When WinRT
        has already proven the current Spotify media session, its source chooses
        the browser process; this avoids the old false-negative window-title gate.
        """
        if os.name!="nt":
            return {"ok":False,"reason":"not_windows","error":"Windows required"}
        coinited=False
        try:
            try:
                import comtypes
                try:
                    comtypes.CoInitialize(); coinited=True
                except Exception:pass
            except Exception:
                comtypes=None
            from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
            sessions=AudioUtilities.GetAllSessions()
            targets=[]
            browser_names={"chrome.exe","msedge.exe","firefox.exe","brave.exe","opera.exe","opera_gx.exe"}
            spotify_pids=set()
            try:
                for pr in psutil.process_iter(["pid","name"]):
                    name=str(pr.info.get("name") or "").lower()
                    if name=="spotify.exe" or name.startswith("spotify"):
                        spotify_pids.add(int(pr.info.get("pid") or 0))
            except Exception:pass

            def session_info(sess):
                proc_name=""; proc_pid=0
                try:
                    proc=sess.Process
                    if proc is not None:
                        proc_name=str(proc.name() or "").lower()
                        proc_pid=int(getattr(proc,"pid",0) or 0)
                except Exception:pass
                if not proc_pid:
                    try:proc_pid=int(getattr(sess,"ProcessId",0) or 0)
                    except Exception:pass
                fields=[]
                for attr in ("DisplayName","Identifier","InstanceIdentifier"):
                    try:fields.append(str(getattr(sess,attr,"") or ""))
                    except Exception:pass
                return proc_name,proc_pid," ".join(fields).lower()

            def ctl_for(sess):
                try:return sess._ctl.QueryInterface(ISimpleAudioVolume)
                except Exception:
                    try:return sess.SimpleAudioVolume
                    except Exception:return None

            for sess in sessions:
                proc_name,proc_pid,meta=session_info(sess)
                is_desktop=(proc_name=="spotify.exe" or proc_pid in spotify_pids or "spotify.exe" in meta or "spotifyab.spotifymusic" in meta or ("spotify" in meta and proc_name not in browser_names))
                is_web=(proc_name in browser_names and ("open.spotify" in meta or "spotify" in meta))
                if not (is_desktop or is_web):continue
                ctl=ctl_for(sess)
                if ctl is not None:targets.append((ctl,"desktop" if is_desktop else "web",proc_name,meta))

            if not targets and bool(getattr(self,"spotify_web_volume_optin",False)):
                snap=dict(getattr(self,"_spotify_current",{}) or {})
                raw_source=str(snap.get("source") or "").lower()
                selected=None
                source_map=(("msedge","msedge.exe"),("edge","msedge.exe"),("chrome","chrome.exe"),("firefox","firefox.exe"),("brave","brave.exe"),("opera gx","opera_gx.exe"),("opera","opera.exe"))
                for needle,proc in source_map:
                    if needle in raw_source:
                        selected=proc; break
                media_proven=bool(snap.get("ok")) and bool(selected)
                window_hint=False
                if not media_proven:
                    try:window_hint=bool(self._spotify_browser_window_hint())
                    except Exception:window_hint=False
                allowed={selected} if media_proven and selected else (browser_names if window_hint else set())
                for sess in sessions:
                    proc_name,_,_=session_info(sess)
                    if proc_name not in allowed:continue
                    ctl=ctl_for(sess)
                    if ctl is not None:targets.append((ctl,"web-browser",proc_name,"spotify media-session opt-in"))

            if not targets:
                snap=dict(getattr(self,"_spotify_current",{}) or {})
                src=str(snap.get("source") or "").lower()
                web_detected=bool(snap.get("ok")) and any(x in src for x in ("chrome","msedge","edge","firefox","brave","opera"))
                return {"ok":False,"reason":"web_optin_required" if web_detected and not bool(getattr(self,"spotify_web_volume_optin",False)) else "no_isolated_audio_session","error":"Spotify Web volume requires explicit opt-in." if web_detected else "Spotify audio session not found."}

            levels=[]; mutes=[]
            for ctl,_,_,_ in targets:
                try:levels.append(float(ctl.GetMasterVolume()))
                except Exception:pass
                try:mutes.append(bool(ctl.GetMute()))
                except Exception:pass
            current=max(levels) if levels else 1.0
            muted=bool(mutes and all(mutes))
            act=str(action or "read").lower()

            if act=="set":
                target=max(0.0,min(1.0,float(value)))
                for ctl,_,_,_ in targets:
                    try:ctl.SetMasterVolume(target,None)
                    except Exception:pass
                current=target
                if target>0 and muted:
                    for ctl,_,_,_ in targets:
                        try:ctl.SetMute(0,None)
                        except Exception:pass
                    muted=False
            elif act=="delta":
                target=max(0.0,min(1.0,current+float(value or 0)))
                for ctl,_,_,_ in targets:
                    try:ctl.SetMasterVolume(target,None)
                    except Exception:pass
                current=target
                if target>0 and muted:
                    for ctl,_,_,_ in targets:
                        try:ctl.SetMute(0,None)
                        except Exception:pass
                    muted=False
            elif act=="mute_toggle":
                new_mute=not muted
                for ctl,_,_,_ in targets:
                    try:ctl.SetMute(1 if new_mute else 0,None)
                    except Exception:pass
                muted=new_mute

            kinds={k for _,k,_,_ in targets}
            if "web-browser" in kinds:out_kind="web-browser"
            elif kinds=={"web"}:out_kind="web"
            else:out_kind="desktop"
            return {"ok":True,"volume":current,"muted":muted,"target_count":len(targets),"kind":out_kind}
        except Exception as exc:
            return {"ok":False,"reason":"pycaw_error","error":f"{type(exc).__name__}: {exc}"}
        finally:
            if coinited:
                try:comtypes.CoUninitialize()
                except Exception:pass

'''
regex_rep(
    r'    def _spotify_audio_volume_worker\(self, action="read", value=None\):\n.*?(?=    def _spotify_apply_volume_result\(self,result,quiet=False\):\n)',
    new_volume_worker,
    'spotify volume worker'
)

old_status = '''            if reason=="no_isolated_audio_session":
                self.spotify_volume_state_label.configure(text="VOLUME EXCLUSIVO • abra o Spotify Desktop",text_color="#F0C75E")
                self.spotify_volume_value_label.configure(text="—")
            else:
'''
new_status = '''            if reason=="web_optin_required":
                self.spotify_volume_state_label.configure(text="SPOTIFY WEB DETECTADO • ative o controle Web abaixo",text_color="#F0C75E")
                self.spotify_volume_value_label.configure(text="—")
            elif reason=="no_isolated_audio_session":
                self.spotify_volume_state_label.configure(text="VOLUME EXCLUSIVO • abra o Spotify Desktop",text_color="#F0C75E")
                self.spotify_volume_value_label.configure(text="—")
            else:
'''
rep(old_status,new_status,'spotify volume web status')
old_msg='''            if reason=="no_isolated_audio_session":
                self._spotify_set_status("volume exclusivo não encontrado; o navegador não será alterado para não afetar YouTube","warning")
            else:
'''
new_msg='''            if reason=="web_optin_required":
                self._spotify_set_status("Spotify Web detectado: ative PERMITIR VOLUME NO SPOTIFY WEB para usar volume e mute","warning")
            elif reason=="no_isolated_audio_session":
                self._spotify_set_status("volume exclusivo não encontrado; o navegador não será alterado para não afetar YouTube","warning")
            else:
'''
rep(old_msg,new_msg,'spotify volume web message')

# Spotify mini-player: larger and easier to read.
rep(
    '        f=ctk.CTkFrame(self,width=360,height=112,fg_color="#181818",corner_radius=14,border_width=1,border_color="#1ED760")\n'
    '        f.place(x=-390,rely=1.0,y=-15,anchor="sw"); f.pack_propagate(False); self._spotify_mini_frame=f\n'
    '        art=ctk.CTkFrame(f,width=64,height=64,fg_color="#242424",corner_radius=10); art.pack(side="left",padx=(10,8),pady=10); art.pack_propagate(False)\n'
    '        self._spotify_mini_art_label=ctk.CTkLabel(art,text="♫",text_color="#1ED760",font=ctk.CTkFont(size=20,weight="bold")); self._spotify_mini_art_label.pack(fill="both",expand=True)\n'
    '        left=ctk.CTkFrame(f,fg_color="transparent"); left.pack(side="left",fill="both",expand=True,padx=(0,4),pady=9)\n'
    '        self._spotify_mini_title=ctk.CTkLabel(left,text="Spotify",text_color="#FFFFFF",font=ctk.CTkFont(size=10,weight="bold"),anchor="w"); self._spotify_mini_title.pack(fill="x")\n'
    '        self._spotify_mini_artist=ctk.CTkLabel(left,text="Now Playing do Windows",text_color="#B3B3B3",font=ctk.CTkFont(size=8),anchor="w"); self._spotify_mini_artist.pack(fill="x")\n'
    '        rr=ctk.CTkFrame(left,fg_color="transparent"); rr.pack(fill="x",pady=(5,0))\n'
    '        for lab,cmd in (("⏮","previous"),("▶/⏸","toggle"),("⏭","next")):\n'
    '            ctk.CTkButton(rr,text=lab,width=58,height=26,command=lambda c=cmd:self.spotify_local_command(c),fg_color=t["card_active"],text_color=t["accent"]).pack(side="left",padx=2)\n'
    '        ctk.CTkButton(f,text="×",width=28,height=28,command=self._spotify_hide_mini,fg_color="transparent",hover_color=t["card_active"],text_color=t["text"]).pack(side="right",anchor="n",padx=6,pady=6)\n'
    '        self._play_ui_sound("open",0)\n'
    '        def anim(x=-390):\n',
    '        f=ctk.CTkFrame(self,width=478,height=154,fg_color="#181818",corner_radius=18,border_width=1,border_color="#1ED760")\n'
    '        f.place(x=-515,rely=1.0,y=-18,anchor="sw"); f.pack_propagate(False); self._spotify_mini_frame=f\n'
    '        art=ctk.CTkFrame(f,width=94,height=94,fg_color="#242424",corner_radius=13); art.pack(side="left",padx=(14,12),pady=14); art.pack_propagate(False)\n'
    '        self._spotify_mini_art_label=ctk.CTkLabel(art,text="♫",text_color="#1ED760",font=ctk.CTkFont(size=28,weight="bold")); self._spotify_mini_art_label.pack(fill="both",expand=True)\n'
    '        left=ctk.CTkFrame(f,fg_color="transparent"); left.pack(side="left",fill="both",expand=True,padx=(0,5),pady=14)\n'
    '        self._spotify_mini_title=ctk.CTkLabel(left,text="Spotify",text_color="#FFFFFF",font=ctk.CTkFont(size=14,weight="bold"),anchor="w"); self._spotify_mini_title.pack(fill="x",pady=(2,0))\n'
    '        self._spotify_mini_artist=ctk.CTkLabel(left,text="Now Playing do Windows",text_color="#B3B3B3",font=ctk.CTkFont(size=10),anchor="w"); self._spotify_mini_artist.pack(fill="x",pady=(2,0))\n'
    '        rr=ctk.CTkFrame(left,fg_color="transparent"); rr.pack(fill="x",pady=(10,0))\n'
    '        for lab,cmd in (("⏮","previous"),("▶  /  ⏸","toggle"),("⏭","next")):\n'
    '            ctk.CTkButton(rr,text=lab,width=72,height=34,corner_radius=9,command=lambda c=cmd:self.spotify_local_command(c),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"]).pack(side="left",padx=3)\n'
    '        ctk.CTkButton(f,text="×",width=32,height=32,command=self._spotify_hide_mini,fg_color="transparent",hover_color=t["card_active"],text_color=t["text"]).pack(side="right",anchor="n",padx=8,pady=8)\n'
    '        self._play_ui_sound("open",0)\n'
    '        def anim(x=-515):\n',
    'spotify mini-player size'
)
rep('            nx=min(15,x+46); f.place_configure(x=nx)\n','            nx=min(18,x+58); f.place_configure(x=nx)\n','spotify mini animation')
rep('            if nx<15:self.after(15,lambda:anim(nx))\n','            if nx<18:self.after(15,lambda:anim(nx))\n','spotify mini animation target')
s=s.replace('self._spotify_make_art(snap.get("art") or b"",54)', 'self._spotify_make_art(snap.get("art") or b"",86)')
s=s.replace("self._spotify_make_art(snap.get('art') or b'',54)", "self._spotify_make_art(snap.get('art') or b'',86)")

# Global Apply Settings must include the selected Roblox cursor.
rep(
    '        ok=self._salvar_flags_compiladas(mostrar_popup=False,usar_editor=False)\n'
    '        after=self._snapshot_sistema()\n',
    '        ok=self._salvar_flags_compiladas(mostrar_popup=False,usar_editor=False)\n'
    '        cursor_ok=True\n'
    '        try:\n'
    '            pack=self.cursor_menu.get() if getattr(self,"cursor_menu",None) is not None else getattr(self,"cursor_pack","Roblox Padrão")\n'
    '            self.cursor_pack=str(pack or "Roblox Padrão")\n'
    '            cursor_ok=bool(self.aplicar_cursor_pack(self.cursor_pack,silencioso=True))\n'
    '        except Exception as exc:\n'
    '            cursor_ok=False\n'
    '            try:self.adicionar_log(f"CURSOR: falha no aplicar geral: {exc}")\n'
    '            except Exception:pass\n'
    '        after=self._snapshot_sistema()\n',
    'global apply cursor'
)
rep(
    '        self.last_apply_summary={"ok":bool(ok),"active":active,"flags":flags,"restart":restart,"time":datetime.now().isoformat(timespec=\'seconds\')}\n',
    '        self.last_apply_summary={"ok":bool(ok),"active":active,"flags":flags,"restart":restart,"cursor_ok":bool(cursor_ok),"time":datetime.now().isoformat(timespec=\'seconds\')}\n',
    'apply summary cursor'
)

path.write_text(s,encoding="utf-8")
print("patched v3.18.6",path,"bytes",len(s.encode("utf-8")))
