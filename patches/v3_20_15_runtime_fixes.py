from pathlib import Path
import ast, os, re, textwrap

root=Path(os.environ.get('ZK_SOURCE_DIR','.'))
p=root/'ZKStrap_v3_18_0.py'
s=p.read_text(encoding='utf-8')


def _class(src):
    t=ast.parse(src)
    return t,next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ModernConfigApp')

def _span(src,name):
    t,cls=_class(src); lines=src.splitlines(True)
    node=next((n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if node is None: raise SystemExit(f'v3.20.15 method missing: {name}')
    a=sum(len(x) for x in lines[:node.lineno-1]); b=sum(len(x) for x in lines[:node.end_lineno])
    return node,a,b

def _norm(body):
    raw=textwrap.dedent(body).strip('\n')
    return textwrap.indent(raw+'\n','    ')

def replace_method(src,name,body):
    _,a,b=_span(src,name)
    return src[:a]+_norm(body)+src[b:]

def insert_before(src,before_name,body):
    _,a,_=_span(src,before_name)
    return src[:a]+_norm(body)+'\n'+src[a:]

if 'APP_VERSION = "3.20.14"' not in s:
    raise SystemExit('v3.20.15 expected v3.20.14 final base')
s=s.replace('APP_VERSION = "3.20.14"','APP_VERSION = "3.20.15"',1)
s=re.sub(r'BUILD_TIMESTAMP = "[^"]*"','BUILD_TIMESTAMP = "Runtime State + Thumbnail + First Run Safety Fixes"',s,count=1)

# Combo Planner / Owner Loadout / Build Roulette share this exact resolver.
# Frozen Pillow builds can differ in WEBP decoding, so release assets include PNG
# mirrors and runtime prefers PNG while retaining WEBP as a source fallback.
s=replace_method(s,'_combo_local_icon_path',r'''
def _combo_local_icon_path(self, category, name):
    """Resolve the same bundled item art for Combo, Owner Loadout and Roulette."""
    if category not in ("fruit","style","sword","gun"):
        return ""
    try:
        slug=self._combo_slug(name)
        for ext in ("png","webp"):
            candidate=_resource_path("zkstrap_assets","combo_icons",category,f"{slug}.{ext}")
            if os.path.isfile(candidate):return candidate
        return ""
    except Exception:
        return ""
''')

s=replace_method(s,'_combo_load_local_ctk_thumb',r'''
def _combo_load_local_ctk_thumb(self, category, name, size):
    path=self._combo_local_icon_path(category,name)
    if not path:return None
    try:
        from PIL import Image
        im=Image.open(path);im.load();im=im.convert("RGBA")
        im.thumbnail((int(size),int(size)),Image.Resampling.LANCZOS)
        out=ctk.CTkImage(light_image=im,dark_image=im,size=(int(size),int(size)))
        refs=getattr(self,"_combo_local_image_refs",None)
        if not isinstance(refs,list):refs=[];self._combo_local_image_refs=refs
        refs.append(out)
        if len(refs)>320:del refs[:-240]
        return out
    except Exception as exc:
        try:_startup_log(f"COMBO ICON: failed {category}/{name}: {exc!r}")
        except Exception:pass
        return None
''')

# First-run audio can temporarily force the sound manager on. Normalize that
# state again without requiring the user to close/reopen ZKStrap.
s=insert_before(s,'_global_click_sound',r'''
def _audio_restore_runtime_state(self, restart_music=False):
    try:
        mgr=getattr(self,"_sound_manager",None)
        if mgr is None:return False
        desired=_normalize_audio_pack(getattr(self,"sound_pack",DEFAULT_AUDIO_PACK))
        pack_changed=(getattr(mgr,"pack",None)!=desired)
        self.sound_pack=desired
        mgr.pack=desired
        mgr.enabled=bool(getattr(self,"sounds_enabled",False))
        mgr.sfx_enabled=bool(getattr(self,"sfx_enabled",True))
        mgr.music_enabled=bool(getattr(self,"music_enabled",True))
        mgr.music_volume=float(getattr(self,"music_volume",.22) or .22)
        mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0) or 1.0)
        spotify=bool(getattr(self,"_spotify_internal_music_suppressed",False))
        if not mgr.enabled or not mgr.music_enabled or spotify:
            mgr.stop_music()
        elif restart_music or pack_changed:
            mgr.start_music(force_restart=True)
        return True
    except Exception as exc:
        try:_startup_log("AUDIO: runtime state recovery failed "+repr(exc))
        except Exception:pass
        return False
''')

s=replace_method(s,'_play_ui_sound',r'''
def _play_ui_sound(self, name="click", throttle=0.035):
    try:
        try:
            if self._first_run_stage()=="done" and bool(getattr(self,"_first_run_intro_active",False)):
                self._first_run_intro_active=False
                self._audio_restore_runtime_state(restart_music=True)
            else:
                self._audio_restore_runtime_state(restart_music=False)
        except Exception:pass
        mgr=getattr(self,"_sound_manager",None)
        if mgr is None:return
        active=str(getattr(self,"tema_atual","") or "")
        secret_events={"hover","click","confirm","nav","theme","apply","select","open","back","toggle_on","toggle_off","success"}
        if active in UNLOCKABLE_THEME_NAMES and name in secret_events:
            if self._play_secret_theme_sound(active,name,throttle):return
        mgr.play(name,throttle=throttle)
    except Exception:
        pass
''')

s=replace_method(s,'_audio_select_pack',r'''
def _audio_select_pack(self, pack):
    pack=_normalize_audio_pack(pack)
    if pack not in AUDIO_PACKS:return
    self.sound_pack=pack;self.sounds_enabled=True;self.sound_prompted=True
    self._first_run_intro_active=False
    mgr=getattr(self,"_sound_manager",None)
    if mgr is not None:
        try:mgr.stop_music()
        except Exception:pass
        mgr.pack=pack;mgr.enabled=True
        mgr.sfx_enabled=bool(getattr(self,"sfx_enabled",True));mgr.music_enabled=bool(getattr(self,"music_enabled",True))
        mgr.music_volume=float(getattr(self,"music_volume",0.22));mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0))
        mgr.play("theme",0)
        if mgr.music_enabled and not bool(getattr(self,"_spotify_internal_music_suppressed",False)):
            mgr.start_music(force_restart=True)
    self.salvar_config_app();self._refresh_sound_button()
    try:self.audio_current_label.configure(text=self._L(f"IDENTIDADE ATIVA  //  {pack}",f"ACTIVE IDENTITY  //  {pack}",f"IDENTIDAD ACTIVA  //  {pack}",f"当前身份  //  {pack}",f"IDENTITÉ ACTIVE  //  {pack}"))
    except Exception:pass
    try:
        for name,btn in getattr(self,"audio_pack_buttons",{}).items():
            tt=TEMAS[self.tema_atual];active=(name==pack)
            btn.configure(text=(self._L("ATIVO ✓","ACTIVE ✓","ACTIVO ✓","已启用 ✓","ACTIF ✓") if active else self._L("USAR","USE","USAR","使用","UTILISER")),fg_color=tt["accent"] if active else tt["card_active"],text_color="#050505" if active else tt["text"])
    except Exception:pass
''')

node,a,b=_span(s,'_first_run_route'); chunk=s[a:b]
old='''        self._first_run_active_stage="done"'''
new='''        self._first_run_active_stage="done"\n        if bool(getattr(self,"_first_run_intro_active",False)):\n            self._first_run_intro_active=False\n            self._audio_restore_runtime_state(restart_music=True)'''
if old not in chunk:raise SystemExit('v3.20.15 first-run audio restore anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

# Persist first-run avatar bytes exactly like the regular profile linker does.
s=insert_before(s,'_render_profile_button',r'''
def _persist_profile_avatar_bytes(self, data):
    if not data:return False
    try:
        from PIL import Image
        import io
        raw=bytes(data)
        im=Image.open(io.BytesIO(raw));im.verify()
        path=self._profile_cache_path();os.makedirs(os.path.dirname(path),exist_ok=True)
        tmp=path+".tmp"
        with open(tmp,"wb") as f:f.write(raw)
        os.replace(tmp,path)
        self._profile_avatar_ctk=None
        return True
    except Exception as exc:
        try:self.log_output(f"[!] Avatar cache save failed: {exc}")
        except Exception:pass
        return False
''')

node,a,b=_span(s,'_abrir_onboarding_username_ui_3205'); chunk=s[a:b]
old='''                self.linked_profile={"id":int(profile.get("id",0)),"name":str(profile.get("name","") or ""),"displayName":str(profile.get("displayName","") or profile.get("name","") or ""),"avatar_url":str(profile.get("avatar_url","") or "")}\n                self._mark_roblox_onboarding_done(self.linked_profile['name']);refresh_top_profile();self.after(60,refresh_top_profile)'''
new='''                self.linked_profile={"id":int(profile.get("id",0)),"name":str(profile.get("name","") or ""),"displayName":str(profile.get("displayName","") or profile.get("name","") or ""),"avatar_url":str(profile.get("avatar_url","") or "")}\n                self._persist_profile_avatar_bytes(pending.get("avatar"))\n                self.config_data["linked_profile"]=dict(self.linked_profile)\n                self._mark_roblox_onboarding_done(self.linked_profile['name']);self.salvar_config_app();refresh_top_profile();self.after(60,refresh_top_profile);self.after(220,refresh_top_profile)'''
if old not in chunk:raise SystemExit('v3.20.15 first-run avatar anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

node,a,b=_span(s,'_confirmar_perfil');chunk=s[a:b]
old='''        if avatar_bytes:\n            try:\n                path = self._profile_cache_path(); os.makedirs(os.path.dirname(path), exist_ok=True)\n                with open(path, "wb") as f: f.write(avatar_bytes)\n            except Exception: pass'''
new='''        self._persist_profile_avatar_bytes(avatar_bytes)\n        self.config_data["linked_profile"]=dict(self.linked_profile)'''
if old not in chunk:raise SystemExit('v3.20.15 regular avatar anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

# Owner development unlocks are global. They must never leak into an isolated
# Fresh User Test profile, otherwise a zero-progress first run sees every secret.
s=replace_method(s,'_owner_secret_theme_unlocked',r'''
def _owner_secret_theme_unlocked(self,name):
    real=name in set(getattr(self,"unlocked_secret_themes",set()))
    in_test=bool(_owner_test_profile_enabled())
    dev=bool((not in_test) and self._owner_key_valid() and dict(getattr(self,"_owner_state",{}) or {}).get("unlock_all_themes",False))
    return bool(real or dev)
''')

old='''            dev_unlock=bool(self._owner_key_valid() and dict(getattr(self,"_owner_state",{}) or {}).get("unlock_all_themes",False))'''
new='''            dev_unlock=bool((not _owner_test_profile_enabled()) and self._owner_key_valid() and dict(getattr(self,"_owner_state",{}) or {}).get("unlock_all_themes",False))'''
if old not in s:raise SystemExit('v3.20.15 secret gallery override anchor missing')
s=s.replace(old,new,1)

node,a,b=_span(s,'_owner_prepare_test_profile');chunk=s[a:b]
old='''cfg={"version":APP_VERSION,"language":"pt","language_selected":False,"language_picker_revision":0,"tutorial_completed":False,"sound_prompted":False,"sounds_enabled":False,"first_run_intro_audio":True,"music_enabled":True,"sfx_enabled":True,"sound_pack":DEFAULT_AUDIO_PACK,"modules":{},"advanced_values":{},"combo_entries":[]}'''
new='''cfg={"version":APP_VERSION,"language":"pt","language_selected":False,"language_picker_revision":0,"tutorial_completed":False,"sound_prompted":False,"sounds_enabled":False,"first_run_intro_audio":True,"music_enabled":True,"sfx_enabled":True,"sound_pack":DEFAULT_AUDIO_PACK,"modules":{},"advanced_values":{},"combo_entries":[],"unlocked_secret_themes":[],"creator_total_completed":0,"roulette_roll_count":0,"secret_music_seconds":0,"creator_history":[],"roulette_history":[],"roulette_favorites":[]}'''
if old not in chunk:raise SystemExit('v3.20.15 fresh test config anchor missing')
chunk=chunk.replace(old,new,1);s=s[:a]+chunk+s[b:]

ast.parse(s)
for needle in (
    'APP_VERSION = "3.20.15"',
    'for ext in ("png","webp")',
    'def _audio_restore_runtime_state',
    'self._persist_profile_avatar_bytes(pending.get("avatar"))',
    'not _owner_test_profile_enabled()',
    '"unlocked_secret_themes":[]',
):
    if needle not in s:raise SystemExit('v3.20.15 validation missing: '+needle)

p.write_text(s,encoding='utf-8')
print('Applied v3.20.15 runtime fixes: thumbnails, audio recovery, first-run avatar, secret test isolation')
