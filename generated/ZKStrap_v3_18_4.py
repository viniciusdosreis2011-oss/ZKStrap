#!/usr/bin/env python3
# ZKStrap.py
# Internacionalizado: textos em Português / English. Troque idioma no menu para aplicar.

import json
import sys
import os
import glob
from datetime import datetime
import unicodedata
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas, Toplevel, Label, PhotoImage, Tk, colorchooser, simpledialog
import tkinter as tk
import subprocess
import psutil
import threading
import time
import random
import math
import re
import shutil
import socket
import requests
import traceback
import webbrowser
import ctypes
import uuid
from ctypes import wintypes
from collections import deque
from io import BytesIO
import textwrap
import tempfile
import struct
import statistics
import hashlib
import base64
import secrets
import urllib.parse
import http.server
import socketserver
import zipfile
from pathlib import Path
try:
    import winsound
except Exception:
    winsound = None

APP_VERSION = "3.18.4"
BUILD_TIMESTAMP = "Support Hub + GitHub Pages"
APP_NAME = "ZKSTRAP"
SUPPORT_PAGE_URL = "https://viniciusdosreis2011-oss.github.io/ZKStrap/"

# UPDATE CENTER v3.18.0
UPDATE_MANIFEST_URLS = {
    "stable": "https://raw.githubusercontent.com/viniciusdosreis2011-oss/ZKStrap/main/channels/stable.json",
    "beta": "https://raw.githubusercontent.com/viniciusdosreis2011-oss/ZKStrap/main/channels/beta.json",
    "dev": "https://raw.githubusercontent.com/viniciusdosreis2011-oss/ZKStrap/main/channels/dev.json",
}
UPDATE_REPO_URL = "https://github.com/viniciusdosreis2011-oss/ZKStrap"
UPDATER_VERSION = "1.0.0"

# OWNER LAB v3.17.x
# The actual owner key is NOT shipped inside the public app package.
# Only its SHA-256 fingerprint is embedded here.
OWNER_KEY_SHA256 = "d8f16d2d9daac69789a42fe64723acfe880f5afdff7803db59b06d924c64a464"
OWNER_SEARCH_TRIGGER = "zkstrap_adm"

def _owner_vault_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "ZKSTRAP_OWNER")

def _owner_key_path():
    return os.path.join(_owner_vault_dir(), "owner_access.key")

def _owner_state_path():
    return os.path.join(_owner_vault_dir(), "owner_state.json")

def _owner_auth_path():
    return os.path.join(_owner_vault_dir(), "owner_auth.json")

def _owner_key_valid_global():
    try:
        path=_owner_key_path()
        if not os.path.isfile(path): return False
        token=Path(path).read_text(encoding="utf-8").strip()
        return bool(token) and hashlib.sha256(token.encode("utf-8")).hexdigest()==OWNER_KEY_SHA256
    except Exception:
        return False

def _owner_state_read_global():
    if not _owner_key_valid_global():
        return {}
    try:
        path=_owner_state_path()
        if os.path.isfile(path):
            with open(path,"r",encoding="utf-8") as f:
                data=json.load(f)
            return data if isinstance(data,dict) else {}
    except Exception:
        pass
    return {}

def _owner_state_write_global(data):
    if not _owner_key_valid_global():
        return False
    try:
        os.makedirs(_owner_vault_dir(),exist_ok=True)
        tmp=_owner_state_path()+".tmp"
        with open(tmp,"w",encoding="utf-8") as f:
            json.dump(data if isinstance(data,dict) else {},f,indent=2,ensure_ascii=False)
        os.replace(tmp,_owner_state_path())
        return True
    except Exception:
        return False

def _owner_test_profile_enabled():
    try:
        return bool(_owner_state_read_global().get("test_profile",False))
    except Exception:
        return False

AUDIO_PACKS = {
    "ZK Signature": {"folder":"zk_signature", "desc":"Lo-fi eletrônico com acordes e lead suave."},
    "Neon Tech": {"folder":"neon_tech", "desc":"Synthwave leve com arpejo neon e bateria digital."},
    "Glass UI": {"folder":"glass_ui", "desc":"Melodia cristalina, pads leves e ritmo calmo."},
    "Tactical": {"folder":"tactical", "desc":"Beat contido, bass curto e motivo rítmico."},
    "Deep Space": {"folder":"deep_space", "desc":"Ambient musical espacial com acordes e arpejos lentos."},
    "Arcade": {"folder":"arcade", "desc":"Chiptune moderno com melodia e groove de arcade."},
    "Soft Clicks": {"folder":"soft_clicks", "desc":"Lo-fi discreto e relaxado para ficar horas aberto."},
    "Cyber Pulse": {"folder":"cyber_pulse", "desc":"Electro com baixo pulsante e lead sincopado."},
    "Retro Digital": {"folder":"retro_digital", "desc":"Chiptune retrô com progressão e melodia de verdade."},
    "Void Calm": {"folder":"void_calm", "desc":"Trilha escura e calma, com piano sintético e pads."},
}
DEFAULT_AUDIO_PACK = "ZK Signature"

# IPC simples entre o processo principal e a splash destacada.
_DETACHED_SPLASH_STATUS_FILE = None
_DETACHED_SPLASH_CANCEL_FILE = None

def _startup_log(message):
    """Log mínimo do boot para diagnosticar falhas silenciosas sem afetar a UI."""
    try:
        base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "zkstrap_startup.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")
    except Exception:
        pass

class StartupCancelled(Exception):
    """Fechamento solicitado pelo usuário ainda na tela de carregamento."""

def _resource_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

def _boot_config_path():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    if _owner_test_profile_enabled():
        return os.path.join(_owner_vault_dir(), "TEST_PROFILE", "config.json")
    return os.path.join(base, "ZKSTRAP", "config.json")

def _boot_audio_config():
    try:
        path = _boot_config_path()
        if not os.path.exists(path): return {}
        with open(path, "r", encoding="utf-8") as f:
            data=json.load(f)
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}

def _boot_sounds_enabled():
    data=_boot_audio_config()
    return bool(data.get("sound_prompted", False) and data.get("sounds_enabled", False) and data.get("sfx_enabled", True))

def _boot_play_sound(name):
    if winsound is None or not _boot_sounds_enabled():
        return
    try:
        data=_boot_audio_config()
        pack=str(data.get("sound_pack",DEFAULT_AUDIO_PACK) or DEFAULT_AUDIO_PACK)
        folder=AUDIO_PACKS.get(pack,AUDIO_PACKS[DEFAULT_AUDIO_PACK])["folder"]
        candidates=glob.glob(_resource_path("zkstrap_assets","sounds","packs",folder,f"{name}*.wav"))
        if not candidates:
            candidates=glob.glob(_resource_path("zkstrap_assets","sounds",f"{name}*.wav"))
        if candidates:
            winsound.PlaySound(random.choice(candidates), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception:
        pass

def _audio_cli_arg(name, default=""):
    try:
        idx=sys.argv.index(name)
        return sys.argv[idx+1] if idx+1 < len(sys.argv) else default
    except Exception:
        return default

def _windows_pid_alive(pid):
    try:
        pid=int(pid)
        if pid <= 0:
            return False
        if os.name != "nt":
            try:
                os.kill(pid, 0)
                return True
            except Exception:
                return False
        PROCESS_QUERY_LIMITED_INFORMATION=0x1000
        STILL_ACTIVE=259
        handle=ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            code=wintypes.DWORD()
            ok=ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            return bool(ok and code.value == STILL_ACTIVE)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        return False

def _run_audio_helper():
    """Processo dedicado para a música ambiente.

    Usa winsound em OUTRO processo para a música em loop não ser interrompida
    pelos efeitos sonoros do processo principal.
    """
    path=_audio_cli_arg("--audio-file", "")
    stop_file=_audio_cli_arg("--audio-stop", "")
    parent=_audio_cli_arg("--parent-pid", "0")
    try:
        parent=int(parent or 0)
    except Exception:
        parent=0
    if winsound is None or not path or not os.path.isfile(path):
        raise SystemExit(0)
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP | winsound.SND_NODEFAULT)
        while True:
            if stop_file and os.path.exists(stop_file):
                break
            if parent and not _windows_pid_alive(parent):
                break
            time.sleep(.35)
    except Exception:
        pass
    finally:
        try: winsound.PlaySound(None, 0)
        except Exception: pass
    raise SystemExit(0)

class ZKSoundManager:
    """Áudio local do ZKStrap.

    SFX usam winsound. A música ambiente usa MCI do Windows para continuar
    tocando enquanto efeitos são disparados. Se MCI falhar, o helper antigo
    permanece como fallback.
    """
    def __init__(self, root, enabled=False, pack=DEFAULT_AUDIO_PACK, music_enabled=True, sfx_enabled=True, music_volume=0.22, sfx_volume=1.0):
        self.root=root
        self.enabled=bool(enabled)
        self.music_enabled=bool(music_enabled)
        self.sfx_enabled=bool(sfx_enabled)
        try: self.music_volume=max(0.0,min(0.65,float(music_volume)))
        except Exception: self.music_volume=0.22
        try: self.sfx_volume=max(0.0,min(1.5,float(sfx_volume)))
        except Exception: self.sfx_volume=1.0
        self.pack=pack if pack in AUDIO_PACKS else DEFAULT_AUDIO_PACK
        self._last_sfx_by_name={}
        self._music_proc=None
        self._music_stop_file=None
        self._mci_alias=f"zkambient_{os.getpid()}"
        self._mci_active=False
        self._scaled_music_temp=None
        self._scaled_sfx_cache={}

    def _pack_folder(self):
        return AUDIO_PACKS.get(self.pack,AUDIO_PACKS[DEFAULT_AUDIO_PACK])["folder"]

    def paths(self, name):
        base=_resource_path("zkstrap_assets","sounds","packs",self._pack_folder())
        matches=sorted(glob.glob(os.path.join(base,f"{name}*.wav")))
        if matches: return matches
        return sorted(glob.glob(_resource_path("zkstrap_assets","sounds",f"{name}*.wav")))

    def path(self, name):
        paths=self.paths(name)
        return random.choice(paths) if paths else ""

    def _scaled_sfx_path(self, path):
        """Aplica volume independente aos SFX. 100% preserva o WAV original; até 150% permite boost com clipping seguro."""
        try:
            vol=max(0.0,min(1.5,float(self.sfx_volume)))
            if abs(vol-1.0) < 0.015:
                return path
            key=(path,round(vol,2))
            cached=self._scaled_sfx_cache.get(key)
            if cached and os.path.isfile(cached):
                return cached
            import wave, array
            with wave.open(path,'rb') as src:
                params=src.getparams(); raw=src.readframes(src.getnframes())
            if params.sampwidth != 2:
                return path
            samples=array.array('h'); samples.frombytes(raw)
            for i,v in enumerate(samples):
                samples[i]=max(-32768,min(32767,int(v*vol)))
            digest=hashlib.sha1((path+str(round(vol,2))).encode('utf-8','ignore')).hexdigest()[:12]
            dst=os.path.join(tempfile.gettempdir(),f"zkstrap_sfx_{os.getpid()}_{digest}.wav")
            with wave.open(dst,'wb') as out:
                out.setparams(params); out.writeframes(samples.tobytes())
            self._scaled_sfx_cache[key]=dst
            return dst
        except Exception:
            return path

    def play(self, name, throttle=0.035):
        if not (self.enabled and self.sfx_enabled) or winsound is None: return
        now=time.monotonic(); last=float(self._last_sfx_by_name.get(name,0.0))
        if now-last < float(throttle): return
        self._last_sfx_by_name[name]=now
        try:
            path=self.path(name)
            if path and os.path.exists(path):
                path=self._scaled_sfx_path(path)
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception: pass

    def _helper_command(self, path, stop_file):
        args=["--zk-audio-helper","--audio-file",path,"--audio-stop",stop_file,"--parent-pid",str(os.getpid())]
        if getattr(sys,"frozen",False): return [sys.executable] + args
        return [sys.executable, os.path.abspath(__file__)] + args

    def _mci(self, command):
        if os.name != "nt": return 1
        try:
            buf=ctypes.create_unicode_buffer(256)
            return int(ctypes.windll.winmm.mciSendStringW(str(command),buf,255,0))
        except Exception: return 1

    def _scaled_music_path(self, path):
        """Renderiza uma cópia PCM temporária no volume da música, sem baixar os SFX."""
        try:
            vol=max(0.0,min(0.65,float(self.music_volume)))
            if vol >= 0.649:
                return path
            import wave, array
            with wave.open(path,'rb') as src:
                params=src.getparams(); raw=src.readframes(src.getnframes())
            if params.sampwidth != 2:
                return path
            samples=array.array('h'); samples.frombytes(raw)
            for i,v in enumerate(samples):
                samples[i]=max(-32768,min(32767,int(v*vol)))
            safe=re.sub(r"[^a-zA-Z0-9_-]+","_",os.path.basename(path))
            dst=os.path.join(tempfile.gettempdir(),f"zkstrap_mix_{os.getpid()}_{safe}_{int(vol*1000):03d}.wav")
            with wave.open(dst,'wb') as out:
                out.setparams(params); out.writeframes(samples.tobytes())
            old=self._scaled_music_temp; self._scaled_music_temp=dst
            if old and old!=dst and os.path.isfile(old):
                try: os.remove(old)
                except Exception: pass
            return dst
        except Exception as exc:
            _startup_log("AUDIO: volume render failed "+repr(exc))
            return path

    def _start_music_mci(self, path):
        try:
            self._mci(f"close {self._mci_alias}")
            err=self._mci(f'open "{path}" type waveaudio alias {self._mci_alias}')
            if err: return False
            err=self._mci(f"play {self._mci_alias} repeat")
            if err:
                self._mci(f"close {self._mci_alias}"); return False
            self._mci_active=True
            _startup_log(f"AUDIO: MCI ambient started pack={self.pack!r}")
            return True
        except Exception as exc:
            _startup_log("AUDIO: MCI failed "+repr(exc)); return False

    def _start_music_helper(self, path):
        try:
            if self._music_proc is not None and self._music_proc.poll() is None: return True
        except Exception: self._music_proc=None
        try:
            stop_file=os.path.join(tempfile.gettempdir(),f"zkstrap_audio_{os.getpid()}_{uuid.uuid4().hex}.stop")
            try:
                if os.path.exists(stop_file): os.remove(stop_file)
            except Exception: pass
            flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if os.name=="nt" else 0
            self._music_proc=subprocess.Popen(self._helper_command(path,stop_file),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,close_fds=True)
            self._music_stop_file=stop_file
            _startup_log(f"AUDIO: helper fallback started pid={getattr(self._music_proc,'pid',None)}")
            return True
        except Exception as exc:
            self._music_proc=None; self._music_stop_file=None
            _startup_log("AUDIO: helper fallback failed "+repr(exc)); return False

    def start_music(self, force_restart=False):
        if not (self.enabled and self.music_enabled) or os.name != "nt": return False
        path=self.path("ambient")
        if not path or not os.path.isfile(path):
            _startup_log(f"AUDIO: ambient missing for pack {self.pack!r}"); return False
        if float(getattr(self,"music_volume",0.22)) <= 0.001:
            self.stop_music(); return False
        if force_restart: self.stop_music()
        path=self._scaled_music_path(path)
        if self._mci_active: return True
        try:
            if self._music_proc is not None and self._music_proc.poll() is None: return True
        except Exception: self._music_proc=None
        if self._start_music_mci(path): return True
        return self._start_music_helper(path)

    def stop_music(self):
        if self._mci_active:
            try: self._mci(f"stop {self._mci_alias}")
            except Exception: pass
            try: self._mci(f"close {self._mci_alias}")
            except Exception: pass
            self._mci_active=False
        stop_file=self._music_stop_file; proc=self._music_proc
        self._music_stop_file=None; self._music_proc=None
        try:
            if stop_file:
                with open(stop_file,"w",encoding="utf-8") as f: f.write("stop")
        except Exception: pass
        try:
            if proc is not None and proc.poll() is None: proc.wait(timeout=.7)
        except Exception:
            try: proc.terminate()
            except Exception: pass
        try:
            if stop_file and os.path.exists(stop_file): os.remove(stop_file)
        except Exception: pass
        temp=self._scaled_music_temp; self._scaled_music_temp=None
        try:
            if temp and os.path.isfile(temp): os.remove(temp)
        except Exception: pass

    def set_enabled(self, enabled):
        self.enabled=bool(enabled)
        if self.enabled and self.music_enabled: self.start_music(force_restart=True)
        elif not self.enabled: self.stop_music()

    def set_pack(self, pack):
        if pack not in AUDIO_PACKS: return
        changed=(pack!=self.pack); self.pack=pack
        if changed and self.enabled and self.music_enabled: self.start_music(force_restart=True)

    def set_music_enabled(self, enabled):
        self.music_enabled=bool(enabled)
        if self.enabled and self.music_enabled: self.start_music(force_restart=True)
        else: self.stop_music()

    def set_sfx_enabled(self, enabled): self.sfx_enabled=bool(enabled)

    def set_sfx_volume(self, value):
        try: self.sfx_volume=max(0.0,min(1.5,float(value)))
        except Exception: self.sfx_volume=1.0
        # Descarta somente renders antigos; o próximo clique gera a variante nova.
        old=list(self._scaled_sfx_cache.values()); self._scaled_sfx_cache={}
        for temp_path in old:
            try:
                if temp_path and os.path.isfile(temp_path): os.remove(temp_path)
            except Exception: pass

    def set_music_volume(self, value, restart=True):
        try: self.music_volume=max(0.0,min(0.65,float(value)))
        except Exception: self.music_volume=0.22
        if restart and self.enabled and self.music_enabled:
            self.start_music(force_restart=True)

    def shutdown(self):
        self.stop_music()
        for temp_path in list(getattr(self,"_scaled_sfx_cache",{}).values()):
            try:
                if temp_path and os.path.isfile(temp_path): os.remove(temp_path)
            except Exception: pass
        self._scaled_sfx_cache={}

def _detached_splash_report(progress, main="", sub="", term=""):
    path = _DETACHED_SPLASH_STATUS_FILE
    if not path:
        return
    try:
        payload = {
            "progress": max(0.0, min(1.0, float(progress))),
            "main": str(main or ""),
            "sub": str(sub or ""),
            "term": str(term or ""),
            "time": time.time(),
        }
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass

def _splash_cancel_requested():
    path = _DETACHED_SPLASH_CANCEL_FILE
    return bool(path and os.path.exists(path))

def _raise_if_splash_cancelled():
    if _splash_cancel_requested():
        raise StartupCancelled("Inicialização cancelada na splash")


# FastFlags locais aceitas pelo cliente conforme a allowlist pública do Roblox.
# A lista pode mudar; flags fora dela são ignoradas pelo app por padrão.
ROBLOX_LOCAL_FFLAG_ALLOWLIST = {
    "DFIntCSGLevelOfDetailSwitchingDistance",
    "DFIntCSGLevelOfDetailSwitchingDistanceL12",
    "DFIntCSGLevelOfDetailSwitchingDistanceL23",
    "DFIntCSGLevelOfDetailSwitchingDistanceL34",
    "FFlagHandleAltEnterFullscreenManually",
    "DFFlagTextureQualityOverrideEnabled",
    "DFIntTextureQualityOverride",
    "FIntDebugForceMSAASamples",
    "DFFlagDisableDPIScale",
    "FFlagDebugGraphicsPreferD3D11",
    "FFlagDebugGraphicsPreferVulkan",
    "FFlagDebugGraphicsPreferOpenGL",
    "FFlagDebugSkyGray",
    "DFFlagDebugPauseVoxelizer",
    "DFIntDebugFRMQualityLevelOverride",
    "FIntFRMMaxGrassDistance",
    "FIntFRMMinGrassDistance",
    "FIntGrassMovementReducedMotionFactor",
}

FLAG_MODULES = {
    "base": {
        "pt": "Pack Base / Whitelist",
        "en": "Base Pack / Whitelist",
        "tooltip_pt": "Pack base de compatibilidade e desempenho usando apenas flags locais conhecidas.",
        "tooltip_en": "Base compatibility/performance pack using only known local flags.",
        "flags": {
            "DFFlagTextureQualityOverrideEnabled": True,
            "DFIntDebugFRMQualityLevelOverride": 1,
            "FIntDebugForceMSAASamples": 0,
            "FFlagDebugGraphicsPreferD3D11": True,
        },
    },
    "textures": {
        "pt": "Texturas no mínimo",
        "en": "Minimum textures",
        "tooltip_pt": "Força o nível de textura para 0. Útil para reduzir uso de VRAM e deixar o visual mais simples.",
        "tooltip_en": "Forces texture level 0 to reduce VRAM use and simplify visuals.",
        "flags": {
            "DFFlagTextureQualityOverrideEnabled": True,
            "DFIntTextureQualityOverride": 0,
        },
    },
    "grass": {
        "pt": "Grama no mínimo",
        "en": "Minimum grass",
        "tooltip_pt": "Reduz a distância e movimento da grama do terreno.",
        "tooltip_en": "Reduces terrain grass distance and motion.",
        "flags": {
            "FIntFRMMaxGrassDistance": 0,
            "FIntFRMMinGrassDistance": 0,
            "FIntGrassMovementReducedMotionFactor": 100,
        },
    },
    "msaa": {
        "pt": "Anti-aliasing desligado",
        "en": "Anti-aliasing off",
        "tooltip_pt": "Define MSAA como 0 para reduzir custo de suavização de bordas.",
        "tooltip_en": "Sets MSAA to 0 to reduce edge-smoothing cost.",
        "flags": {"FIntDebugForceMSAASamples": 0},
    },
    "lod": {
        "pt": "LOD / geometria no mínimo",
        "en": "Minimum LOD / geometry",
        "tooltip_pt": "Reduz as distâncias de troca de detalhe CSG para priorizar desempenho.",
        "tooltip_en": "Reduces CSG detail switching distances to prioritize performance.",
        "flags": {
            "DFIntCSGLevelOfDetailSwitchingDistance": 0,
            "DFIntCSGLevelOfDetailSwitchingDistanceL12": 0,
            "DFIntCSGLevelOfDetailSwitchingDistanceL23": 0,
            "DFIntCSGLevelOfDetailSwitchingDistanceL34": 0,
        },
    },
    "frm_low": {
        "pt": "Qualidade 3D mínima",
        "en": "Minimum 3D quality",
        "tooltip_pt": "Força o nível FRM de qualidade para 1.",
        "tooltip_en": "Forces FRM graphics quality level to 1.",
        "flags": {"DFIntDebugFRMQualityLevelOverride": 1},
    },
    "gray_sky": {
        "pt": "Céu cinza",
        "en": "Gray sky",
        "tooltip_pt": "Usa a flag de céu cinza. O efeito depende do céu usado pelo jogo.",
        "tooltip_en": "Uses the gray-sky flag. The visible effect depends on the game's sky.",
        "flags": {"FFlagDebugSkyGray": True},
    },
    "voxelizer": {
        "pt": "Pausar voxelizer",
        "en": "Pause voxelizer",
        "tooltip_pt": "Pausa atualizações do voxelizer de iluminação quando suportado pelo cliente.",
        "tooltip_en": "Pauses lighting voxelizer updates when supported by the client.",
        "flags": {"DFFlagDebugPauseVoxelizer": True},
    },
    "d3d11": {
        "pt": "Forçar Direct3D 11",
        "en": "Force Direct3D 11",
        "tooltip_pt": "Prioriza Direct3D 11 e desativa preferência por Vulkan/OpenGL nas flags locais.",
        "tooltip_en": "Prefers Direct3D 11 and disables Vulkan/OpenGL preference in local flags.",
        "flags": {
            "FFlagDebugGraphicsPreferD3D11": True,
            "FFlagDebugGraphicsPreferVulkan": False,
            "FFlagDebugGraphicsPreferOpenGL": False,
        },
    },
    "dpi": {
        "pt": "Desativar DPI Scale",
        "en": "Disable DPI scale",
        "tooltip_pt": "Desativa a escala DPI do renderizador. Pode alterar nitidez/tamanho em monitores com escala do Windows.",
        "tooltip_en": "Disables renderer DPI scaling. It can change sharpness/size on Windows-scaled displays.",
        "flags": {"DFFlagDisableDPIScale": True},
    },
}


# Perfil gráfico agressivo usando somente controles locais que já existem nos módulos acima.
# Ele não tenta contornar a allowlist do cliente e o JSON personalizado continua tendo prioridade.
BATATA_TOTAL_FLAGS = {}
for _batata_key in ("textures", "grass", "msaa", "lod", "frm_low", "gray_sky", "voxelizer", "d3d11"):
    BATATA_TOTAL_FLAGS.update(FLAG_MODULES[_batata_key]["flags"])

FLAG_MODULES["batata_total"] = {
    "pt": "BATATA TOTAL (agressivo)",
    "en": "TOTAL POTATO (aggressive)",
    "tooltip_pt": "Combina textura mínima, MSAA 0, qualidade 3D 1, grama/LOD mínimos, céu cinza, voxelizer pausado e D3D11. Pode deixar o visual bem feio; JSON personalizado ainda sobrescreve valores conflitantes.",
    "tooltip_en": "Combines minimum textures, MSAA 0, 3D quality 1, minimum grass/LOD, gray sky, paused voxelizer and D3D11. Visuals may look very rough; custom JSON still overrides conflicting values.",
    "flags": BATATA_TOTAL_FLAGS,
}


# Packs enviados pela comunidade. Eles são gravados exatamente no ClientAppSettings,
# mas muitas dessas chaves NÃO pertencem à allowlist local atual do Roblox e podem ser ignoradas.
TELEMETRY_OFF_FLAGS = {
    "DFFlagBrowserTrackerIdTelemetryEnabled": False,
    "DFFlagDSTelemetryEnableMetricRecorder": False,
    "DFFlagEmitSafetyTelemetryInCallbackEnable": False,
    "DFFlagEnableCppSoundTelemetry6": False,
    "DFFlagEnablePerfDataGatherTelemetry2": False,
    "DFFlagEnableTelemetryV2FRMStats": False,
    "DFFlagRccLoadSoundLengthTelemetryEnabled": False,
    "DFFlagWindowsWebViewTelemetryEnabled": False,
    "FFlagEnableAvatarFacechatReplOverRCCTelemetry": False,
    "FFlagEnableClickToMoveUsageTelemetry2": False,
    "FFlagEnableLogCullingTelemetryForControl": False,
    "FFlagEnableMessageBusUnSubscribeErrorTelemetry": False,
    "FFlagEnableServiceInitBreakdownTelemetry": False,
    "FFlagEnableSoundSessionTelemetry5": False,
    "FFlagEnableTelemetryProtocol": False,
    "FFlagEnableTelemetryService1": False,
    "FFlagEnableTelemetryServiceMemoryCPUInfo": False,
    "FFlagEnableTelemetryServicePlaySessionInfo": False,
    "FFlagEnableVRComfortSettingsTelemetry": False,
    "FFlagOpenTelemetryEnabled2": False,
    "FFlagOpenTelemetryUseOtlpExportingEnabled": False,
    "FFlagSimCSGV3EnableMemoryTelemetry": False,
    "FFlagSimCSGV3EnableSpeedMemoryTelemetry": False,
    "FFlagSimStepPhysicsEnableTelemetry": False,
    "FFlagVoiceChatCullingEnableStaleSubsTelemetry": False,
    "FFlagVoiceChatCustomAudioDeviceEnableNeedMorePlayoutTelemetry3": False,
    "FFlagVoiceChatRobloxAudioDeviceUpdateRecordedBufferTelemetryEnabled": False,
    "DFFlagDebugDisableTelemetryAfterTest": True,
    "DFFlagDisableFastLogTelemetry": True,
    "DFFlagEnableQualityResetSessionTracking": False,
    "FFlagEnableAffiliateLinksAuthenticatedVisitTracking": False,
    "FFlagEnableAffiliateLinksQualifiedSignUpTracking": False,
    "FFlagEnableExperienceMenuSessionTracking": False,
    "FFlagEnableLastLoginMethodTracking": False,
    "FFlagDisableMemoryTracking": True,
    "FFlagDisableStreamingTunableMemoryTracking": True,
    "DFFlagCLI_147010_ReportAttributesWithHangTelemetry2": False,
    "DFFlagReportAssetRequestV1Telemetry": False,
    "DFFlagReportAssetRequestV2Telemetry": False,
    "DFFlagReportLegacyFRMStatsToTelemetryV2": False,
    "DFFlagReportMemoryStatsToTelemetryV2": False,
    "DFFlagReportRenderDistanceTelemetry": False,
    "DFFlagReportReplicatorStatsToTelemetryV22": False,
    "FFlagReportFRMGPUFrameTimeTelemetryInPerfdata": False,
    "FFlagReportMeshesUploadTelemetry": False,
    "FFlagReportRenderDistanceTelemetry": False,
    "DFIntPerformanceControlEventBasedTelemetryEffectPredictionEventNumReportsPerSecond": 0,
    "DFIntPerformanceControlEventBasedTelemetryTunableChangeEventNumReportsPerSecond": 0,
    "DFIntServerReportRakNetBandwidthTelemetryHundredthsPercentage": 0,
    "DFStringAltHttpPointsReporterUrl": None,
    "DFStringHttpPointsReporterUrl": None,
    "DFStringTelemetryV2Url": None,
    "FStringTencentAuthPath": None,
    "DFFlagPolicyServiceReportIsNotSubjectToChinaPolicies": True,
    "DFFlagPolicyServiceReportDetailIsNotSubjectToChinaPolicies": True,
    "DFIntPolicyServiceReportDetailIsNotSubjectToChinaPoliciesHundredthsPercentage": 0,
    "FStringDevPublishChinaRequirementsLink": None,
    "DFFlagReportOutputDeviceWithRobloxTelemetry": False,
    "DFIntReportDeviceInfoRate": 0,
    "DFIntReportOutputDeviceInfoEventRateHundredthsPercentage": 0,
    "DFIntReportOutputDeviceInfoRateHundredthsPercentage": 0,
    "DFIntReportRecordingDeviceInfoEventRateHundredthsPercentage": 0,
    "DFIntReportRecordingDeviceInfoRateHundredthsPercentage": 0,
    "FFlagCrashpadReportVendorDeviceFLevelQLevelWindows": False,
    "FFlagLoadAndReportDeviceBTIDCookie": False,
    "FIntReportDeviceInfoRollout": 0,
    "FIntProfileTelemetryTickRateMs": 2147483647,
    "DFIntAnimatorTelemetryCollectionRate": 0,
    "DFIntPerformanceControlEventBasedTelemetryEffectPredictionEventRatePoints": 0,
    "DFIntPerformanceControlEventBasedTelemetryTunableChangeEventRatePoints": 0,
    "FIntOpenTelemetrySampleRateHundredthPercent": 0,
    "DFIntTrackerTelemetryEventRate": 0,
    "DFFlagRobloxTelemetryReliabilityCounterRefactor2": False,
    "DFStringRobloxTelemetryReliabilityCountAllowList": None,
}

MICRO_OPT_STATIC_FLAGS = {
    "DFFlagTeleportClientAssetPreloadingDoingExperiment2": True,
    "DFFlagTeleportClientAssetPreloadingEnabledIXP2": True,
    "DFFlagNextGenRepRollbackOverbudgetPackets": True,
    "DFFlagTeleportClientAssetPreloadingEnabled9": True,
    "FFlagDebugNextGenReplicatorEnabledWriteCFrameColor": True,
    "FFlagFixTextureCompositorFramebufferManagement2": True,
    "FFlagUserCameraControlLastInputTypeUpdate": True,
    "FFlagRenderDynamicResolutionScale9": True,
    "FFlagGraphicsEnableD3D10Compute": True,
    "FFlagDebugRenderCollectGpuCounters": True,
    "FFlagRenderSkipReadingShaderData": True,
    "FFlagSimEnableDCD16": True,
    "FFlagTouchscreenSupport": True,
    "FFlagNewCameraControls_SpeedAdjustEnum": False,
    "FFlagReportGpuLimitedToPerfControl": False,
    "FFlagAdServiceEnabled": False,
    "DFIntTeleportClientAssetPreloadingHundredthsPercentage2": 1000,
    "DFIntGraphicsOptimizationModeFRMFrameRateTarget": 144,
    "DFIntPerformanceControlReportingPeriodInMs": 700,
    "DFIntDebugPerformanceControlFrameTime": 2,
    "DFIntFrameRateMSToReduceTouchEvents": 30,
    "DFIntPerformanceControlFrameTimeMax": 4,
    "DFIntNumAssetsMaxToPreload": 9999999,
    "DFIntMaxFrameBufferSize": 4,
    # Estes valores são substituídos automaticamente pela contagem de processadores lógicos do PC.
    "DFIntRuntimeConcurrency": 1,
    "DFIntMegaReplicatorNumParallelTasks": 1,
    "DFIntNetworkClusterPacketCacheNumParallelTasks": 1,
    "DFIntReplicationDataCacheNumParallelTasks": 1,
    "DFIntTaskSchedulerJobInGameThreads": 1,
    "DFIntTaskSchedulerJobInitThreads": 1,
    "FIntEnableCullableScene2HundredthPercent3": 1000,
    "FIntLuaGcParallelMinMultiTasks": 1,
    "FIntSmoothClusterTaskQueueMaxParallelTasks": 1,
    "FIntTaskSchedulerAutoThreadLimit": 1,
}

MICRO_THREAD_KEYS = {
    "DFIntRuntimeConcurrency",
    "DFIntMegaReplicatorNumParallelTasks",
    "DFIntNetworkClusterPacketCacheNumParallelTasks",
    "DFIntReplicationDataCacheNumParallelTasks",
    "DFIntTaskSchedulerJobInGameThreads",
    "DFIntTaskSchedulerJobInitThreads",
    "FIntLuaGcParallelMinMultiTasks",
    "FIntSmoothClusterTaskQueueMaxParallelTasks",
    "FIntTaskSchedulerAutoThreadLimit",
}

FLAG_MODULES.update({
    "telemetry_off": {
        "pt": "Desativar telemetria (experimental)",
        "en": "Disable telemetry (experimental)",
        "tooltip_pt": "Pack comunitário de telemetria. Grava todas as chaves fornecidas, mas o Roblox pode ignorar flags fora da allowlist e alguns recursos podem ser afetados.",
        "tooltip_en": "Community telemetry pack. Writes all supplied keys, but Roblox may ignore flags outside the allowlist and some features can be affected.",
        "flags": TELEMETRY_OFF_FLAGS,
    },
    "draco_aura": {
        "pt": "Draco V4: reduzir aura (experimental)",
        "en": "Draco V4: reduce aura (experimental)",
        "tooltip_pt": "Aplica DFIntRemoteEventSingleInvocationSizeLimit=2900 exatamente como enviado pela comunidade. Não há garantia de que essa flag controle a aura e ela pode afetar outros RemoteEvents.",
        "tooltip_en": "Applies DFIntRemoteEventSingleInvocationSizeLimit=2900 exactly as supplied by the community. It is not guaranteed to control the aura and can affect other RemoteEvents.",
        "flags": {"DFIntRemoteEventSingleInvocationSizeLimit": 2900},
    },
    "micro_opt": {
        "pt": "Micro-otimização CPU/FPS (experimental)",
        "en": "CPU/FPS micro-optimization (experimental)",
        "tooltip_pt": "Pack do print/Discord. Threads são ajustadas automaticamente para os processadores lógicos do PC e o alvo de FPS é escolhido na aba DESEMPENHO. Muitas chaves podem ser ignoradas pela allowlist atual.",
        "tooltip_en": "Community Discord pack. Thread values are set automatically to the PC logical processor count and FPS target is selected in PERFORMANCE. Many keys can be ignored by the current allowlist.",
        "flags": MICRO_OPT_STATIC_FLAGS,
    },
})


# Módulos principais expostos na interface moderna. Os módulos menores antigos continuam
# definidos acima apenas para migração, mas não poluem mais a navegação.
PERFORMANCE_BOOST_FLAGS = dict(BATATA_TOTAL_FLAGS)
PERFORMANCE_BOOST_FLAGS.pop("FFlagDebugSkyGray", None)
PERFORMANCE_BOOST_FLAGS.update(FLAG_MODULES["base"]["flags"])

FLAG_MODULES.update({
    "performance_boost": {
        "pt": "FPS / Gráficos no mínimo",
        "en": "FPS / Minimum graphics",
        "tooltip_pt": "Junta textura mínima, MSAA 0, grama/LOD mínimos, FRM baixo, voxelizer e D3D11 em um único botão. O céu cinza agora é opcional e separado.",
        "tooltip_en": "Combines minimum textures, MSAA 0, minimum grass/LOD, low FRM, voxelizer and D3D11 in one switch. Gray sky is now optional and separate.",
        "flags": PERFORMANCE_BOOST_FLAGS,
    },
    "fps_unlock": {
        "pt": "Desbloquear / elevar limite de FPS (experimental)",
        "en": "Unlock / raise FPS limit (experimental)",
        "tooltip_pt": "Grava os alvos de FPS escolhidos. O cliente atual pode ignorar algumas FastFlags fora da allowlist.",
        "tooltip_en": "Writes the selected FPS targets. The current client may ignore FastFlags outside the allowlist.",
        "flags": {},
    },
    "ping_boost": {
        "pt": "Otimizar rede / ping (experimental)",
        "en": "Optimize network / ping (experimental)",
        "tooltip_pt": "Pack legado de rede. Não promete reduzir o ping físico da sua conexão e várias flags podem ser ignoradas pelo cliente atual.",
        "tooltip_en": "Legacy network pack. It cannot reduce the physical latency of your connection and several flags may be ignored by the current client.",
        "flags": {},
    },
})

MAIN_MODULE_KEYS = (
    "performance_boost", "gray_sky", "fps_unlock", "ping_boost",
    "telemetry_off", "micro_opt", "draco_aura"
)

# Mantido apenas para compatibilidade com configs antigas; a v2.3 não usa presets gráficos.
PERFORMANCE_PRESETS = {"Padrão": {}}
ADVANCED_MANAGED_KEYS = {
    "DFFlagTextureQualityOverrideEnabled", "DFIntTextureQualityOverride",
    "FIntDebugForceMSAASamples", "DFIntDebugFRMQualityLevelOverride",
    "FIntFRMMaxGrassDistance", "FIntFRMMinGrassDistance",
    "DFIntCSGLevelOfDetailSwitchingDistance", "DFIntCSGLevelOfDetailSwitchingDistanceL12",
    "DFIntCSGLevelOfDetailSwitchingDistanceL23", "DFIntCSGLevelOfDetailSwitchingDistanceL34",
}



def show_startup_error(exc):
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        with open("teste_error.log", "w", encoding="utf-8") as f:
            f.write(tb)
    except:
        pass
    try:
        root = Tk()
        root.withdraw()
        messagebox.showerror("Erro ao iniciar", f"O app encontrou um erro na inicialização.\nTraceback salvo em teste_error.log\n\nPrimeiras linhas:\n{tb[:1500]}")
        root.destroy()
    except:
        print(tb)

def get_splash_title():
    return "◈ ZKSTRAP"

def get_splash_assets():
    return [
        "zkstrap_core", "gfx_pack", "net_tuner", "graphics_core", "ui_skin",
        "audio_opt", "tile_cache", "mem_guard", "render_prefab", "dx11_patch"
    ]

def show_splash_screen(duration=3.0, status_file=None, cancel_file=None):
    """Splash nativa do ZKStrap: UI montada no Canvas; só o logo é carregado como asset."""
    splash = None
    try:
        from PIL import Image, ImageTk

        BASE_W, BASE_H = 1180, 670
        splash = ctk.CTk()
        splash.overrideredirect(True)
        splash.configure(fg_color="#05020A")
        try:
            splash.attributes("-alpha", 0.0)
        except Exception:
            pass

        sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
        scale = min(1.0, (sw - 44) / BASE_W, (sh - 44) / BASE_H)
        scale = max(0.68, scale)
        W, H = int(BASE_W * scale), int(BASE_H * scale)
        splash.geometry(f"{W}x{H}+{max(0,(sw-W)//2)}+{max(0,(sh-H)//2)}")

        canvas = Canvas(splash, width=W, height=H, bg="#05020A", highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        _boot_play_sound("splash")
        _splash_audio_step=[-1]

        def S(v): return int(round(v * scale))

        def rounded_rect(x1, y1, x2, y2, radius, **kwargs):
            r = max(2, int(radius))
            pts = [
                x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
                x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
                x1, y2, x1, y2-r, x1, y1+r, x1, y1
            ]
            return canvas.create_polygon(pts, smooth=True, splinesteps=24, **kwargs)

        # Base + borda em camadas para dar profundidade sem usar uma imagem da tela inteira.
        canvas.create_rectangle(0, 0, W, H, fill="#05020A", outline="")
        for inset, color, width in [(25, "#271033", 1), (27, "#61118D", 1), (29, "#B217F4", 1)]:
            rounded_rect(S(inset), S(inset), W-S(inset), H-S(inset), S(24), fill="", outline=color, width=max(1,S(width)))
        rounded_rect(S(31), S(31), W-S(31), H-S(31), S(22), fill="#08060E", outline="#120B1B", width=1)

        # Grid técnico discreto, restrito ao lado esquerdo.
        for gx in range(72, 472, 34):
            canvas.create_line(S(gx), S(90), S(gx), S(515), fill="#100A18")
        for gy in range(90, 516, 34):
            canvas.create_line(S(72), S(gy), S(472), S(gy), fill="#100A18")

        # Divisor.
        canvas.create_line(S(500), S(74), S(500), S(603), fill="#4C1D6F", width=max(1,S(1)))

        # Cabeçalho esquerdo.
        canvas.create_text(S(78), S(76), text="BUILD A\nBETTER\nEXPERIENCE", anchor="nw", justify="left",
                           fill="#9B6FE8", font=("Segoe UI", max(8,S(9)), "bold"))
        canvas.create_text(S(440), S(75), text="EST.\n2023", anchor="ne", justify="right",
                           fill="#80649D", font=("Consolas", max(7,S(8)), "bold"))

        # Orbitas do logo.
        cx, cy = S(272), S(288)
        r_outer, r_mid = S(154), S(130)
        canvas.create_oval(cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer, outline="#342047", width=max(1,S(1)))
        canvas.create_oval(cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid, outline="#4E2370", width=max(1,S(1)))
        arc1 = canvas.create_arc(cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer, start=15, extent=92,
                                 style="arc", outline="#C12AFF", width=max(1,S(3)))
        arc2 = canvas.create_arc(cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid, start=205, extent=62,
                                 style="arc", outline="#7626C9", width=max(1,S(2)))

        node_ids=[]
        for px, py in [(272,134),(272,442),(118,288),(426,288),(163,179),(381,397)]:
            rr=S(5)
            node_ids.append(canvas.create_rectangle(S(px)-rr,S(py)-rr,S(px)+rr,S(py)+rr,
                                                    fill="#A725E3", outline="#D471FF", width=max(1,S(1))))

        # Só o logo é um asset; o restante da splash é UI real.
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "zkstrap_icon.png")
        logo_photo = None
        if os.path.exists(icon_path):
            icon = Image.open(icon_path).convert("RGBA")
            logo_size = S(230)
            icon = icon.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(icon)
            canvas.create_image(cx, cy, image=logo_photo, anchor="center")
            splash._zk_logo_photo = logo_photo
        else:
            rounded_rect(S(165),S(181),S(379),S(395),S(30),fill="#0D0715",outline="#B217F4",width=max(1,S(3)))
            canvas.create_text(cx,cy,text="ZK",fill="#C22BFF",font=("Segoe UI",max(34,S(52)),"bold"))

        canvas.create_text(cx, S(468), text="SIGNATURE CORE", anchor="center", fill="#C376FF",
                           font=("Segoe UI", max(10,S(15)), "bold"))
        canvas.create_text(cx, S(493), text="Performance  •  Visual  •  Assets", anchor="center", fill="#82758F",
                           font=("Segoe UI", max(8,S(10))))

        # Rodapé esquerdo.
        chip_x, chip_y = S(79), S(565)
        canvas.create_rectangle(chip_x, chip_y, chip_x+S(22), chip_y+S(22), outline="#B217F4", width=max(1,S(2)))
        for off in (4,10,16):
            canvas.create_line(chip_x-S(5), chip_y+S(off), chip_x, chip_y+S(off), fill="#B217F4")
            canvas.create_line(chip_x+S(22), chip_y+S(off), chip_x+S(27), chip_y+S(off), fill="#B217F4")
            canvas.create_line(chip_x+S(off), chip_y-S(5), chip_x+S(off), chip_y, fill="#B217F4")
            canvas.create_line(chip_x+S(off), chip_y+S(22), chip_x+S(off), chip_y+S(27), fill="#B217F4")
        canvas.create_text(S(118), S(562), text="OPTIMIZE\nCUSTOMIZE\nPLAY FURTHER", anchor="nw", justify="left",
                           fill="#9D73D8", font=("Segoe UI", max(7,S(9)), "bold"))
        canvas.create_text(S(435), S(566), text="ZKSTRAP\nCORE ENGINE", anchor="ne", justify="right",
                           fill="#756986", font=("Consolas", max(7,S(8)), "bold"))

        # Cabeçalho direito.
        canvas.create_text(S(546), S(73), text="ZK", anchor="nw", fill="#B217F4",
                           font=("Segoe UI", max(28,S(46)), "bold"))
        canvas.create_text(S(641), S(73), text="STRAP", anchor="nw", fill="#F6F2FA",
                           font=("Segoe UI", max(28,S(46)), "bold"))
        canvas.create_text(S(548), S(143), text="ROBLOX CLIENT CONFIGURATOR  •  LOCAL MODE", anchor="nw",
                           fill="#A467E2", font=("Segoe UI", max(8,S(11)), "bold"))
        rounded_rect(S(999),S(77),S(1117),S(115),S(10),fill="#120819",outline="#B217F4",width=max(1,S(2)))
        canvas.create_text(S(1058),S(96),text=f"BUILD {APP_VERSION}",anchor="center",fill="#F2E9F8",
                           font=("Segoe UI",max(8,S(11)),"bold"))
        # Controles reais da splash (a versão anterior só desenhava os símbolos).
        min_tag="zk_splash_min"; close_tag="zk_splash_close"; min_text="zk_splash_min_text"; close_text="zk_splash_close_text"
        canvas.create_rectangle(S(1062),S(37),S(1092),S(66),fill="#08060E",outline="",tags=(min_tag,))
        canvas.create_text(S(1077),S(51),text="—",anchor="center",fill="#CDBAE0",font=("Segoe UI",max(10,S(14))),tags=(min_tag,min_text))
        canvas.create_rectangle(S(1095),S(37),S(1125),S(66),fill="#08060E",outline="",tags=(close_tag,))
        canvas.create_text(S(1110),S(51),text="×",anchor="center",fill="#CDBAE0",font=("Segoe UI",max(10,S(15))),tags=(close_tag,close_text))

        def _signal_cancel_and_close():
            if cancel_file:
                try:
                    with open(cancel_file,"w",encoding="utf-8") as f: f.write("cancel")
                except Exception:
                    pass
            try: splash.destroy()
            except Exception: pass

        def _restore_override(event=None):
            try:
                splash.after(80, lambda: (splash.overrideredirect(True), splash.lift()))
            except Exception:
                pass

        def _minimize_splash():
            try:
                # Override-redirect puro não minimiza direito no Windows. Libera o
                # window manager só durante a minimização e restaura ao voltar.
                splash.overrideredirect(False)
                splash.iconify()
            except Exception:
                try: splash.withdraw()
                except Exception: pass

        canvas.tag_bind(min_tag,"<Button-1>",lambda e:_minimize_splash())
        canvas.tag_bind(close_tag,"<Button-1>",lambda e:_signal_cancel_and_close())
        canvas.tag_bind(min_tag,"<Enter>",lambda e:canvas.itemconfigure(min_text,fill="#FFFFFF"))
        canvas.tag_bind(close_tag,"<Enter>",lambda e:canvas.itemconfigure(close_text,fill="#FF6175"))
        canvas.tag_bind(min_tag,"<Leave>",lambda e:canvas.itemconfigure(min_text,fill="#CDBAE0"))
        canvas.tag_bind(close_tag,"<Leave>",lambda e:canvas.itemconfigure(close_text,fill="#CDBAE0"))
        splash.bind("<Map>",_restore_override,add="+")
        splash.protocol("WM_DELETE_WINDOW",_signal_cancel_and_close)

        canvas.create_text(S(548),S(188),text="PREPARANDO SEU AMBIENTE",anchor="nw",fill="#F7F3FA",
                           font=("Segoe UI",max(15,S(21)),"bold"))
        canvas.create_text(S(548),S(221),text="Inicializando os módulos do ZKStrap com segurança.",anchor="nw",fill="#998CAA",
                           font=("Segoe UI",max(9,S(12))))

        # Cards de módulos.
        module_specs=[
            ("CLIENT","ClientSettings","CFG"),
            ("GRAPHICS","FPS & render","FPS"),
            ("ASSETS","Cursor & fonts","AST"),
            ("SYSTEM","Watchdog & UI","SYS"),
        ]
        module_boxes=[]
        positions=[(548,258),(837,258),(548,356),(837,356)]
        for idx,(title,desc,short) in enumerate(module_specs):
            x,y=positions[idx]
            box=rounded_rect(S(x),S(y),S(x+267),S(y+80),S(12),fill="#0C0912",outline="#30203F",width=max(1,S(1)))
            dot=canvas.create_oval(S(x+16),S(y+24),S(x+42),S(y+50),fill="#0C0912",outline="#51415F",width=max(1,S(2)))
            tick=canvas.create_text(S(x+29),S(y+37),text="",fill="#09060D",font=("Segoe UI",max(8,S(10)),"bold"))
            title_id=canvas.create_text(S(x+58),S(y+25),text=title,anchor="nw",fill="#F1EBF5",font=("Segoe UI",max(10,S(13)),"bold"))
            desc_id=canvas.create_text(S(x+58),S(y+49),text=desc,anchor="nw",fill="#8E819B",font=("Segoe UI",max(8,S(10))))
            tag=rounded_rect(S(x+220),S(y+22),S(x+250),S(y+51),S(8),fill="#120C19",outline="#3A2550",width=1)
            tagtxt=canvas.create_text(S(x+235),S(y+36),text=short,anchor="center",fill="#8765A8",font=("Consolas",max(7,S(8)),"bold"))
            module_boxes.append((box,dot,tick,title_id,desc_id,tag,tagtxt))

        # Status: separado dos badges para nada se sobrepor em resoluções menores.
        rounded_rect(S(548),S(467),S(1104),S(558),S(14),fill="#090710",outline="#2C2038",width=max(1,S(1)))
        status_id=canvas.create_text(S(572),S(487),text="Inicializando ZKStrap…",anchor="nw",fill="#F8F4FA",
                                     font=("Segoe UI",max(12,S(16)),"bold"))
        sub_id=canvas.create_text(S(572),S(516),text="configuração local",anchor="nw",fill="#8E809F",
                                  font=("Segoe UI",max(8,S(10))))
        pct_id=canvas.create_text(S(1078),S(488),text="0%",anchor="ne",fill="#F7F2FA",
                                  font=("Segoe UI",max(13,S(18)),"bold"))
        bx1,by1,bx2,by2=S(572),S(536),S(1078),S(547)
        rounded_rect(bx1,by1,bx2,by2,S(6),fill="#22202C",outline="")
        progress_fill=rounded_rect(bx1,by1,bx1+S(2),by2,S(6),fill="#B217F4",outline="")

        # Badges em uma faixa própria.
        badge_data=[("Void Purple","#8B2CF5"),("Safe startup","#3FD66D"),("Low latency","#FF435B")]
        bx=S(548)
        for label,color in badge_data:
            w=S(112 if label!="Safe startup" else 124)
            rounded_rect(bx,S(581),bx+w,S(613),S(13),fill="#0D0913",outline="#342442",width=max(1,S(1)))
            canvas.create_oval(bx+S(11),S(592),bx+S(20),S(601),fill=color,outline=color)
            canvas.create_text(bx+S(28),S(597),text=label,anchor="w",fill="#B7A8C7",font=("Segoe UI",max(7,S(9))))
            bx+=w+S(9)
        canvas.create_text(S(1103),S(597),text="Inicialização local  •  perfil otimizado",anchor="e",fill="#897C98",
                           font=("Segoe UI",max(7,S(9))))

        stages=[
            (0.00,"Lendo preferências…","configuração local"),
            (0.18,"Preparando cliente Roblox…","ClientSettings e caminhos"),
            (0.40,"Inicializando gráficos…","FPS, render e compatibilidade"),
            (0.60,"Carregando assets…","cursor, fontes e ícones"),
            (0.80,"Validando sistema…","watchdog e interface"),
            (0.96,"Finalizando interface…","quase pronto"),
        ]
        module_thresholds=[0.20,0.43,0.68,0.88]

        def set_module_state(index,state):
            box,dot,tick,title_id,desc_id,tag,tagtxt=module_boxes[index]
            if state=="done":
                canvas.itemconfigure(box,fill="#130D1A",outline="#A42BE8")
                canvas.itemconfigure(dot,fill="#B217F4",outline="#D079FF")
                canvas.itemconfigure(tick,text="✓",fill="#09060D")
                canvas.itemconfigure(title_id,fill="#FFFFFF")
                canvas.itemconfigure(desc_id,fill="#B8A8C9")
                canvas.itemconfigure(tag,fill="#160D20",outline="#74419B")
                canvas.itemconfigure(tagtxt,fill="#C58AFF")
            elif state=="active":
                canvas.itemconfigure(box,fill="#100B17",outline="#7E2BB3")
                canvas.itemconfigure(dot,fill="#0C0912",outline="#B217F4")
                canvas.itemconfigure(tick,text="•",fill="#D99AFF")
                canvas.itemconfigure(title_id,fill="#F9F5FB")
                canvas.itemconfigure(desc_id,fill="#A694B8")
                canvas.itemconfigure(tag,fill="#120C19",outline="#5D3379")
                canvas.itemconfigure(tagtxt,fill="#A980C9")
            else:
                canvas.itemconfigure(box,fill="#0C0912",outline="#30203F")
                canvas.itemconfigure(dot,fill="#0C0912",outline="#51415F")
                canvas.itemconfigure(tick,text="")
                canvas.itemconfigure(title_id,fill="#DCD5E4")
                canvas.itemconfigure(desc_id,fill="#82758F")
                canvas.itemconfigure(tag,fill="#100B15",outline="#342243")
                canvas.itemconfigure(tagtxt,fill="#775D91")

        def _render_progress(q, i, main_override="", sub_override=""):
            # Som discreto apenas nos marcos de 25/50/75/100 quando o usuário já
            # autorizou áudio numa execução anterior.
            try:
                step=min(4,int(max(0.0,min(1.0,q))*4.001))
                if step>_splash_audio_step[0]:
                    if _splash_audio_step[0]>=0: _boot_play_sound("progress")
                    _splash_audio_step[0]=step
            except Exception:
                pass
            stage_idx=0
            for j,(th,_,_) in enumerate(stages):
                if q>=th:
                    stage_idx=j
            _,fallback_main,fallback_secondary=stages[stage_idx]
            main=main_override or fallback_main
            secondary=sub_override or fallback_secondary
            canvas.itemconfigure(status_id,text=main)
            canvas.itemconfigure(sub_id,text=secondary)
            canvas.itemconfigure(pct_id,text=f"{int(round(q*100)):d}%")

            canvas.delete(progress_fill_holder[0])
            fill_x2=bx1+max(S(2),int((bx2-bx1)*q))
            progress_fill_holder[0]=rounded_rect(bx1,by1,fill_x2,by2,S(6),fill="#B217F4",outline="")

            prev=0.0
            for mm,th in enumerate(module_thresholds):
                if q>=th: set_module_state(mm,"done")
                elif q>=prev: set_module_state(mm,"active")
                else: set_module_state(mm,"idle")
                prev=th

            canvas.itemconfigure(arc1,start=(15+i*5)%360)
            canvas.itemconfigure(arc2,start=(205-i*4)%360)
            for n,node in enumerate(node_ids):
                canvas.itemconfigure(node,fill="#D44CFF" if ((i//4)+n)%2==0 else "#7722A7",outline="#F0B3FF" if ((i//4)+n)%2==0 else "#9D53C2")
            try:
                # fade-in apenas; o fade-out acontece depois de mostrar 100%.
                splash.attributes("-alpha", min(1.0, max(.12, q/.08)) if q < .08 else 1.0)
            except Exception:
                pass
            splash.update_idletasks(); splash.update()

        progress_fill_holder=[progress_fill]
        if status_file:
            q=0.0; target=.02; i=0; started=time.time(); done_since=None
            main_text="Inicializando ZKStrap…"; sub_text="aguardando módulos"
            while True:
                if cancel_file and os.path.exists(cancel_file):
                    try: splash.destroy()
                    except Exception: pass
                    return
                try:
                    if os.path.exists(status_file):
                        with open(status_file,"r",encoding="utf-8") as f:
                            payload=json.load(f)
                        target=max(target,max(0.0,min(1.0,float(payload.get("progress",target)))))
                        main_text=str(payload.get("main") or main_text)
                        sub_text=str(payload.get("sub") or sub_text)
                except Exception:
                    pass

                if q < target:
                    # aproximação suave, mas nunca inventa progresso além do que o
                    # processo principal já confirmou.
                    delta=max(.0025,min(.022,(target-q)*.24))
                    q=min(target,q+delta)
                _render_progress(q,i,main_text,sub_text); i+=1

                if target>=.999 and q>=.999:
                    if done_since is None: done_since=time.time()
                    if time.time()-done_since>=.62:
                        break
                if time.time()-started>120:
                    # Segurança visual: continua responsiva, mas não pula para 100%.
                    main_text="Ainda preparando o ZKStrap…"
                    sub_text="aguardando a interface principal"
                time.sleep(.028)
        else:
            steps=max(60,int(duration/0.038))
            for i in range(steps+1):
                q=i/steps
                _render_progress(q,i)
                time.sleep(duration/steps)

        # 100% fica visível antes da troca para a janela principal.
        try:
            canvas.itemconfigure(pct_id,text="100%")
            canvas.itemconfigure(status_id,text="Tudo pronto.")
            canvas.itemconfigure(sub_id,text="Abrindo ZKStrap")
            _boot_play_sound("splash_done")
            splash.update_idletasks(); splash.update()
            time.sleep(.22)
            for a in (.86,.68,.46,.24,.08):
                splash.attributes("-alpha",a); splash.update_idletasks(); splash.update(); time.sleep(.025)
        except Exception:
            pass
        try: splash.destroy()
        except Exception: pass
    except Exception:
        try:
            if splash is not None:
                splash.destroy()
        except Exception:
            pass

TEMAS = {'Matrix Terminal': {'bg': '#000302',
                     'card': '#031008',
                     'card_active': '#082516',
                     'panel': '#010905',
                     'sidebar': '#010704',
                     'icon_bg': '#092014',
                     'accent': '#00F578',
                     'hover': '#43FF9B',
                     'text': '#D8FFE8',
                     'muted': '#639877',
                     'border': '#00C963'},
 'Cyberpunk Neon': {'bg': '#050108',
                    'card': '#150322',
                    'card_active': '#2B0744',
                    'panel': '#0C0214',
                    'sidebar': '#08010E',
                    'icon_bg': '#260534',
                    'accent': '#FF2D95',
                    'hover': '#FF69B7',
                    'text': '#EFFFFF',
                    'muted': '#A781B6',
                    'border': '#22D3EE'},
 'Electric Blue': {'bg': '#01060C',
                   'card': '#061421',
                   'card_active': '#0B2A43',
                   'panel': '#03111D',
                   'sidebar': '#020D17',
                   'icon_bg': '#0B2B43',
                   'accent': '#17C7FF',
                   'hover': '#69DCFF',
                   'text': '#E9FAFF',
                   'muted': '#789DB3',
                   'border': '#38BDF8'},
 'Deep Ocean': {'bg': '#01070A',
                'card': '#061923',
                'card_active': '#0D3343',
                'panel': '#04131B',
                'sidebar': '#031017',
                'icon_bg': '#0B2A38',
                'accent': '#38BDF8',
                'hover': '#7DD3FC',
                'text': '#E6F8FF',
                'muted': '#7999A7',
                'border': '#0EA5E9'},
 'Blood & Bone': {'bg': '#080101',
                  'card': '#1B0708',
                  'card_active': '#3B1013',
                  'panel': '#120405',
                  'sidebar': '#0E0304',
                  'icon_bg': '#300B0D',
                  'accent': '#FF3B45',
                  'hover': '#FF7077',
                  'text': '#FFF0E8',
                  'muted': '#AC7D7D',
                  'border': '#FF535D'},
 'Forest Hacker': {'bg': '#010803',
                   'card': '#071A0C',
                   'card_active': '#12351A',
                   'panel': '#041108',
                   'sidebar': '#030D06',
                   'icon_bg': '#102A16',
                   'accent': '#4DFF72',
                   'hover': '#7CFF96',
                   'text': '#E9FFED',
                   'muted': '#71977A',
                   'border': '#22C55E'},
 'Sunset Synthwave': {'bg': '#160518',
                      'card': '#2A0A31',
                      'card_active': '#4B1355',
                      'panel': '#200727',
                      'sidebar': '#19051E',
                      'icon_bg': '#401047',
                      'accent': '#FFD166',
                      'hover': '#FFE19A',
                      'text': '#FFF3FF',
                      'muted': '#C08BB9',
                      'border': '#FF5ACD'},
 'Void Purple': {'bg': '#05020A',
                 'card': '#12091D',
                 'card_active': '#2A1640',
                 'panel': '#0C0514',
                 'sidebar': '#090411',
                 'icon_bg': '#231135',
                 'accent': '#A855F7',
                 'hover': '#C084FC',
                 'text': '#F7EDFF',
                 'muted': '#A18BB4',
                 'border': '#7C3AED'},
 'Obsidian Gold': {'bg': '#070604',
                   'card': '#171208',
                   'card_active': '#30250D',
                   'panel': '#0E0B06',
                   'sidebar': '#0B0905',
                   'icon_bg': '#261D0B',
                   'accent': '#F6C453',
                   'hover': '#FFE08A',
                   'text': '#FFF7DF',
                   'muted': '#AC9C73',
                   'border': '#D4A72C'},
 'Arctic Glass': {'bg': '#031018',
                  'card': '#081A25',
                  'card_active': '#123449',
                  'panel': '#06151E',
                  'sidebar': '#05121A',
                  'icon_bg': '#103247',
                  'accent': '#67E8F9',
                  'hover': '#B8F6FF',
                  'text': '#EFFDFF',
                  'muted': '#85A8B5',
                  'border': '#38BDF8'},
 'Sakura Night': {'bg': '#0D050B',
                  'card': '#1C0C17',
                  'card_active': '#38172D',
                  'panel': '#140912',
                  'sidebar': '#10070E',
                  'icon_bg': '#311227',
                  'accent': '#FF73B3',
                  'hover': '#FFA0CC',
                  'text': '#FFF1F7',
                  'muted': '#B58EA2',
                  'border': '#F472B6'},
 'Midnight Chrome': {'bg': '#05070A',
                     'card': '#11161C',
                     'card_active': '#202A34',
                     'panel': '#0B0F14',
                     'sidebar': '#090C10',
                     'icon_bg': '#1A222B',
                     'accent': '#CBD5E1',
                     'hover': '#F1F5F9',
                     'text': '#F8FAFC',
                     'muted': '#8793A1',
                     'border': '#64748B'},
 'Inferno Core': {'bg': '#090302',
                  'card': '#1D0A05',
                  'card_active': '#3D1609',
                  'panel': '#140704',
                  'sidebar': '#100503',
                  'icon_bg': '#321006',
                  'accent': '#FF7A1A',
                  'hover': '#FFA45C',
                  'text': '#FFF4E8',
                  'muted': '#B38B72',
                  'border': '#EF4444'},
 'Emerald Glass': {'bg': '#010807',
                   'card': '#071A17',
                   'card_active': '#10362F',
                   'panel': '#041310',
                   'sidebar': '#03100D',
                   'icon_bg': '#0C2C26',
                   'accent': '#34D399',
                   'hover': '#6EE7B7',
                   'text': '#ECFFF8',
                   'muted': '#759B8E',
                   'border': '#2DD4BF'},
 'Clean': {'bg': '#0D1012',
           'card': '#15191C',
           'card_active': '#20262A',
           'panel': '#111518',
           'sidebar': '#101416',
           'icon_bg': '#1D2423',
           'accent': '#A7F3D0',
           'hover': '#D1FAE5',
           'text': '#F4F9F7',
           'muted': '#8C9894',
           'border': '#6EE7B7'},
 'ZKStrap Core': {'bg': '#030207',
                  'card': '#100B18',
                  'card_active': '#1B1228',
                  'panel': '#08060D',
                  'sidebar': '#06040A',
                  'icon_bg': '#171022',
                  'accent': '#A855F7',
                  'hover': '#C084FC',
                  'text': '#FAF7FF',
                  'muted': '#91869D',
                  'border': '#E11D48'},
 'Minecraft': {'bg': '#0E1610',
               'card': '#172219',
               'card_active': '#263A29',
               'panel': '#111B13',
               'sidebar': '#101912',
               'icon_bg': '#2B402E',
               'accent': '#69C04A',
               'hover': '#8ED06F',
               'text': '#F5F0DB',
               'muted': '#9FA58D',
               'border': '#7B5A3A'},
 'Hollow Knight': {'bg': '#05070B',
                   'card': '#0B1017',
                   'card_active': '#151F2B',
                   'panel': '#080C12',
                   'sidebar': '#070A0F',
                   'icon_bg': '#111A24',
                   'accent': '#E8EEF4',
                   'hover': '#FFFFFF',
                   'text': '#F8FBFF',
                   'muted': '#8192A5',
                   'border': '#52708B'},
 'Blox Fruits': {'bg': '#06111C',
                 'card': '#0C2235',
                 'card_active': '#123A58',
                 'panel': '#081A29',
                 'sidebar': '#071724',
                 'icon_bg': '#12324A',
                 'accent': '#4DB8FF',
                 'hover': '#7CCBFF',
                 'text': '#F3FAFF',
                 'muted': '#86A9C1',
                 'border': '#F4C542'},
 'Valorant': {'bg': '#0F1116',
              'card': '#181B22',
              'card_active': '#282D36',
              'panel': '#13161C',
              'sidebar': '#111319',
              'icon_bg': '#242832',
              'accent': '#FF4655',
              'hover': '#FF6B77',
              'text': '#ECE8E1',
              'muted': '#9A9895',
              'border': '#FF4655'},
 'CS GO': {'bg': '#101418',
           'card': '#1A2026',
           'card_active': '#29323A',
           'panel': '#151A1F',
           'sidebar': '#12171B',
           'icon_bg': '#273038',
           'accent': '#F2A900',
           'hover': '#FFC247',
           'text': '#EAEFF2',
           'muted': '#8E9AA3',
           'border': '#64727D'},
 'Terraria': {'bg': '#07131B',
              'card': '#10252D',
              'card_active': '#1C3B3D',
              'panel': '#0B1C22',
              'sidebar': '#091820',
              'icon_bg': '#17342F',
              'accent': '#79D65A',
              'hover': '#A1EA85',
              'text': '#F0F7E7',
              'muted': '#85A393',
              'border': '#4FA8D8'},
 'Celeste': {'bg': '#0B0B22',
             'card': '#171735',
             'card_active': '#292657',
             'panel': '#11112B',
             'sidebar': '#0E0E26',
             'icon_bg': '#25234C',
             'accent': '#FF7CA8',
             'hover': '#FFA3C1',
             'text': '#FFF4FA',
             'muted': '#A69CC4',
             'border': '#6EA8FF'}}

# v3.16.2 — Reward/Secret themes are full visual identities, not palette-only recolors.
_SECRET_THEME_PALETTES = {
    "Party": {"bg":"#10071A","card":"#20102F","card_active":"#3A1D50","panel":"#170B24","sidebar":"#12091D","icon_bg":"#321745","accent":"#FFD166","hover":"#FF8FD8","text":"#FFF7FF","muted":"#BFA7C9","border":"#7EE7FF"},
    "Frequency": {"bg":"#030812","card":"#071425","card_active":"#0E2940","panel":"#050E1B","sidebar":"#040B15","icon_bg":"#0B2235","accent":"#53F6C7","hover":"#8CFFE0","text":"#EDFFFB","muted":"#78A69C","border":"#33B8FF"},
    "Flagborn": {"bg":"#020806","card":"#071711","card_active":"#0E3221","panel":"#04110C","sidebar":"#030D09","icon_bg":"#0C2A1B","accent":"#72FF8F","hover":"#A0FFB2","text":"#F0FFF3","muted":"#7CA487","border":"#22D3A6"},
    "Architect": {"bg":"#070713","card":"#111126","card_active":"#24234A","panel":"#0C0C1D","sidebar":"#090918","icon_bg":"#1D1D3C","accent":"#A7B4FF","hover":"#CCD3FF","text":"#F5F6FF","muted":"#9097BD","border":"#7C83FF"},
    "Jackpot": {"bg":"#080603","card":"#181006","card_active":"#35240A","panel":"#100B05","sidebar":"#0C0804","icon_bg":"#2A1C08","accent":"#FFD45A","hover":"#FFE79B","text":"#FFF9E8","muted":"#AD9B70","border":"#FF9F1C"},
    "No Dash": {"bg":"#02090D","card":"#071921","card_active":"#103444","panel":"#051219","sidebar":"#040F15","icon_bg":"#0D2A36","accent":"#6FE8FF","hover":"#A9F4FF","text":"#F0FDFF","muted":"#7DA5AF","border":"#49BFD5"},
    "Millionaire": {"bg":"#060504","card":"#151108","card_active":"#2E260F","panel":"#0E0B06","sidebar":"#0A0805","icon_bg":"#251D0B","accent":"#FFE06A","hover":"#FFF0A5","text":"#FFFBEA","muted":"#B4A36E","border":"#D6A928"},
    "Pure Combat": {"bg":"#090303","card":"#1B0808","card_active":"#391212","panel":"#120606","sidebar":"#0E0505","icon_bg":"#301010","accent":"#FF6464","hover":"#FF9696","text":"#FFF2F2","muted":"#B48888","border":"#FF3D3D"},
    "Untouchable": {"bg":"#04040A","card":"#0D0E1A","card_active":"#1D2040","panel":"#090A14","sidebar":"#070811","icon_bg":"#171A34","accent":"#9B8CFF","hover":"#C2B8FF","text":"#F7F5FF","muted":"#908AAE","border":"#695CFF"},
    "Endurance": {"bg":"#03100B","card":"#0A2118","card_active":"#154632","panel":"#071810","sidebar":"#05130D","icon_bg":"#103A29","accent":"#76F3A7","hover":"#A5FAC4","text":"#F0FFF5","muted":"#83A991","border":"#33D17A"},
}
TEMAS.update(_SECRET_THEME_PALETTES)

for _nome_tema, _tema in TEMAS.items():
    _tema.setdefault("panel", _tema["card"])
    _tema.setdefault("sidebar", _tema["card"])
    _tema.setdefault("icon_bg", _tema["card_active"])
    _tema.setdefault("muted", "#8A939E")
TEMAS_PADRAO = {nome: valores.copy() for nome, valores in TEMAS.items()}

THEME_DECOR = {'Matrix Terminal': {'tag': 'MATRIX RAIN', 'icon': '>_', 'symbols': '01ZK{}[]<>'},
 'Cyberpunk Neon': {'tag': 'NEON DISTRICT', 'icon': '//', 'symbols': '<>::##'},
 'Electric Blue': {'tag': 'CIRCUIT FLOW', 'icon': '◈', 'symbols': '+o-'},
 'Deep Ocean': {'tag': 'ABYSS FLOW', 'icon': '○', 'symbols': 'oO°~'},
 'Blood & Bone': {'tag': 'CRIMSON SLASH', 'icon': 'X', 'symbols': 'X/+'},
 'Forest Hacker': {'tag': 'FOREST CODE', 'icon': '♧', 'symbols': '01♧⌁'},
 'Sunset Synthwave': {'tag': 'SYNTH SUN', 'icon': '◒', 'symbols': '.+*'},
 'Void Purple': {'tag': 'VOID ORBIT', 'icon': '◇', 'symbols': '◇·✦'},
 'Obsidian Gold': {'tag': 'GOLD CIRCUIT', 'icon': '◆', 'symbols': '◆+━'},
 'Arctic Glass': {'tag': 'FROST GRID', 'icon': '❄', 'symbols': '✧❄·'},
 'Sakura Night': {'tag': 'SAKURA DRIFT', 'icon': '✿', 'symbols': '✿·*'},
 'Midnight Chrome': {'tag': 'CHROME LINE', 'icon': '◫', 'symbols': '◫━·'},
 'Inferno Core': {'tag': 'INFERNO CORE', 'icon': '▲', 'symbols': '▲/·'},
 'Emerald Glass': {'tag': 'EMERALD WAVE', 'icon': '◉', 'symbols': '◉~·'},
 'Clean': {'tag': 'SOFT UI', 'icon': '•', 'symbols': '...'},
 'ZKStrap Core': {'tag': 'CORE // SIGNATURE', 'icon': 'ZK', 'symbols': 'ZK✦//<>'},
 'Minecraft': {'tag': 'PIXEL OVERWORLD', 'icon': '▦', 'symbols': '▦▓▒'},
 'Hollow Knight': {'tag': 'PALE KINGDOM', 'icon': '◌', 'symbols': '◌⋄⌁'},
 'Blox Fruits': {'tag': 'GRAND LINE', 'icon': '⚓', 'symbols': '≈⚓✦'},
 'Valorant': {'tag': 'TACTICAL RED', 'icon': 'V', 'symbols': 'V//<>'},
 'CS GO': {'tag': 'TACTICAL GRID', 'icon': '+', 'symbols': '+[]•'},
 'Terraria': {'tag': 'PIXEL FRONTIER', 'icon': '▧', 'symbols': '▧✦▓'},
 'Celeste': {'tag': 'SUMMIT SKY', 'icon': '✦', 'symbols': '✦△·'}}

THEME_STYLE = {
 'Matrix Terminal': {'radius': 12, 'nav_radius': 10, 'card_radius': 14, 'border_width': 1, 'accent2': '#8AFFB8', 'motif': '>_'},
 'Cyberpunk Neon': {'radius': 16, 'nav_radius': 12, 'card_radius': 16, 'border_width': 1, 'accent2': '#22D3EE', 'motif': '//'},
 'Electric Blue': {'radius': 18, 'nav_radius': 13, 'card_radius': 18, 'border_width': 1, 'accent2': '#93E9FF', 'motif': 'CIR'},
 'Deep Ocean': {'radius': 22, 'nav_radius': 16, 'card_radius': 20, 'border_width': 1, 'accent2': '#99E6FF', 'motif': '~'},
 'Blood & Bone': {'radius': 10, 'nav_radius': 8, 'card_radius': 11, 'border_width': 1, 'accent2': '#FFE2D5', 'motif': 'X'},
 'Forest Hacker': {'radius': 15, 'nav_radius': 11, 'card_radius': 15, 'border_width': 1, 'accent2': '#C2FF88', 'motif': '{}'},
 'Sunset Synthwave': {'radius': 20, 'nav_radius': 14, 'card_radius': 19, 'border_width': 1, 'accent2': '#FF5ACD', 'motif': 'SUN'},
 'Void Purple': {'radius': 19, 'nav_radius': 13, 'card_radius': 18, 'border_width': 1, 'accent2': '#E879F9', 'motif': 'ORB'},
 'Obsidian Gold': {'radius': 14, 'nav_radius': 10, 'card_radius': 14, 'border_width': 1, 'accent2': '#FFF0B0', 'motif': '◆'},
 'Arctic Glass': {'radius': 23, 'nav_radius': 17, 'card_radius': 21, 'border_width': 1, 'accent2': '#D9FBFF', 'motif': 'ICE'},
 'Sakura Night': {'radius': 21, 'nav_radius': 15, 'card_radius': 19, 'border_width': 1, 'accent2': '#FBCFE8', 'motif': '✿'},
 'Midnight Chrome': {'radius': 15, 'nav_radius': 11, 'card_radius': 15, 'border_width': 1, 'accent2': '#60A5FA', 'motif': 'CHR'},
 'Inferno Core': {'radius': 13, 'nav_radius': 10, 'card_radius': 13, 'border_width': 1, 'accent2': '#EF4444', 'motif': '▲'},
 'Emerald Glass': {'radius': 21, 'nav_radius': 15, 'card_radius': 19, 'border_width': 1, 'accent2': '#2DD4BF', 'motif': '◉'},
 'Clean': {'radius': 21, 'nav_radius': 15, 'card_radius': 19, 'border_width': 1, 'accent2': '#FFFFFF', 'motif': '•'},
 'ZKStrap Core': {'radius': 18, 'nav_radius': 13, 'card_radius': 18, 'border_width': 1, 'accent2': '#E11D48', 'motif': 'ZK'},
 'Minecraft': {'radius': 7, 'nav_radius': 5, 'card_radius': 8, 'border_width': 2, 'accent2': '#8CCB62', 'motif': 'BLOCK'},
 'Hollow Knight': {'radius': 20, 'nav_radius': 14, 'card_radius': 20, 'border_width': 1, 'accent2': '#9ABFD7', 'motif': 'SOUL'},
 'Blox Fruits': {'radius': 18, 'nav_radius': 12, 'card_radius': 18, 'border_width': 1, 'accent2': '#F4C542', 'motif': 'SEA'},
 'Valorant': {'radius': 8, 'nav_radius': 6, 'card_radius': 9, 'border_width': 1, 'accent2': '#ECE8E1', 'motif': 'V'},
 'CS GO': {'radius': 8, 'nav_radius': 6, 'card_radius': 9, 'border_width': 1, 'accent2': '#F2A900', 'motif': 'RADAR'},
 'Terraria': {'radius': 8, 'nav_radius': 6, 'card_radius': 9, 'border_width': 2, 'accent2': '#4FA8D8', 'motif': 'WORLD'},
 'Celeste': {'radius': 18, 'nav_radius': 13, 'card_radius': 18, 'border_width': 1, 'accent2': '#6EA8FF', 'motif': 'SUMMIT'},
}
# Unlockable themes live in a dedicated locked gallery.
UNLOCKABLE_THEME_NAMES = ["Party","Frequency","Flagborn","Architect","Jackpot","No Dash","Millionaire","Pure Combat","Untouchable","Endurance"]
SECRET_THEME_RULES = {
    "Party": {"hint":"Um bom histórico eventualmente vira festa.", "desc":"Recompensa de progressão dos desafios."},
    "Frequency": {"hint":"Uma faixa precisa terminar de te conhecer.", "desc":"Um tema para quem realmente usa a camada musical do ZKStrap."},
    "Flagborn": {"hint":"Escolher não basta. A máquina só acredita no que foi aplicado.", "desc":"Nascido das configurações que realmente chegam ao Roblox."},
    "Architect": {"hint":"Uma biblioteca pequena ainda não impressiona o arquiteto.", "desc":"Feito para quem monta e guarda builds no Planner."},
    "Jackpot": {"hint":"O acaso recompensa insistência.", "desc":"Um prêmio escondido dentro da Build Roulette."},
    "No Dash": {"hint":"Há uma vitória escondida nos passos que você decide não dar.", "desc":"Tema ligado a um desafio secreto de movimentação."},
    "Millionaire": {"hint":"Sete dígitos mudam qualquer interface.", "desc":"Tema ligado a um desafio secreto de bounty."},
    "Pure Combat": {"hint":"Quando todo o resto vira peso morto, sobra o essencial.", "desc":"Tema ligado a um desafio secreto de Fighting Style."},
    "Untouchable": {"hint":"Continue vencendo até o contador parecer errado.", "desc":"Tema ligado a uma sequência secreta."},
    "Endurance": {"hint":"Tempo e caça precisam sobreviver juntos.", "desc":"Tema ligado a uma prova secreta longa."},
}
THEME_DECOR.update({
    "Party":{"tag":"PARTY UNLOCK","icon":"✦","symbols":"✦*+o"},
    "Frequency":{"tag":"AUDIO SIGNAL","icon":"♫","symbols":"♫≈▮"},
    "Flagborn":{"tag":"FLAG MATRIX","icon":"{}","symbols":"01{}+"},
    "Architect":{"tag":"BUILD BLUEPRINT","icon":"▦","symbols":"▦+//"},
    "Jackpot":{"tag":"LUCK ENGINE","icon":"◆","symbols":"◆777✦"},
    "No Dash":{"tag":"STILL VELOCITY","icon":"◇","symbols":"◇//·"},
    "Millionaire":{"tag":"SEVEN DIGITS","icon":"$","symbols":"$◆+"},
    "Pure Combat":{"tag":"FIST ONLY","icon":"X","symbols":"X+//"},
    "Untouchable":{"tag":"STREAK CORE","icon":"∞","symbols":"∞✦·"},
    "Endurance":{"tag":"LONG RUN","icon":"◴","symbols":"◴+·"},
})
THEME_STYLE.update({
    "Party":{"radius":24,"nav_radius":18,"card_radius":22,"border_width":2,"accent2":"#FF8FD8","motif":"✦"},
    "Frequency":{"radius":16,"nav_radius":11,"card_radius":16,"border_width":1,"accent2":"#33B8FF","motif":"WAVE"},
    "Flagborn":{"radius":10,"nav_radius":7,"card_radius":11,"border_width":1,"accent2":"#22D3A6","motif":"01"},
    "Architect":{"radius":7,"nav_radius":5,"card_radius":8,"border_width":1,"accent2":"#7C83FF","motif":"GRID"},
    "Jackpot":{"radius":20,"nav_radius":14,"card_radius":18,"border_width":2,"accent2":"#FF9F1C","motif":"777"},
    "No Dash":{"radius":12,"nav_radius":8,"card_radius":12,"border_width":1,"accent2":"#49BFD5","motif":"//"},
    "Millionaire":{"radius":15,"nav_radius":10,"card_radius":15,"border_width":2,"accent2":"#D6A928","motif":"$"},
    "Pure Combat":{"radius":8,"nav_radius":6,"card_radius":9,"border_width":2,"accent2":"#FF3D3D","motif":"X"},
    "Untouchable":{"radius":26,"nav_radius":18,"card_radius":24,"border_width":1,"accent2":"#695CFF","motif":"∞"},
    "Endurance":{"radius":18,"nav_radius":12,"card_radius":18,"border_width":2,"accent2":"#33D17A","motif":"◴"},
})
SPECIAL_THEME_NAMES = {"Minecraft", "Hollow Knight", "Blox Fruits", "Valorant", "CS GO", "Terraria", "Celeste"}

# Assets usados como elementos de cena dos temas especiais.
# A UI v3.11 posiciona esses recursos dentro de composições inspiradas nos jogos,
# em vez de tratá-los como simples ícones soltos.
SPECIAL_THEME_ASSETS = {
    "Minecraft": {"dir":"minecraft", "icons":["brand","real_diamond_sword","real_golden_apple","real_ender_pearl","real_bow","real_diamond","real_red_apple","real_hunger_icon","real_cake","real_gold_ingot","real_water_bucket","real_blaze_rod","real_watermelon","real_diamond_pickaxe"]},
    "Hollow Knight": {"dir":"hollow_knight", "icons":["brand","real_charm_purple","real_charm_wings","real_charm_green","real_charm_round","real_charm_white","real_charm_key","real_charm_wind"]},
    "Blox Fruits": {"dir":"blox_fruits", "icons":["brand","legacy_01","legacy_02","legacy_03","legacy_04","legacy_05","legacy_06","legacy_07","legacy_08","legacy_09","legacy_10","legacy_11"]},
    "Valorant": {"dir":"valorant", "icons":["brand","real_rank_iron","real_rank_bronze","real_rank_silver","real_rank_gold","real_rank_platinum","real_rank_diamond","real_rank_immortal","real_rank_radiant"]},
    "CS GO": {"dir":"cs_go", "icons":["brand","real_mp7","real_bizon","real_p90","real_awp","real_scout","real_auto_sniper","real_mp9","real_ump"]},
    "Terraria": {"dir":"terraria", "icons":["brand","real_magic_staff","real_staff","real_banana","real_blue_blade","real_sword","real_ring","real_accessory","real_green_blade","real_potion","real_pickaxe_like"]},
    "Celeste": {"dir":"celeste", "icons":["brand","real_strawberry","real_crystal"]},
}

# Banner principal dos temas especiais. Os backgrounds usam as composições aprovadas
# pelo usuário; os objetos por cima são recortes de imagens reais enviadas por ele.
SPECIAL_THEME_BANNER_META = {
    "Blox Fruits": {
        "subtitle": "Grand Line", "tagline": "Desperte seu potencial. Navegue por novos horizontes.",
        "focus": (0.50, 0.50), "square": "pvp",
        "float_icons": ["legacy_01","legacy_02","legacy_03","legacy_04","legacy_05","legacy_06","legacy_07"],
        "float_slots": [(0.22,0.30),(0.34,0.67),(0.47,0.30),(0.60,0.67),(0.72,0.30),(0.83,0.67),(0.90,0.34)],
        "float_sizes": [0.30,0.29,0.31,0.29,0.30,0.29,0.30],
    },
    "Valorant": {
        "subtitle": "Tactical Red", "tagline": "Precisão, leitura e controle em cada round.",
        "focus": (0.50, 0.50), "square": "keyart",
        "float_icons": ["real_rank_bronze","real_rank_silver","real_rank_gold","real_rank_platinum","real_rank_diamond","real_rank_radiant"],
        "float_slots": [(0.23,0.30),(0.36,0.68),(0.50,0.30),(0.64,0.68),(0.77,0.30),(0.89,0.66)],
        "float_sizes": [0.29,0.29,0.30,0.30,0.30,0.31],
    },
    "Minecraft": {
        "subtitle": "Pixel Overworld", "tagline": "Explore, construa e personalize seu mundo.",
        "focus": (0.50, 0.48), "square": "scene",
        "float_icons": ["real_diamond_sword","real_golden_apple","real_ender_pearl","real_diamond","real_cake","real_blaze_rod","real_diamond_pickaxe"],
        "float_slots": [(0.22,0.31),(0.34,0.68),(0.47,0.30),(0.60,0.68),(0.72,0.30),(0.83,0.68),(0.91,0.34)],
        "float_sizes": [0.30,0.29,0.30,0.29,0.29,0.29,0.30],
    },
    "Celeste": {
        "subtitle": "Summit Sky", "tagline": "Continue subindo. Cada tentativa deixa você mais perto.",
        "focus": (0.50, 0.48), "square": "keyart",
        "float_icons": ["real_strawberry","real_crystal","real_strawberry","real_crystal"],
        "float_slots": [(0.28,0.30),(0.48,0.68),(0.68,0.30),(0.86,0.66)],
        "float_sizes": [0.29,0.30,0.29,0.30],
    },
    "Hollow Knight": {
        "subtitle": "Pale Kingdom", "tagline": "Silêncio, Soul e caminhos esquecidos de Hallownest.",
        "focus": (0.50, 0.48), "square": "knight",
        "float_icons": ["real_charm_purple","real_charm_wings","real_charm_green","real_charm_round","real_charm_white","real_charm_key"],
        "float_slots": [(0.23,0.30),(0.36,0.68),(0.50,0.30),(0.64,0.68),(0.77,0.30),(0.89,0.66)],
        "float_sizes": [0.29,0.30,0.29,0.29,0.29,0.29],
    },
    "Terraria": {
        "subtitle": "Pixel Frontier", "tagline": "Aventure-se, equipe-se e transforme o mundo.",
        "focus": (0.50, 0.49), "square": "keyart",
        "float_icons": ["real_magic_staff","real_blue_blade","real_sword","real_ring","real_potion","real_pickaxe_like"],
        "float_slots": [(0.23,0.30),(0.36,0.68),(0.50,0.30),(0.64,0.68),(0.77,0.30),(0.89,0.66)],
        "float_sizes": [0.29,0.29,0.29,0.28,0.28,0.29],
    },
    "CS GO": {
        "subtitle": "Tactical Grid", "tagline": "Economia, timing e leitura do mapa em primeiro lugar.",
        "focus": (0.50, 0.48), "square": "keyart",
        "float_icons": ["real_mp7","real_bizon","real_p90","real_awp","real_scout","real_auto_sniper"],
        "float_slots": [(0.23,0.30),(0.36,0.68),(0.50,0.30),(0.64,0.68),(0.77,0.30),(0.89,0.66)],
        "float_sizes": [0.29,0.30,0.29,0.31,0.30,0.31],
    },
}

SPECIAL_THEME_DESCRIPTIONS = {
    "Minecraft": "Overworld no banner superior com itens reais do jogo em flutuação curta e sem invadir a interface.",
    "Hollow Knight": "Hallownest ocupa apenas o banner, com charms reais em movimento e o shell preservado.",
    "Blox Fruits": "Arte principal confinada ao banner, com itens nostálgicos reais e identidade Grand Line sem invadir a interface.",
    "Valorant": "Arte tática confinada ao banner, com ranks reais em movimento e o restante da interface limpo.",
    "CS GO": "Armas reais ficam distribuídas no banner tático, sem atravessar a UI.",
    "Terraria": "A arte de Terraria fica no banner com itens reais do inventário em movimento discreto.",
    "Celeste": "Arte de Celeste no banner com morangos e cristais reais em movimento sutil.",
}
CORE_THEME_NAMES = [name for name in TEMAS if name not in SPECIAL_THEME_NAMES and name not in UNLOCKABLE_THEME_NAMES]

CHANGELOG = [
    ("v3.18.2", "Spotify Web + Hover Fix", ["Spotify Web aceita sessão musical com metadata rica (título + artista + álbum), mesmo quando o Windows não marca PlaybackType=MUSIC", "Sessões VIDEO continuam rejeitadas para não controlar YouTube por engano", "Cards de temas secretos tocam apenas um hover por entrada no card, sem metralhar SFX ao cruzar widgets internos"]),
    ("v3.18.1", "Fast Themes + Spotify Deck", ["Troca de tema sem reconstruir todas as páginas, eliminando travamentos longos", "Owner Lab deixa de forçar rebuild ao retirar override de temas secretos", "Spotify Web ganha detecção por sessão MUSIC ou janela ativa confirmada", "Aba Spotify recebe identidade verde própria e logo local", "Volume do Spotify Desktop reforçado; Web ganha opt-in explícito para volume do navegador", "Áudio ganha controle separado de volume dos SFX até 150%", "Aba Resolução removida da navegação principal"]),
    ("v3.18.0", "Update Center", ["Atualizações automáticas via GitHub com canais Stable/Beta/Dev", "Download com progresso e validação SHA-256", "ZKUpdater separado instala após o app fechar", "Backup automático da instalação e rollback para a versão anterior", "Dados pessoais ficam fora da pasta atualizada"]),
    ("v3.17.2", "Secret Vault Alive", ["Cards bloqueados ficam realmente selados: mais escuros, dessaturados e com preview dormente", "Hover acorda o preview bloqueado e revela a pista dentro do card", "Temas secretos recebem uma segunda camada de animação exclusiva e elementos internos mais vivos", "Cada identidade secreta ganha assinatura sonora própria para hover, navegação, clique, confirmação, aplicar e desbloquear"]),
    ("v3.17.1", "Secret Vault Gallery Rework", ["Temas secretos ganham cards completos com preview visual LIVE", "Cards bloqueados revelam a dica inline ao passar o mouse por qualquer área do card", "Hover deixa de depender do Tooltip do frame-pai e não é mais perdido pelos widgets internos", "Secret Vault recebe progresso visual, badges LOCKED/UNLOCKED e organização maior por identidade"]),
    ("v3.17.0", "Owner Lab + Safe Test Profiles", ["Comando secreto na Busca Universal abre o Owner Lab apenas quando a chave local do dono está instalada", "Senha do Owner Lab é criada no primeiro acesso e armazenada somente como PBKDF2 hash+salt", "Modo Fresh User usa perfil de teste isolado e preserva o perfil principal intacto", "Backups manuais e restauração do último snapshot ficam fora da pasta normal do ZKStrap", "Overrides de teste liberam temas secretos e podem forçar desafios SECRET sem alterar progressão real", "Reset de dados sempre oferece snapshot automático antes da limpeza"]),
    ("v3.16.2", "Secret Theme Identity Fix", ["Temas secretos deixam de ser simples recolors e recebem cenas visuais próprias", "Party/Frequency/Flagborn/Architect/Jackpot/No Dash/Millionaire/Pure Combat/Untouchable/Endurance ganham identidade exclusiva", "Hero, preview da galeria, header, sidebar e dock passam a refletir o tema secreto ativo", "Aplicar um tema secreto reconstrói o shell inteiro com sua identidade, sem reaproveitar a atmosfera do tema anterior"]),
    ("v3.16.1", "Secret Sync + Kill Timer Fix", ["Temas secretos atualizam a galeria imediatamente após o desbloqueio", "SECRET Endurance agora conclui em 20 kills sem morrer; cronômetro mede apenas o tempo levado", "Ao atingir 20/20 o relógio para, o desafio é arquivado e a recompensa é aplicada na hora"]),
    ("v3.16.0", "Creator Rewards + Assist Rework", ["Creator Mode focado em desafios: ideias/projetos removidos", "Pool de desafios reclassificada com SECRET raro e tracking manual avançado", "Histórico persistente, desafios ativos temporários e celebração com confete", "Party e galeria de temas secretos com desbloqueios por desafios e ações dentro do app", "Build Roulette recebeu acabamento visual sem remover Style/Fruit/Sword/Gun", "ZK Assist simplificado com categorias e busca local de ajuda"]),
    ("v3.15.8", "Safe Browser Media Gate", ["Spotify Desktop continua com controle exclusivo por sessão", "Sessões de navegador só são aceitas quando o Windows expõe tipo MUSIC + artista + álbum", "Sessões ambíguas do Chrome/Edge são bloqueadas para nunca controlar YouTube por engano", "Status deixa de chamar qualquer sessão do navegador de Spotify Web", "Diagnóstico mostra quando o navegador está expondo mídia ambígua"]),
    ("v3.15.6", "Spotify Target Session", ["Sessão do Spotify passa a ser selecionada explicitamente", "Sessões de vídeo do navegador são rejeitadas para evitar controlar YouTube", "Playback deixa de usar fallback por tecla multimídia global", "Diagnóstico técnico da leitura WinRT fica visível na própria aba"]),
    ("v3.15.4", "Spotify Local Media", ["Spotify deixa de depender de OAuth, Client ID, Web API e Premium", "Controles passam a usar teclas de mídia nativas do Windows", "Adicionados abrir Spotify, anterior, play/pause, próxima, mute e volume do Windows", "Status local detecta se o processo Spotify está aberto", "Mini-player vira mini-controle local sem login"]),
    ("v3.15.3", "All Local Combo Icons", ["Fruits, Fighting Styles, Swords e Guns passam a usar exclusivamente os ícones locais enviados pelo usuário", "40 Swords e 14 Guns adicionadas ao pack local", "Pole V1/V2 recebem mapeamento local explícito", "Planner deixa de depender de cache/wiki/API para thumbnails dos quatro catálogos", "Mantém o tutorial guiado do Spotify da v3.15.2"]),
    ("v3.15.2", "Local Style Pack + Spotify Guide Polish", ["Superhuman, Godhuman e Sanguine Art passam a usar os ícones locais enviados pelo usuário", "Triple Dark Blade removida do catálogo visual", "Tutorial do Spotify revisado para explicar Client ID, Redirect URI e teste sem jargão", "Aviso de compatibilidade da Web API atualizado para conta Premium"]),
    ("v3.15.1", "Local Icons + Spotify Guide", ["Fruits e Fighting Styles passam a usar primeiro o pack local enviado pelo usuário", "Fruits deixam de depender de internet para exibir thumbnail quando existe asset local", "Combo Planner evita prefetch online para itens presentes no pack local", "Spotify ganha tutorial passo a passo dentro da própria página"]),
    ("v3.15.0", "Fruit CDN Recovery", ["Fruits deixam de depender do Fandom para carregar thumbs", "GitHub raw vira fonte primária para o catálogo de Fruits", "Magnet usa asset direto atualizado como exceção", "Cache de Fruits muda de revisão para descartar placeholders vazios"]),
    ("v3.14.9", "Weapon Strictness Hotfix", ["Weapons param de usar fallbacks amplos que puxavam player/screenshot/arte antiga", "Swords e Guns ganham cache novo para descartar ícones errados já salvos", "Fishing Trophy sai do catálogo visual do Planner/Roulette", "Pole V1/V2, Dog Blade, Flail, Dual-Headed Blade e Slingshots recebem candidatos manuais de arquivo"]),
    ("v3.14.8", "Stability Rework", ["Fruits passam a resolver o arquivo exato pela MediaWiki API antes dos fallbacks", "Cache de Fruits reiniciado para remover thumbs antigas incorretas", "Magnet corrigida no mapa de raridade usado pelo resolver de assets", "Spotify ganhou status visível, teste de conexão, refresh de token e fallback local do Windows", "Build padrão passa a usar ONEDIR para reduzir a extração repetida dos assets durante a abertura", "Callbacks de erro que podiam falhar silenciosamente foram corrigidos"]),
    ("v3.14.7", "Fruit Direct Files", ["Cards de Fruit tentam primeiro o arquivo exato da própria wiki pelo padrão Nome + Raridade", "Natural, Elemental e Beast permanecem apenas como fallback estrito", "Player, screenshot, skill e transformação continuam proibidos como thumbnail de Fruit", "Cache de Fruits isolado em nova revisão"]),
    ("v3.14.6.1", "Build Package Fix", ["Corrige o BUILD_EXE que apontava para um requirements inexistente", "Build passa a usar requirements.txt estável para evitar quebra por número de versão"]),
    ("v3.14.6", "Fruit Icons Fix", ["Corrige a leitura dos ícones nas páginas Natural/Elemental/Beast", "Aceita o padrão real da wiki como RocketCommon / FlameUncommon", "As três páginas são baixadas no máximo uma vez por sessão", "Cache de Fruits isolado em nova revisão"]),
    ("v3.14.5", "Fruit Catalog Rebuild", ["Fruits passam a usar somente Natural/Elemental/Beast como fontes", "Player, screenshot, skill, transformação e mídia antiga são rejeitados", "Cache de Fruits isolado em nova revisão", "Quando não existe mídia confiável, o app prefere placeholder a imagem incorreta"]),
    ("v3.14.4", "Full Build Catalog Restore", ["Combo Planner volta a usar 4 etapas visuais: Fighting Style, Fruit, Sword e Gun", "Build Roulette volta a sortear e revelar os 4 slots em sequência", "Inventário da Roulette ganhou filtros separados para Style, Fruit, Sword e Gun", "Histórico, favoritos e salvar no Combo Planner preservam a build completa", "Miniaturas de Sword/Gun usam cache e carregamento sob demanda sem pesar o boot"]),
    ("v3.14.3", "Fruit Physical Media + Inventory Stability", ["Inventário da Roulette refeito com botões de estado, sem o caminho de checkbox que abria uma janela vazia", "Cache de Fruits/Styles reiniciado e Fruit nunca mais aceita ícone genérico de habilidade como fallback", "Advanced Combat deixa de usar o asset hardcoded incorreto", "Se a wiki não fornecer uma imagem física confiável, o app mostra placeholder em vez de screenshot/personagem/imagem errada"]),
    ("v3.14.2", "Stability + Session State Fix", ["Boot deixa de pré-carregar dezenas de miniaturas em rede e abre a UI sem saturar o processo", "Pipeline de ícones de Fruits/Fighting Styles prioriza o ícone atual da infobox e invalida o cache anterior", "Inventário da Roulette foi simplificado para uma janela estável e fechável", "Desafios do Creator Mode agora são apenas da sessão e somem ao fechar o app", "SETUPS ganhou salvar/parar edição claramente no topo", "Spotify valida Client ID antes de abrir o navegador e explica que link do Spotify não é Client ID", "Sobre remove o texto antigo de 10 horas e mostra tempo decorrido desta fase"]),
    ("v3.14.1", "Blox Hub Stability Fix", ["Inventário da Build Roulette corrigido: renderização, botão fechar, ESC e explicação do filtro", "Advanced Combat não reutiliza mais a miniatura errada e recebe fonte dedicada", "Creator Mode ganhou textos mais específicos para ideias ligadas à Build Roulette", "Cards de progresso deixam de ser recriados a cada tick do cronômetro, reduzindo o pisca-pisca", "Blox Hub deixa de duplicar a navegação da sidebar", "Spotify callback local ganhou servidor reutilizável e espera robusta por retorno OAuth"]),
    ("v3.14.0", "Blox Hub + Creator + Setups + Spotify", ["Blox Hub centraliza Build Roulette, Combo Planner e Creator Mode", "Build Roulette ganhou animação sequencial, inventário local de estilos/frutas, histórico e favoritos", "Creator Mode ganhou desafios por dificuldade, progresso visual para kills/bounty/tempo/winstreak e projetos salvos", "SETUPS permite salvar até 5 combinações locais, aplicar, editar, renomear e excluir com snapshot antes da troca", "Spotify ganhou integração por OAuth PKCE, página própria e mini-player animado sem pedir senha", "Scroll rápido recebeu controlador suavizado e pausa temporária de animações pesadas", "Combo Planner adiciona Advanced Combat / Combat V2 e acelera o cache de estilos/frutas com prefetch paralelo", "Sobre 2.0 conta dinamicamente os dias da fase intensiva iniciada em 10/09/2026"]),
    ("v3.13.3.11", "Strict Icons + Music Identity Fix", ["Combo Planner rejeita banners/cards horizontais e prioriza o ícone específico de Fighting Styles e Fruits", "Cache novo evita reaproveitar thumbnails incorretas das builds anteriores", "Quando não existe um ícone quadrado confiável, o planner mostra placeholder em vez de uma imagem errada", "Packs de música receberam novas composições e previews próprios para ficarem claramente diferentes"]),
    ("v3.13.3.11", "Icon Pipeline + Distinct Music Rework", ["Combo Planner invalida o cache antigo e busca primeiro o ícone exato do item, evitando thumbs genéricas do jogo", "Fallbacks de imagem agora validam título/página antes de aceitar og:image e priorizam arquivo original/MediaWiki exato", "Música voltou a ter volume próprio separado dos SFX, com padrão em 22%", "20 faixas foram recompostas com BPM, compassos, progressões, melodias e instrumentação diferentes entre os packs"]),
    ("v3.13.3.9", "Full Combo Catalog + Music Balance", ["Combo Planner agora tem 4 catálogos visuais: Fighting Style, Fruit, Sword e Gun", "Busca e miniaturas foram estendidas para swords e guns, com cache local e múltiplas fontes", "Builds antigas reaproveitam os antigos SLOT 3 e SLOT 4 como Sword e Gun", "Volume das trilhas de fundo foi reduzido nos arquivos locais para não cobrir os SFX da interface"]),
    ("v3.13.3.7", "Real Music + Smart DNS + Thumbnail Recovery", ["Trilhas de fundo melódicas novas: 2 músicas por pack em vez de ruído ambiente curto", "DNS Lab mede RTT real dos resolvers por UDP, memoriza o melhor perfil e permite aplicar/reverter com confirmação", "Ao aplicar DNS, o painel repete o teste de rota Roblox para facilitar comparação antes/depois", "Combo Planner ganhou recuperação de miniaturas por múltiplas fontes e placeholder visível quando uma imagem não está em cache"]),
    ("v3.13.3.6", "Audio Studio + DNS Lab + Catalog Recovery", ["Central de áudio com 10 packs locais e música ambiente longa por pack", "Sons variados para scroll, sliders, navegação, temas, Combo Planner, alertas e splash", "Engine de música ambiente trocada para MCI do Windows com fallback dedicado", "Combo Planner volta a carregar miniaturas de estilos e frutas em fila limitada/cache local", "Ping & Latência ganhou laboratório de DNS, perfis reversíveis e reparo avançado da pilha de rede com confirmação"]),
    ("v3.13.3.5", "Core Motion + Reliable Audio", ["ZKStrap Core e Clean receberam animações multicamada mais visíveis", "Música ambiente passou a tocar em processo dedicado para não ser interrompida pelos SFX", "Novos efeitos de navegação, confirmação, retorno, tema, modal, sucesso e erro", "Sons de interface variam conforme a ação em vez de usar o mesmo clique para tudo", "Preview ao passar o mouse continua animando com a arte atual de cada tema"]),
    ("v3.13.3.4", "Live Previews + Audio Layer", ["Todos os temas Core ganharam uma camada de movimento própria em vez de ficarem majoritariamente estáticos", "Galeria de temas usa o preview visual atual e anima ao passar o mouse", "Áudio opt-in com overlay desfocado no primeiro uso, SFX de interface, sons da splash e música ambiente local", "Botão de áudio no header permite revisar a escolha depois", "Nenhum som é ativado antes do consentimento do usuário"]),
    ("v3.13.3.3", "Core Theme Lock-In", ["Temas Core refeitos com cenas procedurais exclusivas e muito mais densidade visual", "Hero/galeria Core não reutilizam mais o fundo genérico de círculos/radar antes da identidade própria", "Cada tema ganhou composição, moldura, profundidade e microanimação próprias", "Bloco ZK CORE do header ganhou layout vertical fixo para impedir CORE de sobrepor ZK em escalas altas do Windows", "Header recebeu mais respiro sem mexer na splash, Combo Planner ou Painel de Latência"]),
    ("v3.13.3.2", "Theme Identity + Header Fix", ["Header refeito com separador externo contínuo e marca ZKSTRAP sem cortes", "Temas Core ganharam composições realmente diferentes por identidade em vez do mesmo radar/círculos", "Galeria Core também usa previews coerentes com a personalidade de cada tema", "Mantidos Combo Planner offline-first e Painel de Latência da 3.13.3.1"]),
    ("v3.13.3.1", "Stability + Latency Deck", ["Banners especiais reequilibrados: menos exagero, itens reais em tamanho médio e flutuação mais natural", "Header corrigido para não cortar ZKSTRAP e manter a linha inferior contínua", "Combo Planner virou offline-first e não dispara dezenas de downloads de miniaturas ao abrir", "Ping & Rede virou Painel de Latência com teste de rota Roblox, jitter e limpeza DNS segura", "Temas Core ganharam heroes procedurais mais ricos e atuais, sem depender de imagens externas", "Espaçamento do bloco abaixo do banner e hierarquia visual receberam correções de alinhamento"]),
    ("v3.13.3.0", "Performance Deck + Real Theme Motion", ["Temas especiais agora usam somente itens reais extraídos das referências dos jogos", "Blox Fruits perdeu os ícones/frutas artificiais e ganhou itens nostálgicos maiores com flutuação orgânica", "Minecraft removeu o coração problemático e ganhou novos itens reais recortados da folha original", "Camada frontal dos banners ganhou partículas e profundidade sem cobrir a arte", "MANUTENÇÃO virou CENTRAL DE DESEMPENHO com Game Mode, GPU, prioridade, plano de energia e foco de sessão", "Limpeza, backups e voltar ao original foram separados em RECUPERAÇÃO", "Header, sidebar, cards e galeria receberam um passe de organização e acabamento"]),
    ("v3.13.2.9", "Layout + Item Scale Fix", ["Itens flutuantes ficaram maiores e legíveis sem atravessar o banner", "Coração do Minecraft reextraído da HUD original para não aparecer cortado", "Glow dos itens agora ignora pixels soltos e não forma círculos artificiais", "Mais itens reais distribuídos nos banners especiais sem poluir a composição", "Header, sidebar, cards e galeria receberam espaçamento e hierarquia visual mais profissionais", "Terraria preserva a escala visual aprovada na versão anterior"]),
    ("v3.13.2.8", "Theme Glow + ZK Assist", ["Itens reais dos temas especiais ganharam glow suave sem círculos artificiais", "Margens e padding dos itens foram reforçados para evitar cortes nas bordas", "Mais itens flutuantes adicionados aos temas especiais com tamanhos equilibrados", "Temas Core receberam acabamento visual mais rico e consistente", "ZK AI virou Central de Ajuda do app: Assistente ZKStrap liberado e PvP/IA bloqueado como recurso futuro", "Assistente do app ganhou uma biblioteca ampla de dúvidas e atalhos guiados"]),
    ("v3.13.2.7", "Real Banners + Theme Polish", ["Banners originais enviados pelo usuário restaurados em todos os temas especiais", "Itens flutuantes usam recortes reais dos jogos e respeitam margem segura sem cortar", "Quantidade e distribuição dos itens foi ampliada em todos os temas especiais", "Temas Core receberam composição visual mais rica e acabamento mais profissional", "Startup/splash da v3.13.2.6 foi mantido sem alterações funcionais"]),
    ("v3.13.2.6", "Splash Handoff Fix", ["Corrigida a troca da splash de 100% para a janela principal", "A janela principal agora é revelada somente dentro do mainloop do Tk", "O processo da splash é encerrado pelo processo principal após mostrar 100%", "Fechar a splash continua cancelando a inicialização inteira"]),
    ("v3.13.2.5", "Real Items + Splash Sync Fix", ["Layout do banner puro aplicado também aos temas Core", "Itens reais extraídos das imagens dos jogos foram adicionados aos temas especiais", "Blox Fruits ganhou mais itens nostálgicos flutuando", "Splash agora acompanha o progresso real e só libera o app após 100%", "Minimizar e fechar da splash agora funcionam", "Fechar a splash cancela a inicialização e impede o app de abrir"]),
    ("v3.13.2.4", "Theme Layout Fix", ["Banner dos temas especiais ficou 100% separado do texto da página", "Breadcrumb, título e descrição agora ficam abaixo do banner junto ao conteúdo", "Itens dos jogos flutuam no lugar em vez de atravessar a faixa horizontal", "Ícones dos temas especiais ficaram maiores e melhor distribuídos", "Fundo branco do item clássico verde do Blox Fruits removido", "Galeria especial usa as imagens reais dos banners com composição limpa", "Tutorial Spotlight Fix mantido sem alterar a inicialização"]),
    ("v3.13.2.2", "Banner Theme Rework", ["Temas especiais agora usam as imagens escolhidas pelo usuário somente no banner superior", "Header, busca, sidebar e dock não recebem wallpaper do jogo", "Nome do tema e preview quadrado entram dentro do banner sem fundo preto", "Itens reais dos jogos passam animados dentro do banner usando o loop visual estável existente", "Blox Fruits ganhou itens antigos/reworked como detalhes nostálgicos", "Ícones da sidebar reduzidos e realinhados"]),
    ("v3.13.2", "Startup & Changelog Fix", ["Corrigido crash na inicialização causado por width/height enviados ao .place() do CustomTkinter", "Corrigido o mesmo padrão no destaque do tutorial para evitar falhas silenciosas", "Datas e horários removidos da página de Atualizações", "Changelog agora é ordenado automaticamente por versão, com as builds mais recentes primeiro", "Histórico recente completado com os hotfixes que estavam faltando"]),
    ("v3.13.1", "Startup Hotfix", ["Splash movida para processo separado para não congelar durante a montagem da interface", "Timeout de segurança impede a splash de ficar presa na frente do app", "Galeria completa de temas passou a carregar sob demanda ao abrir Personalizar", "Inicialização ficou mais leve e independente da animação da splash"]),
    ("v3.13.0", "Theme Atmosphere Rework", ["Shell reorganizado com sidebar única e navegação alinhada", "Temas agora ocupam header, hero, sidebar, status e geometria dos componentes", "Temas especiais usam assets do próprio pack como cenário e ambientação, não como ícones presos em cards", "Todos os temas Core também ganharam ambientação procedural própria", "Galeria inteira recebeu previews vivos para temas Core e Especiais", "Tipografia principal modernizada com Segoe UI e Consolas reservada para microdados técnicos", "Cards, módulos, espaçamentos e hierarquia visual foram modernizados", "Animações de tema passaram a priorizar apenas áreas visíveis para reduzir custo", "Layout responsivo revisado para desktop e janelas menores"]),
    ("v3.12.0", "Modern Shell Rework", ["Novo shell com command bar, icon rail e navegação secundária", "Conteúdo passa a usar toda a área útil do app", "Hero de cada página ganhou cena temática grande e contida", "Temas especiais não espalham mais pequenos ícones pelos cards", "Galeria especial refeita em cenas grandes de uma coluna", "Splash agora permanece visível enquanto a UI real é construída e não falha silenciosamente", "Log do sistema virou dock recolhível"]),
    ("v3.11.0", "Interface Rework", ["Rework visual completo do aplicativo", "Header, sidebar, páginas, cards e controles redesenhados", "Temas especiais agora usam cenas completas com assets do próprio pack em vez de pequenos ícones soltos", "Galeria de temas especiais ampliada", "Sistema visual mais denso, moderno e consistente sem virar interface minimalista"]),
    ("v3.10.0", "ZK Dialogue Engine", ["ZK AI sem campo livre e sem modelo generativo", "PvP Coach em árvore guiada com saudação, tópicos, confirmação e respostas combinadas", "Assistente ZKStrap lê o estado real do app por opções prontas", "Uma única rolagem principal por página: chat/feedback não prendem mais o mouse", "Splash redesenhada com visual moderno e mais leve", "Removidos Qwen, llama-server e download de modelo para acelerar abertura"]),
    ("v3.9.6", "ZK AI — Coach Core híbrido", ["Perguntas comuns de PvP respondidas pelo Coach Core local em vez do Qwen", "Movimentação, mira, predict, game sense, endlag, Haki e treino ganharam respostas diretas", "Perguntas explícitas interrompem diagnósticos antigos em vez de herdar contexto errado", "Filtro de saída bloqueia eco da pergunta e frases genéricas do Qwen", "Mensagens vagas de autoavaliação recebem diagnóstico objetivo sem repetir o usuário", "Qwen fica reservado para casos realmente livres/complexos, reduzindo latência no uso comum"]),
    ("v3.9.5", "ZK AI — diálogo PvP corrigido", ["Router local para diagnóstico comum sem chamar o Qwen", "Não pergunta mais o que mudou/diferente sem contexto", "Mira, tracking, predict e combo têm follow-ups próprios", "Mensagens de confusão resetam suposições e pedem contexto real", "Typing bubble também aparece nas respostas locais rápidas", "Histórico do Qwen reduzido para baixar latência", "Prompt endurecido contra repetição e causalidade inventada"]),
    ("v3.9.4", "ZK AI — respostas rápidas + typing estilo chat", ["Typing bubble no lado da ZK AI, sem status Pensando no topo", "Smalltalk e consultas factuais do ZKStrap respondem localmente sem chamar o Qwen", "RAG PvP reduzido para no máximo 2 blocos relevantes por mensagem", "Mira, tracking, predict e movement agora são conceitos separados", "Prompt proíbe diagnóstico causal sem evidência e repetição da resposta anterior", "Histórico/prompt menores para reduzir latência na CPU", "Pré-aquecimento do Qwen ao abrir a aba ZK AI"]),
    ("v3.9.3", "ZK AI — autodetecção de runtime/modelo", ["Corrige o caso do EXE aberto dentro de dist", "Procura ai_runtime e models também na pasta-pai, LocalAppData e versões ZKStrap próximas", "Mantém temas especiais no pack completo"]),
    ("v3.9.2", "ZK AI Context v2", ["Qwen3 conectado ao estado real do ZKStrap", "Snapshot de módulos, FPS, avançado, watchdog, resolução, cursor, fonte, tema, perfil, combos e última aplicação", "Base PvP curada pelo ZKVEZ organizada em contexto relevante", "Atalhos de navegação/aplicar preservados com botões determinísticos"]),
    ("v3.9.1", "ZK AI local — resposta e autostart", ["llama-server inicia oculto ao usar a IA", "Qwen3 em modo non-thinking para respostas rápidas", "Bloqueio de mensagens paralelas pelo Enter", "Contexto reduzido e 1 slot para menor uso de RAM", "Servidor iniciado pelo app é encerrado junto com o ZKStrap"]),
    ("v3.9.0", "ZK AI local com Qwen3", ["Motor principal trocado para llama.cpp local em 127.0.0.1:8080", "Histórico recente enviado ao modelo por modo", "Prompt técnico do ZKStrap e base curada do PvP Coach", "Motor v3.8.2 mantido apenas como fallback se o servidor local estiver offline"]),
    ("v3.8.2", "Conversation Engine v2", ["Camada de conversa antes do diagnóstico PvP", "Entende oi, tudo bem, ok, sim/não, gírias, não entendi e mudanças de assunto", "Medo/nervosismo interrompem corretamente o roteiro e viram contexto", "Perguntas diretas podem interromper um diagnóstico sem serem confundidas com resposta", "Coach admite quando entendeu errado em vez de inventar uma conclusão"]),
    ("v1.0", "Base inicial", ["Interface inicial em CustomTkinter", "Detecção da pasta version-* do Roblox", "ClientSettings + backup", "Packs básicos de desempenho, céu cinza e rede", "Sugestões enviadas pelo Discord webhook"]),
    ("v2.0", "Nova base modular", ["Primeiro grande rework da interface", "Opções de desempenho separadas por função", "Persistência de preferências e compatibilidade revisada"]),
    ("v2.1", "Resolução revisada", ["Fluxo de resolução reorganizado", "Remoção de comportamento que simulava resolução interna apenas redimensionando a janela"]),
    ("v2.2", "Packs experimentais", ["Telemetria e micro-otimizações experimentais", "Ajustes de CPU/threads calculados pelo sistema", "Alvo de FPS configurável"]),
    ("v2.3", "Assets locais", ["Evolução do sistema de cursor", "Backups e restauração de assets locais", "Sincronização após updates do Roblox"]),
    ("v2.4", "Cursor e fontes", ["Importação e normalização de cursores", "Fontes locais TTF/OTF", "Restauração dos arquivos originais"]),
    ("v2.4.1", "Correções de estabilidade", ["Ajustes incrementais de compatibilidade", "Correções no fluxo de assets e configurações locais"]),
    ("v2.5", "Rework visual", ["Layout responsivo", "Sidebar moderna", "Temas com arte própria", "Vínculo visual de perfil público do Roblox"]),
    ("v2.5.1", "Splash técnica", ["Tela de carregamento detalhada", "Progresso modular", "Terminal e indicadores de inicialização"]),
    ("v2.5.2", "Temas vivos", ["Animações específicas por tema", "Mais responsividade", "Sidebar e páginas com rolagem adaptativa"]),
    ("v2.5.3", "Identidade e perfil", ["Ícones de navegação personalizados", "Cards de tema com preview", "Primeira versão do vínculo de perfil Roblox"]),
    ("v2.5.4", "Perfil Roblox corrigido", ["Busca pública de username mais robusta", "Melhor tratamento de erros no vínculo de perfil"]),
    ("v2.5.5", "Polimento de interface", ["Correções de bordas/cabeçalho", "Ajustes visuais de consistência"]),
    ("v2.6.0", "MacroZK experimental", ["Gravação/reprodução de teclado e mouse", "Hotkeys, timeline, loops e parada de emergência", "Proteção para executar somente com Roblox em foco"]),
    ("v2.6.1", "Editor MacroZK", ["Editor reorganizado em estilo de gerenciador de macros", "Lista de macros + editor de ações mais legível"]),
    ("v2.6.2", "Trigger Key", ["Captura de tecla de ativação corrigida", "Melhor tratamento quando a engine de input não está disponível"]),
    ("v2.6.3", "Concorrência de macros", ["Macros diferentes passaram a poder executar em paralelo", "Proteção contra triggers causados por teclas sintéticas"]),
    ("v2.6.4", "Anti-hold", ["Pulsos de tecla com soltura garantida", "Redução de casos de tecla interpretada como segurada"]),
    ("v2.6.5", "Prioridade de hotkey", ["Teste de cancelamento do macro anterior quando uma nova hotkey entra", "Liberação forçada de teclas durante troca"]),
    ("v2.6.6", "Modo TG rápido", ["Reprodução rápida com sobreposição controlada", "Pulsos curtos e temporização mais agressiva", "Última versão do MacroZK antes da remoção"]),
    ("v2.7.0", "Interface limpa", ["MacroZK removido para replanejamento", "Editor livre de FastFlags removido", "Telemetria e micro-opt integradas em FPS & Gráficos", "Céu cinza separado e reversível"]),
    ("v2.8.0", "ZK Signature", ["Tema padrão oficial", "Rework dos temas antigos", "Manutenção ampliada", "Splash e feedback redesenhados", "Ícone próprio do app"]),
    ("v2.8.1", "Feedback Discord", ["Webhook de sugestões/bugs restaurado", "Central de feedback mantida com o novo visual"]),
    ("v2.9.0", "Control Center", ["Dashboard em tempo real", "Benchmark antes/depois", "Otimização em um clique", "Rollback", "Comparador", "Modo compacto", "Tela de resultado", "Primeira central de changelog e temas especiais"]),
    ("v3.0", "ZKStrap", ["Rebranding completo para ZKStrap", "Dashboard e Control Center consolidados", "Aplicar Configurações em destaque", "Temas especiais e fluxo de resultado refinados"]),
    ("v3.1", "Special Theme Media", ["Primeira experiência com mídia animada nos Temas Especiais", "Galeria refeita com cards grandes", "Controle & Recuperação removido da Manutenção"]),
    ("v3.2", "Special Live Packs", ["GIFs genéricos removidos", "Temas especiais passaram a usar HUDs/elementos em loop dentro do app", "Packs visuais próprios por jogo"]),
    ("v3.3", "First Run Guide", ["Tutorial automático no primeiro acesso", "Username Roblox salvo localmente e pré-preenchido no vínculo", "Tutorial personalizado usando @username", "Botão permanente para rever o tutorial", "Branding interno ZK"]),
    ("v3.4", "Performance Hub", ["Draco V4 integrado em FPS & Gráficos", "Etapa separada de Draco removida do tutorial", "Rodapé lateral corrigido para não cortar o nome do tema", "Histórico de versões passa a mostrar data/hora quando existe registro confiável"]),
    ("v3.5", "Combo Planner", ["Nova central para salvar builds e sequências de combo", "Catálogo visual de estilos de luta e frutas com miniaturas reais baixadas sob demanda", "Cards de builds ilimitados com editar, duplicar e excluir", "Fontes/créditos exibidos dentro do próprio planner"]),
    ("v3.6", "Interface Flow", ["Busca Universal com Ctrl+K", "Modo Avançado recolhível e persistente", "Notificações internas no lugar de pop-ups de sucesso", "Tutorial integrado à própria interface com destaque de elementos", "Transições de página mais sutis e suaves"]),
    ("v3.6.1", "Search & Lifecycle Fix", ["Busca Universal corrigida", "ESC não deixa painel preto", "Fechamento do app mais robusto", "Splash aliviada"]),
    ("v3.7.0", "Signature Experience", ["Rework do tema Core", "Notificações ampliadas para switches", "Splash Signature revisada"]),
    ("v3.7.1", "Classic Splash Restore", ["Retorno ao layout clássico da splash", "Animação otimizada"]),
    ("v3.7.2", "Seamless Boot", ["Tentativa de manter splash durante montagem da interface", "Símbolo Z restaurado no Core"]),
    ("v3.7.3", "Classic Splash Exact Restore", ["Retorno ao fluxo clássico estável da splash", "Remoção da etapa de boot que travava em 64%"]),
    ("v3.7.4", "Startup Recovery Fix", ["Corrigido KeyError do tema ZKStrap Core", "Temas especiais e metadados restaurados", "Changelog restaurado", "Inicialização protegida contra nomes de tema antigos"]),
    ("v3.8.0", "ZK AI", ["Assistente inteligente integrado ao ZKStrap", "Dois modos: Assistente ZKStrap e PvP Coach", "Chat com memória de contexto durante a sessão", "Coach PvP baseado no conhecimento curado pelo ZKVEZ", "Diagnóstico conversacional, treinos e respostas que perguntam antes de assumir"]),
    ("v3.8.1", "Context Engine Fix", ["Coach passa a interpretar respostas pela pergunta anterior antes de usar palavras-chave", "Perguntas de diagnóstico divididas em uma etapa por vez", "Follow-ups como 'o que faço pra melhorar?' usam o assunto anterior", "Assistente ZKStrap reconhece perguntas naturais sobre o estado das configurações", "Evita confundir 'eu observo a movimentação dele' com pedido de dica de movimentação"]),
]

def _startup_splash_create(root):
    """Splash 3.13 ligada ao boot real da aplicação; permanece até a UI terminar."""
    state={"started":time.perf_counter(),"p":0.0}
    try:
        root.title(f"ZKStrap v{APP_VERSION}")
        root.geometry("1440x860")
        root.minsize(1040,680)
        try: root.attributes("-alpha",0.0)
        except Exception: pass

        splash=ctk.CTkToplevel(root); state["splash"]=splash
        splash.overrideredirect(True); splash.configure(fg_color="#05020A")
        try: splash.attributes("-topmost",True)
        except Exception: pass
        W,H=1040,600
        sw,sh=splash.winfo_screenwidth(),splash.winfo_screenheight()
        scale=min(1.0,(sw-36)/W,(sh-36)/H); scale=max(.76,scale)
        W,H=int(W*scale),int(H*scale)
        splash.geometry(f"{W}x{H}+{max(0,(sw-W)//2)}+{max(0,(sh-H)//2)}")

        bg=Canvas(splash,width=W,height=H,bg="#05020A",highlightthickness=0,bd=0)
        bg.place(x=0,y=0,relwidth=1,relheight=1); state["bg"]=bg
        for x in range(0,W,34): bg.create_line(x,0,x,H,fill="#0A0710")
        for y in range(0,H,34): bg.create_line(0,y,W,y,fill="#0A0710")

        shell=ctk.CTkFrame(splash,fg_color="#09070F",corner_radius=25,border_width=2,border_color="#8E22D0")
        shell.place(relx=.5,rely=.5,anchor="center",relwidth=.94,relheight=.90)
        left=ctk.CTkFrame(shell,width=int(350*scale),fg_color="#08060E",corner_radius=21,border_width=1,border_color="#251332")
        left.pack(side="left",fill="y",padx=(18,10),pady=18); left.pack_propagate(False)
        right=ctk.CTkFrame(shell,fg_color="transparent"); right.pack(side="right",fill="both",expand=True,padx=(10,18),pady=18)

        # Left signature core scene.
        logo_canvas=Canvas(left,bg="#08060E",highlightthickness=0,bd=0,height=int(360*scale))
        logo_canvas.pack(fill="x",padx=8,pady=(8,0)); state["logo_canvas"]=logo_canvas
        left.update_idletasks(); cw=max(260,int(320*scale)); ch=max(300,int(350*scale)); cx,cy=cw//2,int(ch*.48)
        for rr,col,wid in [(132,"#23112F",1),(108,"#5C1E83",1),(82,"#A326E2",2)]:
            r=int(rr*scale); logo_canvas.create_oval(cx-r,cy-r,cx+r,cy+r,outline=col,width=max(1,int(wid*scale)))
        arc1=logo_canvas.create_arc(cx-int(132*scale),cy-int(132*scale),cx+int(132*scale),cy+int(132*scale),start=20,extent=96,style="arc",outline="#C234FF",width=max(2,int(3*scale)))
        arc2=logo_canvas.create_arc(cx-int(108*scale),cy-int(108*scale),cx+int(108*scale),cy+int(108*scale),start=204,extent=70,style="arc",outline="#6F28B5",width=max(1,int(2*scale)))
        state["arcs"]=(arc1,arc2)
        # Geometric ZK mark, kept vector so the splash does not depend on an image loading.
        fs=max(35,int(57*scale))
        logo_canvas.create_text(cx-8,cy,text="ZK",fill="#C52EFF",font=("Segoe UI",fs,"bold"),anchor="center")
        logo_canvas.create_polygon(cx+int(42*scale),cy-int(44*scale),cx+int(88*scale),cy-int(44*scale),cx+int(65*scale),cy-int(16*scale),cx+int(38*scale),cy-int(16*scale),fill="#FF365B",outline="")
        nodes=[]
        for px,py in [(cx,cy-int(132*scale)),(cx,cy+int(132*scale)),(cx-int(132*scale),cy),(cx+int(132*scale),cy)]:
            r=max(3,int(5*scale)); nodes.append(logo_canvas.create_rectangle(px-r,py-r,px+r,py+r,fill="#A429E0",outline="#E49CFF"))
        state["nodes"]=nodes
        ctk.CTkLabel(left,text="SIGNATURE CORE",text_color="#C47BFF",font=ctk.CTkFont(family="Segoe UI",size=max(11,int(15*scale)),weight="bold")).pack(pady=(2,0))
        ctk.CTkLabel(left,text="Performance  •  Visual  •  Assets",text_color="#80748F",font=ctk.CTkFont(size=max(8,int(10*scale)))).pack(pady=(2,10))
        foot=ctk.CTkFrame(left,fg_color="transparent"); foot.pack(fill="x",side="bottom",padx=14,pady=13)
        ctk.CTkLabel(foot,text="ZKSTRAP CORE ENGINE",text_color="#71627F",font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left")
        ctk.CTkLabel(foot,text=f"BUILD {APP_VERSION}",text_color="#B876ED",font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="right")

        # Right boot telemetry.
        head=ctk.CTkFrame(right,fg_color="transparent"); head.pack(fill="x",pady=(5,0))
        title=ctk.CTkFrame(head,fg_color="transparent"); title.pack(side="left",fill="x",expand=True)
        ctk.CTkLabel(title,text="ZKSTRAP",text_color="#FAF7FF",font=ctk.CTkFont(family="Segoe UI",size=max(24,int(33*scale)),weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title,text="ROBLOX CLIENT CONFIGURATOR  •  LOCAL MODE",text_color="#A95CEB",font=ctk.CTkFont(family="Consolas",size=max(8,int(10*scale)),weight="bold")).pack(anchor="w",pady=(0,4))
        badge=ctk.CTkLabel(head,text=f"BUILD {APP_VERSION}",height=max(28,int(34*scale)),corner_radius=10,fg_color="#130B1B",text_color="#D89BFF",font=ctk.CTkFont(family="Consolas",size=9,weight="bold")); badge.pack(side="right",padx=(10,0))
        ctk.CTkLabel(right,text="PREPARANDO SEU AMBIENTE",text_color="#F8F5FB",font=ctk.CTkFont(family="Segoe UI",size=max(14,int(18*scale)),weight="bold")).pack(anchor="w",pady=(18,2))
        ctk.CTkLabel(right,text="Inicializando o ZKStrap em paralelo — esta tela nunca bloqueia o app.",text_color="#8E819D",font=ctk.CTkFont(size=max(8,int(10*scale)))).pack(anchor="w")

        modules=ctk.CTkFrame(right,fg_color="transparent"); modules.pack(fill="x",pady=(18,12))
        module_specs=[("CLIENT","ClientSettings"),("GRAPHICS","FPS & render"),("ASSETS","Cursor & fonts"),("SYSTEM","Watchdog & UI")]
        module_widgets=[]
        for i,(name,desc) in enumerate(module_specs):
            box=ctk.CTkFrame(modules,fg_color="#0D0A14",corner_radius=12,border_width=1,border_color="#2E203B")
            box.grid(row=i//2,column=i%2,sticky="ew",padx=5,pady=5); modules.grid_columnconfigure(i%2,weight=1)
            row=ctk.CTkFrame(box,fg_color="transparent"); row.pack(fill="x",padx=11,pady=(9,2))
            dot=ctk.CTkLabel(row,text="○",width=24,text_color="#6C5A7B",font=ctk.CTkFont(size=15,weight="bold")); dot.pack(side="left")
            lab=ctk.CTkLabel(row,text=name,text_color="#EDE7F3",font=ctk.CTkFont(family="Segoe UI",size=11,weight="bold")); lab.pack(side="left",padx=(5,0))
            ctk.CTkLabel(box,text=desc,text_color="#786D83",font=ctk.CTkFont(size=8)).pack(anchor="w",padx=40,pady=(0,9))
            module_widgets.append((box,dot,lab))
        state["module_widgets"]=module_widgets

        status_box=ctk.CTkFrame(right,fg_color="#08070D",corner_radius=13,border_width=1,border_color="#2B1D37")
        status_box.pack(fill="x",pady=(6,8))
        sr=ctk.CTkFrame(status_box,fg_color="transparent"); sr.pack(fill="x",padx=14,pady=(11,3))
        status=ctk.CTkLabel(sr,text="Inicializando núcleo…",text_color="#F4EFF7",font=ctk.CTkFont(family="Segoe UI",size=11,weight="bold")); status.pack(side="left")
        percent=ctk.CTkLabel(sr,text="00%",text_color="#D18CFF",font=ctk.CTkFont(family="Consolas",size=12,weight="bold")); percent.pack(side="right")
        sub=ctk.CTkLabel(status_box,text="configuração local",text_color="#776B82",font=ctk.CTkFont(family="Consolas",size=8)); sub.pack(anchor="w",padx=14,pady=(0,7))
        progress=ctk.CTkProgressBar(status_box,height=10,corner_radius=7,fg_color="#1C1824",progress_color="#B529F4"); progress.set(0); progress.pack(fill="x",padx=14,pady=(0,12))
        term=ctk.CTkLabel(right,text="[BOOT] aguardando módulos…",height=29,corner_radius=9,fg_color="#0C0911",text_color="#9F78C4",font=ctk.CTkFont(family="Consolas",size=8),anchor="w"); term.pack(fill="x",pady=(3,0))
        state.update(status=status,percent=percent,progress=progress,sub=sub,term=term)
        splash.deiconify(); splash.lift(); root.update_idletasks(); splash.update_idletasks(); splash.update()
        return state
    except Exception as exc:
        try:
            with open("teste_error.log","a",encoding="utf-8") as f:
                f.write("\n[SPLASH 3.13] "+repr(exc)+"\n")
        except Exception: pass
        try:
            if state.get("splash"): state["splash"].destroy()
        except Exception: pass
        try: root.attributes("-alpha",1.0)
        except Exception: pass
        return state


def _startup_splash_update(root,state,p,main,sub,term,pump=True):
    if not state or not state.get("splash"):
        _raise_if_splash_cancelled()
        _detached_splash_report(p,main,sub,term)
        return
    p=max(0.0,min(1.0,float(p))); state["p"]=p
    try:
        state["status"].configure(text=main); state["sub"].configure(text=sub); state["term"].configure(text="  "+term)
        state["progress"].set(p); state["percent"].configure(text=f"{int(p*100):02d}%")
        thresholds=(.18,.42,.70,.90)
        for i,(box,dot,lab) in enumerate(state.get("module_widgets",[])):
            if p >= thresholds[i]:
                box.configure(fg_color="#171020",border_color="#A42CE5"); dot.configure(text="✓",text_color="#D796FF"); lab.configure(text_color="#FFFFFF")
            elif p >= (thresholds[i-1] if i else 0):
                box.configure(fg_color="#120D19",border_color="#6B278D"); dot.configure(text="◔",text_color="#B65BE8")
            else:
                box.configure(fg_color="#0D0A14",border_color="#2E203B"); dot.configure(text="○",text_color="#6C5A7B")
        # Actual subtle animation on signature core.
        cv=state.get("logo_canvas"); arcs=state.get("arcs",())
        if cv is not None and len(arcs)==2:
            step=int(p*130)
            cv.itemconfigure(arcs[0],start=(20+step*2)%360); cv.itemconfigure(arcs[1],start=(204-step*2)%360)
            for n,node in enumerate(state.get("nodes",[])):
                cv.itemconfigure(node,fill="#D64EFF" if (step+n)%2==0 else "#76219E")
        if pump:
            state["splash"].lift(); state["splash"].update_idletasks(); state["splash"].update()
    except Exception:
        pass


def _startup_splash_finish(root,state,min_visible=3.15):
    """Completa o boot e troca da splash para o app sem intervalo preto."""
    try:
        if not state or not state.get("splash"):
            _raise_if_splash_cancelled()
            _detached_splash_report(.985,"Finalizando interface…","Últimos ajustes antes de abrir","[BOOT] almost ready")
            return
        elapsed=time.perf_counter()-state.get("started",time.perf_counter())
        # Se a UI montou rápido, usa o tempo restante para uma finalização suave.
        remaining=max(.42,float(min_visible)-elapsed)
        start=max(.88,float(state.get("p",.88)))
        steps=max(8,min(24,int(remaining/.035)))
        for i in range(steps+1):
            q=i/max(1,steps)
            # ease-out: o fim desacelera em vez de cortar.
            ease=1-(1-q)**3
            p=start+(1-start)*ease
            _startup_splash_update(root,state,p,
                "Finalizando interface..." if p < .995 else "Tudo pronto.",
                "Sincronizando componentes visuais" if p < .995 else "Abrindo ZKStrap",
                "[UI] interface ready" if p < .995 else "[OK] ZKSTRAP ready",pump=True)
            time.sleep(remaining/max(1,steps))

        splash=state.get("splash")
        try: splash.attributes("-topmost",False)
        except Exception: pass
        try: splash.destroy()
        except Exception: pass

        # A raiz já estava montada e transparente: só é revelada agora.
        try:
            root.deiconify()
            root.update_idletasks()
            root.lift()
            for a in (.18,.38,.62,.82,1.0):
                root.attributes("-alpha",a)
                root.update_idletasks(); root.update()
                time.sleep(.018)
        except Exception:
            try: root.attributes("-alpha",1.0)
            except Exception: pass
    except StartupCancelled:
        raise
    except Exception:
        try: root.attributes("-alpha",1.0)
        except Exception: pass


def _launch_detached_splash():
    """Abre a splash em outro processo e cria canais de status/cancelamento."""
    global _DETACHED_SPLASH_STATUS_FILE, _DETACHED_SPLASH_CANCEL_FILE
    if "--zk-splash" in sys.argv:
        return None
    token=f"{os.getpid()}_{uuid.uuid4().hex}"
    status_file=os.path.join(tempfile.gettempdir(),f"zkstrap_splash_{token}.json")
    cancel_file=os.path.join(tempfile.gettempdir(),f"zkstrap_splash_{token}.cancel")
    _DETACHED_SPLASH_STATUS_FILE=status_file
    _DETACHED_SPLASH_CANCEL_FILE=cancel_file
    try:
        for stale in (status_file,cancel_file,status_file+".tmp"):
            try:
                if os.path.exists(stale): os.remove(stale)
            except Exception: pass
        _detached_splash_report(.02,"Iniciando ZKStrap…","preparando processo principal","[BOOT] process start")
        if getattr(sys,"frozen",False):
            cmd=[sys.executable,"--zk-splash","--status-file",status_file,"--cancel-file",cancel_file]
        else:
            cmd=[sys.executable,os.path.abspath(__file__),"--zk-splash","--status-file",status_file,"--cancel-file",cancel_file]
        kwargs={}
        if os.name=="nt":
            try: kwargs["creationflags"]=subprocess.CREATE_NO_WINDOW
            except Exception: pass
        proc=subprocess.Popen(cmd,**kwargs)
        return {"proc":proc,"status_file":status_file,"cancel_file":cancel_file}
    except Exception as exc:
        try:
            with open("teste_error.log","a",encoding="utf-8") as f: f.write("\n[SPLASH 3.13.2.8 launcher] "+repr(exc)+"\n")
        except Exception: pass
        return None

def _splash_handle_proc(handle):
    if isinstance(handle,dict): return handle.get("proc")
    return handle

def _cleanup_splash_ipc(handle):
    global _DETACHED_SPLASH_STATUS_FILE, _DETACHED_SPLASH_CANCEL_FILE
    paths=[]
    if isinstance(handle,dict):
        paths += [handle.get("status_file"),handle.get("cancel_file")]
    paths += [_DETACHED_SPLASH_STATUS_FILE,_DETACHED_SPLASH_CANCEL_FILE]
    for path in paths:
        if path:
            for x in (path,path+".tmp"):
                try:
                    if os.path.exists(x): os.remove(x)
                except Exception: pass
    _DETACHED_SPLASH_STATUS_FILE=None; _DETACHED_SPLASH_CANCEL_FILE=None

def _close_detached_splash(handle, cleanup=True):
    proc=_splash_handle_proc(handle)
    if proc is not None:
        try:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=1.2)
                except Exception: pass
        except Exception: pass
    if cleanup: _cleanup_splash_ipc(handle)

def _arg_value(name, default=""):
    try:
        idx=sys.argv.index(name)
        return sys.argv[idx+1] if idx+1<len(sys.argv) else default
    except Exception:
        return default

def _run_splash_process():
    """Processo visual independente, sincronizado com o progresso real do app."""
    status_file=_arg_value("--status-file","")
    cancel_file=_arg_value("--cancel-file","")
    try:
        show_splash_screen(duration=14.0,status_file=status_file or None,cancel_file=cancel_file or None)
    except Exception as exc:
        try:
            with open("teste_error.log","a",encoding="utf-8") as f: f.write("\n[SPLASH 3.13.2.8 child] "+repr(exc)+"\n")
        except Exception: pass


class Tooltip:
    def __init__(self, widget, text, delay=450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._id = None
        self.tw = None
        self.mouse_y = 0
        widget.bind("<Enter>", self.on_enter)
        widget.bind("<Leave>", self.hide)
        widget.bind("<Motion>", self.on_motion)

    def on_enter(self, event):
        self.mouse_y = event.y
        self.unschedule()
        self._id = self.widget.after(self.delay, self.show_if_center)

    def on_motion(self, event):
        self.mouse_y = event.y

    def unschedule(self):
        if self._id:
            try:
                self.widget.after_cancel(self._id)
            except:
                pass
            self._id = None

    def show_if_center(self):
        try:
            h = self.widget.winfo_height()
            if h <= 0:
                return
            if not (h * 0.3 <= self.mouse_y <= h * 0.7):
                return
        except:
            pass
        self.show()

    def show(self):
        if self.tw:
            return
        try:
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except:
            x = y = 0
        self.tw = Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        lbl = Label(self.tw, text=self.text, justify='left', background='#111111', foreground='#FFFFFF', bd=0, padx=6, pady=4, font=("Consolas", 9))
        lbl.pack()

    def hide(self, event=None):
        self.unschedule()
        if self.tw:
            try:
                self.tw.destroy()
            except:
                pass
            self.tw = None

class ModernConfigApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"ZKStrap v{APP_VERSION}")
        self.geometry("1440x860")
        self.minsize(1040, 680)
        self.resizable(True, True)
        # A janela principal fica escondida até a splash realmente concluir 100%.
        try: self.withdraw()
        except Exception: pass
        # 3.13.2: a splash roda em processo separado. A UI principal nunca fica
        # presa atrás de um Toplevel de loading caso a montagem demore ou falhe.
        self._startup_state = None
        self._closing = False
        self.protocol("WM_DELETE_WINDOW", self._shutdown_app)
        # Abre em um tamanho confortável. A janela continua totalmente redimensionável
        # e pode ser maximizada normalmente; o layout abaixo se adapta ao tamanho.

        self.config_path = self.get_app_config_path()
        self.config_data = self.carregar_config_app()
        self._owner_state = _owner_state_read_global() if _owner_key_valid_global() else {}
        self._owner_panel = None
        self._owner_skip_shutdown_save = False
        self.sound_prompted = bool(self.config_data.get("sound_prompted", False))
        self.sounds_enabled = bool(self.config_data.get("sounds_enabled", False))
        self.sound_pack = str(self.config_data.get("sound_pack", DEFAULT_AUDIO_PACK) or DEFAULT_AUDIO_PACK)
        if self.sound_pack not in AUDIO_PACKS: self.sound_pack = DEFAULT_AUDIO_PACK
        self.music_enabled = bool(self.config_data.get("music_enabled", True))
        self.sfx_enabled = bool(self.config_data.get("sfx_enabled", True))
        try: self.music_volume=max(0.0,min(0.65,float(self.config_data.get("music_volume",0.22))))
        except Exception: self.music_volume=0.22
        try: self.sfx_volume=max(0.0,min(1.5,float(self.config_data.get("sfx_volume",1.0))))
        except Exception: self.sfx_volume=1.0
        self.spotify_web_volume_optin=bool(self.config_data.get("spotify_web_volume_optin",False))
        self._sound_prompt_open = False
        self._sound_prompt_panel = None
        self._sound_manager = ZKSoundManager(self, self.sounds_enabled, self.sound_pack, self.music_enabled, self.sfx_enabled, self.music_volume, self.sfx_volume)
        self._last_hover_sound = 0.0
        self._last_scroll_sound = 0.0
        tema_salvo = str(self.config_data.get("theme", "ZKStrap Core") or "ZKStrap Core")
        _theme_aliases = {
            "ZKVEZ Signature": "ZKStrap Core",
            "ZK Signature": "ZKStrap Core",
            "ZKSTRAP Signature": "ZKStrap Core",
        }
        tema_salvo = _theme_aliases.get(tema_salvo, tema_salvo)
        self.tema_atual = tema_salvo if tema_salvo in TEMAS else "ZKStrap Core"
        if self.tema_atual not in TEMAS:
            self.tema_atual = next(iter(TEMAS))
        self.cor_personalizada = self.config_data.get("accent_color", "")
        _saved_font = str(self.config_data.get("font", "") or "").strip()
        # 3.13 migra o antigo default Consolas para Segoe UI. Consolas continua
        # disponível no menu e permanece reservado aos micro-rótulos técnicos.
        self.fonte_ui = "Segoe UI" if (not _saved_font or _saved_font == "Consolas") else _saved_font
        # v2.1: módulos específicos em vez de presets genéricos.
        self.preset_grafico = "Padrão"  # compatibilidade com config antiga
        self.resolucao_jogo = str(self.config_data.get("game_resolution", "1280x720") or "1280x720")
        self.custom_width = int(self.config_data.get("custom_width", 1280) or 1280)
        self.custom_height = int(self.config_data.get("custom_height", 720) or 720)
        self.custom_flags = {}  # v2.7: editor livre removido; somente opções do executor são aplicadas
        self.last_custom_keys = set(self.config_data.get("last_custom_keys", []))
        self.module_states = self.config_data.get("modules", {}) if isinstance(self.config_data.get("modules", {}), dict) else {}
        if not self.module_states:
            # Migração simples da v2.0.
            self.module_states = {
                "base": bool(self.config_data.get("switch_whitelist", False)),
                "gray_sky": bool(self.config_data.get("switch_sky", False)),
            }
        # v2.5: converte vários switches antigos nos seis controles principais.
        _old_states = dict(self.module_states)
        self.module_states = {
            "performance_boost": bool(_old_states.get("performance_boost", _old_states.get("batata_total", False) or any(_old_states.get(k, False) for k in ("textures", "grass", "msaa", "lod", "frm_low", "voxelizer", "d3d11")))),
            "gray_sky": bool(_old_states.get("gray_sky", _old_states.get("performance_boost", False))),
            "fps_unlock": bool(_old_states.get("fps_unlock", False)),
            "ping_boost": bool(_old_states.get("ping_boost", self.config_data.get("switch_ping", False))),
            "telemetry_off": bool(_old_states.get("telemetry_off", False)),
            "micro_opt": bool(_old_states.get("micro_opt", False)),
            "draco_aura": bool(_old_states.get("draco_aura", False)),
        }
        self.advanced_values = self.config_data.get("advanced_values", {}) if isinstance(self.config_data.get("advanced_values", {}), dict) else {}
        for k in ("texture", "msaa", "frm", "grass", "lod"):
            self.advanced_values.setdefault(k, "Auto")

        # v2.4.1: watchdog + cursor real do Roblox.
        self.config_watchdog_enabled = bool(self.config_data.get("config_watchdog_enabled", False))
        self.micro_fps_target = str(self.config_data.get("micro_fps_target", "144"))
        if self.micro_fps_target not in {"30", "60", "120", "144", "165", "240", "360", "540", "1000"}:
            self.micro_fps_target = "144"
        self.cursor_pack = str(self.config_data.get("cursor_pack", "Roblox Padrão") or "Roblox Padrão")
        try:
            self.cursor_visual_size = max(8, min(48, int(self.config_data.get("cursor_visual_size", 24) or 24)))
        except Exception:
            self.cursor_visual_size = 24
        self.cursor_auto_remove_white = bool(self.config_data.get("cursor_auto_remove_white", True))
        self.cursor_anchor_mode = str(self.config_data.get("cursor_anchor_mode", "Ponta no centro") or "Ponta no centro")
        self.theme_overrides = self.config_data.get("theme_overrides", {}) if isinstance(self.config_data.get("theme_overrides", {}), dict) else {}
        if "ZKVEZ Signature" in self.theme_overrides and "ZKStrap Core" not in self.theme_overrides:
            try:
                self.theme_overrides["ZKStrap Core"] = dict(self.theme_overrides.get("ZKVEZ Signature", {}))
            except Exception:
                pass
        self.game_font_source = str(self.config_data.get("game_font_source", "") or "")
        self.current_page_key = str(self.config_data.get("current_page", "home") or "home")
        if self.current_page_key == "resolution":
            self.current_page_key = "fps"
        self.linked_profile = self.config_data.get("linked_profile", {}) if isinstance(self.config_data.get("linked_profile", {}), dict) else {}
        # v3.3: onboarding local. O username serve apenas para personalizar o tutorial
        # e pré-preencher a busca pública de perfil; nunca solicita senha, e-mail ou nome real.
        self.onboarding_username = str(self.config_data.get("onboarding_username", "") or "").strip().lstrip("@")
        self.tutorial_completed = bool(self.config_data.get("tutorial_completed", False))
        # v3.6: interface progressiva. O modo avançado fica recolhido por padrão
        # e a preferência é persistida localmente.
        self.advanced_mode = bool(self.config_data.get("advanced_mode", False))
        self._tutorial_window = None  # legado; o tutorial v3.6 não cria Toplevel
        self._tutorial_panel = None
        self._tutorial_spotlight = None
        self._tutorial_step_index = 0
        self._tutorial_replay = False
        self._search_overlay = None
        self._search_result_buttons = []
        self._toast_items = []
        self._profile_avatar_ctk = None
        self._profile_search_busy = False
        self._visible_page = None
        self._pending_page = None
        self._page_anim_job = None
        self.compact_mode = bool(self.config_data.get("compact_mode", False))
        self.bg_capture_changed_by_app = bool(self.config_data.get("bg_capture_changed_by_app", False))
        self.last_benchmark = self.config_data.get("last_benchmark", {}) if isinstance(self.config_data.get("last_benchmark", {}), dict) else {}
        self.last_apply_summary = self.config_data.get("last_apply_summary", {}) if isinstance(self.config_data.get("last_apply_summary", {}), dict) else {}
        # v3.5: Combo Planner. Builds ficam apenas no config local do ZKStrap.
        _combo_raw = self.config_data.get("combo_entries", []) if isinstance(self.config_data.get("combo_entries", []), list) else []
        # Configs antigas/corrompidas não podem derrubar a página inteira.
        self.combo_entries = []
        for _entry in _combo_raw:
            if not isinstance(_entry, dict):
                continue
            _clean = dict(_entry)
            _clean.setdefault("id", uuid.uuid4().hex)
            _clean.setdefault("name", "Combo")
            _clean.setdefault("style", "")
            _clean.setdefault("fruit", "")
            _clean.setdefault("sword", str(_clean.get("slot3", "") or ""))
            _clean.setdefault("gun", str(_clean.get("slot4", "") or ""))
            _clean["slot3"] = str(_clean.get("sword", "") or "")
            _clean["slot4"] = str(_clean.get("gun", "") or "")
            _clean.setdefault("combo", "")
            self.combo_entries.append(_clean)
        self._combo_thumb_cache = {}
        self._combo_fetching = set()
        self._combo_fetch_sem = threading.Semaphore(4)
        self._combo_online_thumbs = True
        self._combo_prefetching = set()
        self._combo_refresh_job = None

        # v3.14: Blox Hub / Roulette / Creator / Setups / Spotify.
        self.roulette_inventory = self.config_data.get("roulette_inventory", {}) if isinstance(self.config_data.get("roulette_inventory", {}), dict) else {}
        self.roulette_history = self.config_data.get("roulette_history", []) if isinstance(self.config_data.get("roulette_history", []), list) else []
        self.roulette_favorites = self.config_data.get("roulette_favorites", []) if isinstance(self.config_data.get("roulette_favorites", []), list) else []
        self.last_roulette_build = self.config_data.get("last_roulette_build", {}) if isinstance(self.config_data.get("last_roulette_build", {}), dict) else {}
        self.creator_projects = self.config_data.get("creator_projects", []) if isinstance(self.config_data.get("creator_projects", []), list) else []
        self.creator_used_ideas = self.config_data.get("creator_used_ideas", []) if isinstance(self.config_data.get("creator_used_ideas", []), list) else []
        self.creator_challenges = []  # v3.16.1: ativos são SEMPRE temporários e somem ao fechar.
        self.creator_history = self.config_data.get("creator_history", []) if isinstance(self.config_data.get("creator_history", []), list) else []
        self.creator_total_completed = int(self.config_data.get("creator_total_completed", 0) or 0)
        self.unlocked_secret_themes = set(self.config_data.get("unlocked_secret_themes", []) if isinstance(self.config_data.get("unlocked_secret_themes", []), list) else [])
        self.secret_music_seconds = int(self.config_data.get("secret_music_seconds", 0) or 0)
        self.roulette_roll_count = int(self.config_data.get("roulette_roll_count", 0) or 0)
        self._creator_celebration_open = False
        self._creator_session_started_at = 0.0
        self._creator_session_initial_count = 0
        self._creator_secret_reveal_open = False
        self._secret_music_job = None
        if self.creator_total_completed >= 5:
            self.unlocked_secret_themes.add("Party")
        if len(self.combo_entries) >= 5:
            self.unlocked_secret_themes.add("Architect")
        if self.roulette_roll_count >= 20:
            self.unlocked_secret_themes.add("Jackpot")
        if self.secret_music_seconds >= 60:
            self.unlocked_secret_themes.add("Frequency")
        self.zk_setups = self.config_data.get("zk_setups", []) if isinstance(self.config_data.get("zk_setups", []), list) else []
        self.zk_setups = self.zk_setups[:5]
        self.setup_edit_id = ""  # modo de edição nunca atravessa reinicializações
        self.last_setup_snapshot = self.config_data.get("last_setup_snapshot", {}) if isinstance(self.config_data.get("last_setup_snapshot", {}), dict) else {}
        # v3.15.4: Spotify is local-only. OAuth/API credentials from older builds are intentionally ignored.
        self.spotify_client_id = ""
        self.spotify_auth = {}
        self.spotify_mini_hidden = bool(self.config_data.get("spotify_mini_hidden", True))
        self._spotify_mini_frame = None
        self._spotify_poll_job = None
        self._spotify_volume_job = None
        self._spotify_polling = False
        self._spotify_pending_volume = 50
        self._spotify_last_error = ""
        self._spotify_current = {}
        self._spotify_art_ctk = None
        self._spotify_mini_art_ctk = None
        self._spotify_snapshot_busy = False
        self._spotify_last_snapshot_at = 0.0
        self._spotify_last_volume_probe = 0.0
        # v3.18.0: Update Center. User data stays in LOCALAPPDATA; only program files are replaced.
        self.update_channel = str(self.config_data.get("update_channel", "stable") or "stable").lower()
        if self.update_channel not in UPDATE_MANIFEST_URLS:
            self.update_channel = "stable"
        # Dev channel only makes sense on the owner's machine; public installs fall back to beta/stable.
        if self.update_channel == "dev" and not _owner_key_valid_global():
            self.update_channel = "beta"
        self.update_auto_check = bool(self.config_data.get("update_auto_check", True))
        self._update_manifest = {}
        self._update_check_busy = False
        self._update_download_busy = False
        self._update_download_cancel = False
        self._creator_timer_job = None
        self._scroll_active_until = 0.0

        # v3.10: ZK Dialogue Engine — fluxo guiado, sem modelo generativo e sem campo livre.
        self.zkai_mode = "zkstrap"
        self.zkai_histories = {"zkstrap": [], "pvp": []}
        self.zkai_greeting_done = False
        self.zkai_dialog_node = None
        self.zkai_dialog_tags = set()
        self.zkai_dialog_facts = {}
        self._zkai_typing_job = None
        self._zkai_typing_row = None
        self._zkai_typing_label = None
        self._zkai_typing_anim_job = None
        self._zkai_typing_step = 0
        if self.cursor_anchor_mode not in {"Ponta no centro", "Centro", "Preservar 64x64"}:
            self.cursor_anchor_mode = "Ponta no centro"
        self._watchdog_last_message = ""
        self._watchdog_last_pids = tuple()
        self._watchdog_editor_state = ""

        # Restaura personalizações de cada tema.
        for _theme_name in list(TEMAS.keys()):
            TEMAS[_theme_name] = TEMAS_PADRAO[_theme_name].copy()
            _ov = self.theme_overrides.get(_theme_name, {}) if isinstance(self.theme_overrides.get(_theme_name, {}), dict) else {}
            for _k, _v in _ov.items():
                if _k in TEMAS[_theme_name] and self._cor_hex_valida(_v):
                    TEMAS[_theme_name][_k] = _v.upper()
        if self._cor_hex_valida(self.cor_personalizada) and not self.theme_overrides.get(self.tema_atual):
            TEMAS[self.tema_atual]["accent"] = self.cor_personalizada
            TEMAS[self.tema_atual]["border"] = self.cor_personalizada
            TEMAS[self.tema_atual]["hover"] = self._clarear_hex(self.cor_personalizada, 0.22)
        self.configure(fg_color=TEMAS[self.tema_atual]["bg"])
        _startup_splash_update(self,self._startup_state,.24,"Preferências carregadas","Tema, perfil e configurações locais","[CFG] local settings ready",pump=True)

        self.idioma = self.config_data.get("language", "pt")
        if self.idioma not in ("pt", "en"):
            self.idioma = "pt"
        self.tr = {
            'pt': {
                'lista_branca': "Whitelist",
                'ceu_cinza': "Céu Cinza + FPS",
                'ping_opt': "Ping FastFlags (LEGADO)",
                'modulos': "// MÓDULOS PERFORMANCE",
                'localizar': "LOCALIZAR ARQUIVOS DO ROBLOX",
                'diretorio_buscando': "Diretório: Buscando...",
                'diretorio_nao_encontrado': "Diretório: Não encontrado",
                'salvar_compilacao': "APLICAR CONFIGURAÇÕES",
                'resetar': "RESETAR PARA O ORIGINAL",
                'limpar_logs': "LIMPAR LOGS E CACHE",
                'fechar_pesados': "FECHAR APPS PESADOS",
                'sobre_tab': "SOBRE",
                'config_tab': "CONFIGURAÇÕES",
                'manut_tab': "DESEMPENHO",
                'sugest_tab': "SUGESTÕES & REPORTAR BUGS",
                'sugest_hint': "Envie sugestões ou reporte bugs usando o formulário abaixo.",
                'sug_type_vals': ["Sugestão", "Reportar Bug"],
                'enviar': "ENVIAR",
                'about_me_tab': "SOBRE MIM",
                'tooltip_whitelist': "Ativa o pack de flags da whitelist (mantém compatibilidade).",
                'tooltip_sky': "Aplica configurações para reduzir efeitos e melhorar FPS.",
                'tooltip_ping': "Flags de rede antigas não estão na allowlist atual do Roblox e podem ser ignoradas.",
                'tooltip_select_roblox': "Clique para selecionar a pasta do Roblox (a pasta 'version-*' que contém RobloxPlayerBeta.exe).",
                'tooltip_pasta': "Mostra a pasta detectada do Roblox. Se não encontrada, siga as instruções exibidas.",
                'tooltip_theme': "Escolha o tema visual da interface.",
                'tooltip_lang': "Escolha o idioma da interface.",
                'tooltip_apply': "Salva as flags ativadas em ClientAppSettings.json (fará backup automático).",
                'manut_desc': "Ferramentas para melhorar a sessão do Roblox e diagnosticar gargalos.",
                'reset_confirm_title': "Confirmar Reset",
                'reset_success': "Roblox resetado para o padrão!",
                'clean_success': "Limpeza concluída!",
                'no_dir_warning': "Vincule o diretório do Roblox primeiro!",
                'short_message_warning': "A mensagem está muito curta!",
                'sug_sent': "Sugestão enviada!",
                'webhook_fail': "Falha na conexão ao enviar sugestão.",
                'confirm_kill_title': "Confirmar",
                'confirm_kill_body': "Os seguintes processos foram encontrados:\n\n{lista}\n\nDeseja fechá-los agora? Isso pode causar perda de dados em apps não salvos.",
                'about_notice_title': "Localização não encontrada",
                'about_location_instructions': "Para localizar manualmente:\n\n1) Abra o Explorador de Arquivos (Win+E).\n2) Cole na barra de endereços e pressione Enter:\n   %LOCALAPPDATA%\\Roblox\\Versions\n   OU\n   C:\\Program Files (x86)\\Roblox\\Versions\n\n3) Dentro desta pasta, abra a subpasta mais recente que começa com 'version-' e selecione-a no botão 'LOCALIZAR ARQUIVOS DO ROBLOX'.",
                'msg_ok': "OK",
                'msg_error': "Erro",
                'msg_warning': "Aviso",
                'smart_info': "Se o Windows mostrar SmartScreen, clique em Mais informações → Executar mesmo assim.",
                'channel_text': "Canal do YouTube"
            },
            'en': {
                'lista_branca': "Whitelist",
                'ceu_cinza': "Gray Sky + FPS",
                'ping_opt': "Ping FastFlags (LEGACY)",
                'modulos': "// PERFORMANCE MODULES",
                'localizar': "FIND ROBLOX FILES",
                'diretorio_buscando': "Directory: Searching...",
                'diretorio_nao_encontrado': "Directory: Not found",
                'salvar_compilacao': "APPLY SETTINGS",
                'resetar': "RESET TO ORIGINAL",
                'limpar_logs': "CLEAN LOGS & CACHE",
                'fechar_pesados': "CLOSE HEAVY APPS",
                'sobre_tab': "ABOUT",
                'config_tab': "SETTINGS",
                'manut_tab': "MAINTENANCE",
                'sugest_tab': "SUGGESTIONS & REPORT BUGS",
                'sugest_hint': "Send suggestions or report bugs using the form below.",
                'sug_type_vals': ["Suggestion", "Report Bug"],
                'enviar': "SEND",
                'about_me_tab': "ABOUT ME",
                'tooltip_whitelist': "Enable the whitelist flags pack (keeps compatibility).",
                'tooltip_sky': "Apply settings to reduce effects and improve FPS.",
                'tooltip_ping': "Old network flags are not in Roblox current allowlist and may be ignored.",
                'tooltip_select_roblox': "Click to select the Roblox folder (the 'version-*' folder containing RobloxPlayerBeta.exe).",
                'tooltip_pasta': "Shows the detected Roblox folder. If not found, follow the displayed instructions.",
                'tooltip_theme': "Choose the visual theme of the interface.",
                'tooltip_lang': "Choose the UI language.",
                'tooltip_apply': "Save enabled flags into ClientAppSettings.json (will auto-backup).",
                'manut_desc': "Tools to reset the game\nor clean temporary files.",
                'reset_confirm_title': "Confirm Reset",
                'reset_success': "Roblox reset to defaults!",
                'clean_success': "Cleanup completed!",
                'no_dir_warning': "Bind the Roblox directory first!",
                'short_message_warning': "Message is too short!",
                'sug_sent': "Suggestion sent!",
                'webhook_fail': "Failed to send suggestion.",
                'confirm_kill_title': "Confirm",
                'confirm_kill_body': "The following processes were found:\n\n{lista}\n\nDo you want to close them now? This may cause unsaved data loss.",
                'about_notice_title': "Location not found",
                'about_location_instructions': "To locate manually:\n\n1) Open File Explorer (Win+E).\n2) Paste into address bar and press Enter:\n   %LOCALAPPDATA%\\Roblox\\Versions\n   OR\n   C:\\Program Files (x86)\\Roblox\\Versions\n\n3) Inside that folder open the most recent folder starting with 'version-' and select it using the 'FIND ROBLOX FILES' button.",
                'msg_ok': "OK",
                'msg_error': "Error",
                'msg_warning': "Warning",
                'smart_info': "If Windows shows SmartScreen, click More info → Run anyway.",
                'channel_text': "YouTube Channel"
            }
        }

        self.texto_sobre = {
            'pt': """ZKSTRAP

Este projeto nasceu de uma necessidade simples: otimizar o desempenho do Roblox sem comprometer a segurança da sua conta.

O objetivo do zkstrap é facilitar configurações locais de desempenho sem injetar código nem ler a memória do Roblox. Esta versão não possui editor livre: apenas os módulos visíveis no executor são aplicados. O Roblox pode ignorar configurações que não estejam disponíveis na allowlist atual do cliente.

🛡️ Compromisso de Segurança

Este software foi desenvolvido com foco total em performance e segurança. O código é 100% livre de malware, sendo o seu único propósito a otimização técnica do motor gráfico do jogo.

⚠️ Aviso de Distribuição

A segurança dos meus utilizadores é a minha prioridade. Por isso, nunca utilize versões deste programa que não tenham sido distribuídas diretamente por mim através dos meus canais oficiais (GitHub ou Discord). Versões obtidas em fontes de terceiros podem conter código modificado e não são seguras.

Desenvolvido com foco na comunidade.""",
            'en': """ZKSTRAP

This project was born from a simple need: to optimize Roblox performance without compromising account security.

zkstrap is designed to manage local performance settings without injecting code or reading Roblox memory. This build has no free-form editor: only the options exposed by ZKStrap are applied. Roblox may ignore settings that are not available in the current client allowlist.

🛡️ Security Commitment

This software was developed with full focus on performance and security. The code is free of malware and its sole purpose is to provide technical optimization for the game's graphics engine.

⚠️ Distribution Notice

User safety is my priority. Never use versions of this program obtained from third-party sources — only download from my official channels (GitHub or Discord). Third-party builds may contain modified code and are not safe.

Built with the community in mind."""
        }

        self.author_texts = {
            'pt': (
                "Meu nome é zkvez e faço alguns vídeos de Blox Fruits.\n\n"
                "Criei o ZKStrap depois de usar FastFlags em um PC fraco e perceber como pequenos ajustes podiam fazer diferença. "
                "O projeto cresceu e hoje reúne desempenho, personalização e ferramentas para quem joga Roblox e Blox Fruits. "
                "A fase de reconstrução intensiva começou em 10/09/2026 e continua evoluindo versão após versão.\n\n"
                "Se quiser acompanhar meu trabalho, se inscreve no canal e dá uma força!"
            ),
            'en': (
                "My name is zkvez and I make Blox Fruits videos.\n\n"
                "I created ZKStrap to put Roblox performance and configuration tools in one simple interface. "
                "The current version avoids injection and memory reading and applies only the options exposed in the interface. "
                "The intensive rebuild phase started on 2026-09-10 and keeps evolving version after version.\n\n"
                "If you want to follow my work, subscribe to the channel and show some support!"
            )
        }

        self.flag_whitelist = {
            "FFlagHandleAltEnterFullscreenManually": False, "DFFlagTextureQualityOverrideEnabled": True,
            "DFIntDebugFRMQualityLevelOverride": 1, "DFIntTextureQualityOverride": 0,
            "FIntGrassMovementReducedMotionFactor": 0, "DFIntCSGLevelOfDetailSwitchingDistanceL34": 0,
            "DFIntCSGLevelOfDetailSwitchingDistanceL23": 0, "DFIntCSGLevelOfDetailSwitchingDistanceL12": 0,
            "DFIntCSGLevelOfDetailSwitchingDistance": 0, "FIntDebugForceMSAASamples": 0,
            "DFFlagDisableDPIScale": False, "DFFlagDebugPauseVoxelizer": True, "FFlagDebugGraphicsPreferD3D11": True,
            "FIntFRMMaxGrassDistance": 0, "FIntFRMMinGrassDistance": 0, "disabled_FFlagDebugGraphicsPreferVulkan": True,
            "disabled_FFlagDebugGraphicsPreferOpenGL": True, "disabled_FFlagDebugGraphicsDisableDirect3D11": True,
            "disabled_FFlagDebugSkyGray": True
        }

        self.flag_gray_sky = {
            "DFFlagAcceleratorUpdateOnPropsAndValueTimeChange": "True", "DFFlagTextureQualityOverrideEnabled": "True",
            "DFFlagDebugSkipMeshVoxelizer": "True", "DFFlagMergeFakeInputEvents4": "True", "DFFlagDebugPauseVoxelizer": "True",
            "DFFlagDisableDPIScale": "True", "DFFlagSupportMeshLOD": "True", "DFFlagAggCpuMemRCC": "True",
            "DFIntCSGLevelOfDetailSwitchingDistanceL34": "0", "DFIntCSGLevelOfDetailSwitchingDistanceL23": "0",
            "DFIntCSGLevelOfDetailSwitchingDistanceL12": "0", "DFIntCSGLevelOfDetailSwitchingDistance": "0",
            "DFIntDebugFRMQualityLevelOverride": "1", "DFIntRenderPostFxBasePixelCount": "-1", "DFIntCanHideGuiGroupId": "32380007",
            "DFIntTextureQualityOverride": "0", "FFlagEnablePreferredTextSizeGuiService": "True",
            "FFlagHandleAltEnterFullscreenManually": "False", "FFlagRenderEnablePreferredTextSizeScale": "True",
            "FFlagDebugGraphicsPreferD3D11": "True", "FFlagRenderNoLowFrmBloom": "True", "FFlagNewLightAttenuation": "True",
            "FFlagDebugSkyGray": "True", "FIntDebugFRMOptionalMSAALevelOverride": "0"
        }

        self.flag_otimizar_ping = {
            "DFIntBandwidthManagerApplicationDefaultBps": "1024000", "DFIntBandwidthManagerDataSenderMaxWorkCatchupMs": "8",
            "DFFlagAlwaysSkipDiskCache": "False", "DFFlagHttpSslCertCacheEnabled3": "True", "DFIntFileCacheReserveSize": "2147483647",
            "DFIntMemCacheMaxCapacityMB": "2147483647", "DFIntTaskSchedulerBackgroundCycleRateMs": "1", "FFlagResetCacheOnLeaveGame": "True",
            "FIntTaskSchedulerMaxTempArenaSizeBytes": "2147483647", "DFIntClientPacketExcessMicroseconds": "1000", "DFIntClientPacketHealthyAllocationPercent": "20",
            "DFIntClientPacketMaxDelayMs": "1", "DFIntClientPacketMaxFrameMicroseconds": "200", "DFIntClientPacketMinMicroseconds": "1",
            "DFIntLargePacketQueueSizeCutoffMB": "1000", "DFIntMaxProcessPacketsJobScaling": "5000000", "DFIntMaxProcessPacketsStepsAccumulated": "5"
        }

        self.pasta_roblox_salva = self.config_data.get("roblox_dir", "")
        _startup_splash_update(self,self._startup_state,.48,"Preparando interface…","Montando shell, navegação e páginas","[UI] building workspace",pump=True)
        self.inicializar_efeito_matrix()
        self.criar_interface()
        _startup_splash_update(self,self._startup_state,.78,"Interface montada","Sincronizando módulos e temas","[UI] components mounted",pump=True)
        try:
            for key, sw in getattr(self, "module_switches", {}).items():
                data = FLAG_MODULES[key]
                sw.configure(text=data["pt"] if self.idioma == "pt" else data["en"])
        except Exception:
            pass
        self.restaurar_estado_interface()
        # A varredura de fontes em toda a árvore era uma das tarefas que seguravam a abertura.
        # Agora roda depois que a janela já apareceu.
        self.after(700, lambda: self.aplicar_fonte_widgets(self))

        # Layout responsivo com debounce para não recalcular dezenas de vezes
        # durante o redimensionamento da janela.
        self._layout_job = None
        self._last_layout_size = (0, 0)
        self.bind("<Configure>", self._on_root_configure, add="+")
        self.bind("<Control-k>", self.abrir_busca_universal, add="+")
        self.bind("<Control-K>", self.abrir_busca_universal, add="+")
        self.bind("<Escape>", self._handle_global_escape, add="+")
        self.bind("<F11>", self._toggle_window_fullscreen, add="+")
        self.bind("<Alt-Return>", self._toggle_window_fullscreen, add="+")
        self.after(120, self._apply_responsive_layout)

        try:
            self.load_icon()
        except Exception as e:
            try:
                self.log_output(f"[-] load_icon exception: {e}")
            except:
                pass

        self.loop_animacao = True
        self.after(40, self.animar_chuva_matrix_frame)
        self.pulse_phase = 0.0
        self.after(60, self.animate_title_pulse)

        threading.Thread(target=self.tentar_achar_roblox_automatico, daemon=True).start()
        self.loop_verificar_jogo = True
        threading.Thread(target=self.watchdog_processo_jogo_thread, daemon=True).start()
        threading.Thread(target=self.monitorar_ping_thread, daemon=True).start()
        # O watchdog de configuração roda no thread da UI para não acessar widgets Tk a partir de worker threads.
        self.after(5000, self.watchdog_clientsettings_tick)

        self.log_output("[*] Hub carregado com sucesso.")
        _startup_splash_update(self,self._startup_state,.94,"Validando sistema…","Watchdog, assets e estado do cliente","[SYS] startup checks complete",pump=True)
        _startup_splash_finish(self,self._startup_state,min_visible=2.85)

        # Áudio é opt-in. No primeiro uso o app mostra um painel focado sobre um
        # snapshot desfocado da interface; o tutorial espera essa escolha terminar.
        try:
            self.bind_all("<Button-1>", self._global_click_sound, add="+")
            self.bind_all("<MouseWheel>", self._global_scroll_sound, add="+")
        except Exception:
            pass
        self.after(650, self._maybe_show_sound_consent)
        self.after(1050, self._start_ambient_if_enabled)
        self.after(1800, self._secret_music_tick)
        if getattr(self, "update_auto_check", True):
            self.after(4200, lambda: self._update_check_async(silent=True))

        # Primeiro acesso: abre após a interface terminar de montar e após a escolha
        # de áudio, para os dois overlays nunca brigarem entre si.
        self.after(1150, self._maybe_show_first_run_tutorial)

    def _toggle_window_fullscreen(self, event=None):
        """F11 / Alt+Enter: fallback seguro para fullscreen em qualquer perfil."""
        try:
            current=bool(self.attributes("-fullscreen"))
            self.attributes("-fullscreen",not current)
            return "break"
        except Exception:
            try:
                self.state("zoomed")
            except Exception:
                pass
        return "break"

    @staticmethod
    def _cor_hex_valida(cor):
        if not isinstance(cor, str) or len(cor) != 7 or not cor.startswith("#"):
            return False
        try:
            int(cor[1:], 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _clarear_hex(cor, fator=0.2):
        try:
            r, g, b = (int(cor[i:i+2], 16) for i in (1, 3, 5))
            r = min(255, int(r + (255-r)*fator))
            g = min(255, int(g + (255-g)*fator))
            b = min(255, int(b + (255-b)*fator))
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return cor

    def get_app_config_path(self):
        """Main profile by default; OWNER TEST PROFILE is isolated and never overwrites real data."""
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        if _owner_test_profile_enabled():
            pasta=os.path.join(_owner_vault_dir(),"TEST_PROFILE")
            try:
                os.makedirs(pasta,exist_ok=True)
                return os.path.join(pasta,"config.json")
            except Exception:
                pass
        pasta = os.path.join(base, "ZKSTRAP")
        try:
            os.makedirs(pasta, exist_ok=True)
            novo = os.path.join(pasta, "config.json")
            legado = os.path.join(base, "ZKVEZ_EXECUTOR", "config.json")
            if not os.path.exists(novo) and os.path.exists(legado):
                try:
                    shutil.copy2(legado, novo)
                except Exception:
                    pass
            return novo
        except Exception:
            return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "config.json")

    def carregar_config_app(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                return dados if isinstance(dados, dict) else {}
        except Exception:
            pass
        return {}

    def salvar_config_app(self):
        try:
            dados = {
                "version": APP_VERSION,
                "theme": getattr(self, "tema_atual", "ZKStrap Core"),
                "accent_color": getattr(self, "cor_personalizada", ""),
                "font": getattr(self, "fonte_ui", "Segoe UI"),
                "language": getattr(self, "idioma", "pt"),
                "roblox_dir": getattr(self, "pasta_roblox_salva", ""),
                "performance_preset": "Padrão",
                "game_resolution": str(getattr(self, "resolucao_jogo", "1280x720")),
                "custom_width": int(getattr(self, "custom_width", 1280)),
                "custom_height": int(getattr(self, "custom_height", 720)),
                "custom_flags": getattr(self, "custom_flags", {}),
                "last_custom_keys": sorted(getattr(self, "last_custom_keys", set())),
                # Salva a partir do estado Python, sem consultar widgets Tk. Isso deixa esta função segura
                # quando chamada por threads de detecção do diretório do Roblox.
                "modules": dict(getattr(self, "module_states", {})),
                "advanced_values": dict(getattr(self, "advanced_values", {})),
                "config_watchdog_enabled": bool(getattr(self, "config_watchdog_enabled", False)),
                "micro_fps_target": str(getattr(self, "micro_fps_target", "144")),
                "cursor_pack": str(getattr(self, "cursor_pack", "Roblox Padrão")),
                "cursor_visual_size": int(getattr(self, "cursor_visual_size", 24)),
                "cursor_auto_remove_white": bool(getattr(self, "cursor_auto_remove_white", True)),
                "cursor_anchor_mode": str(getattr(self, "cursor_anchor_mode", "Ponta no centro")),
                "theme_overrides": dict(getattr(self, "theme_overrides", {})),
                "game_font_source": str(getattr(self, "game_font_source", "")),
                "current_page": str(getattr(self, "current_page_key", "home")),
                "linked_profile": dict(getattr(self, "linked_profile", {})),
                "onboarding_username": str(getattr(self, "onboarding_username", "")),
                "tutorial_completed": bool(getattr(self, "tutorial_completed", False)),
                "sound_prompted": bool(getattr(self, "sound_prompted", False)),
                "sounds_enabled": bool(getattr(self, "sounds_enabled", False)),
                "sound_pack": str(getattr(self, "sound_pack", DEFAULT_AUDIO_PACK)),
                "music_enabled": bool(getattr(self, "music_enabled", True)),
                "sfx_enabled": bool(getattr(self, "sfx_enabled", True)),
                "music_volume": float(getattr(self, "music_volume", 0.22)),
                "sfx_volume": float(getattr(self, "sfx_volume", 1.0)),
                "spotify_web_volume_optin": bool(getattr(self, "spotify_web_volume_optin", False)),
                "advanced_mode": bool(getattr(self, "advanced_mode", False)),
                "compact_mode": bool(getattr(self, "compact_mode", False)),
                "bg_capture_changed_by_app": bool(getattr(self, "bg_capture_changed_by_app", False)),
                "last_benchmark": dict(getattr(self, "last_benchmark", {})),
                "last_apply_summary": dict(getattr(self, "last_apply_summary", {})),
                "combo_entries": list(getattr(self, "combo_entries", [])),
                "roulette_inventory": dict(getattr(self, "roulette_inventory", {})),
                "roulette_history": list(getattr(self, "roulette_history", []))[-60:],
                "roulette_favorites": list(getattr(self, "roulette_favorites", []))[-60:],
                "last_roulette_build": dict(getattr(self, "last_roulette_build", {})),
                "creator_projects": list(getattr(self, "creator_projects", []))[-80:],
                "creator_used_ideas": list(getattr(self, "creator_used_ideas", []))[-200:],
                "creator_history": list(getattr(self, "creator_history", []))[-300:],
                "creator_total_completed": int(getattr(self, "creator_total_completed", 0) or 0),
                "unlocked_secret_themes": sorted(list(getattr(self, "unlocked_secret_themes", set()))),
                "secret_music_seconds": int(getattr(self, "secret_music_seconds", 0) or 0),
                "roulette_roll_count": int(getattr(self, "roulette_roll_count", 0) or 0),
                "zk_setups": list(getattr(self, "zk_setups", []))[:5],
                "last_setup_snapshot": dict(getattr(self, "last_setup_snapshot", {})),
                "spotify_mini_hidden": bool(getattr(self, "spotify_mini_hidden", True)),
                "update_channel": str(getattr(self, "update_channel", "stable")),
                "update_auto_check": bool(getattr(self, "update_auto_check", True)),
                # chaves antigas mantidas para migração/compatibilidade
                "switch_whitelist": bool(getattr(self, "module_states", {}).get("base", False)),
                "switch_sky": bool(getattr(self, "module_states", {}).get("gray_sky", False)),
                "switch_ping": False,
            }
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            tmp = self.config_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.config_path)
        except Exception as e:
            try:
                self.log_output(f"[!] Não foi possível salvar preferências: {e}")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # OWNER LAB v3.17.0 — hidden local developer/test console
    # ------------------------------------------------------------------
    def _owner_key_valid(self):
        return _owner_key_valid_global()

    def _owner_state_load(self):
        self._owner_state=_owner_state_read_global() if self._owner_key_valid() else {}
        return dict(self._owner_state)

    def _owner_state_save(self):
        if not self._owner_key_valid(): return False
        return _owner_state_write_global(dict(getattr(self,"_owner_state",{}) or {}))

    def _owner_secret_theme_unlocked(self,name):
        real=name in set(getattr(self,"unlocked_secret_themes",set()))
        dev=bool(self._owner_key_valid() and dict(getattr(self,"_owner_state",{}) or {}).get("unlock_all_themes",False))
        return bool(real or dev)

    def _owner_main_profile_dir(self):
        base=os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base,"ZKSTRAP")

    def _owner_backups_dir(self):
        p=os.path.join(_owner_vault_dir(),"BACKUPS")
        os.makedirs(p,exist_ok=True)
        return p

    def _owner_test_profile_dir(self):
        return os.path.join(_owner_vault_dir(),"TEST_PROFILE")

    def _owner_password_record(self):
        try:
            if not os.path.isfile(_owner_auth_path()): return {}
            with open(_owner_auth_path(),"r",encoding="utf-8") as f:data=json.load(f)
            return data if isinstance(data,dict) else {}
        except Exception:return {}

    def _owner_hash_password(self,password,salt_b64,iterations=240000):
        salt=base64.b64decode(salt_b64.encode("ascii"))
        raw=hashlib.pbkdf2_hmac("sha256",str(password).encode("utf-8"),salt,int(iterations))
        return base64.b64encode(raw).decode("ascii")

    def _owner_setup_password(self):
        first=simpledialog.askstring("ZK OWNER LAB","Primeiro acesso do Owner Lab.\nCrie sua senha ADM:",show="*",parent=self)
        if not first:return False
        if len(first)<6:
            messagebox.showwarning("ZK OWNER LAB","Use pelo menos 6 caracteres.",parent=self);return False
        second=simpledialog.askstring("ZK OWNER LAB","Confirme a senha ADM:",show="*",parent=self)
        if first!=second:
            messagebox.showerror("ZK OWNER LAB","As senhas não conferem.",parent=self);return False
        try:
            os.makedirs(_owner_vault_dir(),exist_ok=True)
            salt=base64.b64encode(secrets.token_bytes(18)).decode("ascii")
            iterations=240000
            record={"salt":salt,"iterations":iterations,"hash":self._owner_hash_password(first,salt,iterations),"created":datetime.now().isoformat(timespec="seconds")}
            tmp=_owner_auth_path()+".tmp"
            with open(tmp,"w",encoding="utf-8") as f:json.dump(record,f,indent=2)
            os.replace(tmp,_owner_auth_path())
            return True
        except Exception as e:
            messagebox.showerror("ZK OWNER LAB",f"Não foi possível criar a senha:\n{e}",parent=self);return False

    def _owner_authenticate(self):
        if not self._owner_key_valid():
            return False
        record=self._owner_password_record()
        if not record:
            return self._owner_setup_password()
        pwd=simpledialog.askstring("ZK OWNER LAB","Senha ADM:",show="*",parent=self)
        if pwd is None:return False
        try:
            calc=self._owner_hash_password(pwd,record.get("salt",""),int(record.get("iterations",240000)))
            ok=secrets.compare_digest(calc,str(record.get("hash","")))
        except Exception:ok=False
        if not ok:
            self._play_ui_sound("warning",0)
            messagebox.showerror("ZK OWNER LAB","Senha incorreta.",parent=self)
            return False
        return True

    def _owner_restart(self):
        try:
            self._owner_skip_shutdown_save=True
            if getattr(sys,"frozen",False): cmd=[sys.executable]
            else: cmd=[sys.executable,os.path.abspath(__file__)]
            kwargs={}
            if os.name=="nt": kwargs["creationflags"]=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
            subprocess.Popen(cmd,**kwargs)
            self.after(120,self._shutdown_app)
        except Exception as e:
            messagebox.showerror("ZK OWNER LAB",f"Não foi possível reiniciar:\n{e}",parent=self)

    def _owner_make_snapshot(self,label="manual"):
        if not self._owner_key_valid():return ""
        src=self._owner_main_profile_dir()
        if not os.path.isdir(src):
            os.makedirs(src,exist_ok=True)
        stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        safe=re.sub(r"[^a-zA-Z0-9_-]+","_",str(label or "snapshot"))[:32]
        base=os.path.join(self._owner_backups_dir(),f"{stamp}_{safe}")
        try:
            archive=shutil.make_archive(base,"zip",root_dir=src)
            st=self._owner_state_load();st["last_snapshot"]=archive;self._owner_state=st;self._owner_state_save()
            return archive
        except Exception as e:
            messagebox.showerror("ZK OWNER LAB",f"Falha no snapshot:\n{e}",parent=self);return ""

    def _owner_restore_snapshot_path(self,archive):
        if not archive or not os.path.isfile(archive):
            messagebox.showwarning("ZK OWNER LAB","Snapshot não encontrado.",parent=self);return
        if not messagebox.askyesno("ZK OWNER LAB","Restaurar este snapshot no PERFIL PRINCIPAL?\n\nO perfil principal atual será salvo automaticamente antes.",parent=self):return
        self._owner_make_snapshot("before_restore")
        dst=self._owner_main_profile_dir()
        try:
            if os.path.isdir(dst):shutil.rmtree(dst,ignore_errors=True)
            os.makedirs(dst,exist_ok=True)
            with zipfile.ZipFile(archive,"r") as z:z.extractall(dst)
            st=self._owner_state_load();st["test_profile"]=False;self._owner_state=st;self._owner_state_save()
            self._owner_restart()
        except Exception as e:
            messagebox.showerror("ZK OWNER LAB",f"Falha ao restaurar:\n{e}",parent=self)

    def _owner_backup_now(self):
        path=self._owner_make_snapshot("manual")
        if path:
            self.show_toast("OWNER SNAPSHOT",os.path.basename(path),kind="success",duration=4200)
            self._owner_refresh_panel_status()

    def _owner_restore_last(self):
        st=self._owner_state_load();path=str(st.get("last_snapshot","") or "")
        self._owner_restore_snapshot_path(path)

    def _owner_choose_restore(self):
        path=filedialog.askopenfilename(parent=self,title="Selecionar snapshot do ZKStrap",initialdir=self._owner_backups_dir(),filetypes=[("ZKStrap Snapshot","*.zip"),("ZIP","*.zip")])
        if path:self._owner_restore_snapshot_path(path)

    def _owner_enter_fresh_test(self):
        if not self._owner_key_valid():return
        if not messagebox.askyesno("FRESH USER TEST","Abrir um PERFIL DE TESTE zerado?\n\nSeu perfil principal NÃO será apagado. O ZKStrap vai reiniciar usando uma pasta isolada, como se fosse a primeira vez.",parent=self):return
        # Safety snapshot of the real profile before switching.
        self._owner_make_snapshot("before_fresh_test")
        test=self._owner_test_profile_dir()
        try:
            if os.path.isdir(test):shutil.rmtree(test,ignore_errors=True)
            os.makedirs(test,exist_ok=True)
            st=self._owner_state_load();st["test_profile"]=True;self._owner_state=st;self._owner_state_save()
            self._owner_restart()
        except Exception as e:messagebox.showerror("ZK OWNER LAB",str(e),parent=self)

    def _owner_return_main(self):
        st=self._owner_state_load()
        if not st.get("test_profile",False):
            self.show_toast("OWNER LAB","Você já está no perfil principal.",kind="info");return
        st["test_profile"]=False;self._owner_state=st;self._owner_state_save();self._owner_restart()

    def _owner_reset_test_profile(self):
        if not _owner_test_profile_enabled():
            messagebox.showinfo("ZK OWNER LAB","Entre no FRESH USER TEST primeiro.",parent=self);return
        if not messagebox.askyesno("RESET TEST PROFILE","Apagar TODOS os dados do perfil de teste e reiniciar como primeira execução?\n\nO perfil principal continua intacto.",parent=self):return
        test=self._owner_test_profile_dir()
        try:
            if os.path.isdir(test):shutil.rmtree(test,ignore_errors=True)
            os.makedirs(test,exist_ok=True)
            self._owner_restart()
        except Exception as e:messagebox.showerror("ZK OWNER LAB",str(e),parent=self)

    def _owner_factory_reset_current(self):
        is_test=_owner_test_profile_enabled()
        target=self._owner_test_profile_dir() if is_test else self._owner_main_profile_dir()
        msg=("Apagar o PERFIL DE TESTE atual?" if is_test else "Apagar TODOS os dados do seu PERFIL PRINCIPAL do ZKStrap?\n\nAntes disso será criado um snapshot automático para recuperação.")
        if not messagebox.askyesno("FACTORY RESET",msg,parent=self):return
        if not is_test:
            if simpledialog.askstring("CONFIRMAÇÃO","Digite RESET para confirmar:",parent=self)!="RESET":return
            self._owner_make_snapshot("before_factory_reset")
        try:
            if os.path.isdir(target):shutil.rmtree(target,ignore_errors=True)
            os.makedirs(target,exist_ok=True)
            self._owner_restart()
        except Exception as e:messagebox.showerror("ZK OWNER LAB",str(e),parent=self)

    def _owner_toggle(self,key,var):
        st=self._owner_state_load();st[key]=bool(var.get());self._owner_state=st;self._owner_state_save()
        if key=="unlock_all_themes":
            if not bool(var.get()) and getattr(self,"tema_atual","") in UNLOCKABLE_THEME_NAMES and getattr(self,"tema_atual","") not in set(getattr(self,"unlocked_secret_themes",set())):
                self.after(1,lambda:self.mudar_tema_interface("ZKStrap Core"))
            try:
                refresh=getattr(self,"_refresh_secret_theme_gallery",None)
                if callable(refresh):refresh()
            except Exception:pass
        self._owner_refresh_panel_status()

    def _owner_play_session_complete(self):
        try:
            if list(getattr(self,"creator_challenges",[]) or []):
                self.show_toast("OWNER LAB","Finalize/remova os desafios ativos antes de testar SESSION COMPLETE para não alterar a sessão atual.",kind="warning",duration=4800);return
            fake=[
                {"title":"OWNER TEST // 3 KILLS","done":True,"unlocked_now":[]},
                {"title":"OWNER TEST // +50K","done":True,"unlocked_now":["Party"]},
            ]
            self._creator_session_started_at=time.time()-83
            self._creator_show_session_complete(fake)
        except Exception as e:
            self.show_toast("OWNER LAB",f"Falha ao simular celebração: {e}",kind="warning")

    def _owner_test_secret_reveal(self):
        try:self._creator_secret_reveal(["OWNER LAB TEST"])
        except Exception:self.show_toast("OWNER LAB","Abra Creator Challenges para visualizar o reveal completo.",kind="info")

    def _owner_open_folder(self,path):
        try:
            os.makedirs(path,exist_ok=True)
            if os.name=="nt":os.startfile(path)
            else:webbrowser.open("file://"+path)
        except Exception as e:messagebox.showerror("ZK OWNER LAB",str(e),parent=self)

    def _owner_apply_progression_values(self,challenge_entry,roll_entry,music_entry):
        try:
            c=max(0,int(challenge_entry.get().strip() or 0));r=max(0,int(roll_entry.get().strip() or 0));m=max(0,int(music_entry.get().strip() or 0))
        except Exception:
            messagebox.showwarning("ZK OWNER LAB","Use apenas números inteiros.",parent=self);return
        if not _owner_test_profile_enabled():
            if not messagebox.askyesno("PROGRESSION LAB","Você está no PERFIL PRINCIPAL. Alterar esses contadores reais mesmo?\n\nPara testes sem risco, use Fresh User Test.",parent=self):return
        self.creator_total_completed=c;self.roulette_roll_count=r;self.secret_music_seconds=m
        # Derived unlocks follow the same real rules.
        self._check_app_secret_unlocks()
        if m>=60:self._unlock_secret_theme("Frequency","Owner Lab progression test",announce=False)
        self.salvar_config_app()
        try:
            refresh=getattr(self,"_refresh_secret_theme_gallery",None)
            if callable(refresh):refresh()
        except Exception:pass
        self.show_toast("OWNER PROGRESSION","Contadores aplicados ao perfil atual.",kind="success")

    def _owner_clear_reward_progress(self):
        if not _owner_test_profile_enabled():
            if not messagebox.askyesno("OWNER LAB","Limpar progresso REAL de rewards/temas secretos no perfil principal?\n\nUm snapshot será criado antes.",parent=self):return
            self._owner_make_snapshot("before_reward_reset")
        self.creator_total_completed=0;self.roulette_roll_count=0;self.secret_music_seconds=0;self.unlocked_secret_themes=set();self.creator_history=[]
        was_secret=getattr(self,"tema_atual","") in UNLOCKABLE_THEME_NAMES
        self.salvar_config_app()
        if was_secret:self.after(1,lambda:self.mudar_tema_interface("ZKStrap Core"))
        self.show_toast("OWNER LAB","Progressão secreta resetada.",kind="success")

    def _owner_refresh_panel_status(self):
        try:
            st=self._owner_state_load();test=bool(st.get("test_profile",False))
            lbl=getattr(self,"_owner_status_label",None)
            if lbl is not None and lbl.winfo_exists():
                lbl.configure(text=("TEST PROFILE // ISOLADO" if test else "MAIN PROFILE // OWNER DATA"))
            snap=getattr(self,"_owner_snapshot_label",None)
            if snap is not None and snap.winfo_exists():
                last=str(st.get("last_snapshot","") or "")
                snap.configure(text=("Último snapshot: "+(os.path.basename(last) if last else "nenhum")))
        except Exception:pass

    def _owner_open_panel(self):
        if not self._owner_authenticate():return
        if getattr(self,"_owner_panel",None) is not None:
            try:
                if self._owner_panel.winfo_exists():self._owner_panel.lift();return
            except Exception:pass
        t=TEMAS[self.tema_atual]
        win=ctk.CTkToplevel(self);self._owner_panel=win;win.title("ZK OWNER LAB // PRIVATE");self._center_child_window(win,980,760);win.transient(self)
        win.protocol("WM_DELETE_WINDOW",lambda:(setattr(self,"_owner_panel",None),win.destroy()))
        shell=ctk.CTkFrame(win,fg_color=t["bg"]);shell.pack(fill="both",expand=True)
        head=ctk.CTkFrame(shell,fg_color=t["panel"],corner_radius=12,border_width=1,border_color=t["accent"]);head.pack(fill="x",padx=14,pady=(14,8))
        ctk.CTkLabel(head,text="ZK OWNER LAB  //  PRIVATE",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=18,weight="bold")).pack(anchor="w",padx=16,pady=(14,3))
        ctk.CTkLabel(head,text="Console local de testes. Não aparece na navegação normal e não é necessária para usuários comuns.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10)).pack(anchor="w",padx=16,pady=(0,8))
        self._owner_status_label=ctk.CTkLabel(head,text="",text_color="#58E38C",font=ctk.CTkFont(family="Consolas",size=10,weight="bold"));self._owner_status_label.pack(anchor="w",padx=16,pady=(0,12))
        tabs=ctk.CTkTabview(shell,fg_color=t["panel"],segmented_button_selected_color=t["accent"],segmented_button_selected_hover_color=t["hover"],segmented_button_unselected_color=t["card"]);tabs.pack(fill="both",expand=True,padx=14,pady=(0,14))
        tab_test=tabs.add("Test Overrides");tab_profile=tabs.add("Profile Lab");tab_prog=tabs.add("Progression Lab");tab_data=tabs.add("Data / Debug")
        st=self._owner_state_load()
        # TEST OVERRIDES
        ctk.CTkLabel(tab_test,text="OVERRIDES DE DESENVOLVEDOR",text_color=t["accent"],font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=16,pady=(16,4))
        ctk.CTkLabel(tab_test,text="Esses switches servem para TESTAR. Não contam como unlock real nem alteram o histórico do usuário.",text_color=t.get("muted","gray")).pack(anchor="w",padx=16,pady=(0,12))
        unlock_var=ctk.BooleanVar(value=bool(st.get("unlock_all_themes",False)))
        force_var=ctk.BooleanVar(value=bool(st.get("force_secret_challenges",False)))
        row1=ctk.CTkFrame(tab_test,fg_color=t["card_active"],corner_radius=10);row1.pack(fill="x",padx=16,pady=5)
        ctk.CTkLabel(row1,text="Liberar todos os SECRET THEMES para teste",text_color=t["text"],anchor="w").pack(side="left",fill="x",expand=True,padx=12,pady=12)
        ctk.CTkSwitch(row1,text="",variable=unlock_var,command=lambda:self._owner_toggle("unlock_all_themes",unlock_var),fg_color=t["card"],progress_color=t["accent"]).pack(side="right",padx=12)
        row2=ctk.CTkFrame(tab_test,fg_color=t["card_active"],corner_radius=10);row2.pack(fill="x",padx=16,pady=5)
        ctk.CTkLabel(row2,text="Forçar desafios SECRET ao gerar",text_color=t["text"],anchor="w").pack(side="left",fill="x",expand=True,padx=12,pady=12)
        ctk.CTkSwitch(row2,text="",variable=force_var,command=lambda:self._owner_toggle("force_secret_challenges",force_var),fg_color=t["card"],progress_color=t["accent"]).pack(side="right",padx=12)
        quick=ctk.CTkFrame(tab_test,fg_color="transparent");quick.pack(fill="x",padx=16,pady=(16,6))
        ctk.CTkButton(quick,text="SECRET REVEAL",command=self._owner_test_secret_reveal,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(quick,text="SESSION COMPLETE",command=self._owner_play_session_complete,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=4)
        ctk.CTkButton(quick,text="TEMAS",command=lambda:(setattr(self,"_owner_panel",None),win.destroy(),self.show_page("theme",animate=True)),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=4)
        ctk.CTkButton(quick,text="CREATOR",command=lambda:(setattr(self,"_owner_panel",None),win.destroy(),self.show_page("creator",animate=True)),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(4,0))
        # PROFILE LAB
        ctk.CTkLabel(tab_profile,text="FRESH USER LAB",text_color=t["accent"],font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=16,pady=(16,4))
        ctk.CTkLabel(tab_profile,text="O perfil de teste fica em uma pasta separada. Seu perfil real permanece intacto e volta com um clique.",text_color=t.get("muted","gray"),wraplength=850,justify="left").pack(anchor="w",padx=16,pady=(0,12))
        for txt,cmd,fg in [
            ("ENTRAR EM FRESH USER TEST",self._owner_enter_fresh_test,t["accent"]),
            ("VOLTAR AO PERFIL PRINCIPAL",self._owner_return_main,t["card_active"]),
            ("RESETAR PERFIL DE TESTE",self._owner_reset_test_profile,t["card_active"]),
            ("FACTORY RESET DO PERFIL ATUAL",self._owner_factory_reset_current,"#8C2837")]:
            ctk.CTkButton(tab_profile,text=txt,command=cmd,fg_color=fg,hover_color=t["hover"],text_color="#050505" if fg==t["accent"] else t["text"],height=42).pack(fill="x",padx=16,pady=5)
        # PROGRESSION LAB
        ctk.CTkLabel(tab_prog,text="PROGRESSION LAB",text_color=t["accent"],font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=16,pady=(16,4))
        ctk.CTkLabel(tab_prog,text="Edite contadores para testar unlocks reais. Recomendado usar isso dentro do Fresh User Test.",text_color=t.get("muted","gray"),wraplength=850,justify="left").pack(anchor="w",padx=16,pady=(0,12))
        form=ctk.CTkFrame(tab_prog,fg_color=t["card_active"],corner_radius=10);form.pack(fill="x",padx=16,pady=6)
        vals=[("Desafios concluídos",str(int(getattr(self,"creator_total_completed",0)))),("Rolls da Roulette",str(int(getattr(self,"roulette_roll_count",0)))),("Segundos de música",str(int(getattr(self,"secret_music_seconds",0))))]
        ents=[]
        for label,val in vals:
            row=ctk.CTkFrame(form,fg_color="transparent");row.pack(fill="x",padx=12,pady=6)
            ctk.CTkLabel(row,text=label,text_color=t["text"],width=220,anchor="w").pack(side="left")
            ent=ctk.CTkEntry(row,height=36);ent.insert(0,val);ent.pack(side="left",fill="x",expand=True);ents.append(ent)
        prow=ctk.CTkFrame(tab_prog,fg_color="transparent");prow.pack(fill="x",padx=16,pady=(10,4))
        ctk.CTkButton(prow,text="APLICAR CONTADORES",command=lambda:self._owner_apply_progression_values(ents[0],ents[1],ents[2]),fg_color=t["accent"],text_color="#050505").pack(side="left",expand=True,fill="x",padx=(0,5))
        ctk.CTkButton(prow,text="ZERAR REWARDS / HISTÓRICO",command=self._owner_clear_reward_progress,fg_color="#8C2837",text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(5,0))
        ctk.CTkLabel(tab_prog,text="Dica: 5 desafios = Party • 20 rolls = Jackpot • 60s música = Frequency. Architect depende de 5 builds salvas.",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=9),wraplength=850,justify="left").pack(anchor="w",padx=16,pady=(14,4))

        # DATA / DEBUG
        ctk.CTkLabel(tab_data,text="BACKUP / RESTORE",text_color=t["accent"],font=ctk.CTkFont(size=15,weight="bold")).pack(anchor="w",padx=16,pady=(16,6))
        self._owner_snapshot_label=ctk.CTkLabel(tab_data,text="",text_color=t.get("muted","gray"),anchor="w");self._owner_snapshot_label.pack(fill="x",padx=16,pady=(0,10))
        drow=ctk.CTkFrame(tab_data,fg_color="transparent");drow.pack(fill="x",padx=16,pady=4)
        ctk.CTkButton(drow,text="CRIAR SNAPSHOT",command=self._owner_backup_now,fg_color=t["accent"],text_color="#050505").pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(drow,text="RESTAURAR ÚLTIMO",command=self._owner_restore_last,fg_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=4)
        ctk.CTkButton(drow,text="ESCOLHER SNAPSHOT",command=self._owner_choose_restore,fg_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(4,0))
        drow2=ctk.CTkFrame(tab_data,fg_color="transparent");drow2.pack(fill="x",padx=16,pady=4)
        ctk.CTkButton(drow2,text="ABRIR BACKUPS",command=lambda:self._owner_open_folder(self._owner_backups_dir()),fg_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(drow2,text="ABRIR DADOS PRINCIPAIS",command=lambda:self._owner_open_folder(self._owner_main_profile_dir()),fg_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=4)
        ctk.CTkButton(drow2,text="ABRIR VAULT OWNER",command=lambda:self._owner_open_folder(_owner_vault_dir()),fg_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(4,0))
        ctk.CTkLabel(tab_data,text="Segurança: a chave OWNER fica fora do pacote público. A senha nunca é salva em texto puro; apenas hash+salt local.",text_color=t.get("muted","gray"),wraplength=840,justify="left").pack(anchor="w",padx=16,pady=(18,6))
        self._owner_refresh_panel_status()

    def _owner_search_submit(self,event=None):
        entry=getattr(self,"_search_entry",None)
        if not self._widget_alive(entry):return None
        q=self._search_normalize(entry.get())
        if q==OWNER_SEARCH_TRIGGER:
            # Without the external owner key this behaves like an unknown easter egg command.
            if not self._owner_key_valid():
                self._play_ui_sound("back",0)
                return "break"
            self._fechar_busca_universal()
            self.after(80,self._owner_open_panel)
            return "break"
        # Normal Enter behavior: open the first result when available.
        try:
            buttons=list(getattr(self,"_search_result_buttons",[]) or [])
            if buttons:
                buttons[0].invoke();return "break"
        except Exception:pass
        return None

    def restaurar_estado_interface(self):
        try:
            for key, sw in getattr(self, "module_switches", {}).items():
                if self.module_states.get(key, False):
                    sw.select()
                else:
                    sw.deselect()
        except Exception:
            pass
        try:
            if getattr(self, "theme_menu", None) is not None:
                self.theme_menu.set(self.tema_atual)
        except Exception:
            pass
        try:
            if getattr(self, "lang_menu", None) is not None:
                self.lang_menu.set("Português" if self.idioma == "pt" else "English")
            if getattr(self, "font_menu", None) is not None:
                self.font_menu.set(self.fonte_ui)
        except Exception:
            pass
        try:
            for key, menu in getattr(self, "advanced_menus", {}).items():
                menu.set(str(self.advanced_values.get(key, "Auto")))
            if getattr(self, "micro_fps_menu", None) is not None:
                self.micro_fps_menu.set(str(self.micro_fps_target))
        except Exception:
            pass
        try:
            if getattr(self, "switch_config_watchdog", None) is not None:
                if self.config_watchdog_enabled:
                    self.switch_config_watchdog.select()
                else:
                    self.switch_config_watchdog.deselect()
        except Exception:
            pass
        try:
            if getattr(self, "cursor_menu", None) is not None:
                values = self.listar_cursor_packs()
                if self.cursor_pack not in values:
                    self.cursor_pack = "Roblox Padrão"
                self.cursor_menu.configure(values=values)
                self.cursor_menu.set(self.cursor_pack)
            if getattr(self, "cursor_size_slider", None) is not None:
                self.cursor_size_slider.set(self.cursor_visual_size)
                self.lbl_cursor_size.configure(text=f"Tamanho visível: {self.cursor_visual_size}px")
            if getattr(self, "switch_cursor_white", None) is not None:
                if self.cursor_auto_remove_white: self.switch_cursor_white.select()
                else: self.switch_cursor_white.deselect()
        except Exception:
            pass
        try:
            self.txt_custom_flags.delete("0.0", "end")
            self.txt_custom_flags.insert("0.0", json.dumps(self.custom_flags, indent=4, ensure_ascii=False))
        except Exception:
            pass
        self.atualizar_estilos_cards()

    def aplicar_fonte_widgets(self, widget):
        """Aplica a fonte escolhida sem destruir a camada tipográfica técnica."""
        for child in widget.winfo_children():
            try:
                fonte=child.cget("font")
                if isinstance(fonte,ctk.CTkFont):
                    tamanho=fonte.cget("size"); peso=fonte.cget("weight")
                    try: familia=str(fonte.cget("family") or "")
                    except Exception: familia=""
                    # Micro labels de sistema continuam monoespaçados: dão identidade
                    # ao app sem transformar a interface inteira em terminal antigo.
                    if familia in ("Consolas","Courier New") and int(tamanho or 0)<=8 and self.fonte_ui!="Consolas":
                        pass
                    else:
                        child.configure(font=ctk.CTkFont(family=self.fonte_ui,size=tamanho,weight=peso))
                elif fonte:
                    child.configure(font=(self.fonte_ui,11))
            except Exception:
                pass
            try: self.aplicar_fonte_widgets(child)
            except Exception: pass

    def escolher_fonte(self, fonte):
        self.fonte_ui = fonte
        self.aplicar_fonte_widgets(self)
        self.salvar_config_app()
        self.log_output(f"[*] Fonte alterada para: {fonte}")
        self.show_toast("FONTE DA INTERFACE",f"{fonte} aplicada ao ZKStrap.",kind="success",duration=2200)

    def escolher_cor_destaque(self):
        cor = colorchooser.askcolor(color=TEMAS[self.tema_atual]["accent"], title="Cor de destaque")[1]
        if not cor or not self._cor_hex_valida(cor):
            return
        cor = cor.upper()
        self.cor_personalizada = cor
        ov = self.theme_overrides.setdefault(self.tema_atual, {})
        ov["accent"] = cor
        ov["border"] = cor
        ov["hover"] = self._clarear_hex(cor, 0.22)
        for k, v in ov.items():
            if k in TEMAS[self.tema_atual] and self._cor_hex_valida(v):
                TEMAS[self.tema_atual][k] = v
        self.salvar_config_app()
        self.after(10, self.reconstruir_interface)


    def escolher_cor_parte_tema(self, chave):
        atual = TEMAS[self.tema_atual].get(chave, "#FFFFFF")
        cor = colorchooser.askcolor(color=atual, title=f"Cor: {chave}")[1]
        if not cor or not self._cor_hex_valida(cor):
            return
        cor = cor.upper()
        self.theme_overrides.setdefault(self.tema_atual, {})[chave] = cor
        TEMAS[self.tema_atual][chave] = cor
        if chave == "accent":
            self.cor_personalizada = cor
        self.salvar_config_app()
        self.after(10, self.reconstruir_interface)

    def restaurar_tema_atual(self):
        self.theme_overrides.pop(self.tema_atual, None)
        self.cor_personalizada = ""
        TEMAS[self.tema_atual] = TEMAS_PADRAO[self.tema_atual].copy()
        self.salvar_config_app()
        self.after(10, self.reconstruir_interface)

    def _font_target_dir(self):
        self.atualizar_pasta_roblox_atual()
        if not self.pasta_roblox_salva:
            return ""
        return os.path.join(self.pasta_roblox_salva, "content", "fonts")

    def _font_backup_dir(self, roblox_dir=None):
        roblox_dir = roblox_dir or self.pasta_roblox_salva
        versao = os.path.basename((roblox_dir or "unknown").rstrip("\\/"))
        p = os.path.join(os.path.dirname(self.config_path), "font_backups", versao)
        os.makedirs(p, exist_ok=True)
        return p

    def _bloxstrap_font_dir(self):
        try:
            local = os.environ.get("LOCALAPPDATA", "")
            root = os.path.join(local, "Bloxstrap")
            if os.path.isdir(root):
                return os.path.join(root, "Modifications", "content", "fonts")
        except Exception:
            pass
        return ""

    @staticmethod
    def _font_file_is_text(name):
        n = name.lower()
        if not n.endswith((".ttf", ".otf")):
            return False
        # Não substitui emoji/símbolos especiais para evitar quadrados e ícones quebrados.
        blocked = ("emoji", "twemoji", "symbol", "icons")
        return not any(x in n for x in blocked)

    def importar_fonte_jogo(self):
        origem = filedialog.askopenfilename(title="Escolha uma fonte", filetypes=[("Fontes", "*.ttf *.otf"), ("TrueType", "*.ttf"), ("OpenType", "*.otf")])
        if not origem:
            return
        try:
            # Validação simples do container da fonte.
            try:
                from fontTools.ttLib import TTFont
                f = TTFont(origem, lazy=True); f.close()
            except Exception:
                from PIL import ImageFont
                ImageFont.truetype(origem, 16)
            store = os.path.join(os.path.dirname(self.config_path), "font_packs")
            os.makedirs(store, exist_ok=True)
            safe = re.sub(r'[^A-Za-z0-9 _.-]+', '_', os.path.basename(origem))
            dst = os.path.join(store, safe)
            shutil.copy2(origem, dst)
            self.game_font_source = dst
            try: self.lbl_game_font.configure(text=os.path.basename(dst))
            except Exception: pass
            self.salvar_config_app()
            self.log_output(f"[+] Fonte importada: {os.path.basename(dst)}")
            self.aplicar_fonte_jogo()
        except Exception as e:
            messagebox.showerror(self.tr[self.idioma]['msg_error'], f"Fonte inválida ou não suportada:\n{e}")

    def aplicar_fonte_jogo(self, silencioso=False, somente_se_precisar=False):
        src = getattr(self, "game_font_source", "")
        if not src or not os.path.isfile(src):
            if not silencioso:
                messagebox.showwarning(self.tr[self.idioma]['msg_warning'], "Escolha uma fonte .ttf ou .otf primeiro.")
            return False
        target = self._font_target_dir()
        if not target or not os.path.isdir(target):
            if not silencioso:
                messagebox.showwarning(self.tr[self.idioma]['msg_warning'], "Pasta content\\fonts do Roblox não encontrada.")
            return False
        try:
            targets = [n for n in os.listdir(target) if self._font_file_is_text(n) and os.path.isfile(os.path.join(target,n))]
            if not targets:
                raise FileNotFoundError("Nenhum arquivo de fonte de texto foi encontrado em content\\fonts.")
            backup = self._font_backup_dir(self.pasta_roblox_salva)
            changed = 0
            for name in targets:
                dst = os.path.join(target, name)
                bak = os.path.join(backup, name)
                if not os.path.exists(bak):
                    shutil.copy2(dst, bak)
                if somente_se_precisar and self._arquivos_iguais(src, dst):
                    continue
                shutil.copy2(src, dst); changed += 1

            bs = self._bloxstrap_font_dir()
            if bs:
                os.makedirs(bs, exist_ok=True)
                bs_backup = os.path.join(os.path.dirname(self.config_path), "font_backups", "bloxstrap")
                os.makedirs(bs_backup, exist_ok=True)
                marker = os.path.join(bs_backup, ".zkvez_created")
                for name in targets:
                    dst = os.path.join(bs, name)
                    bak = os.path.join(bs_backup, name)
                    if os.path.isfile(dst) and not os.path.exists(bak): shutil.copy2(dst, bak)
                    elif not os.path.exists(dst):
                        try: open(marker, "a", encoding="utf-8").close()
                        except Exception: pass
                    if not (somente_se_precisar and self._arquivos_iguais(src, dst)):
                        shutil.copy2(src, dst)
            self.salvar_config_app()
            msg = f"Fonte aplicada em {len(targets)} arquivo(s) de texto" + (" + Bloxstrap" if bs else "") + ". Feche todo o Roblox e abra novamente."
            try: self.lbl_font_status.configure(text=msg)
            except Exception: pass
            if not silencioso:
                self.log_output(f"[+] {msg}")
                self._legacy_info(self.tr[self.idioma]['msg_ok'], msg)
            return True
        except Exception as e:
            if not silencioso: messagebox.showerror(self.tr[self.idioma]['msg_error'], f"Falha ao aplicar fonte:\n{e}")
            return False

    def restaurar_fonte_jogo(self, silencioso=False):
        self.atualizar_pasta_roblox_atual()
        if not self.pasta_roblox_salva:
            return False
        target = self._font_target_dir(); backup = self._font_backup_dir(self.pasta_roblox_salva)
        restored = 0
        try:
            if os.path.isdir(backup):
                for name in os.listdir(backup):
                    src = os.path.join(backup,name)
                    if os.path.isfile(src) and self._font_file_is_text(name):
                        shutil.copy2(src, os.path.join(target,name)); restored += 1
            bs = self._bloxstrap_font_dir()
            bs_backup = os.path.join(os.path.dirname(self.config_path), "font_backups", "bloxstrap")
            marker = os.path.join(bs_backup, ".zkvez_created")
            if bs and os.path.isdir(bs_backup):
                for name in os.listdir(bs_backup):
                    if name.startswith("."): continue
                    src = os.path.join(bs_backup,name); dst = os.path.join(bs,name)
                    if os.path.isfile(src): os.makedirs(bs, exist_ok=True); shutil.copy2(src,dst)
                if os.path.exists(marker) and os.path.isdir(bs):
                    # Remove apenas arquivos que o ZKVEZ criou quando não havia mod anterior.
                    for name in os.listdir(target):
                        if self._font_file_is_text(name):
                            p = os.path.join(bs,name)
                            if os.path.isfile(p) and not os.path.isfile(os.path.join(bs_backup,name)):
                                try: os.remove(p)
                                except Exception: pass
            if not silencioso:
                self.log_output(f"[+] {restored} fonte(s) original(is) restaurada(s).")
                self._legacy_info(self.tr[self.idioma]['msg_ok'], f"{restored} arquivo(s) de fonte restaurado(s).")
            return True
        except Exception as e:
            if not silencioso: messagebox.showerror(self.tr[self.idioma]['msg_error'], f"Falha ao restaurar fontes:\n{e}")
            return False

    def load_icon(self):
        """Aplica apenas o ícone da janela; o cabeçalho moderno já possui seu próprio badge."""
        try:
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        for name in ("zkstrap_icon.ico", "zkstrap_icon.png", "zkvez_icon.ico", "zkvez_icon.png", "zkvez_icon.gif"):
            path = os.path.join(base_dir, name)
            if not os.path.exists(path):
                continue
            try:
                if name.lower().endswith('.ico'):
                    self.iconbitmap(path)
                else:
                    from PIL import Image, ImageTk
                    pil = Image.open(path).convert('RGBA').resize((32,32), Image.Resampling.LANCZOS)
                    self._win_icon = ImageTk.PhotoImage(pil)
                    self.iconphoto(False, self._win_icon)
                return True
            except Exception as e:
                try: self.log_output(f"[!] Ícone não aplicado ({name}): {e}")
                except Exception: pass
        return False

    def monitorar_ping_thread(self):
        while self.loop_verificar_jogo:
            try:
                start = time.perf_counter()
                _sock=socket.create_connection(("1.1.1.1", 443), timeout=1)
                try: _sock.close()
                except Exception: pass
                ping = int((time.perf_counter() - start) * 1000)
                self.after(0, lambda p=ping: self.lbl_ping.configure(text=f"Rede: {p}ms"))
            except:
                self.after(0, lambda: self.lbl_ping.configure(text="Rede: --"))
            time.sleep(3)

    def _measure_tcp_latency(self, host, port=443, attempts=4, timeout=1.8):
        samples=[]
        for _ in range(max(1,int(attempts))):
            sock=None
            try:
                start=time.perf_counter()
                sock=socket.create_connection((host,int(port)),timeout=timeout)
                samples.append((time.perf_counter()-start)*1000.0)
            except Exception:
                pass
            finally:
                try:
                    if sock: sock.close()
                except Exception: pass
            time.sleep(.08)
        if not samples: return None
        avg=sum(samples)/len(samples)
        jitter=(sum((v-avg)**2 for v in samples)/len(samples))**0.5 if len(samples)>1 else 0.0
        return avg,jitter,len(samples)

    def testar_rota_roblox(self):
        lbl=getattr(self,"page_ping_label",None)
        try:
            if lbl is not None: lbl.configure(text="Testando rota…",text_color=TEMAS[self.tema_atual]["accent"])
        except Exception: pass
        def worker():
            targets=[("Cloudflare","1.1.1.1",443),("Roblox Web","www.roblox.com",443),("Roblox Join","gamejoin.roblox.com",443)]
            lines=[]
            for label,host,port in targets:
                res=self._measure_tcp_latency(host,port,attempts=4,timeout=1.6)
                if res:
                    avg,jitter,count=res
                    lines.append(f"{label}: {avg:.0f} ms  •  jitter {jitter:.1f} ms  ({count}/4)")
                else:
                    lines.append(f"{label}: sem resposta")
            try:
                dns=socket.gethostbyname("gamejoin.roblox.com")
                if dns.startswith("127."):
                    lines.append("ALERTA: gamejoin.roblox.com resolve para 127.x.x.x — isso pode bloquear a entrada em servidores.")
            except Exception: pass
            text="\n".join(lines)
            try: self.after(0,lambda: self.page_ping_label.configure(text=text,text_color=TEMAS[self.tema_atual]["text"]))
            except Exception: pass
            try: self.log_output("[rede] "+" | ".join(lines))
            except Exception: pass
        threading.Thread(target=worker,daemon=True).start()

    def otimizar_rede_segura(self):
        """Limpeza local sem trocar DNS, MTU ou parâmetros agressivos da placa."""
        if os.name != "nt":
            messagebox.showwarning("ZKStrap","Esta rotina foi feita para Windows.")
            return
        try:
            flags=getattr(subprocess,"CREATE_NO_WINDOW",0)
            cp=subprocess.run(["ipconfig","/flushdns"],capture_output=True,text=True,timeout=8,creationflags=flags)
            ok=(cp.returncode==0)
            self.log_output("[rede] Cache DNS limpo." if ok else "[rede] Não foi possível limpar o cache DNS.")
            self.show_toast("REDE", "Cache DNS limpo. Isso ajuda resolução de nomes; não altera a distância até o servidor.", kind="success" if ok else "warning", duration=3600)
        except Exception as e:
            self.log_output(f"[rede] Falha na limpeza segura: {e}")
            messagebox.showerror("ZKStrap",f"Não foi possível executar a limpeza de rede:\n{e}")

    def verificar_tcp_autotuning(self):
        if os.name != "nt": return
        try:
            flags=getattr(subprocess,"CREATE_NO_WINDOW",0)
            cp=subprocess.run(["netsh","interface","tcp","show","global"],capture_output=True,text=True,timeout=8,creationflags=flags)
            out=(cp.stdout or cp.stderr or "").strip()
            low=out.lower()
            status="normal" if ("normal" in low and ("auto" in low or "ajuste" in low)) else "verificar"
            self.log_output("[rede] TCP Auto-Tuning consultado.")
            if status=="normal":
                messagebox.showinfo("ZKStrap","TCP Auto-Tuning aparenta estar em NORMAL. Não vou alterar nada.")
            else:
                messagebox.showinfo("ZKStrap","O ZKStrap não confirmou o Auto-Tuning como NORMAL. Abra o log para ver a saída do Windows.\n\nNão alterei nada automaticamente.")
                self.log_output(out[-1200:])
        except Exception as e:
            messagebox.showerror("ZKStrap",f"Não foi possível consultar TCP Auto-Tuning:\n{e}")

    def abrir_network_settings(self):
        try: os.startfile("ms-settings:network-status")
        except Exception:
            try: subprocess.Popen(["control.exe","ncpa.cpl"],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            except Exception as e: messagebox.showerror("ZKStrap",f"Não foi possível abrir Rede e Internet:\n{e}")

    def _active_network_adapter_name(self):
        if os.name != "nt": return ""
        try:
            flags=getattr(subprocess,"CREATE_NO_WINDOW",0)
            cmd=["powershell","-NoProfile","-Command","(Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Sort-Object InterfaceMetric | Select-Object -First 1 -ExpandProperty Name)"]
            cp=subprocess.run(cmd,capture_output=True,text=True,timeout=8,creationflags=flags)
            out=(cp.stdout or "").strip()
            return out.splitlines()[0].strip() if out else ""
        except Exception: return ""

    def _run_elevated_ps_script(self, script_text, label="ZKStrap"):
        if os.name != "nt": return False
        try:
            base=os.path.dirname(self.config_path); os.makedirs(base,exist_ok=True)
            ps1=os.path.join(base,"zkstrap_network_admin.ps1")
            with open(ps1,"w",encoding="utf-8-sig") as f: f.write(script_text)
            flags=getattr(subprocess,"CREATE_NO_WINDOW",0)
            safe=ps1.replace("'","''")
            command=f"& {{ Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','{safe}') }}"
            cp=subprocess.run(["powershell","-NoProfile","-Command",command],timeout=120,creationflags=flags)
            return cp.returncode==0
        except Exception as exc:
            self.log_output(f"[rede] Falha ao elevar {label}: {exc}"); return False

    def _dns_profiles(self):
        return {
            "Cloudflare": ["1.1.1.1", "1.0.0.1"],
            "Google": ["8.8.8.8", "8.8.4.4"],
            "Quad9": ["9.9.9.9", "149.112.112.112"],
        }

    def _dns_udp_latency(self, server, hostname="gamejoin.roblox.com", timeout=1.5):
        """Mede RTT do resolver com uma consulta DNS UDP simples."""
        sock=None
        try:
            tid=random.randint(0,65535)
            header=struct.pack("!HHHHHH",tid,0x0100,1,0,0,0)
            qname=b"".join(bytes([len(part)])+part.encode("idna") for part in hostname.split("."))+b"\x00"
            packet=header+qname+struct.pack("!HH",1,1)
            sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            sock.settimeout(float(timeout))
            t0=time.perf_counter()
            sock.sendto(packet,(server,53))
            data,_=sock.recvfrom(4096)
            dt=(time.perf_counter()-t0)*1000.0
            if len(data)<12 or struct.unpack("!H",data[:2])[0] != tid:
                return None
            return dt
        except Exception:
            return None
        finally:
            try:
                if sock is not None: sock.close()
            except Exception: pass

    def benchmark_dns(self):
        if os.name != "nt":
            messagebox.showwarning("ZKStrap","O laboratório de DNS foi feito para Windows.")
            return
        try:
            self.dns_lab_label.configure(text="Testando DNS por RTT real…",text_color=TEMAS[self.tema_atual]["accent"])
        except Exception: pass
        def worker():
            servers=[("Cloudflare","1.1.1.1"),("Google","8.8.8.8"),("Quad9","9.9.9.9")]
            hosts=["gamejoin.roblox.com","www.roblox.com","clientsettings.roblox.com"]
            rows=[]
            for name,server in servers:
                samples=[]
                for host in hosts:
                    for _ in range(2):
                        val=self._dns_udp_latency(server,host,timeout=1.5)
                        if val is not None: samples.append(val)
                med=statistics.median(samples) if samples else None
                spread=(max(samples)-min(samples)) if len(samples)>1 else 0.0
                rows.append((name,med,spread,len(samples)))
            valid=[r for r in rows if r[1] is not None]
            best=min(valid,key=lambda x:x[1])[0] if valid else None
            self._dns_best_profile=best
            self._dns_last_benchmark={name:{"median_ms":med,"spread_ms":spread,"samples":count} for name,med,spread,count in rows}
            lines=[]
            for name,val,spread,count in rows:
                suffix="  ← melhor RTT DNS" if name==best else ""
                lines.append(f"{name}: {val:.1f} ms  • variação {spread:.1f} ms ({count}/6){suffix}" if val is not None else f"{name}: sem resposta")
            if best:
                lines.append(f"Melhor neste teste: {best}. Use APLICAR MELHOR TESTE para experimentar.")
            lines.append("DNS pode acelerar a resolução de nomes, mas não garante ping menor na partida. Depois de aplicar, o ZKStrap repete o teste de rota para facilitar a comparação.")
            text="\n".join(lines)
            try:
                self.after(0,lambda:self.dns_lab_label.configure(text=text,text_color=TEMAS[self.tema_atual]["text"]))
            except Exception: pass
            try: self.log_output("[dns] "+" | ".join(lines))
            except Exception: pass
        threading.Thread(target=worker,daemon=True).start()

    def aplicar_melhor_dns(self):
        best=getattr(self,"_dns_best_profile",None)
        if not best:
            messagebox.showinfo("ZKStrap — DNS","Rode TESTAR DNS primeiro. O ZKStrap vai guardar o resolver com menor RTT do teste atual.")
            return
        self.aplicar_dns_perfil(best)

    def aplicar_dns_perfil(self, profile):
        profiles=self._dns_profiles()
        if profile not in profiles: return
        adapter=self._active_network_adapter_name()
        if not adapter:
            messagebox.showerror("ZKStrap","Não consegui identificar o adaptador de rede ativo."); return
        dns=profiles[profile]
        msg=(f"Aplicar {profile} no adaptador '{adapter}'?\n\nIsso troca somente o DNS. Pode melhorar resolução de nomes, mas não garante ping menor dentro da partida. Você pode voltar para Automático a qualquer momento.")
        if not messagebox.askyesno("ZKStrap — DNS",msg): return
        a=adapter.replace("'","''")
        script=f"$ErrorActionPreference='Stop'\nSet-DnsClientServerAddress -InterfaceAlias '{a}' -ServerAddresses ('{dns[0]}','{dns[1]}')\nipconfig /flushdns | Out-Null\n"
        ok=self._run_elevated_ps_script(script,"DNS")
        self.show_toast("DNS",f"Perfil {profile} aplicado em {adapter}. Vou repetir o teste de rota." if ok else "Não foi possível aplicar o DNS.",kind="success" if ok else "warning",duration=3800)
        self._play_ui_sound("confirm" if ok else "error",0)
        if ok:
            try: self.after(1400,self.testar_rota_roblox)
            except Exception: pass

    def restaurar_dns_automatico(self):
        adapter=self._active_network_adapter_name()
        if not adapter:
            messagebox.showerror("ZKStrap","Não consegui identificar o adaptador de rede ativo."); return
        if not messagebox.askyesno("ZKStrap — DNS",f"Voltar o DNS de '{adapter}' para Automático/DHCP?"): return
        a=adapter.replace("'","''")
        script=f"$ErrorActionPreference='Stop'\nSet-DnsClientServerAddress -InterfaceAlias '{a}' -ResetServerAddresses\nipconfig /flushdns | Out-Null\n"
        ok=self._run_elevated_ps_script(script,"DNS automático")
        self.show_toast("DNS","DNS voltou para Automático. Vou repetir o teste de rota." if ok else "Não foi possível restaurar o DNS.",kind="success" if ok else "warning",duration=3600)
        self._play_ui_sound("confirm" if ok else "error",0)
        if ok:
            try: self.after(1400,self.testar_rota_roblox)
            except Exception: pass

    def reparar_pilha_rede_avancado(self):
        if os.name != "nt": return
        msg=("Isso executa reparos nativos do Windows: Winsock reset + TCP/IP reset + limpeza DNS.\n\n"
             "A conexão pode ser interrompida e uma reinicialização pode ser necessária. Use só se a rede estiver realmente estranha. Continuar?")
        if not messagebox.askyesno("ZKStrap — Reparo avançado",msg): return
        script="$ErrorActionPreference='Continue'\nnetsh winsock reset\nnetsh int ip reset\nipconfig /flushdns\n"
        ok=self._run_elevated_ps_script(script,"reparo TCP/IP")
        self.show_toast("REDE","Reparo executado. Reinicie o PC antes de avaliar o resultado." if ok else "O reparo não foi concluído.",kind="warning" if ok else "error",duration=5200)
        self._play_ui_sound("warning" if ok else "error",0)

    def _theme_style(self, name=None):
        return THEME_STYLE.get(name or self.tema_atual, THEME_STYLE["Clean"])

    def _special_theme_root(self, theme_name):
        """Retorna a pasta do pack visual do tema, inclusive dentro do PyInstaller."""
        spec = SPECIAL_THEME_ASSETS.get(theme_name, {})
        folder = spec.get("dir", "")
        if not folder:
            return ""
        bases = []
        try:
            if getattr(sys, "_MEIPASS", None):
                bases.append(sys._MEIPASS)
        except Exception:
            pass
        try:
            bases.append(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            pass
        try:
            bases.append(os.getcwd())
        except Exception:
            pass
        for base in bases:
            p = os.path.join(base, "zkstrap_assets", "special_themes", folder)
            if os.path.isdir(p):
                return p
        return ""

    def _special_theme_icon_photo(self, theme_name, icon_name, size):
        """Carrega um PNG do pack e devolve PhotoImage redimensionado com cache."""
        root = self._special_theme_root(theme_name)
        if not root:
            return None
        path = os.path.join(root, f"{icon_name}.png")
        if not os.path.exists(path):
            return None
        size = max(14, int(size))
        key = (theme_name, icon_name, size)
        if not hasattr(self, "_special_icon_cache"):
            self._special_icon_cache = {}
        if key in self._special_icon_cache:
            return self._special_icon_cache[key]
        try:
            from PIL import Image, ImageTk
            im = Image.open(path).convert("RGBA")
            im.thumbnail((size, size), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(im)
            self._special_icon_cache[key] = photo
            if len(self._special_icon_cache) > 220:
                # preserva os itens mais recentes sem deixar o cache crescer após muitos resizes
                self._special_icon_cache = dict(list(self._special_icon_cache.items())[-120:])
                self._special_icon_cache[key] = photo
            return photo
        except Exception:
            return None

    def _special_theme_asset_photo(self, theme_name, icon_name, size, opacity=1.0):
        """Asset real do tema com padding seguro para nunca encostar/cortar nas bordas."""
        root = self._special_theme_root(theme_name)
        if not root:
            return None
        path = os.path.join(root, f"{icon_name}.png")
        if not os.path.exists(path):
            return None
        size = max(18, int(size))
        opacity = max(0.05, min(1.0, float(opacity)))
        key = ("ambient_safe_v2", theme_name, icon_name, size, round(opacity, 2))
        if not hasattr(self, "_special_icon_cache"):
            self._special_icon_cache = {}
        if key in self._special_icon_cache:
            return self._special_icon_cache[key]
        try:
            from PIL import Image, ImageTk, ImageOps
            im = Image.open(path).convert("RGBA")
            bbox = im.getchannel("A").getbbox()
            if bbox:
                im = im.crop(bbox)
            iw0, ih0 = max(1, im.width), max(1, im.height)
            ratio = min(float(size) / iw0, float(size) / ih0)
            nw, nh = max(1, int(round(iw0 * ratio))), max(1, int(round(ih0 * ratio)))
            pixel_like = theme_name in ("Minecraft", "Terraria") or max(iw0, ih0) <= 24
            resample = Image.Resampling.NEAREST if pixel_like else Image.Resampling.LANCZOS
            im = im.resize((nw, nh), resample)
            a = im.getchannel("A").point(lambda v: int(v * opacity))
            im.putalpha(a)
            # padding transparente real: evita que sprite/arma encoste no retângulo do banner
            pad=max(8,int(round(size*.15)))
            im=ImageOps.expand(im,border=pad,fill=(0,0,0,0))
            ph = ImageTk.PhotoImage(im)
            self._special_icon_cache[key] = ph
            if len(self._special_icon_cache) > 320:
                self._special_icon_cache = dict(list(self._special_icon_cache.items())[-190:])
                self._special_icon_cache[key] = ph
            return ph
        except Exception:
            return None

    def _special_theme_glow_photo(self, theme_name, icon_name, size, accent, opacity=.70):
        """Glow suave baseado no alpha real do item — sem círculos desenhados em volta."""
        root=self._special_theme_root(theme_name)
        if not root: return None
        path=os.path.join(root,f"{icon_name}.png")
        if not os.path.exists(path): return None
        size=max(18,int(size)); opacity=max(.08,min(1.0,float(opacity)))
        key=("glow",theme_name,icon_name,size,str(accent),round(opacity,2))
        if not hasattr(self,"_special_icon_cache"): self._special_icon_cache={}
        if key in self._special_icon_cache: return self._special_icon_cache[key]
        try:
            from PIL import Image, ImageTk, ImageFilter, ImageColor
            im=Image.open(path).convert("RGBA")
            bbox=im.getchannel("A").getbbox()
            if bbox: im=im.crop(bbox)
            iw0,ih0=max(1,im.width),max(1,im.height)
            ratio=min(float(size)/iw0,float(size)/ih0)
            nw,nh=max(1,int(round(iw0*ratio))),max(1,int(round(ih0*ratio)))
            alpha=im.getchannel("A").resize((nw,nh),Image.Resampling.LANCZOS)
            # remove partículas soltas/ruído do PNG antes do blur; isso evita halos circulares
            alpha=alpha.point(lambda v: 255 if v >= 92 else 0)
            pad=max(10,int(round(size*.18)))
            mask=Image.new("L",(nw+pad*2,nh+pad*2),0); mask.paste(alpha,(pad,pad))
            mask=mask.filter(ImageFilter.GaussianBlur(radius=max(2,int(size*.055))))
            mask=mask.point(lambda v:min(255,int(v*opacity)))
            rgb=ImageColor.getrgb(str(accent))
            glow=Image.new("RGBA",mask.size,(*rgb,0)); glow.putalpha(mask)
            ph=ImageTk.PhotoImage(glow); self._special_icon_cache[key]=ph
            return ph
        except Exception:
            return None

    def _special_theme_banner_photo(self, theme_name, width, height):
        """Carrega/corta o banner real do tema sem adicionar texto ou shade.

        O banner é uma superfície visual pura: nenhuma descrição, breadcrumb ou
        label é misturada na arte. Isso evita caixas escuras e mantém a imagem
        confinada ao retângulo abaixo da busca universal.
        """
        root = self._special_theme_root(theme_name)
        if not root:
            return None
        path = os.path.join(root, "banner.png")
        if not os.path.exists(path):
            return None
        width=max(80,int(width)); height=max(60,int(height))
        qw=max(80,int(round(width/8)*8)); qh=max(60,int(round(height/4)*4))
        meta=SPECIAL_THEME_BANNER_META.get(theme_name,{})
        focus=meta.get("focus",(0.5,0.5))
        key=("banner_clean",theme_name,qw,qh,round(float(focus[0]),2),round(float(focus[1]),2))
        if not hasattr(self,"_special_banner_cache"):
            self._special_banner_cache={}
        if key in self._special_banner_cache:
            return self._special_banner_cache[key]
        try:
            from PIL import Image, ImageTk, ImageOps, ImageEnhance
            im=Image.open(path).convert("RGB")
            im=ImageOps.fit(im,(qw,qh),method=Image.Resampling.LANCZOS,centering=(float(focus[0]),float(focus[1])))
            im=ImageEnhance.Contrast(im).enhance(1.035)
            im=ImageEnhance.Color(im).enhance(1.03)
            ph=ImageTk.PhotoImage(im)
            self._special_banner_cache[key]=ph
            if len(self._special_banner_cache)>44:
                self._special_banner_cache=dict(list(self._special_banner_cache.items())[-28:])
                self._special_banner_cache[key]=ph
            return ph
        except Exception:
            return None

    def _special_theme_square_photo(self, theme_name, size):
        """Preview quadrado do tema no canto superior esquerdo do banner."""
        root=self._special_theme_root(theme_name)
        if not root:
            return None
        meta=SPECIAL_THEME_BANNER_META.get(theme_name,{})
        source=str(meta.get("square") or "banner")
        candidates=[os.path.join(root,source+".png"),os.path.join(root,"banner.png")]
        path=next((p for p in candidates if os.path.exists(p)),None)
        if not path:
            return None
        size=max(54,int(size))
        key=("square",theme_name,source,size)
        if not hasattr(self,"_special_banner_cache"):
            self._special_banner_cache={}
        if key in self._special_banner_cache:
            return self._special_banner_cache[key]
        try:
            from PIL import Image, ImageTk, ImageOps, ImageEnhance
            im=Image.open(path).convert("RGBA")
            # centraliza a essência da imagem e evita distorção
            im=ImageOps.fit(im,(size,size),method=Image.Resampling.LANCZOS,centering=(.5,.5))
            im=ImageEnhance.Contrast(im).enhance(1.05)
            ph=ImageTk.PhotoImage(im)
            self._special_banner_cache[key]=ph
            return ph
        except Exception:
            return None

    def _draw_special_theme_banner(self, canvas, theme_name, width, height):
        """Banner especial 3.13.3: arte real + itens reais com flutuação orgânica.

        O banner continua isolado abaixo da busca universal. Nenhum texto da página
        entra sobre a imagem e os sprites são limitados pela área segura do banner.
        """
        if theme_name not in SPECIAL_THEME_NAMES:
            return False
        meta=SPECIAL_THEME_BANNER_META.get(theme_name,{})
        t=TEMAS.get(theme_name,TEMAS["Clean"])
        w=max(120,int(width)); h=max(90,int(height))
        phase=float(getattr(self,"_ambient_phase",0.0) or 0.0)
        try:
            canvas.delete("all")
            canvas.configure(bg=t.get("panel",t["bg"]))
            refs=[]
            bg=self._special_theme_banner_photo(theme_name,w,h)
            if bg is None:
                return False
            canvas.create_image(w//2,h//2,image=bg,anchor="center")
            refs.append(bg)

            accent=t["accent"]
            border=self._mix_hex(t.get("border",accent),accent,.50)
            canvas.create_rectangle(1,1,w-2,h-2,outline=border,width=1)
            canvas.create_line(0,h-2,w,h-2,fill=accent,width=2)

            # Moldura técnica minimalista: só nos cantos, sem cobrir a arte.
            corner=self._mix_hex(t.get("border",accent),accent,.70); c=20
            for x1,y1,x2,y2 in [
                (6,6,6+c,6),(6,6,6,6+c),(w-6-c,6,w-6,6),(w-6,6,w-6,6+c),
                (6,h-6,6+c,h-6),(6,h-6,6,h-6-c),(w-6-c,h-6,w-6,h-6),(w-6,h-6,w-6,h-6-c)
            ]:
                canvas.create_line(x1,y1,x2,y2,fill=corner,width=2)

            # Miniatura quadrada do tema, como assinatura visual fixa.
            sq=max(76,min(106,int(h*.60)))
            sx=18; sy=max(12,(h-sq)//2)
            square=self._special_theme_square_photo(theme_name,sq)
            canvas.create_rectangle(sx-3,sy-3,sx+sq+3,sy+sq+3,
                                    fill=self._mix_hex(t["bg"],accent,.08),outline=accent,width=2)
            if square is not None:
                canvas.create_image(sx,sy,image=square,anchor="nw")
                refs.append(square)

            float_icons=list(meta.get("float_icons") or [])
            slots=list(meta.get("float_slots") or [])
            sizes=list(meta.get("float_sizes") or [])
            if not slots:
                slots=[(.22,.28),(.42,.70),(.64,.27),(.83,.69)]

            for i,icon_name in enumerate(float_icons[:len(slots)]):
                fx,fy=slots[i]
                frac=float(sizes[i]) if i < len(sizes) else .34
                # Escala 3.13.3.1: legível, mas sem transformar o banner numa fileira de ícones gigantes.
                if theme_name == "Terraria":
                    target=max(48,min(68,int(h*frac*1.12)))
                else:
                    target=max(50,min(72,int(h*frac*1.14)))
                target += int(round(math.sin(phase*.30+i*1.21)*1.2))
                ph=self._special_theme_asset_photo(theme_name,icon_name,target,.99)
                if ph is None:
                    continue
                iw=max(1,int(ph.width())); ih=max(1,int(ph.height()))

                # Movimento em órbita curta: flutua no lugar, sem viajar pelo banner.
                drift_x=math.sin(phase*.24+i*1.47)*2.8 + math.cos(phase*.15+i*.81)*1.0
                drift_y=math.sin(phase*.46+i*1.73)*4.2 + math.cos(phase*.27+i*1.11)*1.4
                x=int(w*float(fx)+drift_x)
                y=int(h*float(fy)+drift_y)

                extra=18
                left_safe=sx+sq+24+iw//2+extra
                right_safe=w-14-iw//2-extra
                top_safe=12+ih//2+extra
                bottom_safe=h-12-ih//2-extra
                if right_safe < left_safe:
                    left_safe=iw//2+extra; right_safe=w-iw//2-extra
                x=max(left_safe,min(right_safe,x))
                y=max(top_safe,min(bottom_safe,y))

                glow_op=.48 + .08*(.5+.5*math.sin(phase*.45+i))
                glow=self._special_theme_glow_photo(theme_name,icon_name,target,accent,glow_op)
                if glow is not None:
                    canvas.create_image(x,y,image=glow,anchor="center")
                    refs.append(glow)
                canvas.create_image(x,y,image=ph,anchor="center")
                refs.append(ph)

            # Camada frontal: partículas leves e profundidade. Não usa ícones falsos.
            particle=self._mix_hex(t.get("muted",accent),accent,.58)
            particle2=self._mix_hex(t.get("panel",t["bg"]),accent,.40)
            for j in range(10):
                px=int(w*(.14+((j*.071)%0.82)) + math.sin(phase*.19+j*1.41)*10)
                py=int(h*(.13+((j*3)%8)*.105) + math.cos(phase*.24+j*.93)*4)
                r=1+(j%3==0)
                canvas.create_oval(px-r,py-r,px+r,py+r,fill=particle if j%2==0 else particle2,outline="")
            # dois reflexos finos dão sensação de vidro/parallax sem tapar personagens.
            sweep=self._mix_hex(t.get("panel",t["bg"]),accent,.30)
            dx=int(math.sin(phase*.12)*16)
            canvas.create_line(int(w*.34)+dx,9,int(w*.49)+dx,h-10,fill=sweep,width=1)
            canvas.create_line(int(w*.72)-dx,8,int(w*.83)-dx,h-11,fill=sweep,width=1)

            canvas._zk_banner_refs=refs
            return True
        except Exception:
            return False

    @staticmethod
    def _mix_hex(c1, c2, ratio=0.5):
        try:
            ratio=max(0.0,min(1.0,float(ratio)))
            a=c1.lstrip('#'); b=c2.lstrip('#')
            av=[int(a[i:i+2],16) for i in (0,2,4)]; bv=[int(b[i:i+2],16) for i in (0,2,4)]
            out=[int(av[i]*(1-ratio)+bv[i]*ratio) for i in range(3)]
            return '#%02X%02X%02X'%tuple(out)
        except Exception:
            return c1

    def _draw_core_theme_signature(self, canvas, theme_name, w, h, t, phase, zone="hero"):
        """Core Theme Lock-In 3.13.3.3.

        Hero e preview Core são cenas independentes. Cada tema tem linguagem visual,
        moldura, profundidade e microanimação próprias — sem reaproveitar o velho
        círculo/radar como base comum.
        """
        try:
            base=t.get("panel",t["bg"]); accent=t["accent"]; active=t["card_active"]
            border=t.get("border",accent); muted=t.get("muted",border); text=t.get("text",accent)
            st=self._theme_style(theme_name); accent2=st.get("accent2",accent)
            compact=(zone=="gallery")
            line=self._mix_hex(base,accent,.31)
            line2=self._mix_hex(base,accent2,.28)
            soft=self._mix_hex(base,accent,.10)
            soft2=self._mix_hex(base,accent2,.08)
            panel=self._mix_hex(base,active,.28)
            faint=self._mix_hex(base,border,.18)
            pad=4 if compact else 7
            fs=7 if compact else 8

            def rect(x0,y0,x1,y1,fill="",outline=None,width=1):
                canvas.create_rectangle(int(x0),int(y0),int(x1),int(y1),fill=fill,outline=outline or "",width=width)
            def txt(x,y,value,fill=None,size=None,anchor="nw",family="Consolas",weight="bold"):
                canvas.create_text(int(x),int(y),text=value,fill=fill or accent,font=(family,size or fs,weight),anchor=anchor)
            def corner_frame(color=None,cut=20):
                c=color or border; x0=pad; y0=pad; x1=w-pad-1; y1=h-pad-1
                # quatro cantos em L, mais técnico que uma caixa genérica inteira
                for xa,ya,sx,sy in ((x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)):
                    canvas.create_line(xa,ya,xa+sx*cut,ya,fill=c,width=1)
                    canvas.create_line(xa,ya,xa,ya+sy*cut,fill=c,width=1)
            def micro_tag(label, side="left", color=None):
                if compact: return
                c=color or self._mix_hex(muted,accent,.50)
                x=16 if side=="left" else w-16
                txt(x,14,label,c,7,"nw" if side=="left" else "ne")
            def particles(count,color=None,speed=1.0,stars=False):
                c=color or line
                for i in range(count):
                    x=int((i*97+phase*(2.2+i%3)*speed) % max(1,w))
                    y=int((i*43+phase*(.7+(i%4)*.19)*speed) % max(1,h))
                    if stars and i%4==0:
                        txt(x,y,"✦",c,7,"center","Segoe UI Symbol","normal")
                    else:
                        r=1+(i%2); canvas.create_oval(x-r,y-r,x+r,y+r,fill=c,outline="")
            def diagonal_ribbon(x0,y0,x1,y1,color,width=2):
                canvas.create_line(int(x0),int(y0),int(x1),int(y1),fill=color,width=width)

            # Fundo em camadas, mas sem uma moldura universal idêntica em todos.
            rect(0,0,w,h,fill=base)

            if theme_name in UNLOCKABLE_THEME_NAMES:
                # v3.16.2: temas secretos são identidades visuais completas.
                # Antes eles caíam no fallback do Clean e pareciam apenas recolors.
                corner_frame(accent2,24)
                if theme_name=="Party":
                    # Confete, palco central e pequenos bursts em movimento.
                    for i in range(26 if not compact else 16):
                        x=int((i*73+phase*(9+(i%4)*2))%max(1,w))
                        y=int((i*41+phase*(12+(i%3)*2))%max(1,h))
                        c=(accent,accent2,border,"#7EE7FF")[(i+int(phase))%4]
                        if i%3==0:
                            canvas.create_polygon(x,y-4,x+4,y,x,y+4,x-4,y,fill=c,outline="")
                        else:
                            rect(x-2,y-5,x+2,y+5,fill=c)
                    cx=int(w*.52); cy=int(h*.50)
                    for rr,c in ((58,line2),(39,line),(23,accent2)):
                        canvas.create_arc(cx-rr,cy-rr,cx+rr,cy+rr,start=int((phase*7)%360),extent=235,style="arc",outline=c,width=2)
                    txt(cx,cy-4,"PARTY",accent,max(18,int(h*.15)),"center","Segoe UI","bold")
                    txt(cx,cy+26,"5 CHALLENGES // UNLOCKED",accent2,7,"center")
                    micro_tag("SECRET // PARTY MODE")

                elif theme_name=="Frequency":
                    # Deck de áudio: waveform central, equalizador e playhead.
                    mid=int(h*.52)
                    pts=[]
                    for x in range(10,w-10,8):
                        amp=(10+int((x%47)*.34))*(.55+.45*math.sin(phase*.18+x*.035))
                        pts += [x,mid+int(math.sin(x*.065+phase*.14)*amp)]
                    if len(pts)>=4: canvas.create_line(*pts,fill=accent,width=2,smooth=True)
                    for i in range(15):
                        x=20+i*max(12,int((w-40)/15)); bh=8+int((.5+.5*math.sin(phase*.22+i*.72))*max(12,h*.32))
                        rect(x,h-20-bh,x+6,h-20,fill=accent2 if i%4==0 else line)
                    playx=int((phase*18)%max(1,w)); canvas.create_line(playx,12,playx,h-12,fill=self._mix_hex(base,accent,.65),width=1)
                    txt(18,16,"FREQUENCY // NOW PLAYING",accent2,8)
                    txt(w-18,16,"48 kHz",muted,7,"ne")

                elif theme_name=="Flagborn":
                    # Matriz de FastFlags: rows de chave/valor, bits e commit pulse.
                    cols=max(7,w//86)
                    for i in range(cols):
                        x=14+i*max(50,int((w-28)/cols))
                        for j in range(5 if compact else 7):
                            y=22+j*18
                            value="1" if (i+j+int(phase*.3))%3==0 else "0"
                            txt(x,y,value,accent if value=="1" else line2,7)
                    bx=int(w*.45); by=int(h*.22); bw=int(w*.47); bh=int(h*.56)
                    rect(bx,by,bx+bw,by+bh,fill=self._mix_hex(base,active,.23),outline=accent2)
                    txt(bx+14,by+13,"FASTFLAG // APPLY PIPELINE",accent,8)
                    rows=("DFIntTaskSchedulerTargetFps","FFlagDebugGraphicsPreferD3D11","FIntRenderShadowIntensity")
                    for r,key in enumerate(rows):
                        yy=by+38+r*22; txt(bx+14,yy,key,line2,7); txt(bx+bw-14,yy,"APPLIED",accent,7,"ne")
                    px=bx+14+int((phase*12)%max(1,bw-28)); rect(px,by+bh-14,px+35,by+bh-10,fill=accent)
                    micro_tag("SECRET // FLAGBORN")

                elif theme_name=="Architect":
                    # Blueprint técnico: grid, medidas e wireframes.
                    step=24 if not compact else 18
                    for x in range(0,w,step): canvas.create_line(x,0,x,h,fill=self._mix_hex(base,border,.16),width=1)
                    for y in range(0,h,step): canvas.create_line(0,y,w,y,fill=self._mix_hex(base,border,.16),width=1)
                    boxes=[(.08,.22,.34,.72),(.40,.14,.64,.58),(.70,.28,.92,.80)]
                    for idx,(x0,y0,x1,y1) in enumerate(boxes):
                        X0=int(w*x0);Y0=int(h*y0);X1=int(w*x1);Y1=int(h*y1)
                        rect(X0,Y0,X1,Y1,fill=self._mix_hex(base,active,.10),outline=accent if idx==1 else accent2)
                        txt(X0+7,Y0+6,f"MODULE {idx+1:02d}",accent2,7)
                        canvas.create_line(X0,Y1+7,X1,Y1+7,fill=line2); txt((X0+X1)//2,Y1+9,f"{X1-X0}px",muted,6,"n")
                    txt(16,h-16,"BUILD BLUEPRINT // LOCAL UI",accent,8,"sw")

                elif theme_name=="Jackpot":
                    # Slot-machine: três reels, luzes e scan dourado.
                    cx=w//2; reelw=max(45,int(w*.11)); gap=10; y0=int(h*.22); y1=int(h*.72)
                    values=("7","7","7")
                    for i,v in enumerate(values):
                        x0=cx-(reelw*3+gap*2)//2+i*(reelw+gap)
                        rect(x0,y0,x0+reelw,y1,fill=self._mix_hex(base,active,.32),outline=accent2,width=2)
                        txt(x0+reelw//2,(y0+y1)//2,v,accent,max(26,int(h*.26)),"center","Consolas","bold")
                    for i in range(18):
                        x=12+i*max(10,int((w-24)/18)); pulse=.45+.55*math.sin(phase*.25+i)
                        r=2+int(2*pulse); canvas.create_oval(x-r,12-r,x+r,12+r,fill=accent if i%2 else accent2,outline="")
                    sweep=int((phase*24)%(w+100))-50; canvas.create_line(sweep,h,sweep+82,0,fill=self._mix_hex(accent,"#FFFFFF",.45),width=2)
                    micro_tag("SECRET // JACKPOT ENGINE")

                elif theme_name=="No Dash":
                    # Movimento cortado: trilhas interrompidas e zonas STOP.
                    for i in range(8):
                        y=24+i*max(12,int((h-48)/8)); start=int((phase*(12+i)+i*81)%max(1,w))
                        canvas.create_line(start-90,y,start-18,y,fill=line2,width=1)
                        canvas.create_line(start+18,y,start+90,y,fill=accent if i%3==0 else line,width=2 if i%3==0 else 1)
                    cx=int(w*.52); cy=int(h*.48); rr=max(26,int(h*.20))
                    canvas.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline=accent,width=2)
                    canvas.create_line(cx-rr+9,cy+rr-9,cx+rr-9,cy-rr+9,fill=accent2,width=4)
                    txt(cx,cy+rr+18,"NO DASH // HOLD POSITION",accent2,7,"center")
                    micro_tag("SECRET // STILL VELOCITY")

                elif theme_name=="Millionaire":
                    # Ticker financeiro / bounty de sete dígitos.
                    txt(int(w*.52),int(h*.44),"1,000,000",accent,max(26,int(h*.26)),"center","Consolas","bold")
                    txt(int(w*.52),int(h*.64),"BOUNTY // SEVEN DIGITS",accent2,8,"center")
                    for i in range(8):
                        x=18+i*int(max(42,(w-36)/8)); val=(i*137+int(phase*9))%999
                        txt(x,18,f"{val:03d}",line2,7)
                    pts=[]
                    for x in range(0,w+20,20): pts += [x,int(h*.80)+int(math.sin(x*.035+phase*.12)*10)]
                    if len(pts)>3: canvas.create_line(*pts,fill=accent2,width=2,smooth=True)
                    micro_tag("SECRET // MILLIONAIRE")

                elif theme_name=="Pure Combat":
                    # Arena bruta: crosshair quebrado, impactos e barras de hit.
                    cx=int(w*.55); cy=int(h*.49)
                    for rr in (20,38,62):
                        canvas.create_arc(cx-rr,cy-rr,cx+rr,cy+rr,start=int((phase*8+rr)%360),extent=120,style="arc",outline=accent if rr==38 else line2,width=2)
                    for ang in (25,115,205,295):
                        a=math.radians(ang+math.sin(phase*.12)*4); x2=cx+math.cos(a)*92; y2=cy+math.sin(a)*92
                        canvas.create_line(cx,cy,x2,y2,fill=line,width=1)
                    txt(cx,cy,"X",accent,max(34,int(h*.32)),"center","Consolas","bold")
                    for i in range(4):
                        y=22+i*18; rect(18,y,18+int(w*(.15+.07*i)),y+5,fill=accent if i==0 else line2)
                    txt(18,h-20,"FIGHTING STYLE // ONLY",accent2,8,"sw")
                    micro_tag("SECRET // PURE COMBAT")

                elif theme_name=="Untouchable":
                    # Escudo/field: hexágonos, streak counter e barreira pulsante.
                    cx=int(w*.54); cy=int(h*.50); r=max(36,int(h*.28))
                    pts=[]
                    for i in range(6):
                        a=math.radians(60*i-30); pts += [cx+math.cos(a)*r,cy+math.sin(a)*r]
                    canvas.create_polygon(*pts,fill=self._mix_hex(base,active,.18),outline=accent,width=2)
                    r2=int(r*(.70+.05*math.sin(phase*.2))); pts2=[]
                    for i in range(6):
                        a=math.radians(60*i-30); pts2 += [cx+math.cos(a)*r2,cy+math.sin(a)*r2]
                    canvas.create_polygon(*pts2,fill="",outline=accent2,width=1)
                    txt(cx,cy-5,"30",accent,max(28,int(h*.25)),"center","Consolas","bold")
                    txt(cx,cy+25,"STREAK",accent2,8,"center")
                    particles(10,line2,.35,stars=True)
                    micro_tag("SECRET // UNTOUCHABLE")

                else:  # Endurance
                    # Cronômetro/long run: pistas concêntricas + progresso contínuo.
                    cx=int(w*.48); cy=int(h*.49); rr=max(34,int(h*.27))
                    for off,c,wid in ((0,line2,1),(-12,accent2,2),(-24,accent,2)):
                        r=rr+off; canvas.create_arc(cx-r,cy-r,cx+r,cy+r,start=90,extent=300,style="arc",outline=c,width=wid)
                    a=math.radians((phase*6)%360-90); canvas.create_line(cx,cy,cx+math.cos(a)*(rr-8),cy+math.sin(a)*(rr-8),fill=accent,width=3)
                    txt(cx,cy,"20",accent,max(24,int(h*.22)),"center","Consolas","bold")
                    txt(cx,cy+24,"KILLS // NO DEATH",accent2,7,"center")
                    for i in range(10):
                        x=int(w*.70)+i*max(10,int(w*.025)); bh=10+(i%4)*6
                        rect(x,h-20-bh,x+5,h-20,fill=accent if i<6 else line2)
                    micro_tag("SECRET // ENDURANCE")

                # v3.17.2 — second motion layer. The inner scene now behaves like a
                # living secret identity instead of a static decorated panel.
                hover_boost=1.0 if not compact else (1.35 if phase>0 else .75)
                if theme_name=="Party":
                    for k in range(5):
                        ang=phase*.12+k*1.256; rr=22+k*9
                        x=int(w*.52+math.cos(ang)*rr); y=int(h*.50+math.sin(ang)*rr*.55)
                        txt(x,y,("✦","+","◇","*","o")[k],(accent,accent2,border,"#7EE7FF",text)[k],8,"center")
                elif theme_name=="Frequency":
                    for k in range(4):
                        x=int((phase*(14+k*3)+k*w*.23)%max(1,w)); y=int(h*(.25+.14*k))
                        canvas.create_oval(x-3,y-3,x+3,y+3,fill=accent2 if k%2 else accent,outline="")
                        canvas.create_line(max(0,x-34),y,x,y,fill=line2,width=1)
                elif theme_name=="Flagborn":
                    stream=("true","false","120","240","D3D11","APPLY")
                    for k,val in enumerate(stream):
                        x=int((k*117+phase*(8+k))%max(1,w)); y=10+(k%3)*max(15,int(h*.24))
                        txt(x,y,val,accent if (k+int(phase))%3==0 else line2,6)
                elif theme_name=="Architect":
                    scan=int((phase*9)%max(1,w)); canvas.create_line(scan,0,scan,h,fill=self._mix_hex(base,accent,.70),width=1)
                    for k in range(5):
                        x=int(w*(.15+.17*k)); y=int(h*(.30+.08*math.sin(phase*.14+k)))
                        canvas.create_oval(x-3,y-3,x+3,y+3,outline=accent2,width=1)
                elif theme_name=="Jackpot":
                    sym=("7","ZK","★","◆","WIN")
                    for k in range(3):
                        v=sym[(int(phase*.55)+k*2)%len(sym)]
                        x=int(w*.5+(k-1)*max(52,w*.12)); txt(x,int(h*.15),v,accent2,7,"center")
                elif theme_name=="No Dash":
                    for k in range(4):
                        x=int((phase*(19+k*4)+k*91)%max(1,w)); y=int(h*(.20+.18*k))
                        canvas.create_line(x-42,y,x-8,y,fill=accent2,width=2); txt(x+2,y,"STOP",accent,6,"w")
                elif theme_name=="Millionaire":
                    live=750000+int((phase*1379)%250001)
                    txt(w-16,h-16,f"LIVE +{live:,}".replace(",","."),accent2,7,"se")
                    x=int((phase*13)%max(1,w)); canvas.create_line(x,0,x,h,fill=line,width=1)
                elif theme_name=="Pure Combat":
                    for k in range(4):
                        ang=phase*.18+k*math.pi/2; rr=45+8*math.sin(phase*.22+k)
                        x=int(w*.55+math.cos(ang)*rr); y=int(h*.49+math.sin(ang)*rr*.55)
                        txt(x,y,"✦" if k%2 else "X",accent if k%2 else accent2,8,"center")
                elif theme_name=="Untouchable":
                    cx=int(w*.54); cy=int(h*.50)
                    for k in range(6):
                        ang=k*math.pi/3+.35; dist=max(48,int(w*.36)-int((phase*(8+k))%max(60,w*.25)))
                        x=int(cx+math.cos(ang)*dist); y=int(cy+math.sin(ang)*dist*.45)
                        canvas.create_line(x,y,int(cx+math.cos(ang)*max(38,h*.26)),int(cy+math.sin(ang)*max(28,h*.18)),fill=line2,width=1)
                        canvas.create_oval(x-2,y-2,x+2,y+2,fill=accent2,outline="")
                elif theme_name=="Endurance":
                    secs=int(phase*3)%3600; mm=secs//60; ssx=secs%60
                    txt(w-18,18,f"{mm:02d}:{ssx:02d}",accent2,8,"ne")
                    pulse=.5+.5*math.sin(phase*.30); bw=int((w*.22)*pulse); rect(int(w*.70),h-12,int(w*.70)+bw,h-8,fill=accent)
                return True

            if theme_name=="Matrix Terminal":
                # terminal de verdade: pane vertical, prompt, barras de memória e scanline
                rect(0,0,int(w*.34),h,fill=self._mix_hex(base,active,.18))
                cols=max(9,w//54); chars="01{}[]<>ZK/\\"
                for i in range(cols):
                    x=14+i*(w-28)/max(1,cols-1)
                    y0=int((i*31+phase*(9+i%4))%(h+90))-90
                    for j in range(7 if not compact else 5):
                        y=y0+j*16
                        txt(x,y,chars[(i*3+j)%len(chars)],line if j else accent,7,"center")
                scan=int((phase*8)%max(20,h)); canvas.create_line(0,scan,w,scan,fill=self._mix_hex(base,accent,.58),width=1)
                # terminal principal
                x0=int(w*.43); y0=int(h*.18); x1=w-22; y1=int(h*.76)
                rect(x0,y0,x1,y1,fill=self._mix_hex(base,active,.20),outline=line,width=1)
                rect(x0,y0,x1,y0+18,fill=self._mix_hex(base,accent,.12))
                for k in range(3): canvas.create_oval(x0+10+k*12,y0+6,x0+16+k*12,y0+12,fill=accent if k==0 else line2,outline="")
                txt(x0+12,y0+30,"> zkstrap --session matrix",accent,8)
                txt(x0+12,y0+48,"[OK] renderer   [OK] network   [OK] client",line2,7)
                for r in range(3):
                    yy=y0+70+r*18; rect(x0+12,yy,x0+120+(r*42),yy+5,fill=self._mix_hex(base,accent,.35+r*.10))
                corner_frame(accent,18); micro_tag("MATRIX // LIVE TERMINAL")

            elif theme_name=="Cyberpunk Neon":
                # skyline, via de perspectiva, outdoor holográfico e glitch blocks
                horizon=int(h*.66)
                rect(0,horizon,w,h,fill=self._mix_hex(base,active,.20))
                for i,x in enumerate(range(-10,w+60,50)):
                    bh=28+(i*23)%max(36,int(h*.55)); bw=28+(i%3)*8
                    rect(x,horizon-bh,x+bw,horizon,fill=self._mix_hex(base,active,.30))
                    for wy in range(horizon-bh+8,horizon-6,13):
                        canvas.create_line(x+6,wy,min(x+bw-6,w),wy,fill=accent if (wy//13+i)%5==0 else line2,width=1)
                # road perspective
                vanx=int(w*.56); vany=horizon
                for x in range(-100,w+100,max(70,w//10)): canvas.create_line(vanx,vany,x,h,fill=line,width=1)
                for j in range(6):
                    yy=vany+int((h-vany)*(j/6)**1.7); canvas.create_line(0,yy,w,yy,fill=line2,width=1)
                # billboard angular
                bx=int(w*.70); by=16; bw=int(w*.22); bh=max(46,int(h*.34))
                canvas.create_polygon(bx+12,by,bx+bw,by,bx+bw-12,by+bh,bx,by+bh,fill=self._mix_hex(base,active,.36),outline=accent2)
                txt(bx+22,by+12,"NEON//DISTRICT",accent,8)
                txt(bx+22,by+29,"SIGNAL  88.7",accent2,7)
                off=int((phase*6)%90)
                for x in range(-h-off,w+h,120): diagonal_ribbon(x,h,x+h,0,line,1)
                particles(10,accent2,.7)
                corner_frame(accent,22); micro_tag("CYBERPUNK // NIGHT GRID")

            elif theme_name=="Electric Blue":
                # motherboard/PCB com chip central, barramento e pulso elétrico
                for y in (int(h*.22),int(h*.48),int(h*.74)):
                    canvas.create_line(14,y,int(w*.62),y,fill=line,width=1)
                for i in range(8):
                    x=24+i*int(max(38,w*.065)); yy=int(h*(.22+(i%3)*.26))
                    canvas.create_line(x,yy,x,yy+18,x+26,yy+18,fill=accent if i%4==1 else line2,width=2 if i%4==1 else 1)
                    canvas.create_oval(x-3,yy-3,x+3,yy+3,fill=accent2,outline="")
                cx=int(w*.76); cy=int(h*.47); cw=max(105,int(w*.13)); ch=max(70,int(h*.48))
                rect(cx-cw//2,cy-ch//2,cx+cw//2,cy+ch//2,fill=self._mix_hex(base,active,.32),outline=accent,width=2)
                for k in range(-3,4):
                    canvas.create_line(cx+k*14,cy-ch//2,cx+k*14,cy-ch//2-10,fill=accent2)
                    canvas.create_line(cx+k*14,cy+ch//2,cx+k*14,cy+ch//2+10,fill=accent2)
                # raio estilizado dentro do chip
                pts=[cx-18,cy-28,cx+4,cy-7,cx-8,cy-7,cx+19,cy+30,cx+7,cy+5,cx+18,cy+5]
                canvas.create_polygon(*pts,fill=accent,outline=accent2)
                txt(cx,cy+42,"CORE I/O",accent2,7,"center")
                corner_frame(accent2,18); micro_tag("ELECTRIC // PCB ENGINE")

            elif theme_name=="Deep Ocean":
                # profundidade: ondas em planos, trench, sonar exclusivo e bolhas
                horizon=int(h*.38)
                for row in range(6):
                    yy=horizon+row*int(max(10,h*.08)); pts=[]
                    amp=5+row*2
                    for x in range(-10,w+30,24): pts += [x,yy+int(math.sin(x/58+phase*.11+row*.8)*amp)]
                    canvas.create_line(*pts,fill=accent if row==1 else line,width=2 if row==1 else 1,smooth=True)
                canvas.create_polygon(0,h,int(w*.18),int(h*.70),int(w*.31),h,int(w*.47),int(h*.78),int(w*.58),h,fill=self._mix_hex(base,active,.26),outline="")
                # sonar só aqui, propositalmente
                cx=int(w*.82); cy=int(h*.50)
                for rr in (22,40,60): canvas.create_arc(cx-rr,cy-rr,cx+rr,cy+rr,start=195,extent=285,style="arc",outline=self._mix_hex(line,accent,.60),width=1)
                a=phase*.10; canvas.create_line(cx,cy,cx+int(math.cos(a)*62),cy+int(math.sin(a)*62),fill=accent2,width=2)
                particles(13,line2,.45)
                corner_frame(self._mix_hex(border,accent,.60),26); micro_tag("DEEP OCEAN // SONAR DEPTH")

            elif theme_name=="Blood & Bone":
                # estética agressiva: rachaduras, lâminas e placa central quebrada
                shift=int(math.sin(phase*.14)*6)
                for i in range(7):
                    x=int(w*(.06+i*.12))+shift
                    canvas.create_line(x,h-8,x+int(h*(.35+(i%3)*.12)),12,fill=accent if i%3==0 else line,width=3 if i%3==0 else 1)
                # fracture shards
                for i in range(7):
                    x=int(w*.50)+i*35; y=18+(i%3)*18
                    canvas.create_polygon(x,y,x+24,y+6,x+9,y+28,fill=self._mix_hex(base,active,.35),outline=line2)
                bx=int(w*.72); by=int(h*.20); bw=int(w*.20); bh=int(h*.56)
                canvas.create_polygon(bx+18,by,bx+bw,by+8,bx+bw-18,by+bh,bx,by+bh-10,fill=self._mix_hex(base,active,.26),outline=accent)
                txt(bx+bw//2,by+bh//2,"X",accent,max(30,int(h*.30)),"center","Consolas","bold")
                # claw marks
                for k in range(3): diagonal_ribbon(int(w*.18)+k*18,int(h*.24),int(w*.31)+k*18,int(h*.66),accent2,2)
                corner_frame(accent,16); micro_tag("BLOOD & BONE // COMBAT SHELL")

            elif theme_name=="Forest Hacker":
                # árvore-circuito + terminais pendurados + chuva de código verde
                trunk=int(w*.18); rooty=int(h*.80)
                canvas.create_line(trunk,rooty,trunk,int(h*.20),fill=accent,width=4)
                for i in range(9):
                    y=int(h*(.22+i*.06)); direction=1 if i%2==0 else -1
                    end=trunk+direction*(70+(i%4)*34)
                    canvas.create_line(trunk,y,end,y-18+(i%3)*12,fill=line2,width=2 if i%3==0 else 1)
                    canvas.create_oval(end-4,y-22+(i%3)*12,end+4,y-14+(i%3)*12,fill=accent2,outline="")
                # raízes
                for k in range(5): canvas.create_line(trunk,rooty,trunk+(k-2)*48,h-8,fill=line,width=1)
                # terminal cards
                for j in range(3):
                    x=int(w*.43)+j*int(w*.16); y=20+(j%2)*28; ww=int(w*.12); hh=max(42,int(h*.26))
                    rect(x,y,x+ww,y+hh,fill=self._mix_hex(base,active,.23),outline=line,width=1)
                    txt(x+8,y+8,"{ node_%02d }"%(j+1),accent if j==1 else line2,7)
                    rect(x+8,y+26,x+ww-12,y+30,fill=self._mix_hex(base,accent,.34))
                particles(8,accent,.25)
                corner_frame(accent2,20); micro_tag("FOREST HACKER // ROOT NETWORK")

            elif theme_name=="Sunset Synthwave":
                # sol listrado, montanhas em duas camadas, estrada grid e estrelas
                horizon=int(h*.55); cx=int(w*.72); r=max(34,int(h*.34))
                canvas.create_oval(cx-r,horizon-r,cx+r,horizon+r,fill=self._mix_hex(base,accent2,.16),outline=accent2,width=2)
                for yy in range(horizon-r+8,horizon+r,11): canvas.create_line(cx-r,yy,cx+r,yy,fill=base,width=3)
                canvas.create_polygon(0,horizon,int(w*.12),int(h*.35),int(w*.24),horizon,int(w*.34),int(h*.42),int(w*.46),horizon,fill=self._mix_hex(base,active,.26),outline=accent)
                canvas.create_polygon(int(w*.26),horizon,int(w*.40),int(h*.28),int(w*.57),horizon,int(w*.67),int(h*.40),int(w*.79),horizon,fill=self._mix_hex(base,active,.17),outline=line2)
                # road grid
                for j in range(7):
                    frac=(j/7)**1.6; yy=horizon+int((h-horizon)*frac); canvas.create_line(0,yy,w,yy,fill=line,width=1)
                for x in range(-100,w+101,max(80,w//12)): canvas.create_line(w//2,horizon,x,h,fill=line2,width=1)
                particles(12,accent2,.4,True)
                corner_frame(accent,22); micro_tag("SUNSET // SYNTH HIGHWAY")

            elif theme_name=="Void Purple":
                # rasgo dimensional angular, shards, estrelas e núcleo — sem círculos
                cx=int(w*.76); cy=int(h*.48)
                for layer,(rx,ry) in enumerate(((110,58),(82,43),(55,29))):
                    pts=[]
                    for k in range(12):
                        a=phase*.035+k*math.pi/6; mod=1.0+(0.13 if k%2 else -0.08)
                        pts += [cx+math.cos(a)*rx*mod,cy+math.sin(a)*ry*mod]
                    canvas.create_polygon(*pts,outline=accent if layer==0 else line2,fill=self._mix_hex(base,active,.10 if layer==0 else .06),width=2 if layer==0 else 1)
                # core slit
                canvas.create_polygon(cx-12,cy-38,cx+10,cy-12,cx+2,cy+42,cx-16,cy+12,fill=accent2,outline=accent)
                for i in range(15):
                    x=int((i*83+phase*2.7)%w); y=int((i*37+phase*.8)%max(20,h)); sz=4+(i%3)*2
                    canvas.create_polygon(x,y,x+sz,y+2,x+2,y+sz+2,fill=accent if i%4==0 else line,outline="")
                particles(10,line2,.35,True)
                corner_frame(accent2,24); micro_tag("VOID // FRACTURE FIELD")

            elif theme_name=="Obsidian Gold":
                # painel premium com facets, ouro e crest central
                # placas largas assimétricas
                for i in range(4):
                    x=18+i*int(w*.19); y=20+(i%2)*20; ww=max(86,int(w*.15)); hh=max(52,int(h*.42))
                    canvas.create_polygon(x+12,y,x+ww,y,x+ww-12,y+hh,x,y+hh,fill=self._mix_hex(base,active,.24),outline=accent if i==1 else line)
                    canvas.create_line(x+18,y+hh//2,x+ww-18,y+hh//2,fill=accent2,width=1)
                # crest à direita
                cx=int(w*.83); cy=int(h*.50); rr=max(34,int(h*.28))
                canvas.create_polygon(cx,cy-rr,cx+rr,cy,cx,cy+rr,cx-rr,cy,fill=self._mix_hex(base,accent,.11),outline=accent,width=2)
                canvas.create_polygon(cx,cy-int(rr*.55),cx+int(rr*.55),cy,cx,cy+int(rr*.55),cx-int(rr*.55),cy,fill="",outline=accent2,width=1)
                txt(cx,cy,"◆",accent2,18,"center","Segoe UI Symbol","normal")
                for i in range(6):
                    x=int(w*.52)+i*34; canvas.create_line(x,h-23,x+20,h-23,fill=line2,width=2)
                corner_frame(accent,18); micro_tag("OBSIDIAN // GOLD VAULT")

            elif theme_name=="Arctic Glass":
                # facetas de gelo em múltiplos planos + frost cracks
                peaks=[(.02,.88,.13,.28,.25,.88),(.18,.88,.33,.40,.47,.88),(.39,.88,.57,.16,.72,.88),(.62,.88,.78,.34,.96,.88)]
                for i,pv in enumerate(peaks):
                    pts=[int(w*pv[j]) if j%2==0 else int(h*pv[j]) for j in range(6)]
                    canvas.create_polygon(*pts,fill=self._mix_hex(base,active,.18 if i==2 else .10),outline=accent if i==2 else line2)
                    # faceta interior
                    ax,ay,bx,by,cx,cy=pts
                    canvas.create_line(bx,by,(ax+cx)//2,(ay+cy)//2,fill=line,width=1)
                # frost crack left
                x=int(w*.18); y=int(h*.20)
                for dx,dy in ((45,20),(25,48),(58,64),(14,82)):
                    canvas.create_line(x,y,x+dx,y+dy,fill=accent2 if dy==48 else line,width=1)
                particles(16,accent2,.30,True)
                corner_frame(accent2,28); micro_tag("ARCTIC // CRYSTAL ARRAY")

            elif theme_name=="Sakura Night":
                # lua/cidade noturna + torii + galho + pétalas/lanternas
                moonx=int(w*.82); moony=int(h*.28); rr=max(28,int(h*.22))
                canvas.create_oval(moonx-rr,moony-rr,moonx+rr,moony+rr,fill=self._mix_hex(base,accent2,.22),outline=accent2,width=1)
                # corta lua para virar crescente
                canvas.create_oval(moonx-rr+14,moony-rr-3,moonx+rr+14,moony+rr-3,fill=base,outline="")
                tx=int(w*.66); top=int(h*.33); bottom=int(h*.82)
                canvas.create_line(tx-66,top,tx+66,top,fill=accent,width=4)
                canvas.create_line(tx-50,top-11,tx+50,top-11,fill=accent2,width=2)
                canvas.create_line(tx-38,top,tx-38,bottom,fill=line2,width=5); canvas.create_line(tx+38,top,tx+38,bottom,fill=line2,width=5)
                # branch
                canvas.create_line(0,int(h*.30),int(w*.30),int(h*.18),fill=line2,width=4)
                for k in range(6): canvas.create_line(40+k*38,int(h*.28)-k*2,65+k*38,int(h*.12)+(k%2)*14,fill=line,width=2)
                for i in range(20):
                    x=int((i*71+phase*2.5)%w); y=int((i*41+phase*1.2)%max(20,h))
                    txt(x,y,"✿" if i%4==0 else "•",accent if i%4==0 else line2,8,"center","Segoe UI Symbol","normal")
                corner_frame(accent,18); micro_tag("SAKURA // NIGHT SHRINE")

            elif theme_name=="Midnight Chrome":
                # metal/carbono, speedline e telemetry bars
                for i in range(8):
                    y=12+i*int(max(10,h*.10)); shift=int(math.sin(phase*.06+i*.7)*14)
                    canvas.create_line(12+shift,y,int(w*.64)+shift,y,fill=accent if i==3 else line,width=2 if i==3 else 1)
                # plates
                for j in range(3):
                    x=int(w*.68)+j*int(w*.09); y=18+j*11; ww=int(w*.08); hh=max(36,int(h*.44))
                    canvas.create_polygon(x+10,y,x+ww,y,x+ww-10,y+hh,x,y+hh,fill=self._mix_hex(base,active,.26),outline=line2)
                # linear meter
                x0=int(w*.58); x1=w-28; cy=int(h*.80)
                rect(x0,cy-9,x1,cy+9,fill=self._mix_hex(base,active,.20),outline=accent2)
                span=max(10,x1-x0-14); fillw=int(span*(.52+.16*math.sin(phase*.07)))
                rect(x0+7,cy-3,x0+7+fillw,cy+3,fill=accent)
                corner_frame(accent2,16); micro_tag("MIDNIGHT // CHROME TELEMETRY")

            elif theme_name=="Inferno Core":
                # lava core, heat towers e chama angular
                # heat haze horizontal
                for row in range(4):
                    yy=int(h*(.20+row*.14)); pts=[]
                    for x in range(0,w+20,22): pts += [x,yy+int(math.sin(x/45+phase*.13+row)*4)]
                    canvas.create_line(*pts,fill=line if row!=2 else accent,width=1,smooth=True)
                pts=[0,h]
                for i in range(17):
                    x=int(i*w/16); peak=int(h*(.34 if i%2 else .74)+math.sin(phase*.12+i)*7)
                    pts += [x,peak]
                pts += [w,h]
                canvas.create_polygon(*pts,fill=self._mix_hex(base,active,.30),outline=accent)
                # core furnace right
                bx=int(w*.72); by=int(h*.18); bw=int(w*.18); bh=int(h*.50)
                rect(bx,by,bx+bw,by+bh,fill=self._mix_hex(base,active,.24),outline=accent2)
                for i in range(5):
                    barh=12+(i*11)%max(18,int(bh*.55)); rect(bx+18+i*22,by+bh-15-barh,bx+29+i*22,by+bh-15,fill=accent if i==2 else line2)
                txt(bx+bw//2,by+14,"THERMAL CORE",accent2,7,"n")
                corner_frame(accent,20); micro_tag("INFERNO // THERMAL ENGINE")

            elif theme_name=="Emerald Glass":
                # painéis de vidro, células hex/diamante e waveform central
                for i in range(4):
                    x=int(w*(.06+i*.20)); ww=int(w*.16)
                    canvas.create_polygon(x+16,16,x+ww,16,x+ww-16,h-16,x,h-16,fill=self._mix_hex(base,active,.20),outline=line2)
                    for j in range(3):
                        yy=30+j*18; canvas.create_line(x+20,yy,x+ww-22,yy,fill=accent if (i+j)%5==0 else line,width=1)
                pts=[]; yy=int(h*.55)
                for x in range(0,w+18,18): pts += [x,yy+int(math.sin(x/42+phase*.15)*13)]
                canvas.create_line(*pts,fill=accent,width=2,smooth=True)
                # glass diamonds
                for i in range(5):
                    cx=int(w*.58)+i*58; cy=int(h*.23)+(i%2)*24; rr=11
                    canvas.create_polygon(cx,cy-rr,cx+rr,cy,cx,cy+rr,cx-rr,cy,fill=self._mix_hex(base,accent2,.13),outline=accent2)
                corner_frame(accent2,24); micro_tag("EMERALD // GLASS BUS")

            elif theme_name=="ZKStrap Core":
                # assinatura do próprio app: monograma gigante, slashes e módulos assimétricos
                # placas de fundo
                canvas.create_polygon(0,h,int(w*.18),h,int(w*.31),0,int(w*.12),0,fill=self._mix_hex(base,active,.26),outline="")
                canvas.create_polygon(int(w*.70),0,w,0,w,h,int(w*.84),h,fill=self._mix_hex(base,active,.16),outline="")
                # monograma fantasma + slash vermelho
                txt(int(w*.54),int(h*.52),"ZK",self._mix_hex(base,text,.18),max(44,int(h*.48)),"center","Segoe UI","bold")
                diagonal_ribbon(int(w*.26),h,int(w*.52),0,accent,4)
                diagonal_ribbon(int(w*.31),h,int(w*.57),0,accent2,1)
                # módulos inferiores
                for i in range(5):
                    x=int(w*.46)+i*46; rect(x,h-34,x+30,h-16,fill=self._mix_hex(base,active,.26),outline=line)
                    if i%2==0: rect(x+6,h-28,x+22,h-22,fill=accent)
                # badge signature
                bx=int(w*.76); by=18; bw=int(w*.16); bh=max(42,int(h*.30))
                canvas.create_polygon(bx+12,by,bx+bw,by,bx+bw-12,by+bh,bx,by+bh,fill=self._mix_hex(base,active,.30),outline=accent)
                txt(bx+bw//2,by+13,"SIGNATURE",accent2,7,"n")
                txt(bx+bw//2,by+29,"LOCAL CORE",text,8,"n")
                corner_frame(accent,24); micro_tag("ZKSTRAP // SIGNATURE CONTROL")

            else:  # Clean
                # painel editorial limpo, propositalmente diferente dos temas gamer
                rect(16,18,int(w*.60),46,fill=self._mix_hex(base,active,.18),outline=line)
                rect(16,58,int(w*.42),82,fill=self._mix_hex(base,active,.12),outline=line2)
                rect(int(w*.65),18,w-18,h-18,fill=self._mix_hex(base,active,.15),outline=accent)
                for i in range(4): canvas.create_line(28,108+i*14,int(w*.53),108+i*14,fill=line,width=1)
                canvas.create_line(16,h-18,int(w*.60),h-18,fill=accent,width=2)
                corner_frame(border,14); micro_tag("CLEAN // EDITORIAL SHELL")

            # Motion layer 3.13.3.4: cada Core usa uma linguagem de movimento própria.
            # O overlay é leve e reaproveita a mesma fase do loop visual; nada de um
            # radar/círculo universal copiado entre temas.
            ph=phase
            if theme_name=="Matrix Terminal":
                x=int((ph*22)%max(1,w)); canvas.create_line(x,0,x,h,fill=self._mix_hex(base,accent,.55),width=1)
                if int(ph*4)%2==0: txt(int(w*.47),int(h*.78),"█",accent,8,"w")
            elif theme_name=="Cyberpunk Neon":
                y=int(h*.76); x=int((ph*34)%(w+140))-70
                canvas.create_line(x,y,x+58,y-18,fill=accent2,width=3); canvas.create_line(x-18,y+4,x+24,y-9,fill=accent,width=1)
            elif theme_name=="Electric Blue":
                for j,yy in enumerate((int(h*.22),int(h*.48),int(h*.74))):
                    x=int((ph*(28+j*5)+j*97)%max(1,int(w*.62)))
                    canvas.create_oval(x-4,yy-4,x+4,yy+4,fill=accent,outline=self._mix_hex(accent,"#FFFFFF",.45))
            elif theme_name=="Deep Ocean":
                for j in range(7):
                    x=int(w*(.10+.11*j)); y=h-int((ph*(8+j*.7)+j*25)%(h+24))
                    rr=2+(j%3); canvas.create_oval(x-rr,y-rr,x+rr,y+rr,outline=line2,width=1)
            elif theme_name=="Blood & Bone":
                sweep=int((ph*19)%(w+160))-80
                for k in range(3): canvas.create_line(sweep+k*18,h,sweep+95+k*18,0,fill=accent if k==1 else line2,width=2 if k==1 else 1)
            elif theme_name=="Forest Hacker":
                for j in range(5):
                    x=int(w*(.42+j*.09)); y=int((ph*(7+j)+j*21)%max(1,h))
                    txt(x,y,"01{}ZK"[(j+int(ph))%6],accent if j%2==0 else line2,7,"center")
            elif theme_name=="Sunset Synthwave":
                off=int((ph*7)%18)
                for j in range(5):
                    yy=h-8-j*18+off
                    if 0<yy<h: canvas.create_line(int(w*.28),yy,int(w*.75),yy,fill=line,width=1)
            elif theme_name=="Void Purple":
                for j in range(5):
                    cx=int(w*(.18+j*.16)+math.sin(ph*.11+j)*8); cy=int(h*(.35+(j%2)*.22)+math.cos(ph*.13+j)*7); rr=5+(j%2)*3
                    canvas.create_polygon(cx,cy-rr,cx+rr,cy,cx,cy+rr,cx-rr,cy,fill=self._mix_hex(base,accent,.18),outline=accent2)
            elif theme_name=="Obsidian Gold":
                x=int((ph*26)%(w+220))-110
                canvas.create_line(x,h,x+125,0,fill=self._mix_hex(accent,"#FFFFFF",.45),width=3)
            elif theme_name=="Arctic Glass":
                for j in range(12):
                    x=int((j*83+ph*(3+j%3))%max(1,w)); y=int((j*27+ph*(8+j%4))%max(1,h)); r=1+(j%2)
                    canvas.create_oval(x-r,y-r,x+r,y+r,fill=accent2,outline="")
            elif theme_name=="Sakura Night":
                for j in range(9):
                    x=int((j*101+ph*(6+j%3))%max(1,w)); y=int((j*19+ph*(10+j%2))%max(1,h))
                    txt(x,y,"✦",accent2 if j%3 else accent,7,"center","Segoe UI Symbol","normal")
            elif theme_name=="Midnight Chrome":
                for j in range(5):
                    x=int((ph*(32+j*4)+j*129)%(w+180))-90; yy=int(h*(.22+j*.13))
                    canvas.create_line(x,yy,x+90,yy,fill=accent if j==2 else line2,width=2 if j==2 else 1)
            elif theme_name=="Inferno Core":
                for j in range(10):
                    x=int(w*(.08+(j*.083)% .84)+math.sin(ph*.12+j)*6); y=h-int((ph*(11+j%4)+j*17)%(h+18)); r=1+(j%3)
                    canvas.create_oval(x-r,y-r,x+r,y+r,fill=accent if j%2 else accent2,outline="")
            elif theme_name=="Emerald Glass":
                x=int((ph*20)%max(1,w)); canvas.create_rectangle(x-2,16,x+2,h-16,fill=self._mix_hex(base,accent,.52),outline="")
            elif theme_name=="ZKStrap Core":
                # Movimento assinatura: slash principal + trilhas paralelas + módulos pulsantes
                x=int((ph*28)%(w+220))-110
                canvas.create_line(x,h,x+145,0,fill=self._mix_hex(accent,"#FFFFFF",.42),width=3)
                canvas.create_line(x-58,h,x+88,0,fill=self._mix_hex(accent2,base,.34),width=1)
                canvas.create_line(x+64,h,x+205,0,fill=line2,width=1)
                # pequenos data packets atravessando a faixa inferior
                for j in range(6):
                    px=int((ph*(20+j*2)+j*97)%(w+70))-35
                    py=h-28-(j%2)*8
                    rr=3+(j%2)
                    canvas.create_rectangle(px-rr,py-rr,px+rr,py+rr,fill=accent if j%3==0 else line2,outline="")
                # pulso nos módulos inferiores
                pulse=.5+.5*math.sin(ph*.30)
                pw=max(8,int(22+10*pulse))
                cx=int(w*.54)
                canvas.create_rectangle(cx-pw,h-38,cx+pw,h-34,fill=self._mix_hex(base,accent,.48),outline="")
                # scanline vertical curta no badge
                bx=int(w*.76); bw=int(w*.16); sx=bx+int((ph*11)%max(1,bw))
                canvas.create_line(sx,20,sx,min(h-18,78),fill=self._mix_hex(accent,"#FFFFFF",.32),width=1)
                # partículas técnicas discretas
                for j in range(7):
                    px=int((j*131+ph*(4+j%2))%max(1,w)); py=int(h*(.18+.09*(j%5)))
                    canvas.create_oval(px-1,py-1,px+1,py+1,fill=accent2 if j%2 else accent,outline="")
            else:  # Clean
                # Clean continua minimalista, mas agora tem movimento editorial em várias camadas.
                x=int(16+(ph*15)%max(1,int(w*.56)))
                canvas.create_rectangle(x,h-20,min(w-16,x+48),h-17,fill=accent,outline="")
                # cursor editorial deslizando pelas linhas
                cx=int(28+(ph*9)%max(1,int(w*.48)))
                cy=109+int((math.sin(ph*.18)+1)*14)
                canvas.create_oval(cx-3,cy-3,cx+3,cy+3,fill=accent,outline="")
                canvas.create_line(cx+8,cy,cx+42,cy,fill=line2,width=1)
                # painel direito com barras suaves pulsando
                rx=int(w*.68); rw=max(36,int(w*.25))
                for j in range(3):
                    yy=42+j*22; amp=.5+.5*math.sin(ph*.20+j*1.7)
                    ww=int(20+(rw-30)*amp)
                    canvas.create_rectangle(rx,yy,rx+ww,yy+4,fill=self._mix_hex(base,accent,.20+j*.08),outline="")
                # scan muito leve na horizontal
                sy=int((ph*7)%max(1,h))
                canvas.create_line(0,sy,w,sy,fill=self._mix_hex(base,border,.14),width=1)

            return True
        except Exception:
            return False

    def _draw_theme_atmosphere(self, canvas, theme_name, zone="hero"):
        """Sistema 3.13: o tema vira atmosfera do shell, não um preview dentro de caixa."""
        try:
            t=TEMAS.get(theme_name,TEMAS["Clean"])
            w=max(8,int(canvas.winfo_width())); h=max(8,int(canvas.winfo_height()))
            phase=float(getattr(self,"_ambient_phase",0.0) or 0.0)
            if bool(getattr(canvas,"_zk_preview",False)) and not bool(getattr(canvas,"_zk_preview_hover",False)):
                if theme_name in UNLOCKABLE_THEME_NAMES:
                    # Secret Vault previews stay alive even before hover. Locked cards
                    # run in a slow dormant state; hover wakes the full animation.
                    phase=phase*(0.20 if bool(getattr(canvas,"_zk_secret_locked",False)) else 0.55)
                else:
                    phase=0.0
            canvas.delete("all")
            base=t.get("panel",t["bg"])
            canvas.configure(bg=base)
            accent=t["accent"]; border=t["border"]; active=t["card_active"]
            refs=[]

            # Imagens reais dos jogos ficam EXCLUSIVAMENTE no banner superior.
            # A galeria continua com previews próprios, sem jogar wallpaper pelo shell.
            if theme_name in SPECIAL_THEME_NAMES and zone=="hero":
                if self._draw_special_theme_banner(canvas,theme_name,w,h):
                    return
            if theme_name in SPECIAL_THEME_NAMES and zone=="gallery":
                if self._draw_special_theme_scene(canvas,theme_name,w,h):
                    return

            # Core 3.13.3.3: hero/galeria são 100% identidade própria.
            # Não desenha mais o antigo fundo genérico (grid/radar/círculos) antes
            # da composição exclusiva de cada tema.
            if theme_name not in SPECIAL_THEME_NAMES and zone in ("hero","gallery"):
                self._draw_core_theme_signature(canvas,theme_name,w,h,t,phase,zone)
                canvas._zk_special_refs=refs
                return

            # Base procedural compartilhada apenas para header/sidebar/dock.
            line=self._mix_hex(active,accent,.24)
            soft=self._mix_hex(base,accent,.10)
            if zone=="header":
                canvas.create_line(0,h-2,w,h-2,fill=accent,width=2)
            elif zone=="sidebar":
                canvas.create_line(w-2,0,w-2,h,fill=self._mix_hex(border,accent,.4),width=1)
            elif zone=="dock":
                canvas.create_line(0,1,w,1,fill=self._mix_hex(border,accent,.35),width=1)

            # v3.16.2: a identidade secreta continua pelo shell inteiro (header/sidebar/dock),
            # em vez de herdar apenas a cor do tema anterior.
            if theme_name in UNLOCKABLE_THEME_NAMES:
                dd=THEME_DECOR.get(theme_name,{})
                motif=str(dd.get("icon","✦"))
                if zone=="header":
                    for i in range(8):
                        x=int((i*137+phase*(5+i%3))%max(1,w)); y=9+(i%2)*7
                        canvas.create_text(x,y,text=motif,fill=accent if i%3==0 else line,font=("Consolas",7,"bold"),anchor="center")
                    canvas.create_text(w-18,h//2,text=str(dd.get("tag",theme_name)).upper(),fill=accent2,font=("Consolas",8,"bold"),anchor="e")
                elif zone=="sidebar":
                    for i in range(9):
                        y=int((i*71+phase*(4+i%2))%max(1,h));
                        canvas.create_line(max(0,w-18-(i%3)*7),y,w-3,y,fill=accent if i%4==0 else line,width=2 if i%4==0 else 1)
                elif zone=="dock":
                    x=int((phase*19)%max(1,w)); canvas.create_rectangle(max(0,x-24),3,min(w,x+24),6,fill=accent,outline="")
                canvas._zk_special_refs=refs
                return

            # Temas especiais fora da galeria: assets grandes e discretos ocupam o shell.
            special_focus={
                "Minecraft":("grass_block","creeper"), "Hollow Knight":("mask","soul"),
                "Blox Fruits":("compass","fruit_blue"), "Valorant":("vmark","rank"),
                "CS GO":("radar","badge"), "Terraria":("tree","slime"), "Celeste":("crystal","feather")
            }
            if False and theme_name in special_focus:
                a1,a2=special_focus[theme_name]
                sz=max(42,min(int(h*.90),190 if zone!="sidebar" else 120))
                ph=self._special_theme_asset_photo(theme_name,a1,sz,.24 if zone!="sidebar" else .18)
                if ph:
                    canvas.create_image(w-int(sz*.34),h//2,image=ph,anchor="center"); refs.append(ph)
                ph2=self._special_theme_asset_photo(theme_name,a2,max(34,int(sz*.56)),.16)
                if ph2:
                    canvas.create_image(max(28,int(w*.72)),max(22,int(h*.24)),image=ph2,anchor="center"); refs.append(ph2)
                if zone=="header":
                    brand=self._special_theme_asset_photo(theme_name,"brand",max(54,min(105,int(h*.95))),.12)
                    if brand:
                        canvas.create_image(w-18,h//2,image=brand,anchor="e"); refs.append(brand)

            # Identidades procedurais de TODOS os temas.
            if theme_name in ("Valorant","Blood & Bone","Inferno Core"):
                off=int((phase*10)%90)
                for x in range(-h,w+h,120): canvas.create_line(x+off,0,x-h+off,h,fill=line,width=1)
                canvas.create_polygon(w*.80,0,w,0,w,h,w*.90,h,fill=soft,outline="")
            elif theme_name in ("Minecraft","Terraria"):
                step=max(18,int(h*.22)); off=int(phase*2)%step
                for x in range(-off,w,step): canvas.create_line(x,0,x,h,fill=line,width=1)
                for y in range(-off,h,step): canvas.create_line(0,y,w,y,fill=line,width=1)
            elif theme_name in ("Blox Fruits","Deep Ocean"):
                for row in range(4):
                    yy=int(h*.28+row*h*.17); pts=[]
                    for x in range(-10,w+20,26): pts += [x,yy+int(math.sin(x/60+phase*.18+row)*5)]
                    canvas.create_line(*pts,fill=line if row!=1 else accent,width=1,smooth=True)
            elif theme_name in ("Hollow Knight","Arctic Glass"):
                for k in range(7):
                    x=int((k+.2)*w/6.5)
                    canvas.create_arc(x-55,-30,x+55,h+65,start=0,extent=180,style="arc",outline=line,width=1)
                for i in range(14):
                    x=(i*83+int(phase*3))%w; y=(i*47)%h
                    canvas.create_oval(x,y,x+2,y+2,fill=accent,outline="")
            elif theme_name in ("CS GO","Electric Blue","Midnight Chrome"):
                for x in range(20,w,72):
                    canvas.create_line(x,0,x,h,fill=line,width=1)
                for y in range(14,h,34): canvas.create_line(0,y,w,y,fill=soft,width=1)
                cx=int(w*.82); cy=h//2; rr=max(18,min(h//3,80))
                canvas.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline=line,width=1)
                canvas.create_line(cx-rr,cy,cx+rr,cy,fill=line); canvas.create_line(cx,cy-rr,cx,cy+rr,fill=line)
            elif theme_name in ("Celeste","Sunset Synthwave"):
                canvas.create_polygon(0,h,w*.18,h*.35,w*.34,h,w*.55,h*.24,w*.72,h,w*.90,h*.42,w,h,fill=soft,outline="")
                for i in range(12):
                    x=(i*97+int(phase*6))%w; y=(i*53+int(phase*2))%max(12,h)
                    canvas.create_text(x,y,text="✦" if i%4==0 else "·",fill=line,font=("Consolas",7))
            elif theme_name in ("Matrix Terminal","Forest Hacker"):
                chars="01{}[]<>ZK"
                for i in range(max(8,w//55)):
                    x=12+i*55; y=int((i*31+phase*18)%(h+30))-15
                    canvas.create_text(x,y,text=chars[i%len(chars)],fill=line,font=("Consolas",8,"bold"))
            elif theme_name in ("Void Purple","ZKStrap Core","Obsidian Gold"):
                cx=int(w*.83); cy=h//2
                for rr in (22,38,58): canvas.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline=line if rr<58 else accent,width=1)
                a=phase*.8; ox=cx+int(math.cos(a)*58); oy=cy+int(math.sin(a)*58)
                canvas.create_oval(ox-3,oy-3,ox+3,oy+3,fill=accent,outline="")
                if theme_name=="ZKStrap Core": canvas.create_line(w*.62,h,w*.88,0,fill="#E11D48",width=3)
            elif theme_name=="Sakura Night":
                for i in range(18):
                    x=int((i*71+phase*4)%w); y=int((i*41+phase*2)%h)
                    canvas.create_text(x,y,text="✿" if i%5==0 else "·",fill=line,font=("Segoe UI Symbol",8))
            elif theme_name=="Emerald Glass":
                for row in range(5):
                    pts=[]; yy=12+row*18
                    for x in range(0,w+20,28): pts += [x,yy+int(math.sin(x/52+phase*.17+row)*6)]
                    canvas.create_line(*pts,fill=line if row!=2 else accent,width=1,smooth=True)
            else: # Clean e fallbacks
                for x in range(0,w,70): canvas.create_line(x,0,x,h,fill=soft,width=1)
                for y in range(0,h,42): canvas.create_line(0,y,w,y,fill=soft,width=1)

            decor=THEME_DECOR.get(theme_name,THEME_DECOR["Clean"])
            if zone in ("header","sidebar","dock"):
                canvas.create_text(12 if zone!="sidebar" else w-10, 10 if zone!="dock" else h//2,
                    text=decor["tag"], anchor="nw" if zone!="sidebar" else "ne", fill=self._mix_hex(t.get("muted","#888888"),accent,.25),
                    font=("Consolas",7,"bold"))
            canvas._zk_special_refs=refs
        except Exception:
            pass

    def _draw_special_theme_scene(self, canvas, theme_name, width, height):
        """Preview da galeria: banner real + três itens reais, sem ícones inventados."""
        if theme_name not in SPECIAL_THEME_NAMES or not self._special_theme_root(theme_name):
            return False
        try:
            t=TEMAS.get(theme_name,TEMAS["Clean"]); meta=SPECIAL_THEME_BANNER_META.get(theme_name,{})
            phase=float(getattr(self,"_ambient_phase",0.0) or 0.0)
            w,h=max(24,int(width)),max(24,int(height))
            canvas.configure(bg=t.get("panel",t["bg"])); canvas.delete("all"); refs=[]
            bg=self._special_theme_banner_photo(theme_name,w,h)
            if bg is not None:
                canvas.create_image(w//2,h//2,image=bg,anchor="center"); refs.append(bg)
            icons=list(meta.get("float_icons") or [])[:3]
            scene_slots=[(.22,.29),(.79,.69),(.70,.25)]
            for i,ic in enumerate(icons):
                size=max(48,min(76,int(h*.43)))
                x=int(w*scene_slots[i][0]+math.sin(phase*.26+i*1.2)*3)
                y=int(h*scene_slots[i][1]+math.sin(phase*.55+i*1.9)*4)
                ph=self._special_theme_asset_photo(theme_name,ic,size,.96)
                if ph is not None:
                    iw=max(1,ph.width()); ih=max(1,ph.height())
                    x=max(iw//2+8,min(w-iw//2-8,x)); y=max(ih//2+8,min(h-ih//2-8,y))
                    canvas.create_image(x,y,image=ph,anchor="center"); refs.append(ph)
            canvas.create_rectangle(1,1,w-2,h-2,outline=self._mix_hex(t.get("border",t["accent"]),t["accent"],.46),width=1)
            canvas.create_line(0,h-2,w,h-2,fill=t["accent"],width=2)
            canvas._zk_special_refs=refs
            return True
        except Exception:
            return False

    def _make_nav_icon(self, key, theme_name=None, size=28):
        """Cria ícones reais (Pillow) para a navegação; evita a aparência de símbolos soltos."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            name = theme_name or self.tema_atual
            t = TEMAS[name]
            st = self._theme_style(name)
            scale = 3
            S = 28 * scale
            im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)

            def hx(c, a=255):
                c = c.lstrip('#')
                return tuple(int(c[i:i+2], 16) for i in (0,2,4)) + (a,)
            bg = hx(t.get("icon_bg", t["card_active"]), 245)
            accent = hx(t["accent"])
            accent2 = hx(st.get("accent2", t["text"]))
            pad = 3*scale
            r = max(5*scale, int(st.get("nav_radius", 10)*scale*.55))
            d.rounded_rectangle((pad,pad,S-pad,S-pad), radius=r, fill=bg, outline=accent, width=max(2, scale))
            w = max(2, 2*scale)
            cx = cy = S//2
            x0,y0,x1,y1 = 7*scale,7*scale,21*scale,21*scale

            if key == "home":
                d.polygon([(7*scale,14*scale),(14*scale,8*scale),(21*scale,14*scale)], outline=accent, fill=None)
                d.rectangle((9*scale,14*scale,19*scale,21*scale), outline=accent, width=w)
                d.rectangle((13*scale,17*scale,16*scale,21*scale), fill=accent2)
            elif key == "fps":
                d.polygon([(15*scale,6*scale),(9*scale,15*scale),(14*scale,15*scale),(11*scale,22*scale),(20*scale,12*scale),(15*scale,12*scale)], fill=accent)
            elif key == "ping":
                for rr in (5,8,11):
                    box=(cx-rr*scale, cy-rr*scale, cx+rr*scale, cy+rr*scale)
                    d.arc(box, 210, 330, fill=accent, width=w)
                d.ellipse((cx-2*scale,19*scale,cx+2*scale,23*scale), fill=accent2)
            elif key == "resolution":
                d.rounded_rectangle((6*scale,7*scale,22*scale,19*scale), radius=2*scale, outline=accent, width=w)
                d.line((11*scale,22*scale,17*scale,22*scale), fill=accent2, width=w)
                d.line((14*scale,19*scale,14*scale,22*scale), fill=accent2, width=w)
            elif key == "fastflags":
                d.line((8*scale,6*scale,8*scale,22*scale), fill=accent2, width=w)
                d.polygon([(9*scale,7*scale),(20*scale,9*scale),(16*scale,14*scale),(9*scale,13*scale)], fill=accent)
            elif key == "cursor":
                d.polygon([(8*scale,6*scale),(20*scale,15*scale),(15*scale,16*scale),(18*scale,22*scale),(15*scale,23*scale),(12*scale,17*scale),(8*scale,21*scale)], fill=accent)
            elif key == "fonts":
                try:
                    font = ImageFont.truetype("arial.ttf", 16*scale)
                except Exception:
                    font = ImageFont.load_default()
                d.text((7*scale,4*scale), "Aa", font=font, fill=accent, stroke_width=0)
            elif key == "telemetry":
                d.ellipse((6*scale,6*scale,22*scale,22*scale), outline=accent, width=w)
                d.ellipse((11*scale,11*scale,17*scale,17*scale), fill=accent2)
                d.line((7*scale,21*scale,21*scale,7*scale), fill=accent, width=w)
            elif key == "micro":
                d.rounded_rectangle((8*scale,8*scale,20*scale,20*scale), radius=2*scale, outline=accent, width=w)
                for p in (10,14,18):
                    d.line((p*scale,5*scale,p*scale,8*scale), fill=accent2, width=scale)
                    d.line((p*scale,20*scale,p*scale,23*scale), fill=accent2, width=scale)
                    d.line((5*scale,p*scale,8*scale,p*scale), fill=accent2, width=scale)
                    d.line((20*scale,p*scale,23*scale,p*scale), fill=accent2, width=scale)
                d.line((11*scale,14*scale,17*scale,14*scale), fill=accent, width=w)
            elif key == "draco":
                d.polygon([(14*scale,5*scale),(17*scale,11*scale),(23*scale,14*scale),(17*scale,17*scale),(14*scale,23*scale),(11*scale,17*scale),(5*scale,14*scale),(11*scale,11*scale)], outline=accent, fill=accent2)
                d.ellipse((12*scale,12*scale,16*scale,16*scale), fill=bg)
            elif key == "macro":
                # teclado estilizado + tecla de gravação
                d.rounded_rectangle((5*scale,8*scale,23*scale,20*scale), radius=2*scale, outline=accent, width=w)
                for yy in (11,15):
                    for xx in (8,12,16,20):
                        d.rounded_rectangle((xx*scale,yy*scale,(xx+2)*scale,(yy+2)*scale), radius=scale//2, fill=accent2)
                d.ellipse((18*scale,5*scale,23*scale,10*scale), fill=accent, outline=bg)
            elif key == "combo":
                # quatro slots + seta de sequência
                for px,py in ((8,9),(16,9),(8,17),(16,17)):
                    d.rounded_rectangle((px*scale,py*scale,(px+5)*scale,(py+5)*scale), radius=scale, outline=accent, width=scale)
                d.line((7*scale,24*scale,21*scale,24*scale), fill=accent2, width=scale)
                d.polygon([(21*scale,24*scale),(18*scale,22*scale),(18*scale,26*scale)], fill=accent2)
            elif key == "ai":
                # balão de conversa com spark — ZK AI
                d.rounded_rectangle((6*scale,7*scale,22*scale,19*scale), radius=3*scale, outline=accent, width=w)
                d.polygon([(10*scale,19*scale),(10*scale,23*scale),(14*scale,19*scale)], fill=accent)
                d.line((14*scale,9*scale,14*scale,17*scale), fill=accent2, width=scale)
                d.line((10*scale,13*scale,18*scale,13*scale), fill=accent2, width=scale)
                d.ellipse((12*scale,11*scale,16*scale,15*scale), fill=bg, outline=accent, width=scale)
            elif key == "theme":
                d.ellipse((6*scale,7*scale,22*scale,21*scale), outline=accent, width=w)
                for px,py,col in [(10,12,accent),(15,10,accent2),(18,15,accent),(12,17,accent2)]:
                    d.ellipse(((px-1)*scale,(py-1)*scale,(px+1)*scale,(py+1)*scale), fill=col)
                d.ellipse((18*scale,18*scale,23*scale,23*scale), fill=bg)
            elif key == "audio":
                d.arc((7*scale,7*scale,21*scale,21*scale), 210, 150, fill=accent, width=w)
                d.rounded_rectangle((6*scale,12*scale,10*scale,19*scale), radius=scale, fill=accent2)
                d.rounded_rectangle((18*scale,12*scale,22*scale,19*scale), radius=scale, fill=accent2)
                d.line((14*scale,9*scale,14*scale,20*scale), fill=accent, width=scale)
                d.line((12*scale,12*scale,12*scale,17*scale), fill=accent, width=scale)
                d.line((16*scale,11*scale,16*scale,18*scale), fill=accent, width=scale)
            elif key == "maintenance":
                # velocímetro/performance
                d.arc((6*scale,7*scale,22*scale,23*scale), 195, 345, fill=accent, width=w)
                d.line((14*scale,17*scale,20*scale,11*scale), fill=accent2, width=2*scale)
                d.ellipse((12*scale,15*scale,16*scale,19*scale), fill=accent)
                d.line((9*scale,21*scale,19*scale,21*scale), fill=accent, width=scale)
            elif key == "recovery":
                # restauração / rollback
                d.arc((7*scale,7*scale,22*scale,22*scale), 35, 325, fill=accent, width=w)
                d.polygon([(6*scale,8*scale),(12*scale,7*scale),(8*scale,13*scale)], fill=accent2)
                d.line((11*scale,14*scale,18*scale,14*scale), fill=accent, width=scale)
                d.line((14*scale,11*scale,14*scale,18*scale), fill=accent, width=scale)
            elif key == "feedback":
                d.rounded_rectangle((6*scale,7*scale,22*scale,18*scale), radius=3*scale, outline=accent, width=w)
                d.polygon([(10*scale,18*scale),(10*scale,22*scale),(15*scale,18*scale)], fill=accent)
                d.line((10*scale,11*scale,18*scale,11*scale), fill=accent2, width=scale)
                d.line((10*scale,14*scale,16*scale,14*scale), fill=accent2, width=scale)
            elif key == "support":
                # coração / apoio ao projeto
                d.ellipse((7*scale,8*scale,14*scale,15*scale), fill=accent)
                d.ellipse((14*scale,8*scale,21*scale,15*scale), fill=accent)
                d.polygon([(7*scale,12*scale),(21*scale,12*scale),(14*scale,22*scale)], fill=accent)
                d.ellipse((12*scale,11*scale,16*scale,15*scale), fill=accent2)
            elif key == "about":
                d.ellipse((7*scale,7*scale,21*scale,21*scale), outline=accent, width=w)
                d.ellipse((13*scale,10*scale,15*scale,12*scale), fill=accent2)
                d.line((14*scale,14*scale,14*scale,19*scale), fill=accent, width=w)
            else:
                d.ellipse((10*scale,10*scale,18*scale,18*scale), fill=accent)

            im = im.resize((size,size), Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=im, dark_image=im, size=(size,size))
        except Exception:
            return None

    def _profile_cache_path(self):
        return os.path.join(os.path.dirname(self.config_path), "roblox_profile_avatar.png")

    def _load_profile_avatar_ctk(self, size=36):
        try:
            from PIL import Image, ImageDraw
            path = self._profile_cache_path()
            if not os.path.isfile(path):
                return None
            im = Image.open(path).convert("RGBA").resize((size,size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (size,size), 0)
            ImageDraw.Draw(mask).ellipse((0,0,size-1,size-1), fill=255)
            im.putalpha(mask)
            self._profile_avatar_ctk = ctk.CTkImage(light_image=im, dark_image=im, size=(size,size))
            return self._profile_avatar_ctk
        except Exception:
            return None

    def _render_profile_button(self):
        btn = getattr(self, "profile_button", None)
        if btn is None:
            return
        t = TEMAS[self.tema_atual]
        p = getattr(self, "linked_profile", {}) or {}
        try:
            if p.get("id") and p.get("name"):
                display = str(p.get("displayName") or p.get("name"))[:18]
                username = str(p.get("name"))[:18]
                img = self._load_profile_avatar_ctk(34)
                btn.configure(text=f"{display}\n@{username}", image=img, compound="left", fg_color=t["card_active"], hover_color=t["hover"], text_color=t["text"], border_width=1, border_color=t["accent"])
            else:
                img = self._make_nav_icon("home", size=28)
                btn.configure(text="VINCULAR ROBLOX" if self.idioma=="pt" else "LINK ROBLOX", image=img, compound="left", fg_color=t["card_active"], hover_color=t["hover"], text_color=t["accent"], border_width=1, border_color=t["card_active"])
        except Exception:
            pass

    def abrir_vincular_perfil(self):
        """Vincula visualmente um perfil público do Roblox. Não solicita senha e não autentica a conta."""
        t = TEMAS[self.tema_atual]
        pt = self.idioma == "pt"
        win = ctk.CTkToplevel(self)
        win.title("Perfil Roblox")
        win.geometry("460x330")
        win.resizable(False, False)
        win.transient(self)
        try:
            win.lift(); self.after(80, lambda w=win: w.focus_force() if w.winfo_exists() else None)
        except Exception:
            pass
        try:
            self.update_idletasks()
            x = self.winfo_rootx() + max(20, (self.winfo_width()-460)//2)
            y = self.winfo_rooty() + max(20, (self.winfo_height()-330)//2)
            win.geometry(f"460x330+{x}+{y}")
        except Exception:
            pass
        box = ctk.CTkFrame(win, fg_color=t.get("panel", t["card"]), corner_radius=self._theme_style()["card_radius"], border_width=1, border_color=t["border"])
        box.pack(fill="both", expand=True, padx=14, pady=14)
        ctk.CTkLabel(box, text="VINCULAR PERFIL ROBLOX" if pt else "LINK ROBLOX PROFILE", font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"), text_color=t["text"]).pack(anchor="w", padx=18, pady=(18,4))
        ctk.CTkLabel(box, text=("Digite seu username do Roblox. Isso é só uma vinculação visual: o app nunca pede senha." if pt else "Enter your Roblox username. This is only a visual profile link: the app never asks for a password."), wraplength=390, justify="left", text_color=t.get("muted","gray"), font=ctk.CTkFont(size=10)).pack(anchor="w", padx=18, pady=(0,14))
        entry = ctk.CTkEntry(box, placeholder_text="ex: Builderman", height=42, border_color=t["card_active"])
        entry.pack(fill="x", padx=18, pady=4)
        prefill_username = str((self.linked_profile or {}).get("name") or getattr(self, "onboarding_username", "") or "").strip()
        if prefill_username:
            entry.insert(0, prefill_username)
        status = ctk.CTkLabel(box, text="", text_color=t["accent"], font=ctk.CTkFont(size=10))
        status.pack(anchor="w", padx=18, pady=(6,0))
        def go():
            username = entry.get().strip().lstrip('@')
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
                status.configure(text="Username inválido." if pt else "Invalid username.", text_color="#FF6666")
                return
            if self._profile_search_busy:
                return
            self._profile_search_busy = True
            status.configure(text="Buscando perfil..." if pt else "Searching profile...", text_color=t["accent"])
            threading.Thread(target=self._buscar_perfil_roblox_thread, args=(username, win, status), daemon=True).start()
        ctk.CTkButton(box, text="BUSCAR PERFIL" if pt else "FIND PROFILE", command=go, height=40, fg_color=t["accent"], hover_color=t["hover"], text_color="#050505").pack(fill="x", padx=18, pady=(14,6))
        if self.linked_profile:
            ctk.CTkButton(box, text="DESVINCULAR PERFIL" if pt else "UNLINK PROFILE", command=lambda: (self._desvincular_perfil(), win.destroy()), fg_color="transparent", border_width=1, border_color=t["card_active"], text_color=t["text"]).pack(fill="x", padx=18, pady=(4,14))

    def _buscar_perfil_roblox_thread(self, username, parent_win, status_label):
        """Busca um perfil público do Roblox com fallback e sem depender do avatar para dar sucesso."""
        pt = self.idioma == "pt"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"ZKStrap/{APP_VERSION} (Roblox profile linker)"
        }
        session = requests.Session()
        session.headers.update(headers)
        profile = None
        lookup_errors = []

        def set_status(txt, color=None):
            try:
                self.after(0, lambda: status_label.configure(text=txt, text_color=(color or TEMAS[self.tema_atual]["accent"])))
            except Exception:
                pass

        try:
            # 1) Endpoint oficial de lookup exato por username.
            try:
                set_status("Consultando username..." if pt else "Looking up username...")
                r = session.post(
                    "https://users.roblox.com/v1/usernames/users",
                    json={"usernames": [username], "excludeBannedUsers": False},
                    timeout=(4, 10)
                )
                if r.ok:
                    payload = r.json() if r.content else {}
                    data = payload.get("data", []) if isinstance(payload, dict) else []
                    if data:
                        p = data[0]
                        profile = {
                            "id": int(p["id"]),
                            "name": p.get("name") or username,
                            "displayName": p.get("displayName") or p.get("name") or username,
                        }
                else:
                    lookup_errors.append(f"username lookup HTTP {r.status_code}")
            except Exception as e:
                lookup_errors.append(f"username lookup: {type(e).__name__}: {e}")

            # 2) Fallback: busca pública por palavra-chave e procura username exato.
            # Isso ajuda quando o POST acima é bloqueado por proxy/firewall/antivírus.
            if profile is None:
                try:
                    set_status("Tentando busca alternativa..." if pt else "Trying alternate search...")
                    sr = session.get(
                        "https://users.roblox.com/v1/users/search",
                        params={"keyword": username, "limit": 10},
                        timeout=(4, 10)
                    )
                    if sr.ok:
                        sp = sr.json() if sr.content else {}
                        candidates = sp.get("data", []) if isinstance(sp, dict) else []
                        exact = next((x for x in candidates if str(x.get("name", "")).lower() == username.lower()), None)
                        if exact is None:
                            # Se o usuário digitou display name, ainda mostramos o melhor resultado para confirmação.
                            exact = next((x for x in candidates if str(x.get("displayName", "")).lower() == username.lower()), None)
                        if exact:
                            profile = {
                                "id": int(exact["id"]),
                                "name": exact.get("name") or username,
                                "displayName": exact.get("displayName") or exact.get("name") or username,
                            }
                    else:
                        lookup_errors.append(f"search fallback HTTP {sr.status_code}")
                except Exception as e:
                    lookup_errors.append(f"search fallback: {type(e).__name__}: {e}")

            if profile is None:
                details = " | ".join(lookup_errors[-2:]) if lookup_errors else "sem resultados"
                self.log_output(f"[-] Falha ao buscar perfil Roblox @{username}: {details}")
                msg = ("Não achei esse username. Se ele existe, veja o log abaixo: " + details) if pt else ("I couldn't find that username. If it exists, check the log below: " + details)
                set_status(msg, "#FF6666")
                return

            # 3) Atualiza os dados pelo ID. Se falhar, o resultado do lookup continua válido.
            try:
                dr = session.get(f"https://users.roblox.com/v1/users/{profile['id']}", timeout=(4, 8))
                if dr.ok:
                    dp = dr.json()
                    profile["name"] = dp.get("name") or profile["name"]
                    profile["displayName"] = dp.get("displayName") or profile["displayName"]
            except Exception as e:
                self.log_output(f"[!] Perfil encontrado, mas detalhes não puderam ser atualizados: {e}")

            # 4) Avatar é opcional. Antes, qualquer falha aqui fazia o app dizer que a conta não existia.
            avatar_url = ""
            avatar_bytes = b""
            try:
                set_status("Perfil encontrado. Carregando avatar..." if pt else "Profile found. Loading avatar...")
                thumb = session.get(
                    "https://thumbnails.roblox.com/v1/users/avatar-headshot",
                    params={"userIds": str(profile["id"]), "size": "150x150", "format": "Png", "isCircular": "false"},
                    timeout=(4, 10)
                )
                if thumb.ok:
                    td = thumb.json().get("data", [])
                    if td:
                        avatar_url = td[0].get("imageUrl") or ""
                        state = str(td[0].get("state", ""))
                        if not avatar_url and state.lower() == "pending":
                            # Uma tentativa curta extra quando a miniatura está sendo gerada.
                            time.sleep(0.8)
                            thumb2 = session.get(
                                "https://thumbnails.roblox.com/v1/users/avatar-headshot",
                                params={"userIds": str(profile["id"]), "size": "150x150", "format": "Png", "isCircular": "false"},
                                timeout=(4, 10)
                            )
                            if thumb2.ok:
                                td2 = thumb2.json().get("data", [])
                                avatar_url = td2[0].get("imageUrl") if td2 else ""
                    if avatar_url:
                        try:
                            ir = session.get(avatar_url, timeout=(4, 10))
                            if ir.ok:
                                avatar_bytes = ir.content
                        except Exception as e:
                            self.log_output(f"[!] Perfil encontrado, mas CDN do avatar falhou: {e}")
                else:
                    self.log_output(f"[!] Perfil encontrado, mas thumbnail retornou HTTP {thumb.status_code}.")
            except Exception as e:
                self.log_output(f"[!] Perfil encontrado, mas não foi possível carregar o avatar: {e}")

            profile["avatar_url"] = avatar_url
            self.log_output(f"[+] Perfil Roblox encontrado: @{profile.get('name')} (ID {profile.get('id')})")
            self.after(0, lambda p=profile, b=avatar_bytes: self._mostrar_confirmacao_perfil(parent_win, p, b))

        except Exception as e:
            details = f"{type(e).__name__}: {e}"
            self.log_output(f"[-] Erro inesperado na busca de perfil: {details}")
            msg = ("Erro ao consultar o Roblox: " + details) if pt else ("Roblox lookup error: " + details)
            set_status(msg, "#FF6666")
        finally:
            self._profile_search_busy = False

    def _mostrar_confirmacao_perfil(self, search_win, profile, avatar_bytes):
        try: search_win.destroy()
        except Exception: pass
        t = TEMAS[self.tema_atual]
        pt = self.idioma == "pt"
        win = ctk.CTkToplevel(self)
        win.title("Confirmar perfil")
        win.geometry("430x480")
        win.resizable(False, False)
        win.transient(self)
        try:
            win.lift(); self.after(80, lambda w=win: w.focus_force() if w.winfo_exists() else None)
        except Exception:
            pass
        box = ctk.CTkFrame(win, fg_color=t.get("panel",t["card"]), corner_radius=self._theme_style()["card_radius"], border_width=1, border_color=t["border"])
        box.pack(fill="both", expand=True, padx=14, pady=14)
        ctk.CTkLabel(box, text="TEU PERFIL É ESSE?" if pt else "IS THIS YOUR PROFILE?", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=t["text"]).pack(pady=(24,12))
        try:
            from PIL import Image, ImageDraw
            im = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((144,144), Image.Resampling.LANCZOS)
            mask = Image.new("L", (144,144), 0); ImageDraw.Draw(mask).ellipse((0,0,143,143), fill=255); im.putalpha(mask)
            preview = ctk.CTkImage(light_image=im, dark_image=im, size=(144,144))
            lbl = ctk.CTkLabel(box, text="", image=preview); lbl.image = preview; lbl.pack(pady=6)
        except Exception:
            ctk.CTkLabel(box, text="RBX", width=144, height=144, corner_radius=72, fg_color=t["card_active"], text_color=t["accent"], font=ctk.CTkFont(size=28, weight="bold")).pack(pady=6)
        ctk.CTkLabel(box, text=str(profile.get("displayName","")), font=ctk.CTkFont(size=18, weight="bold"), text_color=t["text"]).pack(pady=(10,0))
        ctk.CTkLabel(box, text=f"@{profile.get('name','')}  •  ID {profile.get('id','')}", font=ctk.CTkFont(size=10), text_color=t.get("muted","gray")).pack(pady=(2,14))
        row = ctk.CTkFrame(box, fg_color="transparent"); row.pack(fill="x", padx=20, pady=(10,18))
        ctk.CTkButton(row, text="NÃO" if pt else "NO", command=win.destroy, fg_color=t["card_active"], hover_color=t["hover"], text_color=t["text"]).pack(side="left", expand=True, fill="x", padx=(0,5))
        ctk.CTkButton(row, text="SIM, É MEU PERFIL" if pt else "YES, THAT'S ME", command=lambda: self._confirmar_perfil(profile, avatar_bytes, win), fg_color=t["accent"], hover_color=t["hover"], text_color="#050505").pack(side="left", expand=True, fill="x", padx=(5,0))

    def _confirmar_perfil(self, profile, avatar_bytes, win=None):
        self.linked_profile = {"id": int(profile.get("id",0)), "name": str(profile.get("name", "")), "displayName": str(profile.get("displayName", "")), "avatar_url": str(profile.get("avatar_url", ""))}
        if self.linked_profile.get("name"):
            self.onboarding_username = str(self.linked_profile.get("name"))
        if avatar_bytes:
            try:
                path = self._profile_cache_path(); os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f: f.write(avatar_bytes)
            except Exception: pass
        self.salvar_config_app()
        self._render_profile_button()
        try: self._refresh_home_profile_card()
        except Exception: pass
        try:
            if win is not None: win.destroy()
        except Exception: pass
        self.log_output(f"[+] Perfil Roblox vinculado: @{self.linked_profile.get('name','')}")

    def _desvincular_perfil(self):
        old = str((self.linked_profile or {}).get("name", ""))
        self.linked_profile = {}
        try:
            p = self._profile_cache_path()
            if os.path.isfile(p): os.remove(p)
        except Exception: pass
        self.salvar_config_app(); self._render_profile_button()
        try: self._refresh_home_profile_card()
        except Exception: pass
        if old: self.log_output(f"[*] Perfil Roblox desvinculado: @{old}")

    def _refresh_home_profile_card(self):
        lbl = getattr(self, "home_profile_label", None)
        if lbl is None: return
        p = self.linked_profile or {}
        if p.get("name"):
            lbl.configure(text=f"{p.get('displayName') or p.get('name')}  •  @{p.get('name')}  •  ID {p.get('id')}")
        else:
            nick = str(getattr(self, "onboarding_username", "") or "").strip()
            if nick:
                lbl.configure(text=(f"@{nick} pronto para vincular — clique em VINCULAR / TROCAR." if self.idioma=="pt" else f"@{nick} ready to link — click LINK / CHANGE."))
            else:
                lbl.configure(text="Nenhum perfil vinculado." if self.idioma=="pt" else "No linked profile.")

    # ------------------------------------------------------------------
    # AUDIO / SOUND LAYER v3.13.3.5
    # ------------------------------------------------------------------
    def _secret_theme_sound_key(self, theme_name, event):
        try:
            slug=re.sub(r"[^a-z0-9]+","_",str(theme_name).lower()).strip("_")
            ev=str(event or "click").lower().strip()
            aliases={"apply":"theme","select":"click","open":"nav","back":"nav","toggle_on":"confirm","toggle_off":"click","success":"confirm"}
            ev=aliases.get(ev,ev)
            return f"secret_{slug}_{ev}"
        except Exception:
            return ""

    def _play_secret_theme_sound(self, theme_name, event="click", throttle=0.035):
        try:
            mgr=getattr(self,"_sound_manager",None)
            if mgr is None: return False
            key=self._secret_theme_sound_key(theme_name,event)
            if key and mgr.paths(key):
                mgr.play(key,throttle=throttle); return True
        except Exception:
            pass
        return False

    def _play_ui_sound(self, name="click", throttle=0.035):
        try:
            mgr=getattr(self,"_sound_manager",None)
            if mgr is None: return
            active=str(getattr(self,"tema_atual","") or "")
            secret_events={"hover","click","confirm","nav","theme","apply","select","open","back","toggle_on","toggle_off","success"}
            if active in UNLOCKABLE_THEME_NAMES and name in secret_events:
                if self._play_secret_theme_sound(active,name,throttle): return
            mgr.play(name,throttle=throttle)
        except Exception:
            pass

    def _start_ambient_if_enabled(self):
        try:
            if bool(getattr(self,"sounds_enabled",False)) and bool(getattr(self,"sound_prompted",False)) and bool(getattr(self,"music_enabled",True)):
                mgr=getattr(self,"_sound_manager",None)
                if mgr is not None:
                    mgr.pack=getattr(self,"sound_pack",DEFAULT_AUDIO_PACK); mgr.enabled=True; mgr.music_enabled=True; mgr.music_volume=float(getattr(self,"music_volume",0.22)); mgr.start_music()
        except Exception as exc:
            _startup_log("AUDIO: ambient start exception "+repr(exc))

    def _global_click_sound(self, event=None):
        if not bool(getattr(self,"sounds_enabled",False)):
            return
        try:
            w=getattr(event,"widget",None); cur=w; kind=""; label=""
            for _ in range(6):
                if cur is None: break
                name=cur.__class__.__name__
                if name in ("CTkButton","CTkSwitch","CTkCheckBox","CTkRadioButton","CTkSegmentedButton","CTkOptionMenu","CTkComboBox"):
                    kind=name
                    try: label=str(cur.cget("text") or "").upper()
                    except Exception: label=""
                    break
                cur=getattr(cur,"master",None)
            if not kind: return
            if kind in ("CTkSwitch","CTkCheckBox","CTkRadioButton"):
                snd="toggle_on"
            elif any(k in label for k in ("VOLTAR","BACK","CANCEL","FECHAR","CLOSE","NÃO","NO")):
                snd="back"
            elif any(k in label for k in ("APLICAR","APPLY","ATIVAR","ENABLE","SALVAR","SAVE","CONFIRM","SIM","YES")):
                snd="confirm"
            elif any(k in label for k in ("TEMA","THEME","ATMOSFERA","PERSONALIZAR","CUSTOMIZE")):
                snd="theme"
            elif any(k in label for k in ("INÍCIO","HOME","FPS","PING","REDE","NETWORK","RESOLUÇÃO","RESOLUTION","CURSOR","FONTES","FONTS","COMBO","ZK AI","ÁUDIO","AUDIO","DESEMPENHO","PERFORMANCE","RECUPERAÇÃO","RECOVERY","ATUALIZAÇÕES","UPDATES","SUGESTÕES","BUGS","APOIAR","SUPPORT")):
                snd="nav"
            else:
                snd="click"
            self._play_ui_sound(snd,.025)
        except Exception:
            pass

    def _maybe_show_sound_consent(self):
        try:
            if bool(getattr(self,"sound_prompted",False)):
                self._start_ambient_if_enabled(); return
            self._show_sound_consent(first_run=True)
        except Exception:
            pass

    def _sound_choice(self, enabled, popup=None):
        self.sound_prompted=True
        self.sounds_enabled=bool(enabled)
        if enabled:
            self.music_enabled=True; self.sfx_enabled=True
        try: self.salvar_config_app()
        except Exception: pass
        try:
            mgr=getattr(self,"_sound_manager",None)
            if mgr is not None:
                mgr.pack=getattr(self,"sound_pack",DEFAULT_AUDIO_PACK)
                mgr.sfx_enabled=bool(getattr(self,"sfx_enabled",True)); mgr.music_enabled=bool(getattr(self,"music_enabled",True)); mgr.music_volume=float(getattr(self,"music_volume",0.22))
                if enabled:
                    mgr.enabled=True; mgr.play("enable",throttle=0); self.after(160,lambda: mgr.start_music(force_restart=True))
                else: mgr.set_enabled(False)
        except Exception as exc:
            _startup_log("AUDIO: consent choice failed "+repr(exc))
        self._sound_prompt_open=False
        self._sound_prompt_panel=None
        if popup is not None:
            try: popup.grab_release()
            except Exception: pass
            try: popup.destroy()
            except Exception: pass
        try: self._refresh_sound_button()
        except Exception: pass
        if not bool(getattr(self,"tutorial_completed",False)):
            self.after(320,self._maybe_show_first_run_tutorial)

    def _show_sound_consent(self, first_run=False):
        """Mostra consentimento de áudio sem usar grab_set/Toplevel.

        v3.18.3: um Toplevel overrideredirect com grab_set podia ficar atrás da
        janela em algumas combinações de DPI/Windows. O grab continuava ativo e
        fazia TODOS os cliques da janela principal parecerem quebrados. O card
        agora vive dentro da própria UI e nunca captura o mouse globalmente.
        """
        if bool(getattr(self,"_sound_prompt_open",False)):
            panel=getattr(self,"_sound_prompt_panel",None)
            try:
                if panel is not None and panel.winfo_exists():
                    panel.lift(); return
            except Exception:
                pass
            self._sound_prompt_open=False
            self._sound_prompt_panel=None
        self._sound_prompt_open=True
        if bool(getattr(self,"sounds_enabled",False)):
            self._play_ui_sound("modal",.0)
        t=TEMAS[self.tema_atual]
        host=getattr(self,"main_container",self)

        enabled_now=bool(getattr(self,"sounds_enabled",False))
        panel=ctk.CTkFrame(host,width=500,height=365,fg_color=t.get("panel",t["card"]),corner_radius=24,border_width=2,border_color=t["accent"])
        panel.place(relx=.5,rely=.5,anchor="center")
        panel.pack_propagate(False)
        self._sound_prompt_panel=panel
        try: panel.lift()
        except Exception: pass

        topbar=ctk.CTkFrame(panel,fg_color="transparent")
        topbar.pack(fill="x",padx=18,pady=(14,0))
        ctk.CTkLabel(topbar,text="ZK AUDIO  //  LOCAL",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")
        ctk.CTkButton(topbar,text="×",width=30,height=28,corner_radius=8,fg_color="transparent",hover_color=t["card_active"],text_color=t.get("muted","gray"),command=lambda:self._sound_choice(False,panel)).pack(side="right")

        icon=ctk.CTkFrame(panel,width=76,height=76,corner_radius=38,fg_color=t.get("icon_bg",t["card_active"]),border_width=2,border_color=t["accent"])
        icon.pack(pady=(8,10)); icon.pack_propagate(False)
        ctk.CTkLabel(icon,text="♫",text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI Symbol",size=31,weight="bold")).pack(fill="both",expand=True)
        title=("ATIVAR SONS DO ZKSTRAP?" if first_run else "SONS DO ZKSTRAP") if self.idioma=="pt" else ("ENABLE ZKSTRAP AUDIO?" if first_run else "ZKSTRAP AUDIO")
        ctk.CTkLabel(panel,text=title,text_color=t["text"],font=ctk.CTkFont(size=19,weight="bold")).pack(pady=(0,6))
        msg=("Feedback de clique, sons dos temas e música ambiente. Tudo é local e opcional. Este card não bloqueia o resto do app." if self.idioma=="pt" else "Click feedback, theme sounds and ambient music. Everything is local and optional. This card never blocks the rest of the app.")
        ctk.CTkLabel(panel,text=msg,text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10),wraplength=420,justify="center").pack(padx=30,pady=(0,16))
        row=ctk.CTkFrame(panel,fg_color="transparent"); row.pack(fill="x",padx=24,pady=(0,8))
        off_text=("DESATIVAR" if enabled_now else "AGORA NÃO") if self.idioma=="pt" else ("DISABLE" if enabled_now else "NOT NOW")
        on_text=("♫  MANTER ATIVOS" if enabled_now else "♫  ATIVAR SONS") if self.idioma=="pt" else ("♫  KEEP ENABLED" if enabled_now else "♫  ENABLE AUDIO")
        ctk.CTkButton(row,text=off_text,height=44,corner_radius=12,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],command=lambda:self._sound_choice(False,panel)).pack(side="left",expand=True,fill="x",padx=(0,6))
        ctk.CTkButton(row,text=on_text,height=44,corner_radius=12,fg_color=t["accent"],hover_color=t["hover"],text_color="#05070A",font=ctk.CTkFont(weight="bold"),command=lambda:self._sound_choice(True,panel)).pack(side="left",expand=True,fill="x",padx=(6,0))
        try:
            self.after(80,lambda p=panel: p.lift() if p.winfo_exists() else None)
        except Exception:
            pass

    def abrir_som_config(self):
        try:
            if not bool(getattr(self,"sound_prompted",False)): self._show_sound_consent(first_run=False)
            else: self.show_page("audio",animate=True)
        except Exception: pass

    def _refresh_sound_button(self):
        b=getattr(self,"header_sound_button",None)
        if b is None: return
        t=TEMAS[self.tema_atual]; enabled=bool(getattr(self,"sounds_enabled",False))
        b.configure(text="♫" if enabled else "♩",fg_color=t["card_active"] if enabled else t["card"],text_color=t["accent"] if enabled else t.get("muted","gray"))

    def _global_scroll_sound(self, event=None):
        if not bool(getattr(self,"sounds_enabled",False)) or not bool(getattr(self,"sfx_enabled",True)): return
        now=time.monotonic()
        if now-float(getattr(self,"_last_scroll_sound",0.0)) < .115: return
        self._last_scroll_sound=now; self._play_ui_sound("scroll",0.0)

    def _audio_select_pack(self, pack):
        if pack not in AUDIO_PACKS: return
        self.sound_pack=pack; self.sounds_enabled=True; self.sound_prompted=True
        mgr=getattr(self,"_sound_manager",None)
        if mgr is not None:
            mgr.enabled=True; mgr.sfx_enabled=bool(getattr(self,"sfx_enabled",True)); mgr.music_enabled=bool(getattr(self,"music_enabled",True)); mgr.music_volume=float(getattr(self,"music_volume",0.22)); mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0)); mgr.set_pack(pack); mgr.play("theme",0)
        self.salvar_config_app(); self._refresh_sound_button()
        try: self.audio_current_label.configure(text=f"PACK ATIVO  //  {pack}")
        except Exception: pass
        try:
            for name,btn in getattr(self,"audio_pack_buttons",{}).items():
                tt=TEMAS[self.tema_atual]; active=(name==pack)
                btn.configure(text=("ATIVO ✓" if active else "USAR PACK"),fg_color=tt["accent"] if active else tt["card_active"],text_color="#050505" if active else tt["text"])
        except Exception: pass

    def _audio_test_pack(self, pack):
        mgr=getattr(self,"_sound_manager",None)
        if mgr is None: return
        old_pack=mgr.pack; old_enabled=mgr.enabled; old_sfx=mgr.sfx_enabled
        mgr.pack=pack if pack in AUDIO_PACKS else old_pack; mgr.enabled=True; mgr.sfx_enabled=True; mgr.play("preview",0)
        mgr.pack=old_pack; mgr.enabled=old_enabled; mgr.sfx_enabled=old_sfx

    def _audio_toggle_music(self):
        try: self.music_enabled=bool(self.audio_music_switch.get())
        except Exception: self.music_enabled=not bool(getattr(self,"music_enabled",True))
        self.sounds_enabled=True; self.sound_prompted=True
        mgr=getattr(self,"_sound_manager",None)
        if mgr is not None: mgr.enabled=True; mgr.set_music_enabled(self.music_enabled)
        self.salvar_config_app(); self._refresh_sound_button()

    def _audio_toggle_sfx(self):
        try: self.sfx_enabled=bool(self.audio_sfx_switch.get())
        except Exception: self.sfx_enabled=not bool(getattr(self,"sfx_enabled",True))
        self.sounds_enabled=True; self.sound_prompted=True
        mgr=getattr(self,"_sound_manager",None)
        if mgr is not None:
            mgr.enabled=True; mgr.set_sfx_enabled(self.sfx_enabled)
            if self.sfx_enabled: mgr.play("enable",0)
        self.salvar_config_app(); self._refresh_sound_button()

    def _audio_music_volume_preview(self, value):
        try:
            self.music_volume=max(0.0,min(0.65,float(value)))
            pct=int(round(self.music_volume*100))
            lbl=getattr(self,"audio_music_volume_label",None)
            if lbl is not None: lbl.configure(text=f"{pct}%")
        except Exception: pass

    def _audio_music_volume_apply(self, event=None):
        try:
            mgr=getattr(self,"_sound_manager",None)
            if mgr is not None:
                mgr.enabled=bool(getattr(self,"sounds_enabled",False)); mgr.set_music_volume(self.music_volume,restart=True)
            self.salvar_config_app()
        except Exception as exc:
            _startup_log("AUDIO: volume apply failed "+repr(exc))

    def _audio_sfx_volume_preview(self, value):
        try:
            self.sfx_volume=max(0.0,min(1.5,float(value)))
            pct=int(round(self.sfx_volume*100))
            lbl=getattr(self,"audio_sfx_volume_label",None)
            if lbl is not None: lbl.configure(text=f"{pct}%")
        except Exception: pass

    def _audio_sfx_volume_apply(self, event=None):
        try:
            mgr=getattr(self,"_sound_manager",None)
            if mgr is not None:
                mgr.enabled=bool(getattr(self,"sounds_enabled",False)); mgr.set_sfx_volume(self.sfx_volume)
                if bool(getattr(self,"sfx_enabled",True)): mgr.play("preview",0)
            self.salvar_config_app()
        except Exception as exc:
            _startup_log("AUDIO: sfx volume apply failed "+repr(exc))

    def _audio_master_toggle(self):
        self.sounds_enabled=not bool(getattr(self,"sounds_enabled",False)); self.sound_prompted=True
        mgr=getattr(self,"_sound_manager",None)
        if mgr is not None:
            mgr.pack=getattr(self,"sound_pack",DEFAULT_AUDIO_PACK); mgr.music_enabled=bool(getattr(self,"music_enabled",True)); mgr.sfx_enabled=bool(getattr(self,"sfx_enabled",True)); mgr.music_volume=float(getattr(self,"music_volume",0.22)); mgr.sfx_volume=float(getattr(self,"sfx_volume",1.0)); mgr.set_enabled(self.sounds_enabled)
        self.salvar_config_app(); self._refresh_sound_button()
        try: self.audio_master_button.configure(text=("DESATIVAR ÁUDIO" if self.sounds_enabled else "ATIVAR ÁUDIO"))
        except Exception: pass

    # ------------------------------------------------------------------
    # ONBOARDING / TUTORIAL v3.3
    # ------------------------------------------------------------------
    def _tutorial_username(self):
        nick = str(getattr(self, "onboarding_username", "") or "").strip().lstrip("@")
        return nick or ("jogador" if self.idioma == "pt" else "player")

    def _maybe_show_first_run_tutorial(self):
        if bool(getattr(self,"_sound_prompt_open",False)):
            self.after(350,self._maybe_show_first_run_tutorial)
            return
        if not bool(getattr(self, "tutorial_completed", False)):
            self.abrir_tutorial(primeiro_acesso=True)

    def _tutorial_steps(self):
        nick = self._tutorial_username()
        pt = self.idioma == "pt"
        if pt:
            return [
                ("home", "INÍCIO // DASHBOARD", f"Boa, @{nick}. Aqui você vê o estado geral do ZKStrap: cliente Roblox detectado, perfil, benchmark, preset e resumo das configurações.", "Use esta página como central de controle antes de entrar no jogo."),
                ("fps", "FPS & GRÁFICOS", "Aqui ficam os ajustes mais usados: modo FPS, céu cinza e alvo de FPS. As opções técnicas ficam escondidas no Modo Avançado para manter a tela limpa.", "Depois de mudar algo, use APLICAR CONFIGURAÇÕES — o botão fica visível perto das opções e também no topo."),
                ("ping", "PING & REDE", "Esta área reúne os ajustes locais de rede disponíveis no ZKStrap e o status de conexão.", "O ZKStrap não promete diminuir sua internet magicamente; o resultado depende da conexão, rota e servidor."),
                ("cursor", "CURSOR", "Importe um PNG ou pack, ajuste tamanho/âncora e aplique nos assets locais do Roblox.", "O original fica protegido por backup para você conseguir restaurar depois."),
                ("fonts", "FONTES", "Troque a fonte local do Roblox usando TTF/OTF e restaure os arquivos originais quando quiser.", "Arquivos de emoji são preservados para evitar símbolos quebrados."),
                ("combo", "COMBO PLANNER", "Guarde suas builds e escreva o combo completo de cada uma. Você pode criar quantos cards quiser e voltar neles quando esquecer uma sequência.", "Estilos de luta e frutas podem carregar miniaturas reais da comunidade; o ZKStrap mostra as fontes dentro da própria página."),
                ("ai", "ZK ASSISTÊNCIA", "O Assistente ZKStrap resolve dúvidas do próprio app por opções guiadas. O ZK AI/PvP Coach continua bloqueado enquanto a IA não estiver estável.", "Use a assistência para aplicação, Roblox, FPS, cursor, fontes, temas, desempenho, recuperação e logs."),
                ("theme", "PERSONALIZAR", "Aqui você troca completamente a aparência do ZKStrap: temas Core, Temas Especiais, cores e identidade visual.", "Minecraft, Hollow Knight, Blox Fruits e outros packs mudam HUD, ícones, geometria e animações."),
                ("maintenance", "CENTRAL DE DESEMPENHO", "Ferramentas para preparar o Windows e a sessão do Roblox: Game Mode, GPU, prioridade, energia, overlays e processos pesados.", "As ações são reversíveis e o ZKStrap evita prometer FPS mágico."),
                ("recovery", "RECUPERAÇÃO", "Limpeza segura, backups e retorno ao original ficam separados do boost de desempenho.", "Use aqui quando quiser limpar logs/cache ou desfazer alterações do ZKStrap."),
                ("updates", "ATUALIZAÇÕES", "Veja o changelog completo e acompanhe o que mudou desde a primeira versão até a build atual.", "Quando você receber uma versão nova, confira esta página primeiro."),
                ("feedback", "SUGESTÕES & BUGS", "Achou um bug ou teve uma ideia? Envie por aqui com título, descrição e diagnóstico opcional.", "Quanto mais específico o relato, mais fácil reproduzir e corrigir."),
                ("home", "PRONTO PARA USAR", f"É isso, @{nick}. O botão APLICAR CONFIGURAÇÕES grava os ajustes selecionados e mostra um resumo do resultado.", "Quer rever tudo depois? Clique em TUTORIAL no canto inferior esquerdo quantas vezes quiser."),
            ]
        return [
            ("home", "HOME // DASHBOARD", f"Welcome, @{nick}. This is your ZKStrap control center: Roblox client, profile, benchmark and active configuration status.", "Use this page as your starting point before launching the game."),
            ("fps", "FPS & GRAPHICS", "Main performance controls live here: FPS mode, gray sky and FPS target. Technical options stay inside Advanced Mode to keep the page clean.", "After changing something, use APPLY SETTINGS near the options or in the top bar."),
            ("ping", "PING & NETWORK", "Local network-related controls and connection status are grouped here.", "ZKStrap does not promise magic ping reductions; results depend on your connection, route and server."),
            ("cursor", "CURSOR", "Import a PNG or pack, tune its size/anchor and apply it to local Roblox assets.", "Original files are backed up so they can be restored."),
            ("fonts", "FONTS", "Apply local TTF/OTF fonts to Roblox and restore originals at any time.", "Emoji fonts are preserved to avoid broken symbols."),
            ("combo", "COMBO PLANNER", "Save your builds and write the full combo for each one. Create as many cards as you want and revisit them later.", "Styles, fruits, swords and guns can load community thumbnails; sources are shown inside the planner."),
            ("ai", "ZK ASSISTANCE", "ZKStrap Assistant answers app questions through guided options. ZK AI/PvP Coach stays locked until the AI is stable.", "Use assistance for applying settings, Roblox, FPS, cursor, fonts, themes, performance, recovery and logs."),
            ("theme", "CUSTOMIZE", "Change the whole ZKStrap identity with Core themes, Special Themes, colors and visual packs.", "Minecraft, Hollow Knight, Blox Fruits and other packs change HUD, icons, geometry and animation."),
            ("maintenance", "PERFORMANCE CENTER", "Tools for Windows and Roblox sessions: Game Mode, GPU, priority, power plan, overlays and heavy processes.", "Actions are reversible and ZKStrap does not promise magic FPS."),
            ("recovery", "RECOVERY", "Safe cleanup, backups and rollback live separately from performance tools.", "Use this area to clean logs/cache or undo ZKStrap changes."),
            ("updates", "UPDATES", "Read the complete changelog from the first release to the current build.", "Check this page first after installing a new version."),
            ("feedback", "FEEDBACK & BUGS", "Send a bug report or suggestion with a title, description and optional diagnostics.", "Specific reports are easier to reproduce and fix."),
            ("home", "READY", f"That's it, @{nick}. APPLY SETTINGS writes the selected changes and shows a result summary.", "To replay this guide later, click TUTORIAL in the lower-left corner."),
        ]

    def _center_child_window(self, win, width, height, dx=0, dy=0):
        try:
            self.update_idletasks()
            x = self.winfo_rootx() + max(10, (self.winfo_width() - width)//2) + dx
            y = self.winfo_rooty() + max(10, (self.winfo_height() - height)//2) + dy
            win.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            win.geometry(f"{width}x{height}")

    def abrir_tutorial(self, primeiro_acesso=False):
        """Tutorial v3.6: acontece dentro da janela principal, sem Toplevel/modal."""
        self._fechar_busca_universal()
        # O consentimento de áudio é não-modal. Se o usuário pediu o tutorial,
        # fecha apenas o card visual para não cobrir o onboarding. A preferência
        # continua não definida e pode ser perguntada novamente depois.
        sp=getattr(self,"_sound_prompt_panel",None)
        if sp is not None:
            try:
                if sp.winfo_exists(): sp.destroy()
            except Exception:
                pass
            self._sound_prompt_panel=None
            self._sound_prompt_open=False
        self._tutorial_close(mark_complete=False, voltar_home=False)
        if primeiro_acesso or not str(getattr(self, "onboarding_username", "") or "").strip():
            self._abrir_onboarding_username(primeiro_acesso=primeiro_acesso)
        else:
            self._abrir_tutorial_passos(replay=True)

    def _abrir_onboarding_username(self, primeiro_acesso=True):
        t = TEMAS[self.tema_atual]; pt = self.idioma == "pt"
        # Card central integrado: não abre janela nova e não bloqueia o desktop.
        panel = ctk.CTkFrame(self.main_container, width=540, height=400,
                             fg_color=t.get("panel", t["card"]), corner_radius=18,
                             border_width=2, border_color=t["accent"])
        panel.place(relx=.5, rely=.5, anchor="center")
        panel.pack_propagate(False); panel.lift()
        self._tutorial_panel = panel
        ctk.CTkLabel(panel, text="ZK  //  PRIMEIRO ACESSO" if pt else "ZK  //  FIRST RUN",
                     height=27, corner_radius=7, fg_color=t["card_active"], text_color=t["accent"],
                     font=ctk.CTkFont(family="Consolas", size=9, weight="bold")).pack(anchor="w", padx=22, pady=(22,8))
        ctk.CTkLabel(panel, text="Antes de começar" if pt else "Before we start",
                     font=ctk.CTkFont(family="Segoe UI", size=25, weight="bold"), text_color=t["text"]).pack(anchor="w", padx=22)
        desc=("Qual é o seu username do Roblox? É só o nick do jogo — nunca pedimos nome real, senha ou e-mail. "
              "Ele serve para personalizar o guia e preencher a busca de perfil; fica salvo apenas neste PC." if pt else
              "What's your Roblox username? Only your in-game nickname — we never ask for your real name, password or email. "
              "It personalizes the guide and pre-fills profile linking, and stays only on this PC.")
        ctk.CTkLabel(panel, text=desc, wraplength=490, justify="left", anchor="w",
                     text_color=t.get("muted","gray"), font=ctk.CTkFont(size=10)).pack(fill="x", padx=22, pady=(8,14))
        entry=ctk.CTkEntry(panel, placeholder_text="ex: zak_blox" if pt else "e.g. zak_blox", height=46,
                           border_width=2, border_color=t["card_active"], font=ctk.CTkFont(size=12,weight="bold"))
        entry.pack(fill="x", padx=22)
        old_nick=str(getattr(self,"onboarding_username","") or "").strip()
        if old_nick: entry.insert(0,old_nick)
        status=ctk.CTkLabel(panel,text="",text_color="#FF6B7A",font=ctk.CTkFont(size=9)); status.pack(anchor="w",padx=22,pady=(3,6))
        def start_guide(event=None):
            username=entry.get().strip().lstrip("@")
            if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username):
                status.configure(text="Use um username válido do Roblox (3–20 caracteres)." if pt else "Use a valid Roblox username (3–20 characters).")
                return
            self.onboarding_username=username; self.salvar_config_app()
            try: self._refresh_home_profile_card()
            except Exception: pass
            try: panel.destroy()
            except Exception: pass
            self._tutorial_panel=None
            self._abrir_tutorial_passos(replay=not primeiro_acesso)
        def skip():
            if primeiro_acesso:
                self.tutorial_completed=True; self.salvar_config_app()
            try: panel.destroy()
            except Exception: pass
            self._tutorial_panel=None
            self.show_toast("TUTORIAL PULADO" if pt else "TUTORIAL SKIPPED",
                            "Você pode abrir novamente pelo botão ? TUTORIAL." if pt else "Open it again anytime with ? TUTORIAL.", kind="info")
        ctk.CTkButton(panel,text="COMEÇAR TUTORIAL" if pt else "START TUTORIAL",command=start_guide,height=44,
                      fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=11,weight="bold")).pack(fill="x",padx=22,pady=(5,7))
        ctk.CTkButton(panel,text="PULAR POR ENQUANTO" if pt else "SKIP FOR NOW",command=skip,height=34,
                      fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray")).pack(fill="x",padx=22,pady=(0,18))
        entry.bind("<Return>",start_guide); self.after(80,lambda: entry.focus_force())

    def _abrir_tutorial_passos(self, replay=False):
        t=TEMAS[self.tema_atual]; pt=self.idioma=="pt"
        self._tutorial_replay=bool(replay); self._tutorial_step_index=0
        panel=ctk.CTkFrame(self.main_container,width=475,height=320,fg_color=t.get("panel",t["card"]),
                           corner_radius=16,border_width=2,border_color=t["accent"])
        panel.place(relx=.985,rely=.975,anchor="se"); panel.pack_propagate(False); panel.lift()
        self._tutorial_panel=panel
        top=ctk.CTkFrame(panel,fg_color="transparent"); top.pack(fill="x",padx=17,pady=(15,4))
        self._tutorial_badge=ctk.CTkLabel(top,text="ZK // GUIA INTERATIVO" if pt else "ZK // INTERACTIVE GUIDE",height=25,corner_radius=7,
                         fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")); self._tutorial_badge.pack(side="left")
        self._tutorial_count=ctk.CTkLabel(top,text="",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=9,weight="bold")); self._tutorial_count.pack(side="right")
        self._tutorial_title=ctk.CTkLabel(panel,text="",font=ctk.CTkFont(size=19,weight="bold"),text_color=t["text"],anchor="w"); self._tutorial_title.pack(fill="x",padx=17,pady=(6,2))
        self._tutorial_body=ctk.CTkLabel(panel,text="",wraplength=430,justify="left",anchor="w",text_color=t["text"],font=ctk.CTkFont(size=10)); self._tutorial_body.pack(fill="x",padx=17,pady=(4,5))
        self._tutorial_tip=ctk.CTkLabel(panel,text="",wraplength=430,justify="left",anchor="w",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8)); self._tutorial_tip.pack(fill="x",padx=17,pady=(2,7))
        self._tutorial_progress=ctk.CTkProgressBar(panel,height=5,progress_color=t["accent"],fg_color=t["card_active"]); self._tutorial_progress.pack(fill="x",padx=17,pady=(0,8))
        row=ctk.CTkFrame(panel,fg_color="transparent"); row.pack(fill="x",padx=17,pady=(2,14))
        self._tutorial_prev=ctk.CTkButton(row,text="←" if pt else "←",command=lambda:self._tutorial_move(-1),width=46,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"]); self._tutorial_prev.pack(side="left")
        ctk.CTkButton(row,text="PULAR" if pt else "SKIP",command=lambda:self._tutorial_close(mark_complete=True),width=68,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t.get("muted","gray")).pack(side="left",padx=6)
        self._tutorial_next=ctk.CTkButton(row,text="PRÓXIMO  →" if pt else "NEXT  →",command=lambda:self._tutorial_move(1),fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(weight="bold")); self._tutorial_next.pack(side="right",expand=True,fill="x")
        self._tutorial_render_step()

    def _tutorial_target_widget(self, page):
        # Destinos reais da interface: o guia aponta para a função, não para uma janela explicativa.
        if page=="fps": return getattr(self,"module_cards",{}).get("performance_boost")
        if page=="ping": return getattr(self,"module_cards",{}).get("ping_boost")
        if page=="resolution": return getattr(self,"resolution_card",None)
        if page=="cursor": return getattr(self,"cursor_card",None)
        if page=="fonts": return getattr(self,"font_card",None)
        if page=="combo": return getattr(self,"combo_hero",None)
        if page=="home" and self._tutorial_step_index==len(self._tutorial_steps())-1: return getattr(self,"header_apply_button",None)
        return getattr(self,"nav_buttons",{}).get(page)

    def _tutorial_place_spotlight(self, widget):
        """Destaca o alvo sem cobrir o conteúdo.

        CTkFrame com fg_color="transparent" ainda pode pintar o fundo do pai quando
        usado como overlay. Isso criava os retângulos pretos do tutorial. O destaque
        agora é composto só por quatro barras finas ao redor do widget.
        """
        try:
            old=getattr(self,"_tutorial_spotlight",None)
            if isinstance(old,(list,tuple)):
                for part in old:
                    try: part.destroy()
                    except Exception: pass
            elif old is not None:
                old.destroy()
        except Exception:
            pass
        self._tutorial_spotlight=None
        if widget is None: return
        try:
            self.update_idletasks()
            rx=widget.winfo_rootx()-self.main_container.winfo_rootx()
            ry=widget.winfo_rooty()-self.main_container.winfo_rooty()
            w=max(20,widget.winfo_width())
            h=max(20,widget.winfo_height())
            # Só desenha se o alvo estiver dentro da janela visível.
            if rx+w<0 or ry+h<0 or rx>self.main_container.winfo_width() or ry>self.main_container.winfo_height():
                return
            t=TEMAS[self.tema_atual]
            accent=t["accent"]
            gap=4
            line=3
            x=max(1,rx-gap)
            y=max(1,ry-gap)
            outer_w=w+(gap*2)
            outer_h=h+(gap*2)
            parts=[]
            # Apenas a moldura: o centro permanece totalmente livre/visível.
            specs=(
                (x,y,outer_w,line),
                (x,y+outer_h-line,outer_w,line),
                (x,y,line,outer_h),
                (x+outer_w-line,y,line,outer_h),
            )
            for px,py,pw,ph in specs:
                part=ctk.CTkFrame(self.main_container,width=max(1,pw),height=max(1,ph),
                                  fg_color=accent,corner_radius=0,border_width=0)
                part.place(x=px,y=py)
                part.lift()
                parts.append(part)
            self._tutorial_spotlight=parts
            if self._tutorial_panel is not None:
                self._tutorial_panel.lift()
        except Exception:
            pass

    def _tutorial_render_step(self):
        steps=self._tutorial_steps(); idx=max(0,min(self._tutorial_step_index,len(steps)-1)); self._tutorial_step_index=idx
        page,title,body,tip=steps[idx]
        try: self.show_page(page,animate=True)
        except Exception: pass
        self._tutorial_title.configure(text=title); self._tutorial_body.configure(text=body)
        self._tutorial_tip.configure(text=("DICA // "+tip) if self.idioma=="pt" else ("TIP // "+tip))
        self._tutorial_count.configure(text=f"{idx+1:02d} / {len(steps):02d}")
        self._tutorial_progress.set((idx+1)/max(1,len(steps)))
        self._tutorial_prev.configure(state="disabled" if idx==0 else "normal")
        self._tutorial_next.configure(text=("FINALIZAR  ✓" if self.idioma=="pt" else "FINISH  ✓") if idx==len(steps)-1 else ("PRÓXIMO  →" if self.idioma=="pt" else "NEXT  →"))
        self.after(210,lambda:self._tutorial_place_spotlight(self._tutorial_target_widget(page)))

    def _tutorial_move(self, delta):
        steps=self._tutorial_steps(); nxt=self._tutorial_step_index+int(delta)
        if nxt>=len(steps):
            self._tutorial_close(mark_complete=True); return
        self._tutorial_step_index=max(0,nxt); self._tutorial_render_step()

    def _tutorial_close(self, mark_complete=False, voltar_home=True):
        if mark_complete:
            self.tutorial_completed=True; self.salvar_config_app()
        for name in ("_tutorial_spotlight","_tutorial_panel"):
            obj=getattr(self,name,None)
            if obj is not None:
                if isinstance(obj,(list,tuple)):
                    for part in obj:
                        try: part.destroy()
                        except Exception: pass
                else:
                    try: obj.destroy()
                    except Exception: pass
            setattr(self,name,None)
        self._tutorial_window=None
        if mark_complete:
            self.show_toast("TUTORIAL CONCLUÍDO" if self.idioma=="pt" else "TUTORIAL COMPLETE",
                            "Você pode rever o guia quando quiser em ? TUTORIAL." if self.idioma=="pt" else "Replay it anytime from ? TUTORIAL.",kind="success")
        if voltar_home:
            try: self.show_page("home",animate=True)
            except Exception: pass

    # ------------------------------------------------------------------
    # UI PRO v3.6 — toasts, busca universal e progressive disclosure
    # ------------------------------------------------------------------
    def _legacy_info(self, title, message, *args, **kwargs):
        """Compatibilidade: sucessos antigos agora viram notificações internas."""
        self.show_toast(str(title), str(message), kind="success")
        return "ok"

    def show_toast(self, title, message="", kind="success", duration=3400):
        try:
            if kind == "error": self._play_ui_sound("error",.08)
            elif kind == "warning": self._play_ui_sound("warning",.08)
            elif kind == "success": self._play_ui_sound("success",.08)
            elif kind == "info": self._play_ui_sound("notify",.08)
            t=TEMAS[self.tema_atual]; st=self._theme_style()
            palette={"success":t["accent"],"info":t["accent"],"warning":"#F3B33D","error":"#FF5C6C"}
            accent=palette.get(kind,t["accent"])
            frame=ctk.CTkFrame(self.main_container,width=365,height=96,fg_color=t.get("panel",t["card"]),
                               corner_radius=max(10,st["nav_radius"]),border_width=1,border_color=accent)
            frame.pack_propagate(False)
            rail=ctk.CTkFrame(frame,width=4,fg_color=accent,corner_radius=2); rail.pack(side="left",fill="y",padx=(0,0),pady=8)
            body=ctk.CTkFrame(frame,fg_color="transparent"); body.pack(side="left",fill="both",expand=True,padx=12,pady=10)
            symbol={"success":"✓","info":"i","warning":"!","error":"×"}.get(kind,"•")
            ctk.CTkLabel(body,text=f"{symbol}  {title}",anchor="w",text_color=accent,font=ctk.CTkFont(size=10,weight="bold")).pack(fill="x")
            if message:
                ctk.CTkLabel(body,text=str(message),anchor="w",justify="left",wraplength=320,text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9)).pack(fill="x",pady=(4,0))
            # pilha de no máximo 3 notificações.
            self._toast_items=[x for x in getattr(self,"_toast_items",[]) if self._widget_alive(x)]
            while len(self._toast_items)>=3:
                old=self._toast_items.pop(0)
                try: old.destroy()
                except Exception: pass
            self._toast_items.append(frame)
            self._reposition_toasts()
            frame.lift()
            # entrada sutil de 22 px, sem popup do Windows.
            try:
                y=98+(len(self._toast_items)-1)*106
                frame.place(relx=1.015,y=y,anchor="ne")
                def slide(i=0):
                    if not self._widget_alive(frame): return
                    if i>=10: frame.place_configure(relx=.988); return
                    e=1-(1-i/9)**3
                    frame.place_configure(relx=1.015-(.027*e)); self.after(12,lambda:slide(i+1))
                slide()
            except Exception: pass
            self.after(max(1200,int(duration)),lambda:self._dismiss_toast(frame))
        except Exception:
            try: self.log_output(f"[*] {title}: {message}")
            except Exception: pass

    def _widget_alive(self,w):
        try: return bool(w is not None and w.winfo_exists())
        except Exception: return False

    def _reposition_toasts(self):
        alive=[]
        for w in getattr(self,"_toast_items",[]):
            if self._widget_alive(w): alive.append(w)
        self._toast_items=alive
        for i,w in enumerate(alive):
            try: w.place_configure(relx=.988,y=98+i*106,anchor="ne")
            except Exception: pass

    def _dismiss_toast(self,frame):
        try:
            if frame in self._toast_items: self._toast_items.remove(frame)
            frame.destroy(); self._reposition_toasts()
        except Exception: pass

    def _search_catalog(self):
        pt=self.idioma=="pt"
        return [
            {"title":"Modo FPS","sub":"FPS & Gráficos","keys":"fps desempenho grafico performance batata","page":"fps","target":"performance_boost","scroll":0.0},
            {"title":"Céu Cinza" if pt else "Gray Sky","sub":"FPS & Gráficos","keys":"ceu sky cinza gray","page":"fps","target":"gray_sky","scroll":0.0},
            {"title":"Alvo de FPS" if pt else "FPS Target","sub":"FPS & Gráficos","keys":"fps target alvo unlock desbloquear","page":"fps","target":"fps_unlock","scroll":0.12},
            {"title":"Micro-Otimização","sub":"Modo Avançado • FPS & Gráficos","keys":"micro cpu threads otimização avancado advanced","page":"fps","target":"micro_opt","advanced":True,"scroll":0.60},
            {"title":"Telemetria","sub":"Modo Avançado • FPS & Gráficos","keys":"telemetria telemetry dados avancado advanced","page":"fps","target":"telemetry_off","advanced":True,"scroll":0.66},
            {"title":"Draco V4","sub":"Modo Avançado • Blox Fruits","keys":"draco v4 aura blox fruits avancado","page":"fps","target":"draco_aura","advanced":True,"scroll":0.78},
            {"title":"Ping & Latência" if pt else "Ping & Latency","sub":"Rede","keys":"ping rede network delay latencia","page":"ping","target":"ping_boost","scroll":0.0},
            {"title":"Cursor","sub":"Assets do Roblox","keys":"cursor mouse seta png","page":"cursor","target":"cursor_card","scroll":0.0},
            {"title":"Fontes","sub":"Assets do Roblox","keys":"fonte font ttf otf","page":"fonts","target":"font_card","scroll":0.0},
            {"title":"Combo Planner","sub":"Blox Fruits","keys":"combo build blox fruits guardar planner","page":"combo","target":"combo_hero","scroll":0.0},
            {"title":"ZK Assist","sub":"Assistente do ZKStrap","keys":"ia ai assistente ajuda diagnostico suporte app","page":"ai","target":"zkai_hero","scroll":0.0},
            {"title":"Build Roulette","sub":"Blox Hub","keys":"roleta roulette random build sword gun fruit fighting style","page":"roulette","scroll":0.0},
            {"title":"Creator Challenges","sub":"Blox Hub","keys":"creator desafio challenge bounty kill streak secret party","page":"creator","scroll":0.0},
            {"title":"PvP Coach","sub":"ZK AI • Blox Fruits","keys":"pvp coach melhorar build predict endlag soul dash ken trick game sense","page":"ai","target":"zkai_hero","scroll":0.0},
            {"title":"Temas","sub":"Personalizar","keys":"tema theme personalizar minecraft hollow blox valorant cs","page":"theme","scroll":0.0},
            {"title":"Áudio","sub":"Personalizar","keys":"som sons audio musica ambient pack efeitos sfx interface","page":"audio","scroll":0.0},
            {"title":"Central de Desempenho","sub":"Sistema","keys":"desempenho performance otimizar gpu game mode energia prioridade roblox diagnostico","page":"maintenance","scroll":0.0},
            {"title":"Recuperação","sub":"Sistema","keys":"recuperacao restaurar reset limpar logs cache backup original rollback","page":"recovery","scroll":0.0},
            {"title":"Atualizações","sub":"Changelog","keys":"update atualizacao versão changelog novidades","page":"updates","scroll":0.0},
            {"title":"Sugestões & Bugs","sub":"Feedback","keys":"bug erro sugestao feedback discord","page":"feedback","scroll":0.0},
            {"title":"Aplicar Configurações","sub":"Ação global","keys":"aplicar salvar configuracao flags","action":"apply"},
            {"title":"Tutorial","sub":"Ajuda","keys":"tutorial ajuda guia primeira vez","action":"tutorial"},
        ]

    def _handle_global_escape(self,event=None):
        panel=getattr(self,"_search_overlay",None)
        if panel is not None and self._widget_alive(panel):
            return self._fechar_busca_universal(event)
        return None

    @staticmethod
    def _search_normalize(text):
        text=str(text or "").lower().strip()
        return "".join(ch for ch in unicodedata.normalize("NFKD",text) if not unicodedata.combining(ch))

    def abrir_busca_universal(self,event=None):
        """Busca integrada v3.6.1: painel leve, sem ScrollableFrame/modal e sem fundo órfão."""
        panel=getattr(self,"_search_overlay",None)
        if panel is not None and self._widget_alive(panel):
            try: self._search_entry.focus_force()
            except Exception: pass
            return "break"
        self._tutorial_close(mark_complete=False,voltar_home=False)
        t=TEMAS[self.tema_atual]; st=self._theme_style()
        try:
            panel=ctk.CTkFrame(self,width=610,height=438,fg_color=t.get("panel",t["card"]),corner_radius=16,border_width=2,border_color=t["accent"])
            panel.place(relx=.5,y=96,anchor="n")
            panel.pack_propagate(False)
            panel.lift()
            self._search_overlay=panel

            head=ctk.CTkFrame(panel,fg_color="transparent")
            head.pack(fill="x",padx=16,pady=(14,7))
            ctk.CTkLabel(head,text="⌕  BUSCA UNIVERSAL",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold")).pack(side="left")
            ctk.CTkLabel(head,text="CTRL + K   •   ESC",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8)).pack(side="right")

            self._search_entry=ctk.CTkEntry(panel,placeholder_text="Buscar céu, cursor, combo, FPS, tema...",height=43,border_width=1,border_color=t["card_active"],font=ctk.CTkFont(size=11))
            self._search_entry.pack(fill="x",padx=16,pady=(2,9))
            self._search_entry.bind("<KeyRelease>",self._on_search_keyrelease)
            self._search_entry.bind("<Return>",self._owner_search_submit)
            self._search_entry.bind("<Escape>",self._fechar_busca_universal)

            self._search_results=ctk.CTkFrame(panel,fg_color="transparent",corner_radius=0)
            self._search_results.pack(fill="both",expand=True,padx=12,pady=(0,12))
            self._render_search_results("")
            self.after(40,lambda:self._search_entry.focus_force() if self._widget_alive(getattr(self,"_search_entry",None)) else None)
        except Exception as e:
            self._search_overlay=None
            try: self.log_output(f"[-] Busca Universal: {e}")
            except Exception: pass
            self.show_toast("BUSCA INDISPONÍVEL","Não foi possível montar o painel de busca.",kind="error")
        return "break"

    def _on_search_keyrelease(self,event=None):
        if event is not None and getattr(event,"keysym","") in ("Escape",):
            return "break"
        entry=getattr(self,"_search_entry",None)
        if not self._widget_alive(entry): return "break"
        try: self._render_search_results(entry.get())
        except Exception as e:
            try: self.log_output(f"[-] Busca Universal render: {e}")
            except Exception: pass
        return None

    def _fechar_busca_universal(self,event=None):
        panel=getattr(self,"_search_overlay",None)
        self._search_overlay=None
        self._search_entry=None
        self._search_results=None
        self._search_result_buttons=[]
        if panel is not None:
            try:
                if self._widget_alive(panel): panel.destroy()
            except Exception:
                pass
        try:
            self.focus_set(); self.update_idletasks()
        except Exception:
            pass
        return "break"

    def _render_search_results(self,query):
        holder=getattr(self,"_search_results",None)
        if not self._widget_alive(holder): return
        for w in list(holder.winfo_children()):
            try: w.destroy()
            except Exception: pass
        q=self._search_normalize(query)
        if q==OWNER_SEARCH_TRIGGER:
            # Intentionally do not reveal the Owner Lab in normal search results.
            tokens=["__owner_hidden__"]
        else:
            tokens=q.split()
        scored=[]
        for item in self._search_catalog():
            title=self._search_normalize(item.get("title",""))
            sub=self._search_normalize(item.get("sub",""))
            keys=self._search_normalize(item.get("keys",""))
            hay=f"{title} {sub} {keys}"
            if not tokens:
                score=1
            elif all(tok in hay for tok in tokens):
                score=10 + sum(5 for tok in tokens if tok in title) + sum(2 for tok in tokens if tok in keys)
            else:
                continue
            scored.append((score,item))
        scored.sort(key=lambda x:x[0],reverse=True)
        items=[it for _,it in scored[:7]]
        t=TEMAS[self.tema_atual]
        if not items:
            ctk.CTkLabel(holder,text=(f"Nenhum resultado para ‘{query}’." if self.idioma=="pt" else f"No results for ‘{query}’."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=10)).pack(pady=34)
            return
        self._search_result_buttons=[]
        for item in items:
            line=f"{item['title']}   •   {item.get('sub','')}"
            row=ctk.CTkButton(holder,text=line,anchor="w",height=42,corner_radius=9,
                              fg_color="transparent",hover_color=t["card_active"],text_color=t["text"],border_width=0,
                              font=ctk.CTkFont(size=10,weight="bold"),command=lambda it=item:self._activate_search_result(it))
            row.pack(fill="x",padx=4,pady=2)
            self._search_result_buttons.append(row)

    def _activate_search_result(self,item):
        self._fechar_busca_universal()
        action=item.get("action")
        if action=="apply": self.aplicar_configuracoes(); return
        if action=="tutorial": self.abrir_tutorial(False); return
        if item.get("advanced") and not self.advanced_mode: self.toggle_advanced_mode(force=True,quiet=True)
        page=item.get("page","home"); self.show_page(page,animate=True)
        def focus():
            try:
                body=self.page_scrolls.get(page); frac=float(item.get("scroll",0.0))
                if body is not None and hasattr(body,"_parent_canvas"): body._parent_canvas.yview_moveto(max(0,min(.98,frac)))
            except Exception: pass
            target=None; tid=item.get("target")
            if tid in getattr(self,"module_cards",{}): target=self.module_cards.get(tid)
            elif tid: target=getattr(self,tid,None)
            self._flash_widget(target)
        self.after(190,focus)

    def _flash_widget(self,widget):
        if widget is None: return
        try:
            t=TEMAS[self.tema_atual]
            old_bw=widget.cget("border_width"); old_bc=widget.cget("border_color")
            widget.configure(border_width=2,border_color=t["accent"])
            self.after(900,lambda: widget.configure(border_width=old_bw,border_color=old_bc) if self._widget_alive(widget) else None)
        except Exception: pass

    def toggle_advanced_mode(self,force=None,quiet=False):
        self.advanced_mode=(not bool(self.advanced_mode)) if force is None else bool(force)
        wrap=getattr(self,"advanced_fps_wrap",None)
        if wrap is not None:
            try:
                if self.advanced_mode:
                    wrap.pack(fill="x",after=self.advanced_toggle_holder)
                else:
                    wrap.pack_forget()
            except Exception: pass
        try:
            self.advanced_toggle_button.configure(text=("▾  OCULTAR OPÇÕES AVANÇADAS" if self.advanced_mode else "▸  MOSTRAR OPÇÕES AVANÇADAS") if self.idioma=="pt" else ("▾  HIDE ADVANCED OPTIONS" if self.advanced_mode else "▸  SHOW ADVANCED OPTIONS"))
            self.advanced_state_label.configure(text="ATIVO" if self.advanced_mode else "RECOLHIDO",text_color=TEMAS[self.tema_atual]["accent"] if self.advanced_mode else TEMAS[self.tema_atual].get("muted","gray"))
        except Exception: pass
        self.salvar_config_app()
        if not quiet:
            self.show_toast("MODO AVANÇADO" if self.idioma=="pt" else "ADVANCED MODE",
                            "Opções técnicas exibidas." if self.advanced_mode and self.idioma=="pt" else "Opções técnicas recolhidas." if self.idioma=="pt" else "Technical options shown." if self.advanced_mode else "Technical options hidden.",kind="info",duration=1800)

    def inicializar_efeito_matrix(self):
        t = TEMAS[self.tema_atual]
        self.canvas = Canvas(self, bg=t["bg"], highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.font_size = 12
        self.drops = [random.randint(-30, 0) for _ in range(90)]
        self.caracteres = "01ZK<>[]{}"
        self._ambient_phase = 0.0

    def _bind_theme_canvas(self, canvas, theme_name, zone="hero"):
        """Liga um canvas à atmosfera ativa e redesenha usando o tamanho real do widget."""
        try:
            canvas._zk_theme_name=theme_name
            canvas._zk_zone=zone
            def _redraw(event=None):
                try:
                    if not canvas.winfo_exists(): return
                    if event is not None and (getattr(event,"width",0)<8 or getattr(event,"height",0)<8): return
                    nm=getattr(canvas,"_zk_theme_name",theme_name)
                    self._draw_theme_art(canvas,nm,TEMAS.get(nm,TEMAS[self.tema_atual]))
                except Exception: pass
            def _preview_enter(event=None):
                if not bool(getattr(canvas,"_zk_preview",False)): return
                canvas._zk_preview_hover=True
                try:
                    tile=getattr(canvas,"_zk_preview_tile",None)
                    if tile is not None: tile.configure(border_width=2,border_color=TEMAS[theme_name]["accent"])
                except Exception: pass
                now=time.monotonic()
                if now-getattr(self,"_last_hover_sound",0.0)>.13:
                    self._last_hover_sound=now
                    # Cards SECRET bloqueados têm hover próprio no container inteiro.
                    # Se o canvas também tocar som, mover o mouse entre os filhos gera
                    # vários SFX em sequência.
                    if bool(getattr(canvas,"_zk_secret_locked",False)):
                        pass
                    elif theme_name in UNLOCKABLE_THEME_NAMES:
                        if not self._play_secret_theme_sound(theme_name,"hover",0.0): self._play_ui_sound("hover",.0)
                    else:
                        self._play_ui_sound("hover",.0)
                _redraw()
            def _preview_leave(event=None):
                if not bool(getattr(canvas,"_zk_preview",False)): return
                canvas._zk_preview_hover=False
                try:
                    tile=getattr(canvas,"_zk_preview_tile",None)
                    if tile is not None:
                        selected=(theme_name==self.tema_atual)
                        if bool(getattr(canvas,"_zk_secret_locked",False)):
                            tile.configure(border_width=1,border_color=self._mix_hex("#050505",TEMAS[theme_name]["accent"],.24))
                        else:
                            tile.configure(border_width=2 if selected else 1,border_color=TEMAS[theme_name]["accent"] if selected else TEMAS[theme_name]["card_active"])
                except Exception: pass
                _redraw()
            canvas.bind("<Configure>",_redraw,add="+")
            canvas.bind("<Enter>",_preview_enter,add="+")
            canvas.bind("<Leave>",_preview_leave,add="+")
            self.after(40,_redraw)
        except Exception: pass

    def _draw_theme_art(self, canvas, name, t):
        zone=getattr(canvas,"_zk_zone","hero")
        self._draw_theme_atmosphere(canvas,name,zone)
        # Secret Vault: a locked identity must look sealed, not merely unavailable.
        try:
            if bool(getattr(canvas,"_zk_secret_locked",False)):
                w=max(8,int(canvas.winfo_width())); h=max(8,int(canvas.winfo_height()))
                awake=bool(getattr(canvas,"_zk_preview_hover",False))
                # Two stippled layers make the dormant state visibly darker while
                # keeping enough of the identity visible to tease the reward.
                canvas.create_rectangle(0,0,w,h,fill="#000000",outline="",stipple="gray25" if awake else "gray50")
                if not awake:
                    canvas.create_rectangle(0,0,w,h,fill="#000000",outline="",stipple="gray25")
                accent=t.get("accent","#A855F7"); muted=self._mix_hex("#050505",accent,.42)
                for y in range(8,h,18):
                    canvas.create_line(0,y,w,y,fill=self._mix_hex("#050505",accent,.10 if awake else .06),width=1)
                canvas.create_text(w//2,h//2-5,text="SEALED // ???",fill=accent if awake else muted,font=("Consolas",9,"bold"),anchor="center")
                canvas.create_text(w//2,h//2+14,text="HOVER TO WAKE SIGNAL" if awake else "IDENTITY DORMANT",fill=self._mix_hex("#050505",accent,.58 if awake else .32),font=("Consolas",6,"bold"),anchor="center")
        except Exception:
            pass

    def animar_chuva_matrix_frame(self):
        """Loop visual 3.13: anima só as superfícies que realmente estão visíveis."""
        try:
            if time.monotonic() < float(getattr(self,"_scroll_active_until",0.0)):
                if getattr(self,"loop_animacao",True): self.after(90,self.animar_chuva_matrix_frame)
                return
            self._ambient_phase=(getattr(self,"_ambient_phase",0.0)+0.055)%1000
            name=self.tema_atual; t=TEMAS[name]
            # O canvas raiz antigo fica só como fallback de cor; o shell 3.13 possui
            # canvases próprios em header/sidebar/hero/dock.
            try:
                self.canvas.configure(bg=t["bg"])
                self.canvas.delete("ambient")
            except Exception:
                pass

            for cv in (getattr(self,"header_theme_canvas",None),getattr(self,"sidebar_theme_canvas",None),getattr(self,"dock_theme_canvas",None)):
                try:
                    if cv is not None and cv.winfo_exists(): self._draw_theme_art(cv,name,t)
                except Exception: pass

            current=getattr(self,"current_page_key",getattr(self,"_visible_page",None))
            cv=getattr(self,"page_theme_canvases",{}).get(current)
            try:
                if cv is not None and cv.winfo_exists(): self._draw_theme_art(cv,name,t)
            except Exception: pass

            # Previews só animam quando a galeria está aberta; evita gastar CPU em
            # dezenas de canvases escondidos nas outras páginas.
            if current=="theme":
                for cv,preview_name in getattr(self,"special_theme_preview_canvases",[]):
                    try:
                        if cv.winfo_exists() and (bool(getattr(cv,"_zk_preview_hover",False)) or preview_name==self.tema_atual):
                            self._draw_theme_art(cv,preview_name,TEMAS[preview_name])
                    except Exception: pass
        except Exception:
            pass
        if getattr(self,"loop_animacao",True):
            self.after(115,self.animar_chuva_matrix_frame)

    def _on_root_configure(self, event=None):
        try:
            if event is not None and event.widget is not self:
                return
            size = (self.winfo_width(), self.winfo_height())
            if size == getattr(self, "_last_layout_size", None):
                return
            self._last_layout_size = size
            if getattr(self, "_layout_job", None):
                try: self.after_cancel(self._layout_job)
                except Exception: pass
            self._layout_job = self.after(80, self._apply_responsive_layout)
        except Exception:
            pass

    def _desired_page_width(self):
        """Largura útil do shell 3.13 com sidebar única."""
        try:
            root_w=max(980,self.winfo_width())
            sidebar=(264 if root_w>=1360 else 248) if root_w>=1080 else 0
            return max(720,root_w-sidebar-56)
        except Exception:
            return 980

    def _apply_responsive_layout(self):
        """3.13: desktop com sidebar única; em janela estreita ela recolhe inteira."""
        try:
            w=max(900,self.winfo_width())
            nav=getattr(self,"left_panel",None)
            if nav is not None:
                if w<1080:
                    try: nav.pack_forget()
                    except Exception: pass
                else:
                    nav.configure(width=248 if w<1360 else 264)
                    if not nav.winfo_ismapped():
                        try: nav.pack(side="left",fill="y",before=self.content_host)
                        except Exception: pass
            search=getattr(self,"header_search_button",None)
            if search is not None:
                try:
                    if w<1180: search.pack_forget()
                    elif not search.winfo_ismapped(): search.pack(side="left",fill="x",expand=True,padx=(14,14),pady=30)
                except Exception: pass
            for body in getattr(self,"page_scrolls",{}).values():
                try: body.configure(width=self._desired_page_width())
                except Exception: pass
            self._layout_job=None
        except Exception:
            self._layout_job=None

    def criar_interface(self):
        """Interface 3.13 — navegação única, atmosfera global e hierarquia mais limpa."""
        t=TEMAS[self.tema_atual]; st=self._theme_style(); decor=THEME_DECOR.get(self.tema_atual,THEME_DECOR["Clean"])
        self.main_container=ctk.CTkFrame(self,fg_color=t["bg"])
        self.main_container.place(x=0,y=0,relwidth=1,relheight=1)
        self._toast_items=[]; self._search_overlay=None; self._tutorial_panel=None; self._tutorial_spotlight=None

        # COMMAND BAR limpa: imagens de jogo nunca ficam atrás da busca universal.
        self.header_frame=ctk.CTkFrame(self.main_container,height=112,fg_color=t.get("panel",t["card"]),corner_radius=0,border_width=0)
        self.header_frame.pack(fill="x",padx=0,pady=0); self.header_frame.pack_propagate(False)
        self.header_theme_canvas=None
        brand=ctk.CTkFrame(self.header_frame,fg_color="transparent",width=296); brand.pack(side="left",fill="y",padx=(14,0)); brand.pack_propagate(False)

        # Marca 3.13.3.3: ZK e CORE usam duas linhas físicas independentes.
        # Isso evita o overlap que aparecia com DPI/escala alta do Windows.
        logo=ctk.CTkFrame(brand,width=58,height=62,corner_radius=max(10,st["nav_radius"]),fg_color=t["icon_bg"],border_width=1,border_color=t["accent"])
        logo.pack(side="left",padx=(0,13),pady=25); logo.pack_propagate(False)
        logo_top=ctk.CTkFrame(logo,height=36,fg_color="transparent",corner_radius=0); logo_top.pack(fill="x",padx=3,pady=(4,0)); logo_top.pack_propagate(False)
        ctk.CTkLabel(logo_top,text="ZK",height=30,text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold")).pack(fill="both",expand=True)
        ctk.CTkFrame(logo,height=1,fg_color=self._mix_hex(t["border"],t["accent"],.55),corner_radius=0).pack(fill="x",padx=11,pady=0)
        logo_bottom=ctk.CTkFrame(logo,height=16,fg_color="transparent",corner_radius=0); logo_bottom.pack(fill="x",padx=3,pady=(0,3)); logo_bottom.pack_propagate(False)
        ctk.CTkLabel(logo_bottom,text="CORE",height=14,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=6,weight="bold")).pack(fill="both",expand=True)

        bw=ctk.CTkFrame(brand,fg_color="transparent"); bw.pack(side="left",fill="both",expand=True,pady=23)
        title_row=ctk.CTkFrame(bw,fg_color="transparent"); title_row.pack(fill="x",pady=(3,0))
        self.lbl_titulo=ctk.CTkLabel(title_row,text="ZKSTRAP",text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=17,weight="bold"),anchor="w"); self.lbl_titulo.pack(side="left",anchor="w")
        ctk.CTkLabel(title_row,text="  //  LOCAL",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=6,weight="bold")).pack(side="left",padx=(4,0),pady=(3,0))
        ctk.CTkLabel(bw,text=f"CLIENT CONTROL   •   v{APP_VERSION}",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(anchor="w",pady=(3,0))

        self.header_search_button=ctk.CTkButton(self.header_frame,text="⌕   Buscar página, opção ou ferramenta…                                  CTRL+K" if self.idioma=="pt" else "⌕   Search page, option or tool…                                  CTRL+K",height=48,corner_radius=15,anchor="w",border_spacing=17,fg_color=t["card"],hover_color=t["card_active"],border_width=1,border_color=self._mix_hex(t["card_active"],t["border"],.35),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=10,weight="bold"),command=self.abrir_busca_universal)
        self.header_search_button.pack(side="left",fill="x",expand=True,padx=(14,14),pady=30)
        self.header_art_wrap=None

        actions=ctk.CTkFrame(self.header_frame,fg_color="transparent",width=438); actions.pack(side="right",fill="y",padx=(0,14),pady=20); actions.pack_propagate(False); self.header_actions=actions
        chiprow=ctk.CTkFrame(actions,fg_color="transparent"); chiprow.pack(fill="x",pady=(0,5))
        self.lbl_ping=ctk.CTkLabel(chiprow,text="REDE --",height=22,corner_radius=7,fg_color=t["card"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold")); self.lbl_ping.pack(side="right",padx=(6,0))
        self.lbl_status_jogo=ctk.CTkLabel(chiprow,text=self.tr[self.idioma]['diretorio_buscando'],height=22,corner_radius=7,fg_color=t["card"],text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=7,weight="bold")); self.lbl_status_jogo.pack(side="right")
        act=ctk.CTkFrame(actions,fg_color="transparent"); act.pack(fill="x")
        self.profile_button=ctk.CTkButton(act,text="PERFIL",width=118,height=36,corner_radius=10,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],font=ctk.CTkFont(size=8,weight="bold"),command=self.abrir_vincular_perfil); self.profile_button.pack(side="right",padx=(7,0)); self._render_profile_button()
        self.header_apply_button=ctk.CTkButton(act,text="APLICAR" if self.idioma=="pt" else "APPLY",width=154,height=36,corner_radius=10,fg_color=t["accent"],hover_color=t["hover"],text_color="#06070A",font=ctk.CTkFont(size=9,weight="bold"),command=self.aplicar_configuracoes); self.header_apply_button.pack(side="right"); self.apply_button=self.header_apply_button
        self.header_compact_button=ctk.CTkButton(act,text="▣",width=38,height=36,corner_radius=10,fg_color=t["card"],hover_color=t["card_active"],text_color=t["accent"],command=self.abrir_modo_compacto); self.header_compact_button.pack(side="right",padx=(0,7)); Tooltip(self.header_compact_button,"Modo compacto" if self.idioma=="pt" else "Compact mode")
        self.header_sound_button=ctk.CTkButton(act,text="♫" if self.sounds_enabled else "♩",width=38,height=36,corner_radius=10,fg_color=t["card_active"] if self.sounds_enabled else t["card"],hover_color=t["hover"],text_color=t["accent"] if self.sounds_enabled else t.get("muted","gray"),command=self.abrir_som_config); self.header_sound_button.pack(side="right",padx=(0,7)); Tooltip(self.header_sound_button,"Sons do ZKStrap" if self.idioma=="pt" else "ZKStrap audio")
        self.header_setup_edit_label=ctk.CTkLabel(act,text="",height=30,corner_radius=8,fg_color=t["card"],text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"))
        self.header_setup_edit_label.pack(side="left",padx=(0,7))
        self._refresh_setup_edit_indicator()
        # Separador como irmão do header: garante linha contínua de ponta a ponta,
        # inclusive abaixo do bloco ZKSTRAP e em escalas diferentes do Windows.
        self.header_accent_line=ctk.CTkFrame(self.main_container,height=2,fg_color=t["accent"],corner_radius=0,border_width=0)
        self.header_accent_line.pack(fill="x",side="top",padx=0,pady=0)
        self.header_accent_line.pack_propagate(False)

        # Dock limpo: identidade do tema fica em cor/tipografia, não em wallpaper.
        self.bottom_frame=ctk.CTkFrame(self.main_container,height=46,fg_color=t.get("panel",t["card"]),corner_radius=0,border_width=0)
        self.bottom_frame.pack(fill="x",side="bottom",padx=0,pady=0); self.bottom_frame.pack_propagate(False)
        self.dock_theme_canvas=None
        ctk.CTkFrame(self.bottom_frame,height=1,fg_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.35),corner_radius=0).place(x=0,y=0,relwidth=1)
        statusrow=ctk.CTkFrame(self.bottom_frame,fg_color="transparent"); statusrow.pack(fill="both",expand=True,padx=15,pady=7)
        ctk.CTkLabel(statusrow,text="●",text_color="#4EDC8B",font=ctk.CTkFont(size=9,weight="bold")).pack(side="left",padx=(2,6))
        ctk.CTkLabel(statusrow,text="LOCAL CORE READY",text_color=t["text"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")
        self._log_open=False
        def _toggle_logs():
            self._log_open=not bool(getattr(self,"_log_open",False))
            if self._log_open:
                self.bottom_frame.configure(height=130); self.log_textbox.pack(fill="x",padx=14,pady=(0,10)); self.btn_logs.configure(text="FECHAR LOG")
            else:
                self.log_textbox.pack_forget(); self.bottom_frame.configure(height=46); self.btn_logs.configure(text="ABRIR LOG")
        self.btn_logs=ctk.CTkButton(statusrow,text="ABRIR LOG",width=86,height=28,corner_radius=8,fg_color=t["card"],hover_color=t["card_active"],text_color=t.get("muted","gray"),font=ctk.CTkFont(size=7,weight="bold"),command=_toggle_logs); self.btn_logs.pack(side="right")
        ctk.CTkLabel(statusrow,text=f"{decor['tag']}   •   {APP_VERSION}",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7)).pack(side="right",padx=12)
        self.log_textbox=ctk.CTkTextbox(self.bottom_frame,height=70,font=ctk.CTkFont(family="Consolas",size=8),fg_color=t["bg"],text_color=t["accent"],border_width=1,border_color=t["card_active"]); self.log_textbox.configure(state="disabled")
        for _line in getattr(self,"_log_history",[])[-10:]:
            try: self.log_textbox.configure(state="normal"); self.log_textbox.insert("end",_line+"\n"); self.log_textbox.configure(state="disabled")
            except Exception: pass

        # WORKSPACE: sidebar ÚNICA. Sem rail duplicado.
        self.body_frame=ctk.CTkFrame(self.main_container,fg_color="transparent"); self.body_frame.pack(fill="both",expand=True,padx=0,pady=0)
        self.rail_panel=None; self.nav_rail_buttons={}
        self.left_panel=ctk.CTkFrame(self.body_frame,width=252,fg_color=t.get("sidebar",t["card"]),corner_radius=0,border_width=0); self.left_panel.pack(side="left",fill="y"); self.left_panel.pack_propagate(False)

        # Sidebar sem wallpaper/mini-banner duplicado. O tema já aparece no hero principal.
        self.sidebar_theme_canvas=None
        self.theme_identity_text=None
        side_top=ctk.CTkFrame(self.left_panel,height=13,fg_color="transparent"); side_top.pack(fill="x")

        self.nav_scroll=ctk.CTkScrollableFrame(self.left_panel,fg_color="transparent",corner_radius=0,scrollbar_button_color=t["card_active"],scrollbar_button_hover_color=t["hover"]); self.nav_scroll.pack(fill="both",expand=True,padx=(10,6),pady=(5,5))
        self.nav_buttons={}; self.nav_icon_images={}; self.nav_section_labels=[]
        nav=[("home","INÍCIO" if self.idioma=="pt" else "HOME"),("fps","FPS & GRÁFICOS" if self.idioma=="pt" else "FPS & GRAPHICS"),("ping","PING & LATÊNCIA" if self.idioma=="pt" else "PING & LATENCY"),("cursor","CURSOR"),("fonts","FONTES" if self.idioma=="pt" else "FONTS"),("bloxhub","BLOX HUB"),("setups","SETUPS"),("spotify","SPOTIFY"),("theme","PERSONALIZAR" if self.idioma=="pt" else "CUSTOMIZE"),("audio","ÁUDIO" if self.idioma=="pt" else "AUDIO"),("maintenance","DESEMPENHO" if self.idioma=="pt" else "PERFORMANCE"),("recovery","RECUPERAÇÃO" if self.idioma=="pt" else "RECOVERY"),("updates","ATUALIZAÇÕES" if self.idioma=="pt" else "UPDATES"),("feedback","SUGESTÕES & BUGS" if self.idioma=="pt" else "FEEDBACK & BUGS"),("support","APOIAR" if self.idioma=="pt" else "SUPPORT"),("about","SOBRE" if self.idioma=="pt" else "ABOUT")]
        self._nav_label_map=dict(nav); section_breaks={0:"CORE",3:"PERSONAL",5:"BLOX",10:"TOOLS",12:"SYSTEM",14:"INFO"}
        for idx,(key,labeltxt) in enumerate(nav):
            if idx in section_breaks:
                if idx:
                    ctk.CTkFrame(self.nav_scroll,height=1,fg_color=self._mix_hex(t.get("border",t["card_active"]),t["accent"],.18)).pack(fill="x",padx=12,pady=(10,7))
                lab=ctk.CTkLabel(self.nav_scroll,text=section_breaks[idx],text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold")); lab._zk_text=section_breaks[idx]; lab.pack(anchor="w",padx=14,pady=(5 if idx else 6,5)); self.nav_section_labels.append(lab)
            img=self._make_nav_icon(key,size=20); self.nav_icon_images[key]=img
            b=ctk.CTkButton(self.nav_scroll,text=labeltxt,image=img,compound="left",anchor="w",height=44,corner_radius=max(10,st["nav_radius"]),border_spacing=13,border_width=1,border_color=self._mix_hex(t.get("sidebar",t["card"]),t.get("border",t["accent"]),.25),fg_color="transparent",hover_color=t["card_active"],text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=10,weight="bold"),command=lambda k=key:self.show_page(k,animate=True)); b.pack(fill="x",padx=3,pady=4); self.nav_buttons[key]=b

        footer=ctk.CTkFrame(self.left_panel,fg_color="transparent"); footer.pack(fill="x",padx=14,pady=(6,12))
        stat=ctk.CTkFrame(footer,fg_color="transparent"); stat.pack(fill="x",pady=(0,7))
        ctk.CTkLabel(stat,text="LOCAL CORE",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left")
        ctk.CTkLabel(stat,text="● READY",text_color="#4EDC8B",font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="right")
        self.btn_tutorial=ctk.CTkButton(footer,text="?   TUTORIAL",command=lambda:self.abrir_tutorial(primeiro_acesso=False),height=32,corner_radius=9,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],font=ctk.CTkFont(size=8,weight="bold")); self.btn_tutorial.pack(fill="x")

        self.content_host=ctk.CTkFrame(self.body_frame,fg_color=t.get("panel",t["card"]),corner_radius=0,border_width=0); self.content_host.pack(side="right",fill="both",expand=True)
        self.build_right_tabview()
        self.after(120,self._apply_responsive_layout)

    def _mark_fast_scroll(self):
        self._scroll_active_until=time.monotonic()+0.14

    def _install_smooth_scroll(self, scrollable, units=1):
        """Coalesce mouse-wheel bursts to reduce Tk redraw tearing."""
        try:
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None: return
            state={"pending":0,"job":None}
            def flush():
                state["job"]=None
                step=state["pending"]; state["pending"]=0
                if not step:return
                try: canvas.yview_scroll(max(-3,min(3,step)),"units")
                except Exception: pass
                self._mark_fast_scroll()
            def wheel(event):
                delta=getattr(event,"delta",0)
                if not delta:return "break"
                state["pending"] += (-1 if delta>0 else 1)*max(1,int(units))
                self._mark_fast_scroll()
                if state["job"] is None:
                    try: state["job"]=self.after(14,flush)
                    except Exception: flush()
                return "break"
            canvas.bind("<MouseWheel>",wheel,add=False)
        except Exception:
            pass

    def _bind_outer_scroll(self, widget, page_key):
        """Faz áreas internas usarem a rolagem principal da página.

        Evita o efeito antigo em que Textbox/chat capturava a roda e o usuário
        precisava mover o mouse para fora do card para continuar rolando o app.
        """
        try:
            target = getattr(widget, "_textbox", widget)
            def on_wheel(event):
                body=getattr(self,"page_scrolls",{}).get(page_key)
                if body is None or not self._widget_alive(body): return None
                canvas=getattr(body,"_parent_canvas",None)
                if canvas is None: return None
                delta=getattr(event,"delta",0)
                step=-1 if delta>0 else (1 if delta<0 else 0)
                if step:
                    try: canvas.yview_scroll(step,"units"); self._mark_fast_scroll()
                    except Exception: pass
                return "break"
            target.bind("<MouseWheel>",on_wheel,add=False)
            target.bind("<Button-4>",lambda e:(getattr(self.page_scrolls.get(page_key),"_parent_canvas",None).yview_scroll(-3,"units") if self.page_scrolls.get(page_key) else None,"break")[-1],add=False)
            target.bind("<Button-5>",lambda e:(getattr(self.page_scrolls.get(page_key),"_parent_canvas",None).yview_scroll(3,"units") if self.page_scrolls.get(page_key) else None,"break")[-1],add=False)
        except Exception:
            pass

    def _page_shell(self, key, title, subtitle=""):
        """Banner visual puro em TODOS os temas; texto sempre abaixo da arte."""
        t=TEMAS[self.tema_atual]; st=self._theme_style(); decor=THEME_DECOR.get(self.tema_atual,THEME_DECOR["Clean"])
        page=ctk.CTkFrame(self.content_host,fg_color="transparent"); self.pages[key]=page
        if not hasattr(self,"page_art_wraps"): self.page_art_wraps={}

        hero=ctk.CTkFrame(page,height=194,fg_color=t.get("panel",t["card"]),corner_radius=0,border_width=0)
        hero.pack(fill="x",padx=16,pady=(14,0)); hero.pack_propagate(False)
        art=Canvas(hero,bg=t.get("panel",t["card"]),highlightthickness=0,bd=0)
        art.place(x=0,y=0,relwidth=1,relheight=1)
        art._zk_page_key=key; art._zk_page_title=title; art._zk_page_subtitle=subtitle
        self.page_theme_canvases[key]=art
        self._bind_theme_canvas(art,self.tema_atual,zone="hero")
        self.page_art_wraps[key]=hero

        holder=ctk.CTkFrame(page,fg_color="transparent"); holder.pack(fill="both",expand=True,padx=18,pady=(12,12))
        body=ctk.CTkScrollableFrame(holder,width=self._desired_page_width(),fg_color="transparent",corner_radius=0,scrollbar_button_color=t["accent"],scrollbar_button_hover_color=t["hover"])
        body.pack(fill="both",expand=True,padx=(8,2),pady=0); self.page_scrolls[key]=body
        self._install_smooth_scroll(body,1)

        meta=SPECIAL_THEME_BANNER_META.get(self.tema_atual,{}) if self.tema_atual in SPECIAL_THEME_NAMES else {}
        info=ctk.CTkFrame(body,fg_color=t.get("panel",t["card"]),corner_radius=max(14,st["card_radius"]),border_width=1,border_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.48))
        info.pack(fill="x",padx=6,pady=(2,12))
        ctk.CTkFrame(info,height=2,fg_color=self._mix_hex(t.get("border",t["accent"]),t["accent"],.58),corner_radius=0).pack(fill="x",padx=12,pady=(0,0))
        inner=ctk.CTkFrame(info,fg_color="transparent"); inner.pack(fill="x",padx=24,pady=(18,18))
        top=ctk.CTkFrame(inner,fg_color="transparent"); top.pack(fill="x")
        left=ctk.CTkFrame(top,fg_color="transparent"); left.pack(side="left",fill="x",expand=True)
        crumb=ctk.CTkFrame(left,fg_color="transparent"); crumb.pack(anchor="w")
        ctk.CTkLabel(crumb,text=f"ZK  /  {key.upper().replace('_',' ')}",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left")
        ctk.CTkLabel(crumb,text="LOCAL CLIENT  //  CONTROL DECK",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left",padx=(10,0))
        ctk.CTkLabel(left,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=23,weight="bold"),anchor="w").pack(anchor="w",pady=(4,0))
        if subtitle:
            ctk.CTkLabel(left,text=subtitle,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=10),wraplength=860,justify="left",anchor="w").pack(fill="x",anchor="w",pady=(5,0))
        right=ctk.CTkFrame(top,fg_color="transparent"); right.pack(side="right",anchor="ne",padx=(18,0))
        if self.tema_atual in SPECIAL_THEME_NAMES:
            right_title=str(meta.get("subtitle") or decor["tag"]).upper(); right_sub=f"{self.tema_atual.upper()}  //  SIGNATURE"
        else:
            right_title=str(decor.get("tag","CORE")).upper(); right_sub="SIGNATURE / CORE"
        ctk.CTkLabel(right,text=right_title,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(anchor="e")
        ctk.CTkLabel(right,text=right_sub,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7)).pack(anchor="e",pady=(3,0))
        return page,body

    def _section_card(self, parent, title, description=""):
        t=TEMAS[self.tema_atual]; st=self._theme_style()
        radius=max(14,st["card_radius"])
        border=self._mix_hex(t.get("border",t["accent"]),t["accent"],.38)
        card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=radius,border_width=1,border_color=border)
        card.pack(fill="x",padx=6,pady=10)
        # assinatura visual consistente: rail lateral + linha superior curta.
        ctk.CTkFrame(card,width=4,fg_color=t["accent"],corner_radius=3).place(x=0,y=15,relheight=.68)
        ctk.CTkFrame(card,height=2,width=112,fg_color=st.get("accent2",t["accent"]),corner_radius=2).place(x=18,y=0)
        content=ctk.CTkFrame(card,fg_color="transparent"); content.pack(fill="both",expand=True,padx=22,pady=(16,18))
        head=ctk.CTkFrame(content,fg_color="transparent"); head.pack(fill="x")
        ctk.CTkLabel(head,text=title,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold"),anchor="w").pack(side="left")
        badge=ctk.CTkLabel(head,text="ZK  //  MODULE",height=23,corner_radius=8,fg_color=t.get("icon_bg",t["card_active"]),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=6,weight="bold"))
        badge.pack(side="right")
        if description:
            ctk.CTkLabel(content,text=description,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=10),wraplength=1020,justify="left",anchor="w").pack(fill="x",anchor="w",pady=(8,3))
        return content

    def _module_switch(self, parent, key, label=None, description=None):
        t=TEMAS[self.tema_atual]; st=self._theme_style(); data=FLAG_MODULES[key]
        label=label or (data["pt"] if self.idioma=="pt" else data["en"])
        if description is None: description=data["tooltip_pt"] if self.idioma=="pt" else data["tooltip_en"]
        active=bool(self.module_states.get(key,False))
        card=ctk.CTkFrame(parent,fg_color=t["card"],corner_radius=max(12,st["card_radius"]),border_width=1,border_color=t["accent"] if active else self._mix_hex(t["card_active"],t["border"],.34)); card.pack(fill="x",padx=8,pady=7)
        top=ctk.CTkFrame(card,height=3,fg_color=t["accent"] if active else t["card_active"],corner_radius=2); top.pack(fill="x",padx=12)
        row=ctk.CTkFrame(card,fg_color="transparent"); row.pack(fill="x",padx=15,pady=12)
        txt=ctk.CTkFrame(row,fg_color="transparent"); txt.pack(side="left",fill="both",expand=True)
        ctk.CTkLabel(txt,text=label,text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=13,weight="bold")).pack(anchor="w")
        ctk.CTkLabel(txt,text=description,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=9),wraplength=790,justify="left",anchor="w").pack(anchor="w",fill="x",pady=(3,0))
        controls=ctk.CTkFrame(row,fg_color="transparent"); controls.pack(side="right",padx=(12,0))
        state=ctk.CTkLabel(controls,text=("ATIVO" if active else "OFF") if self.idioma=="pt" else ("ACTIVE" if active else "OFF"),height=24,corner_radius=8,fg_color=t["icon_bg"],text_color=t["accent"] if active else t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")); state.pack(side="left",padx=(0,9))
        sw=ctk.CTkSwitch(controls,text="",width=48,command=lambda k=key:self.evento_switch_modulo(k),progress_color=t["accent"],button_color=t["text"],button_hover_color=t["hover"],fg_color=t["card_active"]); sw.pack(side="left")
        if active: sw.select()
        self.module_switches[key]=sw; self.module_cards[key]=card
        return card,sw

    def _open_support_page(self):
        try:
            webbrowser.open(SUPPORT_PAGE_URL)
            self._play_ui_sound("confirm", .02)
        except Exception as exc:
            try:
                messagebox.showerror("ZKStrap", f"Não foi possível abrir a página de apoio.\n\n{exc}")
            except Exception:
                pass

    def _copy_support_link(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(SUPPORT_PAGE_URL)
            self.update_idletasks()
            self._play_ui_sound("confirm", .02)
            try:
                messagebox.showinfo("ZKStrap", "Link da página de apoio copiado.")
            except Exception:
                pass
        except Exception as exc:
            try:
                messagebox.showerror("ZKStrap", f"Não foi possível copiar o link.\n\n{exc}")
            except Exception:
                pass

    def build_right_tabview(self):
        t = TEMAS[self.tema_atual]
        st = self._theme_style()
        pt = self.idioma == "pt"
        self.pages = {}
        self.page_scrolls = {}
        self.page_theme_canvases = {}
        self.special_theme_preview_canvases = []
        self.theme_preview_canvases = self.special_theme_preview_canvases
        self.module_switches = {}
        self.module_cards = {}
        self.advanced_menus = {}

        # HOME / DASHBOARD
        _, body = self._page_shell("home", "ZKSTRAP", "Painel central para ver o estado do cliente e aplicar tudo sem procurar botões escondidos." if pt else "Central dashboard to see client state and apply everything without hunting for hidden buttons.")

        dash = self._section_card(body, "DASHBOARD // STATUS AO VIVO" if pt else "DASHBOARD // LIVE STATUS", "Resumo rápido do Roblox, módulos, assets e necessidade de reinício." if pt else "Quick summary of Roblox, modules, assets and restart state.")
        stats = ctk.CTkFrame(dash, fg_color="transparent"); stats.pack(fill="x", padx=14, pady=(2,12))
        self.dashboard_labels = {}
        stat_defs = [("client","CLIENTE" if pt else "CLIENT"),("modules","OTIMIZAÇÕES" if pt else "OPTIMIZATIONS"),("assets","ASSETS"),("restart","REINÍCIO" if pt else "RESTART")]
        for i,(key,label) in enumerate(stat_defs):
            box=ctk.CTkFrame(stats,fg_color=t["card_active"],corner_radius=max(11,st["nav_radius"]),border_width=1,border_color=self._mix_hex(t["border"],t["accent"],.24))
            box.grid(row=0,column=i,sticky="ew",padx=5,pady=2); stats.grid_columnconfigure(i,weight=1)
            ctk.CTkFrame(box,height=2,fg_color=t["accent"] if i==0 else self._mix_hex(t["card_active"],t["accent"],.34),corner_radius=2).pack(fill="x",padx=10,pady=(7,5))
            ctk.CTkLabel(box,text=label,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(anchor="w",padx=11,pady=(0,2))
            val=ctk.CTkLabel(box,text="--",text_color=t["accent"],font=ctk.CTkFont(family="Segoe UI",size=13,weight="bold"),wraplength=150,justify="left")
            val.pack(anchor="w",padx=11,pady=(0,11)); self.dashboard_labels[key]=val
        self.dashboard_path_label=ctk.CTkLabel(dash,text="",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8),wraplength=820,justify="left")
        self.dashboard_path_label.pack(anchor="w",padx=18,pady=(0,10))

        quick = self._section_card(body, "CENTRAL RÁPIDA" if pt else "QUICK CENTER", "Aplique as opções atuais ou ative o modo FPS seguro em um clique. Nenhum app é fechado automaticamente." if pt else "Apply current options or enable safe FPS mode in one click. No apps are closed automatically.")
        qrow=ctk.CTkFrame(quick,fg_color="transparent"); qrow.pack(fill="x",padx=16,pady=(2,6))
        ctk.CTkButton(qrow,text="⚡ OTIMIZAR ROBLOX" if pt else "⚡ OPTIMIZE ROBLOX",command=self.otimizar_um_clique,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=46,corner_radius=11,font=ctk.CTkFont(size=11,weight="bold")).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(qrow,text="APLICAR CONFIGURAÇÕES" if pt else "APPLY SETTINGS",command=self.aplicar_configuracoes,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=46,corner_radius=11,font=ctk.CTkFont(size=11,weight="bold")).pack(side="left",expand=True,fill="x",padx=(4,0))
        qrow2=ctk.CTkFrame(quick,fg_color="transparent"); qrow2.pack(fill="x",padx=16,pady=(2,14))
        ctk.CTkButton(qrow2,text="COMPARAR CONFIGURAÇÕES" if pt else "COMPARE SETTINGS",command=self.mostrar_comparador_config,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(qrow2,text="MODO COMPACTO" if pt else "COMPACT MODE",command=self.abrir_modo_compacto,fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(4,0))

        bench = self._section_card(body, "BENCHMARK DO SISTEMA" if pt else "SYSTEM BENCHMARK", "Mede CPU, RAM, processos e memória do Roblox. Não inventa FPS: é um retrato do sistema antes/depois." if pt else "Measures CPU, RAM, processes and Roblox memory. It does not invent FPS: it is a before/after system snapshot.")
        self.lbl_benchmark=ctk.CTkLabel(bench,text="Nenhuma medição ainda." if pt else "No measurement yet.",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=9),justify="left",anchor="w")
        self.lbl_benchmark.pack(fill="x",padx=16,pady=(2,7))
        brow=ctk.CTkFrame(bench,fg_color="transparent"); brow.pack(fill="x",padx=16,pady=(0,14))
        ctk.CTkButton(brow,text="MEDIR AGORA" if pt else "MEASURE NOW",command=self.executar_benchmark,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"]).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(brow,text="ABRIR RECUPERAÇÃO" if pt else "OPEN RECOVERY",command=lambda:self.show_page("recovery",animate=True),fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=t["card_active"],text_color=t["text"]).pack(side="left",expand=True,fill="x",padx=(4,0))

        c1 = self._section_card(body, "CLIENTE ROBLOX", "Localização da version-* atual e sincronização automática após updates." if pt else "Current version-* location and automatic synchronization after updates.")
        self.home_dir_label = ctk.CTkLabel(c1, text=self.pasta_roblox_salva or ("Roblox ainda não localizado" if pt else "Roblox not located yet"), text_color=t["accent"], font=ctk.CTkFont(family="Consolas", size=10), wraplength=820, justify="left")
        self.home_dir_label.pack(anchor="w", padx=16, pady=(0, 8)); self.lbl_pasta_atual=self.home_dir_label
        row = ctk.CTkFrame(c1, fg_color="transparent"); row.pack(fill="x", padx=16, pady=(0, 12))
        self.btn_select_roblox = ctk.CTkButton(row, text=self.tr[self.idioma]['localizar'], command=self.selecionar_pasta_roblox, fg_color=t["card_active"], hover_color=t["hover"], text_color=t["accent"]); self.btn_select_roblox.pack(side="left", expand=True, fill="x", padx=(0,4))
        self.btn_open_clientsettings = ctk.CTkButton(row, text="ABRIR CLIENTSETTINGS" if pt else "OPEN CLIENTSETTINGS", command=self.abrir_pasta_clientsettings, fg_color=t["card_active"], hover_color=t["hover"], text_color=t["accent"]); self.btn_open_clientsettings.pack(side="left", expand=True, fill="x", padx=(4,0))
        self.switch_config_watchdog = ctk.CTkSwitch(c1, text="WATCHDOG 5s — manter configurações após update" if pt else "5s WATCHDOG — keep settings after updates", command=self.evento_watchdog_config, progress_color=t["accent"], fg_color="#44484F", text_color=t["text"]); self.switch_config_watchdog.pack(anchor="w",padx=16,pady=(0,14))
        if self.config_watchdog_enabled: self.switch_config_watchdog.select()
        self.lbl_watchdog = ctk.CTkLabel(c1,text="",font=ctk.CTkFont(size=1))

        prof = self._section_card(body, "PERFIL ROBLOX" if pt else "ROBLOX PROFILE", "Vínculo visual público: não é login e nunca pede senha." if pt else "Public visual link: not a login and never asks for a password.")
        self.home_profile_label = ctk.CTkLabel(prof, text="", text_color=t["accent"], font=ctk.CTkFont(size=10, weight="bold")); self.home_profile_label.pack(anchor="w", padx=16, pady=(0,8)); self._refresh_home_profile_card()
        pr = ctk.CTkFrame(prof, fg_color="transparent"); pr.pack(fill="x", padx=16, pady=(0,14))
        ctk.CTkButton(pr, text="VINCULAR / TROCAR" if pt else "LINK / CHANGE", command=self.abrir_vincular_perfil, fg_color=t["card_active"], hover_color=t["hover"], text_color=t["accent"]).pack(side="left", expand=True, fill="x", padx=(0,4))
        ctk.CTkButton(pr, text="DESVINCULAR" if pt else "UNLINK", command=self._desvincular_perfil, fg_color="transparent", border_width=1, border_color=t["card_active"], text_color=t["text"]).pack(side="left", expand=True, fill="x", padx=(4,0))
        self.after(250, self.refresh_dashboard)

        # FPS
        _, body = self._page_shell("fps", "FPS & GRÁFICOS" if pt else "FPS & GRAPHICS", "Central de desempenho: os principais ajustes ficam juntos e são aplicados com um clique." if pt else "Performance center: the main tweaks live together and apply with one click.")
        core = self._section_card(body, "DESEMPENHO PRINCIPAL" if pt else "CORE PERFORMANCE", "O modo FPS reúne os ajustes gráficos permitidos do executor. Céu cinza fica separado para você escolher o visual normal ou cinza." if pt else "FPS mode combines the executor graphics tweaks. Gray sky stays separate so you can choose normal or gray visuals.")
        self._module_switch(core, "performance_boost", "MODO FPS / GRÁFICOS NO MÍNIMO" if pt else "FPS MODE / MINIMUM GRAPHICS")
        self._module_switch(core, "gray_sky", "CÉU CINZA" if pt else "GRAY SKY")
        self._module_switch(core, "fps_unlock", "DESBLOQUEAR / ELEVAR FPS" if pt else "UNLOCK / RAISE FPS")

        fps_card = self._section_card(body, "ALVO DE FPS" if pt else "FPS TARGET", "Escolha o alvo usado pelo desbloqueio e pela micro-otimização. Algumas chaves podem ser ignoradas pelo cliente dependendo da versão." if pt else "Choose the target used by FPS unlock and micro-optimization. Some keys may be ignored depending on client version.")
        self.micro_fps_menu = ctk.CTkOptionMenu(fps_card, values=["30","60","120","144","165","240","360","540","1000"], command=self.evento_micro_fps_changed, fg_color=t["card_active"], button_color=t["card_active"], button_hover_color=t["hover"], text_color=t["accent"])
        self.micro_fps_menu.set(self.micro_fps_target); self.micro_fps_menu.pack(fill="x", padx=16, pady=(4,14))

        # Progressive disclosure: a tela principal fica limpa e as opções técnicas só aparecem quando pedidas.
        self.advanced_toggle_holder = ctk.CTkFrame(body, fg_color="transparent")
        self.advanced_toggle_holder.pack(fill="x", padx=8, pady=(5,2))
        adv_inner=ctk.CTkFrame(self.advanced_toggle_holder,fg_color=t["card"],corner_radius=st["card_radius"],border_width=1,border_color=t["card_active"])
        adv_inner.pack(fill="x")
        self.advanced_toggle_button=ctk.CTkButton(adv_inner,text=("▾  OCULTAR OPÇÕES AVANÇADAS" if self.advanced_mode else "▸  MOSTRAR OPÇÕES AVANÇADAS") if pt else ("▾  HIDE ADVANCED OPTIONS" if self.advanced_mode else "▸  SHOW ADVANCED OPTIONS"),command=self.toggle_advanced_mode,
            fg_color="transparent",hover_color=t["card_active"],text_color=t["text"],anchor="w",height=42,font=ctk.CTkFont(size=10,weight="bold"))
        self.advanced_toggle_button.pack(side="left",fill="x",expand=True,padx=(6,2),pady=5)
        self.advanced_state_label=ctk.CTkLabel(adv_inner,text="ATIVO" if self.advanced_mode else "RECOLHIDO",text_color=t["accent"] if self.advanced_mode else t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"))
        self.advanced_state_label.pack(side="right",padx=12)

        self.advanced_fps_wrap = ctk.CTkFrame(body, fg_color="transparent")
        self.advanced_fps_wrap.pack(fill="x", after=self.advanced_toggle_holder)
        extras = self._section_card(self.advanced_fps_wrap, "OTIMIZAÇÕES AVANÇADAS" if pt else "ADVANCED OPTIMIZATIONS", "Telemetria, micro-otimizações e ajustes experimentais ficam recolhidos para não poluir a página." if pt else "Telemetry, micro-optimizations and experimental tweaks stay collapsed to keep this page clean.")
        self._module_switch(extras, "micro_opt", "MICRO-OTIMIZAÇÃO CPU / FPS (EXPERIMENTAL)" if pt else "CPU / FPS MICRO-OPTIMIZATION (EXPERIMENTAL)")
        self._module_switch(extras, "telemetry_off", "REDUZIR / DESATIVAR TELEMETRIA (EXPERIMENTAL)" if pt else "REDUCE / DISABLE TELEMETRY (EXPERIMENTAL)")

        draco_box = ctk.CTkFrame(extras, fg_color=t.get("panel", t["card"]), corner_radius=max(7, st["nav_radius"]), border_width=1, border_color=t["card_active"])
        draco_box.pack(fill="x", padx=16, pady=(8,10))
        ctk.CTkLabel(draco_box, text="BLOX FRUITS // DRACO V4" if pt else "BLOX FRUITS // DRACO V4", text_color=t["accent"], font=ctk.CTkFont(family="Consolas", size=9, weight="bold")).pack(anchor="w", padx=12, pady=(10,1))
        ctk.CTkLabel(draco_box, text="Ajuste experimental visual/de desempenho. Não precisa mais de uma aba própria." if pt else "Experimental visual/performance tweak. It no longer needs a separate page.", text_color=t.get("muted", "gray"), font=ctk.CTkFont(family="Segoe UI", size=8), wraplength=760, justify="left").pack(anchor="w", padx=12, pady=(0,4))
        self._module_switch(draco_box, "draco_aura", "REDUZIR AURA DRACO V4 (EXPERIMENTAL)" if pt else "REDUCE DRACO V4 AURA (EXPERIMENTAL)")
        cpu = ctk.CTkFrame(extras, fg_color="transparent")
        cpu.pack(fill="x", padx=16, pady=(0,14))
        ctk.CTkLabel(cpu, text=(f"CPU detectada: {self.get_logical_processors()} processadores lógicos" if pt else f"Detected CPU: {self.get_logical_processors()} logical processors"), text_color=t.get("muted","gray"), font=ctk.CTkFont(family="Segoe UI", size=9)).pack(anchor="w")
        applybar = ctk.CTkFrame(extras, fg_color=t["card_active"], corner_radius=max(7,st["nav_radius"]), border_width=1, border_color=t["border"])
        applybar.pack(fill="x", padx=16, pady=(2,14))
        ctk.CTkLabel(applybar, text="PRONTO PARA APLICAR" if pt else "READY TO APPLY", text_color=t.get("muted","gray"), font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left",padx=12,pady=10)
        ctk.CTkButton(applybar, text="APLICAR CONFIGURAÇÕES" if pt else "APPLY SETTINGS", command=self.aplicar_configuracoes, fg_color=t["accent"], hover_color=t["hover"], text_color="#050505", height=38).pack(side="right",padx=7,pady=7)
        if not self.advanced_mode:
            self.advanced_fps_wrap.pack_forget()

        # PING / LATÊNCIA — ferramentas locais reais; sem prometer reduzir distância física até o servidor.
        _, body = self._page_shell("ping", "PING & LATÊNCIA" if pt else "PING & LATENCY", "Reduza gargalos locais e descubra onde a latência está acontecendo. Distância/rota até o servidor continuam dependendo da internet e do servidor do Roblox." if pt else "Reduce local bottlenecks and diagnose latency. Physical route/server distance still depends on your ISP and Roblox server.")
        info = self._section_card(body, "PAINEL DE LATÊNCIA" if pt else "LATENCY PANEL", "Mede conexão TCP até pontos de referência e mostra jitter. Não é o ping exato dentro da partida, mas ajuda a separar problema local de rota/servidor." if pt else "Measures TCP connection time to reference endpoints and jitter. It is not exact in-game ping, but helps separate local issues from route/server issues.")
        self.page_ping_label = ctk.CTkLabel(info, text="Pronto para testar.", text_color=t["accent"], justify="left", anchor="w", font=ctk.CTkFont(family="Consolas",size=9,weight="bold")); self.page_ping_label.pack(fill="x", anchor="w", padx=16, pady=(2,10))
        prow=ctk.CTkFrame(info,fg_color="transparent"); prow.pack(fill="x",padx=16,pady=(0,8))
        ctk.CTkButton(prow,text="TESTAR ROTA ROBLOX" if pt else "TEST ROBLOX ROUTE",command=self.testar_rota_roblox,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=38).pack(side="left",fill="x",expand=True,padx=(0,5))
        ctk.CTkButton(prow,text="OTIMIZAÇÃO SEGURA" if pt else "SAFE NETWORK CLEANUP",command=self.otimizar_rede_segura,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],height=38).pack(side="left",fill="x",expand=True,padx=(5,0))
        local = self._section_card(body, "REDUZIR GARGALO LOCAL" if pt else "REDUCE LOCAL BOTTLENECKS", "O que realmente pode ajudar quando o problema está no seu PC: evitar downloads/overlays competindo com o Roblox e manter a pilha de rede do Windows em estado normal." if pt else "What can actually help when the issue is local: avoid downloads/overlays competing with Roblox and keep Windows networking in a normal state.")
        r1=ctk.CTkFrame(local,fg_color="transparent"); r1.pack(fill="x",padx=16,pady=(2,6))
        ctk.CTkButton(r1,text="PREPARAR SESSÃO ROBLOX" if pt else "PREPARE ROBLOX SESSION",command=self.preparar_sessao_roblox,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"]).pack(side="left",fill="x",expand=True,padx=(0,4))
        ctk.CTkButton(r1,text="APPS PESADOS / REDE" if pt else "HEAVY / NETWORK APPS",command=self.fechar_apps_pesados,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"]).pack(side="left",fill="x",expand=True,padx=(4,0))
        r2=ctk.CTkFrame(local,fg_color="transparent"); r2.pack(fill="x",padx=16,pady=(2,12))
        ctk.CTkButton(r2,text="VER TCP AUTO-TUNING" if pt else "CHECK TCP AUTO-TUNING",command=self.verificar_tcp_autotuning,fg_color=t["card"],hover_color=t["card_active"],text_color=t["text"]).pack(side="left",fill="x",expand=True,padx=(0,4))
        ctk.CTkButton(r2,text="ABRIR REDE DO WINDOWS" if pt else "OPEN WINDOWS NETWORK",command=self.abrir_network_settings,fg_color=t["card"],hover_color=t["card_active"],text_color=t["text"]).pack(side="left",fill="x",expand=True,padx=(4,0))
        dns_card=self._section_card(body,"DNS LAB // ROTA LOCAL" if pt else "DNS LAB // LOCAL ROUTE","Teste resolvers antes de trocar. DNS pode melhorar a resolução de nomes, mas não encurta a distância física até o servidor da partida." if pt else "Benchmark resolvers before switching. DNS can improve name resolution but cannot shorten the physical route to the match server.")
        self.dns_lab_label=ctk.CTkLabel(dns_card,text="Clique em TESTAR DNS para medir Cloudflare, Google e Quad9 por RTT real e aplicar o melhor resultado com um clique." if pt else "Click TEST DNS to measure Cloudflare, Google and Quad9 by real RTT and apply the best result with one click.",text_color=t.get("muted","gray"),justify="left",anchor="w",font=ctk.CTkFont(family="Consolas",size=8),wraplength=920); self.dns_lab_label.pack(fill="x",padx=16,pady=(3,8))
        d1=ctk.CTkFrame(dns_card,fg_color="transparent"); d1.pack(fill="x",padx=16,pady=(0,6))
        ctk.CTkButton(d1,text="TESTAR DNS" if pt else "TEST DNS",command=self.benchmark_dns,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=38).pack(side="left",fill="x",expand=True,padx=(0,4))
        ctk.CTkButton(d1,text="APLICAR MELHOR TESTE" if pt else "APPLY BEST TEST",command=self.aplicar_melhor_dns,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",fill="x",expand=True,padx=4)
        ctk.CTkButton(d1,text="AUTOMÁTICO / DHCP" if pt else "AUTOMATIC / DHCP",command=self.restaurar_dns_automatico,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],height=38).pack(side="left",fill="x",expand=True,padx=(4,0))
        d2=ctk.CTkFrame(dns_card,fg_color="transparent"); d2.pack(fill="x",padx=16,pady=(0,8))
        for name in ("Cloudflare","Google","Quad9"):
            ctk.CTkButton(d2,text=name.upper(),command=lambda n=name:self.aplicar_dns_perfil(n),fg_color=t["card"],hover_color=t["card_active"],text_color=t["accent"],height=36).pack(side="left",fill="x",expand=True,padx=3)
        ctk.CTkButton(dns_card,text="REPARAR PILHA TCP/IP — AVANÇADO" if pt else "REPAIR TCP/IP STACK — ADVANCED",command=self.reparar_pilha_rede_avancado,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color=t["border"],text_color=t.get("muted","gray"),height=36).pack(fill="x",padx=16,pady=(0,14))

        legacy=self._section_card(body,"FASTFLAGS DE PING — LEGADO" if pt else "PING FASTFLAGS — LEGACY","Flags antigas de rede podem ser ignoradas pelo Roblox atual e não substituem uma rota melhor. Deixei o módulo separado para não vender 'ping mágico'." if pt else "Old network flags may be ignored by current Roblox and cannot replace a better route. The legacy module stays separate so it is not presented as magic ping.")
        self._module_switch(legacy, "ping_boost", "PACK DE REDE LEGADO (EXPERIMENTAL)" if pt else "LEGACY NETWORK PACK (EXPERIMENTAL)")

        # RESOLUTION
        _, body = self._page_shell("resolution", "RESOLUÇÃO", "Controle separado para tamanho da área do cliente Roblox." if pt else "Separate control for Roblox client-area size.")
        res = self._section_card(body, "1080p / 720p / 480p", "O Roblox removeu/bloqueou a FastFlag usada para forçar resolução interna. Por isso esta opção usa o método disponível sem injeção: ajusta a área/janela do cliente Roblox, sem mudar a resolução do Windows." if pt else "Roblox removed/blocked the FastFlag used to force internal render resolution. This option therefore uses the available non-injection method: resizing the Roblox client area/window without changing Windows resolution.")
        self.resolution_card = res
        self.res_menu = ctk.CTkOptionMenu(res, values=["1920x1080","1600x900","1280x720","854x480","1080x1080","Personalizada" if pt else "Custom"], command=self.selecionar_resolucao, fg_color=t["card_active"], button_color=t["card_active"], button_hover_color=t["hover"], text_color=t["accent"])
        self.res_menu.set(self.resolucao_jogo if self.resolucao_jogo in self.res_menu.cget("values") else "1280x720"); self.res_menu.pack(fill="x", padx=16, pady=(4,8))
        custom = ctk.CTkFrame(res, fg_color="transparent"); custom.pack(fill="x", padx=16, pady=4)
        self.entry_res_w = ctk.CTkEntry(custom, placeholder_text="largura", width=120); self.entry_res_w.insert(0, str(self.custom_width)); self.entry_res_w.pack(side="left", padx=(0,6))
        self.entry_res_h = ctk.CTkEntry(custom, placeholder_text="altura", width=120); self.entry_res_h.insert(0, str(self.custom_height)); self.entry_res_h.pack(side="left", padx=6)
        ctk.CTkButton(res, text="APLICAR NO ROBLOX" if pt else "APPLY TO ROBLOX", command=self.aplicar_resolucao_roblox, fg_color=t["accent"], hover_color=t["hover"], text_color="#050505", height=38).pack(fill="x", padx=16, pady=(10,14))

        # CURSOR
        _, body = self._page_shell("cursor", "CURSOR", "Substitui os assets reais ArrowCursor.png e ArrowFarCursor.png; não usa overlay." if pt else "Replaces the real ArrowCursor.png and ArrowFarCursor.png assets; no overlay.")
        cursor_card = self._section_card(body, "CURSOR PERSONALIZADO" if pt else "CUSTOM CURSOR", "Fundo branco conectado às bordas pode ser removido automaticamente antes da normalização." if pt else "White background connected to image edges can be removed automatically before normalization.")
        self.cursor_card = cursor_card
        self.cursor_menu = ctk.CTkOptionMenu(cursor_card, values=self.listar_cursor_packs(), command=self.evento_cursor_pack, fg_color=t["card_active"], button_color=t["card_active"], button_hover_color=t["hover"], text_color=t["accent"])
        if self.cursor_pack not in self.listar_cursor_packs(): self.cursor_pack = "Roblox Padrão"
        self.cursor_menu.set(self.cursor_pack); self.cursor_menu.pack(fill="x", padx=16, pady=(4,8))
        size_row = ctk.CTkFrame(cursor_card, fg_color="transparent"); size_row.pack(fill="x", padx=16, pady=4)
        self.lbl_cursor_size = ctk.CTkLabel(size_row, text=f"Tamanho visível: {self.cursor_visual_size}px", text_color=t["text"]); self.lbl_cursor_size.pack(side="left")
        self.cursor_size_slider = ctk.CTkSlider(size_row, from_=8, to=48, number_of_steps=40, command=self.evento_cursor_tamanho, progress_color=t["accent"], button_color=t["accent"], button_hover_color=t["hover"])
        self.cursor_size_slider.set(self.cursor_visual_size); self.cursor_size_slider.pack(side="right", fill="x", expand=True, padx=(14,0))
        self.switch_cursor_white = ctk.CTkSwitch(cursor_card, text="REMOVER FUNDO BRANCO AUTOMATICAMENTE" if pt else "AUTO REMOVE WHITE BACKGROUND", command=self.evento_cursor_white_bg, progress_color=t["accent"], fg_color="#44484F", text_color=t["text"])
        self.switch_cursor_white.pack(anchor="w", padx=16, pady=6)
        if self.cursor_auto_remove_white: self.switch_cursor_white.select()
        self.cursor_anchor_menu = ctk.CTkOptionMenu(cursor_card, values=["Ponta no centro","Centro","Preservar 64x64"], command=self.evento_cursor_ancora, fg_color=t["card_active"], button_color=t["card_active"], button_hover_color=t["hover"], text_color=t["accent"])
        self.cursor_anchor_menu.set(self.cursor_anchor_mode); self.cursor_anchor_menu.pack(fill="x", padx=16, pady=6)
        r = ctk.CTkFrame(cursor_card, fg_color="transparent"); r.pack(fill="x", padx=16, pady=6)
        ctk.CTkButton(r, text="IMPORTAR PNG", command=self.importar_cursor_png).pack(side="left", expand=True, fill="x", padx=(0,4))
        ctk.CTkButton(r, text="IMPORTAR PACK", command=self.importar_cursor_pack_pasta).pack(side="left", expand=True, fill="x", padx=(4,0))
        self.btn_apply_cursor = ctk.CTkButton(cursor_card, text="APLICAR CURSOR" if pt else "APPLY CURSOR", command=self.aplicar_cursor_selecionado, fg_color=t["accent"], hover_color=t["hover"], text_color="#050505"); self.btn_apply_cursor.pack(fill="x", padx=16, pady=(8,4))
        self.btn_restore_cursor = ctk.CTkButton(cursor_card, text="RESTAURAR ORIGINAL" if pt else "RESTORE ORIGINAL", command=self.restaurar_cursor_original, fg_color="transparent", border_width=1, border_color=t["accent"], text_color=t["text"]); self.btn_restore_cursor.pack(fill="x", padx=16, pady=(4,8))
        self.lbl_cursor_status = ctk.CTkLabel(cursor_card, text="", text_color=t.get("muted", "gray"), wraplength=820, justify="left"); self.lbl_cursor_status.pack(anchor="w", padx=16, pady=(0,14))

        # FONTS
        _, body = self._page_shell("fonts", "FONTES DO ROBLOX" if pt else "ROBLOX FONTS", "Aplica uma fonte TTF/OTF nos arquivos de texto locais do cliente e preserva os originais em backup." if pt else "Applies a TTF/OTF font to local client text font files and preserves originals in backup.")
        font_card = self._section_card(body, "FONTE PERSONALIZADA" if pt else "CUSTOM FONT", "Arquivos de emoji são preservados para evitar quadrados/símbolos quebrados. Bloxstrap, quando detectado, também recebe a modificação para sobreviver a updates." if pt else "Emoji files are preserved to avoid broken symbols. When Bloxstrap is detected, the modification is mirrored there to survive updates.")
        self.font_card = font_card
        self.lbl_game_font = ctk.CTkLabel(font_card, text=(os.path.basename(self.game_font_source) if self.game_font_source else ("Nenhuma fonte selecionada" if pt else "No font selected")), text_color=t["accent"], font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")); self.lbl_game_font.pack(anchor="w", padx=16, pady=(4,8))
        r = ctk.CTkFrame(font_card, fg_color="transparent"); r.pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(r, text="ESCOLHER .TTF / .OTF" if pt else "CHOOSE .TTF / .OTF", command=self.importar_fonte_jogo).pack(side="left", expand=True, fill="x", padx=(0,4))
        ctk.CTkButton(r, text="APLICAR NO JOGO" if pt else "APPLY IN GAME", command=self.aplicar_fonte_jogo, fg_color=t["accent"], text_color="#050505").pack(side="left", expand=True, fill="x", padx=(4,0))
        ctk.CTkButton(font_card, text="RESTAURAR FONTES ORIGINAIS" if pt else "RESTORE ORIGINAL FONTS", command=self.restaurar_fonte_jogo, fg_color="transparent", border_width=1, border_color=t["accent"], text_color=t["text"]).pack(fill="x", padx=16, pady=(6,14))
        self.lbl_font_status = ctk.CTkLabel(font_card, text="", text_color=t.get("muted", "gray"), wraplength=820, justify="left"); self.lbl_font_status.pack(anchor="w", padx=16, pady=(0,14))

        # COMBO PLANNER v3.5
        _, body = self._page_shell("combo", "COMBO PLANNER", "Salve builds e sequências de combo para consultar depois — sem macro e sem automatizar o jogo." if pt else "Save builds and combo sequences for later — no macros or gameplay automation.")
        hero = self._section_card(body, "SEU ARQUIVO DE COMBOS" if pt else "YOUR COMBO LIBRARY", "Escolha o estilo de luta e a fruta, complete os outros slots como texto livre e escreva a sequência inteira. Os cards ficam salvos localmente no seu PC." if pt else "Choose your fighting style and fruit, complete the other slots as free-form text, and write the full sequence. Cards are saved locally on your PC.")
        self.combo_hero = hero
        top = ctk.CTkFrame(hero, fg_color="transparent"); top.pack(fill="x", padx=16, pady=(3,10))
        ctk.CTkButton(top, text="＋ NOVO COMBO" if pt else "＋ NEW COMBO", command=self.combo_novo, fg_color=t["accent"], hover_color=t["hover"], text_color="#050505", height=42).pack(side="left", expand=True, fill="x", padx=(0,5))
        ctk.CTkButton(top, text="FONTES / CRÉDITOS" if pt else "SOURCES / CREDITS", command=self.combo_abrir_fontes, fg_color=t["card_active"], hover_color=t["hover"], text_color=t["accent"], height=42).pack(side="left", expand=True, fill="x", padx=(5,0))
        ctk.CTkLabel(hero, text=("Fruits e Fighting Styles usam primeiro o pack local integrado ao ZKStrap; quando existe imagem local, nenhuma wiki/API é necessária para a thumbnail." if pt else "Fruits and Fighting Styles use the bundled local pack first; when a local image exists, no wiki/API is needed for the thumbnail."), text_color=t.get("muted","gray"), justify="left", anchor="w", wraplength=900, font=ctk.CTkFont(family="Segoe UI", size=9)).pack(fill="x", padx=16, pady=(0,10))
        catalog=self._combo_catalog()
        self.combo_status_label=ctk.CTkLabel(hero,text=(f"CATÁLOGO PRONTO  •  {len(catalog['style'])} ESTILOS  •  {len(catalog['fruit'])} FRUTAS" if pt else f"CATALOG READY  •  {len(catalog['style'])} STYLES  •  {len(catalog['fruit'])} FRUITS"),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w")
        self.combo_status_label.pack(fill="x",padx=16,pady=(0,14))

        library = self._section_card(body, "COMBOS SALVOS" if pt else "SAVED COMBOS", "Sem limite prático: adicione, edite, duplique ou exclua suas builds." if pt else "No practical limit: add, edit, duplicate or delete your builds.")
        self.combo_library_frame = ctk.CTkFrame(library, fg_color="transparent")
        self.combo_library_frame.pack(fill="x", padx=12, pady=(2,14))
        try:
            self.combo_refresh_library()
        except Exception as e:
            self.log_output(f"[combo] Biblioteca abriu em modo seguro: {e}")
            try: ctk.CTkLabel(self.combo_library_frame,text="Planner carregado em modo seguro. Seus combos continuam salvos.",text_color=t.get("muted","gray")).pack(pady=18)
            except Exception: pass


        # BLOX HUB
        _, body = self._page_shell("bloxhub", "BLOX HUB", "Ferramentas para jogar, treinar e criar conteúdo de Blox Fruits." if pt else "Tools to play, practice and create Blox Fruits content.")
        hub=self._section_card(body,"BLOX HUB // CENTRAL","A central reúne as ferramentas de Blox Fruits sem duplicar toda a navegação na barra lateral." if pt else "This hub gathers Blox Fruits tools without duplicating the entire sidebar navigation.")
        hrow=ctk.CTkFrame(hub,fg_color="transparent"); hrow.pack(fill="x",padx=14,pady=(4,14))
        for label,key in (("BUILD ROULETTE","roulette"),("COMBO PLANNER","combo"),("CREATOR MODE","creator"),("ZK AI / PVP COACH","ai")):
            ctk.CTkButton(hrow,text=label,command=lambda k=key:self.show_page(k,animate=True),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=44).pack(side="left",expand=True,fill="x",padx=4)
        status=ctk.CTkFrame(hub,fg_color="transparent"); status.pack(fill="x",padx=14,pady=(0,14))
        latest=dict(getattr(self,"last_roulette_build",{}) or {})
        active=sum(1 for x in getattr(self,"creator_challenges",[]) if isinstance(x,dict) and not x.get("done"))
        combo_count=len(getattr(self,"combo_entries",[]))
        summaries=[
            ("ÚLTIMA ROLETA" if pt else "LAST ROLL", (" + ".join([str(latest.get(k)) for k in ("style","fruit","sword","gun") if latest.get(k)])) if any(latest.get(k) for k in ("style","fruit","sword","gun")) else ("Nenhuma ainda" if pt else "None yet")),
            ("DESAFIOS ATIVOS" if pt else "ACTIVE CHALLENGES", str(active)),
            ("DESAFIOS CONCLUÍDOS" if pt else "COMPLETED CHALLENGES", str(int(getattr(self,"creator_total_completed",0) or 0))),
            ("COMBOS SALVOS" if pt else "SAVED COMBOS", str(combo_count)),
        ]
        for title_txt,value_txt in summaries:
            box=ctk.CTkFrame(status,fg_color=t["card_active"],corner_radius=10); box.pack(side="left",expand=True,fill="x",padx=4)
            ctk.CTkLabel(box,text=title_txt,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(anchor="w",padx=10,pady=(9,2))
            ctk.CTkLabel(box,text=value_txt,text_color=t["text"],font=ctk.CTkFont(size=10,weight="bold"),wraplength=180,justify="left").pack(anchor="w",padx=10,pady=(0,9))

        # BUILD ROULETTE — v3.16 visual rework, mantendo os 4 slots completos.
        _, body = self._page_shell("roulette", "BUILD ROULETTE", "Fighting Style + Fruit + Sword + Gun. Tudo local, visual e pronto para alimentar os desafios do Creator Mode." if pt else "Fighting Style + Fruit + Sword + Gun. Local catalogs with Creator Mode integration.")
        rcard=self._section_card(body,"RANDOM BUILD ENGINE","A build inteira é decidida primeiro e revelada em sequência. Nenhum slot foi removido: Style → Fruit → Sword → Gun." if pt else "The whole build is decided first and then revealed: Style → Fruit → Sword → Gun.")
        self.roulette_slots={}
        topbar=ctk.CTkFrame(rcard,fg_color=t["card_active"],corner_radius=12,border_width=1,border_color=t["border"]); topbar.pack(fill="x",padx=14,pady=(5,10))
        left=ctk.CTkFrame(topbar,fg_color="transparent"); left.pack(side="left",fill="x",expand=True,padx=12,pady=9)
        ctk.CTkLabel(left,text="BUILD ROULETTE // 4-SLOT",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left,text="Ícones locais • histórico • favoritos • inventário por categoria",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8)).pack(anchor="w",pady=(2,0))
        modewrap=ctk.CTkFrame(topbar,fg_color="transparent"); modewrap.pack(side="right",padx=12,pady=9)
        ctk.CTkLabel(modewrap,text="MODO",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(anchor="e")
        self.roulette_mode=ctk.CTkOptionMenu(modewrap,values=["ALEATÓRIO TOTAL","RARIDADE BAIXA"],fg_color=t["card"],button_color=t["accent"],text_color=t["text"],width=185); self.roulette_mode.set("ALEATÓRIO TOTAL"); self.roulette_mode.pack(pady=(3,0))
        rr=ctk.CTkFrame(rcard,fg_color="transparent"); rr.pack(fill="x",padx=14,pady=(2,10))
        for i,(cat,label) in enumerate((("style","FIGHTING STYLE"),("fruit","FRUIT"),("sword","SWORD"),("gun","GUN"))):
            rr.grid_columnconfigure(i%2,weight=1,uniform="roulette")
            box=ctk.CTkFrame(rr,fg_color=t["card_active"],corner_radius=16,border_width=1,border_color=t["border"]); box.grid(row=i//2,column=i%2,sticky="nsew",padx=6,pady=6)
            head=ctk.CTkFrame(box,fg_color="transparent"); head.pack(fill="x",padx=12,pady=(10,2))
            ctk.CTkLabel(head,text=f"0{i+1}",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")
            ctk.CTkLabel(head,text=label,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="right")
            inner=ctk.CTkFrame(box,fg_color=t["card"],corner_radius=13); inner.pack(fill="x",padx=10,pady=(4,8))
            img=ctk.CTkLabel(inner,text="?",width=112,height=112,text_color=t["accent"],font=ctk.CTkFont(size=32,weight="bold")); img.pack(pady=(8,2))
            name=ctk.CTkLabel(inner,text="—",text_color=t["text"],font=ctk.CTkFont(size=13,weight="bold"),wraplength=330); name.pack(pady=(2,10))
            self.roulette_slots[cat]=(img,name)
        actionhero=ctk.CTkFrame(rcard,fg_color=t["card_active"],corner_radius=12); actionhero.pack(fill="x",padx=14,pady=(2,8))
        ctk.CTkLabel(actionhero,text="SORTEIE UMA BUILD COMPLETA",text_color=t["text"],font=ctk.CTkFont(size=12,weight="bold")).pack(anchor="w",padx=12,pady=(9,2))
        ctk.CTkLabel(actionhero,text="Os desafios do Creator Mode ficam mais interessantes usando o resultado daqui, mas continuam funcionando com qualquer build.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),wraplength=820,justify="left").pack(anchor="w",padx=12,pady=(0,8))
        rbtns=ctk.CTkFrame(actionhero,fg_color="transparent"); rbtns.pack(fill="x",padx=10,pady=(0,10))
        ctk.CTkButton(rbtns,text="🎲  SORTEAR BUILD" if pt else "🎲  ROLL BUILD",command=self.roulette_start,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=48,font=ctk.CTkFont(size=11,weight="bold")).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(rbtns,text="INVENTÁRIO" if pt else "INVENTORY",command=self.roulette_inventory_dialog,fg_color=t["card"],hover_color=t["hover"],text_color=t["accent"],height=48).pack(side="left",expand=True,fill="x",padx=4)
        ctk.CTkButton(rbtns,text="FAVORITAR" if pt else "FAVORITE",command=self.roulette_favorite_current,fg_color=t["card"],hover_color=t["hover"],text_color=t["text"],height=48).pack(side="left",expand=True,fill="x",padx=(4,0))
        ract=ctk.CTkFrame(rcard,fg_color="transparent"); ract.pack(fill="x",padx=14,pady=(0,12))
        ctk.CTkButton(ract,text="SALVAR NO COMBO PLANNER" if pt else "SAVE TO COMBO PLANNER",command=self.roulette_save_to_combo,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=40).pack(side="left",expand=True,fill="x",padx=(0,4))
        ctk.CTkButton(ract,text="USAR NOS DESAFIOS" if pt else "USE IN CHALLENGES",command=self.roulette_create_challenge,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],height=40).pack(side="left",expand=True,fill="x",padx=(4,0))
        self.roulette_history_frame=self._section_card(body,"HISTÓRICO DA ROLETA" if pt else "ROULETTE HISTORY")
        self.roulette_refresh_history()

        # CREATOR MODE — v3.16 focado somente em desafios.
        _, body = self._page_shell("creator", "CREATOR CHALLENGES", "Desafios de PvP com progresso manual, raridade SECRET e histórico persistente." if pt else "PvP challenges with manual progress, rare SECRET drops and persistent history.")
        guide=self._section_card(body,"COMO USAR","Os desafios funcionam com qualquer build, mas ficam mais dinâmicos quando você usa uma build aleatória da Build Roulette. Gere 1, 2, 3, 4 ou 5 desafios e acompanhe tudo manualmente." if pt else "Challenges work with any build, but random Roulette builds make them more dynamic.")
        grow=ctk.CTkFrame(guide,fg_color="transparent"); grow.pack(fill="x",padx=14,pady=(4,12))
        ctk.CTkButton(grow,text="IR PARA BUILD ROULETTE",command=lambda:self.show_page("roulette",animate=True),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38).pack(side="left",padx=(0,6))
        ctk.CTkLabel(grow,text="SECRET pode aparecer raramente em qualquer geração. Cada secreto tem identidade própria e pode esconder uma recompensa.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),wraplength=650,justify="left",anchor="w").pack(side="left",fill="x",expand=True,padx=6)
        stats=ctk.CTkFrame(guide,fg_color="transparent"); stats.pack(fill="x",padx=10,pady=(0,12))
        for title_txt,value_fn in [("CONCLUÍDOS",lambda:str(int(getattr(self,'creator_total_completed',0)))), ("PARTY",lambda:f"{min(5,int(getattr(self,'creator_total_completed',0)))}/5"), ("HISTÓRICO",lambda:str(len(getattr(self,'creator_history',[]))))]:
            sb=ctk.CTkFrame(stats,fg_color=t["card_active"],corner_radius=10); sb.pack(side="left",expand=True,fill="x",padx=4)
            ctk.CTkLabel(sb,text=title_txt,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(anchor="w",padx=10,pady=(8,1))
            ctk.CTkLabel(sb,text=value_fn(),text_color=t["accent"],font=ctk.CTkFont(size=16,weight="bold")).pack(anchor="w",padx=10,pady=(0,8))
        challenges=self._section_card(body,"DESAFIOS ATIVOS" if pt else "ACTIVE CHALLENGES","Escolha dificuldade e quantidade. Trocas são limitadas a 2 por desafio. Winstreak/killstreak só contam contra players de 5M+; 2.5M não conta." if pt else "Choose difficulty and quantity. Each challenge can be rerolled only twice.")
        cr=ctk.CTkFrame(challenges,fg_color="transparent"); cr.pack(fill="x",padx=16,pady=(4,10))
        self.creator_diff=ctk.CTkOptionMenu(cr,values=["Fácil","Médio","Difícil","Insano","Misturar"],fg_color=t["card_active"],button_color=t["accent"]); self.creator_diff.set("Médio"); self.creator_diff.pack(side="left",expand=True,fill="x",padx=(0,4))
        self.creator_count=ctk.CTkOptionMenu(cr,values=["1","2","3","4","5"],fg_color=t["card_active"],button_color=t["accent"]); self.creator_count.set("3"); self.creator_count.pack(side="left",padx=4)
        ctk.CTkButton(cr,text="GERAR DESAFIOS" if pt else "GENERATE CHALLENGES",command=self.creator_generate_challenges,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=40).pack(side="left",padx=(4,0))
        self.creator_challenge_frame=ctk.CTkFrame(challenges,fg_color="transparent"); self.creator_challenge_frame.pack(fill="x",padx=12,pady=(2,14))
        self.creator_refresh_challenges()
        hist=self._section_card(body,"HISTÓRICO DE DESAFIOS" if pt else "CHALLENGE HISTORY","Concluídos ficam salvos aqui. Desafios ativos não são salvos e desaparecem ao fechar o ZKStrap." if pt else "Completed challenges stay here; active challenges disappear when ZKStrap closes.")
        self.creator_history_frame=ctk.CTkFrame(hist,fg_color="transparent"); self.creator_history_frame.pack(fill="x",padx=12,pady=(2,14))
        self.creator_refresh_history()

        # SETUPS
        _, body = self._page_shell("setups", "SETUPS", "Salve até 5 combinações locais e aplique com snapshot automático." if pt else "Save up to 5 local combinations and apply them with an automatic snapshot.")
        builtin=self._section_card(body,"SETUPS PRONTOS" if pt else "BUILT-IN SETUPS")
        sr=ctk.CTkFrame(builtin,fg_color="transparent"); sr.pack(fill="x",padx=14,pady=(4,14))
        ctk.CTkButton(sr,text="FPS MÁXIMO",command=lambda:self.apply_builtin_setup("fps_max"),fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=44).pack(side="left",expand=True,fill="x",padx=(0,5))
        ctk.CTkButton(sr,text="PC FRACO",command=lambda:self.apply_builtin_setup("weak_pc"),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=44).pack(side="left",expand=True,fill="x",padx=(5,0))
        self.setup_edit_banner=ctk.CTkLabel(body,text="",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")); self.setup_edit_banner.pack(fill="x",padx=16,pady=(2,2))
        self.setup_edit_controls=ctk.CTkFrame(body,fg_color="transparent")
        self.setup_edit_save_btn=ctk.CTkButton(self.setup_edit_controls,text="SALVAR ALTERAÇÕES",command=self.save_current_setup_edits,fg_color=t["accent"],text_color="#050505")
        self.setup_edit_save_btn.pack(side="left",expand=True,fill="x",padx=(0,4))
        self.setup_edit_cancel_btn=ctk.CTkButton(self.setup_edit_controls,text="PARAR DE EDITAR",command=self.cancel_setup_edit,fg_color=t["card_active"],text_color=t["text"]); self.setup_edit_cancel_btn.pack(side="left",expand=True,fill="x",padx=(4,0))
        saved=self._section_card(body,"MEUS SETUPS" if pt else "MY SETUPS","Monte sua configuração no app e clique em SALVAR COMO SETUP. Ao editar, o topo deixa claro qual setup está recebendo as alterações." if pt else "Configure the app and click SAVE AS SETUP. Edit mode clearly shows which setup is receiving changes.")
        ctk.CTkButton(saved,text="＋ SALVAR COMO SETUP" if pt else "＋ SAVE AS SETUP",command=self.save_current_as_setup,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=42).pack(fill="x",padx=14,pady=(4,10))
        self.setups_list_frame=ctk.CTkFrame(saved,fg_color="transparent"); self.setups_list_frame.pack(fill="x",padx=10,pady=(0,12))
        self.refresh_setups_page(); self._refresh_setup_edit_indicator()

        # SPOTIFY / NOW PLAYING DECK — v3.15.8
        _, body = self._page_shell(
            "spotify",
            "SPOTIFY / MÍDIA" if pt else "SPOTIFY / MEDIA",
            "Now Playing do Windows — sem login, Client ID, OAuth, API ou Premium." if pt else "Windows Now Playing — no login, Client ID, OAuth, API or Premium."
        )

        try: body.configure(fg_color="#121212",scrollbar_button_color="#1ED760",scrollbar_button_hover_color="#18B84F")
        except Exception: pass
        self._spotify_brand_header(body)
        hero=self._spotify_section_card(
            body,
            "NOW PLAYING // LOCAL",
            "Procura a sessão do Spotify no Windows. Spotify Desktop é identificado diretamente. No navegador, o ZKStrap aceita a sessão quando o Windows marca como MÚSICA, quando há metadata musical completa (título + artista + álbum) ou quando a janela confirma Spotify; sessões de VÍDEO continuam bloqueadas."
            if pt else
            "Targets Spotify specifically. Browser MUSIC sessions are preferred and VIDEO sessions are rejected so YouTube is never controlled by mistake."
        )
        deck=ctk.CTkFrame(hero,fg_color="#181818",corner_radius=14,border_width=1,border_color="#2D2D2D"); deck.pack(fill="x",padx=16,pady=(8,10))
        artbox=ctk.CTkFrame(deck,width=156,height=156,fg_color="#242424",corner_radius=12); artbox.pack(side="left",padx=12,pady=12); artbox.pack_propagate(False)
        self.spotify_art_label=ctk.CTkLabel(artbox,text="♫",text_color="#1ED760",font=ctk.CTkFont(size=42,weight="bold")); self.spotify_art_label.pack(fill="both",expand=True)
        meta=ctk.CTkFrame(deck,fg_color="transparent"); meta.pack(side="left",fill="both",expand=True,padx=(6,12),pady=12)
        self.spotify_source_label=ctk.CTkLabel(meta,text="SESSÃO DE MÍDIA",text_color="#1ED760",font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w"); self.spotify_source_label.pack(fill="x",pady=(2,5))
        self.spotify_title_label=ctk.CTkLabel(meta,text="Nenhuma música detectada" if pt else "No media detected",text_color="#FFFFFF",font=ctk.CTkFont(size=21,weight="bold"),anchor="w",justify="left",wraplength=600); self.spotify_title_label.pack(fill="x")
        self.spotify_artist_label=ctk.CTkLabel(meta,text="Abra o Spotify e dê play em uma música." if pt else "Open Spotify and start a track.",text_color="#B3B3B3",font=ctk.CTkFont(size=11),anchor="w",justify="left",wraplength=600); self.spotify_artist_label.pack(fill="x",pady=(3,1))
        self.spotify_album_label=ctk.CTkLabel(meta,text="",text_color="#B3B3B3",font=ctk.CTkFont(family="Consolas",size=8),anchor="w"); self.spotify_album_label.pack(fill="x",pady=(0,8))
        self.spotify_progress=ctk.CTkProgressBar(meta,height=8,corner_radius=8,progress_color="#1ED760",fg_color="#333333"); self.spotify_progress.pack(fill="x",pady=(6,2)); self.spotify_progress.set(0)
        timeline=ctk.CTkFrame(meta,fg_color="transparent"); timeline.pack(fill="x")
        self.spotify_time_label=ctk.CTkLabel(timeline,text="0:00",text_color="#B3B3B3",font=ctk.CTkFont(family="Consolas",size=8)); self.spotify_time_label.pack(side="left")
        self.spotify_duration_label=ctk.CTkLabel(timeline,text="0:00",text_color="#B3B3B3",font=ctk.CTkFont(family="Consolas",size=8)); self.spotify_duration_label.pack(side="right")

        self.spotify_status_label=ctk.CTkLabel(hero,text="Status: procurando sessão de mídia…" if pt else "Status: looking for media session…",text_color="#B3B3B3",font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),anchor="w",justify="left",wraplength=840); self.spotify_status_label.pack(fill="x",padx=16,pady=(0,8))

        controls=self._spotify_section_card(body,"PLAYBACK // WINDOWS","Controles enviados DIRETAMENTE à sessão do Spotify detectada pelo Windows. YouTube e outros players são ignorados; não existe fallback de playback por tecla global." if pt else "Controls target the Spotify session directly. YouTube and other players are ignored; playback never falls back to global media keys.")
        row=ctk.CTkFrame(controls,fg_color="transparent"); row.pack(fill="x",padx=16,pady=(6,8))
        for lab,cmd in (("⏮  ANTERIOR" if pt else "⏮  PREVIOUS","previous"),("▶ / ⏸  PLAY / PAUSE","toggle"),("PRÓXIMA  ⏭" if pt else "NEXT  ⏭","next")):
            ctk.CTkButton(row,text=lab,command=lambda c=cmd:self.spotify_local_command(c),fg_color="#242424",hover_color="#303030",text_color="#1ED760",height=48).pack(side="left",expand=True,fill="x",padx=4)
        action=ctk.CTkFrame(controls,fg_color="transparent"); action.pack(fill="x",padx=16,pady=(0,12))
        ctk.CTkButton(action,text="ABRIR APP" if pt else "OPEN APP",command=self.spotify_open_app,fg_color="#1ED760",hover_color="#1FDF64",text_color="#050505",height=36).pack(side="left",expand=True,fill="x",padx=(4,4))
        ctk.CTkButton(action,text="ABRIR WEB" if pt else "OPEN WEB",command=lambda:webbrowser.open("https://open.spotify.com"),fg_color="#242424",hover_color="#303030",text_color="#1ED760",height=36).pack(side="left",expand=True,fill="x",padx=4)
        ctk.CTkButton(action,text="ATUALIZAR",command=self.spotify_poll_now,fg_color="transparent",border_width=1,border_color="#343434",hover_color="#242424",text_color="#FFFFFF",height=36).pack(side="left",expand=True,fill="x",padx=4)
        ctk.CTkButton(action,text="MINI-PLAYER",command=lambda:self._spotify_show_mini(True),fg_color="transparent",border_width=1,border_color="#343434",hover_color="#242424",text_color="#1ED760",height=36).pack(side="left",expand=True,fill="x",padx=(4,4))

        browse=self._spotify_section_card(body,"NAVEGAR // SPOTIFY WEB" if pt else "BROWSE // SPOTIFY WEB","Pesquise pelo ZKStrap e abra o resultado direto no Spotify. A navegação completa continua no player oficial, porque esta versão não usa a API da sua conta." if pt else "Search from ZKStrap and open the result directly in Spotify. Full browsing stays in the official player because this version does not use your account API.")
        br=ctk.CTkFrame(browse,fg_color="transparent"); br.pack(fill="x",padx=16,pady=(6,12))
        self.spotify_search_entry=ctk.CTkEntry(br,placeholder_text="Música, artista ou álbum…" if pt else "Song, artist or album…",height=40,fg_color="#242424",border_color="#343434",text_color="#FFFFFF",placeholder_text_color="#8C8C8C"); self.spotify_search_entry.pack(side="left",fill="x",expand=True,padx=(0,6)); self.spotify_search_entry.bind("<Return>",lambda e:self.spotify_search_web())
        ctk.CTkButton(br,text="PESQUISAR" if pt else "SEARCH",command=self.spotify_search_web,fg_color="#1ED760",hover_color="#1FDF64",text_color="#050505",width=150,height=40).pack(side="right")

        volume=self._spotify_section_card(
            body,
            "VOLUME DO SPOTIFY" if pt else "SPOTIFY VOLUME",
            "Controla somente a sessão de áudio do Spotify Desktop. Nunca altera o volume geral do Windows nem o áudio do YouTube. No Spotify Web, o controle só é liberado se o Windows expuser uma sessão de áudio identificável como Spotify."
            if pt else
            "Controls only the Spotify Desktop audio session. It never changes Windows master volume or YouTube audio. On Spotify Web, volume is enabled only when Windows exposes an audio session identifiable as Spotify."
        )
        vh=ctk.CTkFrame(volume,fg_color="transparent"); vh.pack(fill="x",padx=16,pady=(6,3))
        self.spotify_volume_state_label=ctk.CTkLabel(vh,text="SPOTIFY • verificando volume…" if pt else "SPOTIFY • checking volume…",text_color="#1ED760",font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),anchor="w")
        self.spotify_volume_state_label.pack(side="left",fill="x",expand=True)
        self.spotify_volume_value_label=ctk.CTkLabel(vh,text="—",text_color="#FFFFFF",font=ctk.CTkFont(family="Consolas",size=10,weight="bold"))
        self.spotify_volume_value_label.pack(side="right")
        self.spotify_volume_slider=ctk.CTkSlider(volume,from_=0,to=100,number_of_steps=100,command=self._spotify_volume_preview,progress_color="#1ED760",button_color="#1ED760",button_hover_color="#1FDF64",fg_color="#343434",height=18)
        self.spotify_volume_slider.pack(fill="x",padx=20,pady=(8,8)); self.spotify_volume_slider.set(100)
        try:self.spotify_volume_slider.bind("<ButtonRelease-1>",lambda e:self._spotify_volume_apply_slider())
        except Exception:pass
        webrow=ctk.CTkFrame(volume,fg_color="transparent"); webrow.pack(fill="x",padx=16,pady=(2,10))
        self.spotify_web_volume_switch=ctk.CTkSwitch(webrow,text="PERMITIR VOLUME NO SPOTIFY WEB (pode afetar outras abas do navegador)" if pt else "ALLOW SPOTIFY WEB VOLUME (may affect other browser tabs)",command=self._spotify_toggle_web_volume,progress_color="#1ED760",fg_color="#3A3A3A",text_color="#B3B3B3")
        self.spotify_web_volume_switch.pack(side="left")
        if bool(getattr(self,"spotify_web_volume_optin",False)): self.spotify_web_volume_switch.select()
        vr=ctk.CTkFrame(volume,fg_color="transparent"); vr.pack(fill="x",padx=16,pady=(0,14))
        for lab,cmd in (("🔇  MUTE","spotify_mute"),("−  5%","spotify_volume_down"),("＋  5%","spotify_volume_up")):
            ctk.CTkButton(vr,text=lab,command=lambda c=cmd:self.spotify_local_command(c),fg_color="#242424",hover_color="#303030",text_color="#FFFFFF",height=40).pack(side="left",expand=True,fill="x",padx=4)

        info=self._spotify_section_card(body,"COMPATIBILIDADE" if pt else "COMPATIBILITY")
        guide=(
            "• Spotify Desktop: metadata e capa vêm da sessão de mídia do Windows.\n"
            "• Spotify Web: funciona quando Chrome/Edge publica a aba no controle multimídia do Windows; a janela ativa com Spotify também serve como confirmação.\n"
            "• Playback mira a sessão selecionada do Spotify; sessões de vídeo continuam rejeitadas.\n"
            "• Volume exclusivo é garantido no Spotify Desktop. No Web, o switch opcional controla o processo do navegador e pode afetar outras abas.\n"
            "• Sem Premium • sem conta Developer • sem Client ID • sem callback."
            if pt else
            "• Spotify Desktop: metadata and artwork come from the Windows media session.\n"
            "• Spotify Web: works when Chrome/Edge exposes the tab to Windows media controls.\n"
            "• If another player becomes the active session, ZKStrap may show it; pause it and refresh.\n"
            "• No Premium • no Developer account • no Client ID • no callback."
        )
        ctk.CTkLabel(info,text=guide,text_color="#FFFFFF",justify="left",anchor="w",wraplength=840).pack(fill="x",padx=16,pady=(6,14))
        self.spotify_now_label=ctk.CTkLabel(info,text="",text_color="#B3B3B3",font=ctk.CTkFont(family="Consolas",size=8),anchor="w",wraplength=840,justify="left"); self.spotify_now_label.pack(fill="x",padx=16,pady=(0,12))
        self.after(180,self.spotify_poll_now)

        # ZK ASSIST v3.16 — help center simplificado.
        _, body = self._page_shell(
            "ai", "ZK ASSIST",
            "Diga o que você quer fazer ou escolha uma categoria. O assistente lê o estado atual do app e leva você direto ao lugar certo." if pt else "Tell ZK Assist what you want to do or choose a category."
        )
        hero = self._section_card(
            body,
            "✦  ASSISTENTE DO ZKSTRAP" if pt else "✦  ZKSTRAP ASSISTANT",
            "Sem menus gigantes: pesquise uma função, rode um diagnóstico rápido ou escolha uma das áreas abaixo. Tudo funciona localmente, sem IA generativa." if pt else "Search a function, run a quick diagnostic or choose an area below. Everything works locally."
        )
        self.zkai_hero=hero
        searchrow=ctk.CTkFrame(hero,fg_color="transparent"); searchrow.pack(fill="x",padx=16,pady=(5,8))
        self.zkai_search_entry=ctk.CTkEntry(searchrow,placeholder_text="Ex.: cursor não aplica, melhorar FPS, trocar tema, achar Roblox..." if pt else "Example: cursor not applying, improve FPS, change theme...",height=42)
        self.zkai_search_entry.pack(side="left",fill="x",expand=True,padx=(0,6)); self.zkai_search_entry.bind("<Return>",lambda e:self._zkassist_search())
        ctk.CTkButton(searchrow,text="BUSCAR AJUDA" if pt else "SEARCH HELP",command=self._zkassist_search,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=42,width=150).pack(side="right")
        quick=ctk.CTkFrame(hero,fg_color=t.get("icon_bg",t["card"]),corner_radius=10,border_width=1,border_color=t["card_active"]); quick.pack(fill="x",padx=16,pady=(0,10))
        ctk.CTkLabel(quick,text="DIAGNÓSTICO RÁPIDO",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left",padx=12,pady=9)
        ctk.CTkLabel(quick,text="Roblox • pasta • flags • watchdog • tema",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8)).pack(side="left",padx=4,pady=9)
        ctk.CTkButton(quick,text="ANALISAR AGORA",command=lambda:self._zkdialog_topic_click("app:status"),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],height=30).pack(side="right",padx=9,pady=6)
        self.zkai_mode_label=ctk.CTkLabel(hero,text="MODO // ASSISTENTE LOCAL",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w"); self.zkai_mode_label.pack(fill="x",padx=16,pady=(0,1))
        self.zkai_context_label=ctk.CTkLabel(hero,text="Lê sua configuração atual • não altera nada sem você clicar",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w"); self.zkai_context_label.pack(fill="x",padx=16,pady=(0,10))

        topic_card=self._section_card(body,"O QUE VOCÊ QUER RESOLVER?" if pt else "WHAT DO YOU WANT TO SOLVE?","Escolha uma área. Depois o assistente mostra só as opções que fazem sentido." if pt else "Choose an area and only relevant actions will be shown.")
        self.zkai_topic_frame=ctk.CTkFrame(topic_card,fg_color="transparent"); self.zkai_topic_frame.pack(fill="x",padx=12,pady=(2,12))

        chat_card=self._section_card(body,"RESPOSTA / PRÓXIMO PASSO" if pt else "ANSWER / NEXT STEP","Você pode voltar às categorias a qualquer momento. Os botões abaixo levam direto à configuração certa." if pt else "Buttons take you directly to the correct setting.")
        self.zkai_chat_frame=ctk.CTkFrame(chat_card,fg_color=t.get("panel",t["card"]),corner_radius=10,border_width=1,border_color=t["card_active"]); self.zkai_chat_frame.pack(fill="x",padx=14,pady=(4,8))
        self.zkai_options_frame=ctk.CTkFrame(chat_card,fg_color="transparent"); self.zkai_options_frame.pack(fill="x",padx=14,pady=(0,14))
        locked=ctk.CTkFrame(body,fg_color=t["card"],corner_radius=10,border_width=1,border_color=t["border"]); locked.pack(fill="x",padx=16,pady=(4,10))
        ctk.CTkLabel(locked,text="🔒  PvP Coach / IA livre ainda está em desenvolvimento. Esta aba é o Assistente do app e já funciona completa.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),wraplength=900).pack(anchor="w",padx=12,pady=8)
        self._zkai_refresh_mode_ui(render=True)

        # THEME / CUSTOMIZE
        _, body = self._page_shell("theme", "PERSONALIZAR ZKSTRAP" if pt else "CUSTOMIZE ZKSTRAP", "Temas especiais usam banner próprio no topo; o restante do app permanece limpo, alinhado e consistente." if pt else "Special themes use their own top banner while the rest of the app stays clean, aligned and consistent.")
        theme_card = self._section_card(body, "GALERIA DE TEMAS" if pt else "THEME GALLERY", "Temas Core mantêm a identidade do ZKStrap. Nos especiais, a arte do jogo fica concentrada no banner superior e os cards continuam organizados." if pt else "Core themes keep ZKStrap's identity. Special themes keep game artwork inside the top banner while cards stay organized.")
        self.theme_menu = None; self.theme_preview_buttons = {}
        tabs=ctk.CTkTabview(theme_card,fg_color="transparent",segmented_button_fg_color=t["card_active"],segmented_button_selected_color=t["accent"],segmented_button_selected_hover_color=t["hover"],segmented_button_unselected_color=t["card"])
        tabs.pack(fill="x",padx=12,pady=(2,8))
        tab_core=tabs.add("ZKStrap / Core")
        tab_special=tabs.add("Temas Especiais" if pt else "Special Themes")
        tab_secret=tabs.add("Temas Secretos" if pt else "Secret Themes")

        def add_theme_grid(parent,names):
            grid=ctk.CTkFrame(parent,fg_color="transparent"); grid.pack(fill="x",padx=8,pady=8)
            grid.grid_columnconfigure(0,weight=1,uniform="core_col"); grid.grid_columnconfigure(1,weight=1,uniform="core_col")
            for i,name in enumerate(names):
                tt=TEMAS[name]; ss=self._theme_style(name); dd=THEME_DECOR.get(name,THEME_DECOR["Clean"]); selected=name==self.tema_atual
                tile=ctk.CTkFrame(grid,fg_color=tt["panel"],corner_radius=max(8,ss["card_radius"]),border_width=2 if selected else 1,border_color=tt["accent"] if selected else tt["card_active"])
                tile.grid(row=i//2,column=i%2,sticky="nsew",padx=8,pady=8)
                head=ctk.CTkFrame(tile,height=54,fg_color="transparent"); head.pack(fill="x",padx=12,pady=(9,2)); head.pack_propagate(False)
                ctk.CTkLabel(head,text=name,text_color=tt["text"],font=ctk.CTkFont(family="Segoe UI",size=13,weight="bold"),anchor="w").pack(anchor="w")
                ctk.CTkLabel(head,text=dd["tag"],text_color=tt["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w").pack(anchor="w",pady=(2,0))
                scene=ctk.CTkFrame(tile,height=118,fg_color=tt["panel"],corner_radius=max(6,ss["nav_radius"]),border_width=0); scene.pack(fill="x",padx=9,pady=(0,6)); scene.pack_propagate(False)
                cv=Canvas(scene,bg=tt["panel"],highlightthickness=0,bd=0,cursor="hand2"); cv.place(x=0,y=0,relwidth=1,relheight=1); cv._zk_preview=True; cv._zk_preview_hover=False; cv._zk_preview_tile=tile; self.special_theme_preview_canvases.append((cv,name)); self._bind_theme_canvas(cv,name,zone="gallery"); cv.bind("<Button-1>",lambda e,n=name:self.mudar_tema_interface(n))
                ctk.CTkLabel(head,text="HOVER  //  LIVE",text_color=tt.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=6,weight="bold")).place(relx=1.0,rely=.15,anchor="ne")
                b=ctk.CTkButton(tile,text=("ATIVO ✓" if selected else "APLICAR ATMOSFERA") if pt else ("ACTIVE ✓" if selected else "APPLY ATMOSPHERE"),height=36,corner_radius=max(7,ss["nav_radius"]),fg_color=tt["accent"] if selected else tt["card_active"],hover_color=tt["hover"],text_color="#07080A" if selected else tt["text"],font=ctk.CTkFont(size=10,weight="bold"),command=lambda n=name:self.mudar_tema_interface(n)); b.pack(fill="x",padx=10,pady=(0,10)); self.theme_preview_buttons[name]=b

        def add_special_theme_gallery(parent,names):
            intro=ctk.CTkFrame(parent,fg_color="transparent"); intro.pack(fill="x",padx=10,pady=(10,6))
            ctk.CTkLabel(intro,text="SPECIAL THEMES  //  GAME PACKS",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(anchor="w")
            ctk.CTkLabel(intro,text="Arte confinada dentro do banner e dos cards. Nada atravessa header, sidebar ou texto." if pt else "Artwork stays inside banners and cards. Nothing crosses headers, sidebar or text.",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Segoe UI",size=9),wraplength=980,justify="left").pack(anchor="w",pady=(3,7))
            grid=ctk.CTkFrame(parent,fg_color="transparent"); grid.pack(fill="x",padx=8,pady=(0,10))
            grid.grid_columnconfigure(0,weight=1,uniform="special_col"); grid.grid_columnconfigure(1,weight=1,uniform="special_col")
            for i,name in enumerate(names):
                tt=TEMAS[name]; selected=name==self.tema_atual; dd=THEME_DECOR.get(name,THEME_DECOR["Clean"]); ss=self._theme_style(name)
                tile=ctk.CTkFrame(grid,fg_color=tt["panel"],corner_radius=max(9,ss["card_radius"]),border_width=2 if selected else 1,border_color=tt["accent"] if selected else tt["card_active"])
                tile.grid(row=i//2,column=i%2,sticky="nsew",padx=9,pady=9)
                head=ctk.CTkFrame(tile,height=54,fg_color="transparent"); head.pack(fill="x",padx=12,pady=(10,2)); head.pack_propagate(False)
                ctk.CTkLabel(head,text=name,text_color=tt["text"],font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold"),anchor="w").pack(anchor="w")
                ctk.CTkLabel(head,text=dd["tag"],text_color=tt["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w").pack(anchor="w",pady=(3,0))
                scene=ctk.CTkFrame(tile,height=166,fg_color=tt["bg"],corner_radius=max(7,ss["card_radius"]),border_width=0); scene.pack(fill="x",padx=10,pady=(1,8)); scene.pack_propagate(False)
                cv=Canvas(scene,bg=tt["bg"],highlightthickness=0,bd=0,cursor="hand2"); cv.place(x=0,y=0,relwidth=1,relheight=1); cv._zk_preview=True; cv._zk_preview_hover=False; cv._zk_preview_tile=tile; self.special_theme_preview_canvases.append((cv,name)); self._bind_theme_canvas(cv,name,zone="gallery"); cv.bind("<Button-1>",lambda e,n=name:self.mudar_tema_interface(n))
                ctk.CTkLabel(head,text="HOVER  //  LIVE",text_color=tt.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=6,weight="bold")).place(relx=1.0,rely=.15,anchor="ne")
                b=ctk.CTkButton(tile,text=("ATIVO ✓" if selected else "APLICAR TEMA") if pt else ("ACTIVE ✓" if selected else "APPLY THEME"),height=38,corner_radius=max(8,ss["nav_radius"]),fg_color=tt["accent"] if selected else tt["card_active"],hover_color=tt["hover"],text_color="#06070A" if selected else tt["text"],font=ctk.CTkFont(size=10,weight="bold"),command=lambda n=name:self.mudar_tema_interface(n)); b.pack(fill="x",padx=10,pady=(0,11)); self.theme_preview_buttons[name]=b

        def add_secret_theme_gallery(parent):
            # v3.17.2 — Secret Vault Alive UI
            # Secret themes now have real live previews and the hint is revealed
            # inside the card itself. This avoids relying on a tooltip bound only
            # to the parent frame (child widgets intercepted the hover before).
            intro=ctk.CTkFrame(parent,fg_color=t.get("panel",t["card"]),corner_radius=14,border_width=1,border_color=t["card_active"])
            intro.pack(fill="x",padx=10,pady=(10,8))
            top=ctk.CTkFrame(intro,fg_color="transparent"); top.pack(fill="x",padx=14,pady=(12,3))
            ctk.CTkLabel(top,text="SECRET VAULT  //  HIDDEN IDENTITIES",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=11,weight="bold")).pack(side="left")
            ctk.CTkLabel(top,text="HOVER LOCKED CARDS",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="right")
            ctk.CTkLabel(intro,text=("Cada identidade é desbloqueada de uma forma diferente. Cards bloqueados escondem a condição real, mas revelam uma pista quando você passa o mouse por qualquer parte deles." if pt else "Every identity unlocks differently. Locked cards hide the real condition, but reveal a hint when you hover anywhere over the card."),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),wraplength=980,justify="left",anchor="w").pack(fill="x",padx=14,pady=(2,9))

            unlocked=set(getattr(self,"unlocked_secret_themes",set()))
            dev_unlock=bool(self._owner_key_valid() and dict(getattr(self,"_owner_state",{}) or {}).get("unlock_all_themes",False))
            shown_unlocked=set(UNLOCKABLE_THEME_NAMES) if dev_unlock else unlocked
            ratio=(len(shown_unlocked)/max(1,len(UNLOCKABLE_THEME_NAMES)))

            progress=ctk.CTkFrame(intro,fg_color=t.get("icon_bg",t["card"]),corner_radius=10,border_width=1,border_color=t["card_active"])
            progress.pack(fill="x",padx=14,pady=(0,12))
            ptxt=ctk.CTkFrame(progress,fg_color="transparent"); ptxt.pack(fill="x",padx=11,pady=(8,2))
            ctk.CTkLabel(ptxt,text=f"VAULT PROGRESS  //  {len(shown_unlocked)}/{len(UNLOCKABLE_THEME_NAMES)}"+("  // OWNER OVERRIDE" if dev_unlock else ""),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="left")
            ctk.CTkLabel(ptxt,text=f"{int(round(ratio*100))}%",text_color=t["text"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(side="right")
            pb=ctk.CTkProgressBar(progress,height=7,corner_radius=4,progress_color=t["accent"],fg_color=t["card"])
            pb.pack(fill="x",padx=11,pady=(2,5)); pb.set(max(0.0,min(1.0,ratio)))
            ctk.CTkLabel(progress,text=f"DESAFIOS CONCLUÍDOS  {int(getattr(self,'creator_total_completed',0))}   •   algumas recompensas vivem fora dos desafios",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7),anchor="w").pack(fill="x",padx=11,pady=(0,8))

            grid=ctk.CTkFrame(parent,fg_color="transparent"); grid.pack(fill="x",padx=8,pady=(0,12))
            grid.grid_columnconfigure(0,weight=1,uniform="secret_col"); grid.grid_columnconfigure(1,weight=1,uniform="secret_col")

            for i,name in enumerate(UNLOCKABLE_THEME_NAMES):
                tt=TEMAS[name]
                unlocked_now=self._owner_secret_theme_unlocked(name)
                selected=name==self.tema_atual
                rule=SECRET_THEME_RULES.get(name,{})
                dd=THEME_DECOR.get(name,{"tag":"SECRET IDENTITY","icon":"✦"})
                ss=self._theme_style(name)

                locked_panel=self._mix_hex(tt["panel"],"#000000",.64)
                locked_card=self._mix_hex(tt["card"],"#000000",.58)
                locked_bg=self._mix_hex(tt["bg"],"#000000",.70)
                border_col=tt["accent"] if (unlocked_now or selected) else self._mix_hex("#050505",tt["accent"],.24)
                tile=ctk.CTkFrame(grid,fg_color=tt["panel"] if unlocked_now else locked_panel,corner_radius=max(12,ss.get("card_radius",14)),border_width=2 if selected else 1,border_color=border_col)
                tile.grid(row=i//2,column=i%2,sticky="nsew",padx=9,pady=9)

                # Header / identity
                head=ctk.CTkFrame(tile,height=58,fg_color="transparent"); head.pack(fill="x",padx=13,pady=(10,3)); head.pack_propagate(False)
                left=ctk.CTkFrame(head,fg_color="transparent"); left.pack(side="left",fill="both",expand=True)
                title_lbl=ctk.CTkLabel(left,text=name,text_color=tt["text"] if unlocked_now else self._mix_hex("#050505",tt["text"],.52),font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold"),anchor="w")
                title_lbl.pack(anchor="w")
                tag_lbl=ctk.CTkLabel(left,text=str(dd.get("tag","SECRET IDENTITY")),text_color=tt["accent"] if unlocked_now else self._mix_hex("#050505",tt["accent"],.42),font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w")
                tag_lbl.pack(anchor="w",pady=(2,0))
                state_text="UNLOCKED" if unlocked_now else "LOCKED // ???"
                state_fg=self._mix_hex(tt["panel"],tt["accent"],.22) if unlocked_now else self._mix_hex(tt["panel"],t["card_active"],.42)
                state_lbl=ctk.CTkLabel(head,text=state_text,fg_color=state_fg,corner_radius=8,text_color=tt["accent"] if unlocked_now else t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),width=96,height=25)
                state_lbl.pack(side="right",anchor="n",pady=2)

                # Large LIVE preview. This was missing from the old secret card layout.
                scene=ctk.CTkFrame(tile,height=172,fg_color=tt["bg"] if unlocked_now else locked_bg,corner_radius=max(8,ss.get("card_radius",12)),border_width=1,border_color=self._mix_hex(tt["border"],tt["accent"],.42 if unlocked_now else .16))
                scene.pack(fill="x",padx=11,pady=(2,8)); scene.pack_propagate(False)
                cv=Canvas(scene,bg=tt["bg"],highlightthickness=0,bd=0,cursor="hand2")
                cv.place(x=0,y=0,relwidth=1,relheight=1)
                cv._zk_preview=True; cv._zk_preview_hover=False; cv._zk_preview_tile=tile; cv._zk_secret_locked=not unlocked_now
                self.special_theme_preview_canvases.append((cv,name))
                self._bind_theme_canvas(cv,name,zone="gallery")
                preview_badge=ctk.CTkLabel(scene,text=("LIVE PREVIEW" if unlocked_now else "SEALED PREVIEW  //  HOVER FOR CLUE"),fg_color=tt["card"],corner_radius=7,text_color=tt["accent"] if unlocked_now else tt.get("muted",t.get("muted","gray")),font=ctk.CTkFont(family="Consolas",size=6,weight="bold"),height=22)
                preview_badge.place(relx=.985,rely=.06,anchor="ne")
                if not unlocked_now:
                    lock_badge=ctk.CTkLabel(scene,text="🔒",fg_color=tt["card"],corner_radius=10,text_color=tt["accent"],font=ctk.CTkFont(size=15,weight="bold"),width=34,height=30)
                    lock_badge.place(relx=.035,rely=.08,anchor="nw")
                else:
                    lock_badge=None
                    cv.bind("<Button-1>",lambda e,n=name:self.mudar_tema_interface(n),add="+")

                # Info / hidden clue panel
                info=ctk.CTkFrame(tile,fg_color=tt["card"] if unlocked_now else locked_card,corner_radius=10,border_width=1,border_color=tt["card_active"] if unlocked_now else self._mix_hex("#050505",tt["accent"],.20))
                info.pack(fill="x",padx=11,pady=(0,8))
                if unlocked_now:
                    info_title=ctk.CTkLabel(info,text="IDENTIDADE DESCOBERTA",text_color=tt["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w")
                    info_title.pack(fill="x",padx=11,pady=(8,1))
                    hint_lbl=ctk.CTkLabel(info,text=rule.get("desc","Tema secreto desbloqueado."),text_color=tt.get("muted","gray"),font=ctk.CTkFont(size=9),wraplength=430,justify="left",anchor="w")
                    hint_lbl.pack(fill="x",padx=11,pady=(1,8))
                else:
                    info_title=ctk.CTkLabel(info,text="PISTA OCULTA  //  PASSE O MOUSE NO CARD",text_color=tt.get("muted",t.get("muted","gray")),font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w")
                    info_title.pack(fill="x",padx=11,pady=(8,1))
                    hint_lbl=ctk.CTkLabel(info,text="A condição continua escondida. Explore o ZKStrap e passe o mouse aqui quando quiser uma pista.",text_color=tt.get("muted",t.get("muted","gray")),font=ctk.CTkFont(size=9),wraplength=430,justify="left",anchor="w")
                    hint_lbl.pack(fill="x",padx=11,pady=(1,8))

                b=ctk.CTkButton(tile,text=(("ATIVO ✓" if selected else "APLICAR TEMA") if pt else ("ACTIVE ✓" if selected else "APPLY THEME")) if unlocked_now else "🔒  TEMA BLOQUEADO",height=39,state="normal" if unlocked_now else "disabled",corner_radius=max(8,ss.get("nav_radius",9)),fg_color=tt["accent"] if selected else (tt["card_active"] if unlocked_now else tt["card"]),hover_color=tt["hover"] if unlocked_now else tt["card"],text_color="#06070A" if selected else (tt["text"] if unlocked_now else tt.get("muted",t.get("muted","gray"))),font=ctk.CTkFont(size=9,weight="bold"),command=lambda n=name:self.mudar_tema_interface(n))
                b.pack(fill="x",padx=11,pady=(0,11)); self.theme_preview_buttons[name]=b

                # Reliable hover: child widgets used to steal <Enter>/<Leave> from the
                # parent frame. Bind the same reveal behavior to every surface and
                # delay hiding slightly so moving between child widgets does not flicker.
                if not unlocked_now:
                    hover_state={"job":None,"active":False}
                    default_title="PISTA OCULTA  //  PASSE O MOUSE NO CARD"
                    default_text="A condição continua escondida. Explore o ZKStrap e passe o mouse aqui quando quiser uma pista."
                    clue=str(rule.get("hint","???"))
                    def reveal_clue(event=None, _tile=tile, _title=info_title, _label=hint_lbl, _tt=tt, _state=hover_state, _clue=clue, _name=name):
                        try:
                            if _state.get("job"):
                                self.after_cancel(_state["job"]); _state["job"]=None
                        except Exception: pass
                        try:
                            first_entry=not bool(_state.get("active",False))
                            _state["active"]=True
                            _tile.configure(border_width=2,border_color=_tt["accent"],fg_color=self._mix_hex(_tt["panel"],"#000000",.38))
                            _title.configure(text="DICA SECRETA  //  SIGNAL FOUND",text_color=_tt["accent"])
                            _label.configure(text=_clue,text_color=_tt["text"])
                            if first_entry:
                                self._play_secret_theme_sound(_name,"hover",.12)
                        except Exception: pass
                    def schedule_hide(event=None, _tile=tile, _title=info_title, _label=hint_lbl, _tt=tt, _state=hover_state, _default_title=default_title, _default_text=default_text):
                        def hide():
                            _state["job"]=None
                            _state["active"]=False
                            try:
                                _tile.configure(border_width=1,border_color=self._mix_hex("#050505",_tt["accent"],.24),fg_color=self._mix_hex(_tt["panel"],"#000000",.64))
                                _title.configure(text=_default_title,text_color=_tt.get("muted",t.get("muted","gray")))
                                _label.configure(text=_default_text,text_color=_tt.get("muted",t.get("muted","gray")))
                            except Exception: pass
                        try:
                            if _state.get("job"): self.after_cancel(_state["job"])
                            _state["job"]=self.after(180,hide)
                        except Exception: hide()
                    hover_widgets=[tile,head,left,title_lbl,tag_lbl,state_lbl,scene,cv,preview_badge,info,info_title,hint_lbl,b]
                    if lock_badge is not None: hover_widgets.append(lock_badge)
                    for hw in hover_widgets:
                        try:
                            hw.bind("<Enter>",reveal_clue,add="+")
                            hw.bind("<Leave>",schedule_hide,add="+")
                        except Exception: pass
        self._secret_theme_tab = tab_secret
        def _refresh_secret_theme_gallery_now():
            try:
                if not getattr(self,"_theme_gallery_built",False):
                    return
                if not self._widget_alive(tab_secret):
                    return
                for child in list(tab_secret.winfo_children()):
                    try: child.destroy()
                    except Exception: pass
                add_secret_theme_gallery(tab_secret)
                try: self.update_idletasks()
                except Exception: pass
            except Exception as e:
                try:self.log_output(f"[!] Falha ao atualizar galeria secreta: {e}")
                except Exception:pass
        self._refresh_secret_theme_gallery = _refresh_secret_theme_gallery_now

        # 3.13.2: a galeria completa é pesada (dezenas de canvases + assets).
        # Ela agora só é construída quando o usuário abre PERSONALIZAR. Isso reduz
        # bastante o tempo de boot e evita a splash ficar aparentemente travada.
        self._theme_gallery_built = False
        core_wait = ctk.CTkLabel(tab_core,text="A galeria será carregada quando esta página for aberta.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9))
        core_wait.pack(pady=24)
        special_wait = ctk.CTkLabel(tab_special,text="Os mundos especiais serão carregados sob demanda.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9))
        special_wait.pack(pady=24)
        secret_wait = ctk.CTkLabel(tab_secret,text="Recompensas secretas serão carregadas junto da galeria.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9))
        secret_wait.pack(pady=24)
        def _build_theme_gallery_once():
            if getattr(self,"_theme_gallery_built",False): return
            self._theme_gallery_built=True
            try: core_wait.destroy()
            except Exception: pass
            try: special_wait.destroy()
            except Exception: pass
            try: secret_wait.destroy()
            except Exception: pass
            add_theme_grid(tab_core,CORE_THEME_NAMES)
            try: self.update_idletasks()
            except Exception: pass
            add_special_theme_gallery(tab_special,[n for n in TEMAS if n in SPECIAL_THEME_NAMES])
            try: self.update_idletasks()
            except Exception: pass
            add_secret_theme_gallery(tab_secret)
            try: self.update_idletasks()
            except Exception: pass
        self._build_theme_gallery_once = _build_theme_gallery_once

        prefs = ctk.CTkFrame(theme_card, fg_color="transparent"); prefs.pack(fill="x", padx=14, pady=(2,14))
        self.font_menu = ctk.CTkOptionMenu(prefs, values=["Segoe UI","Consolas","Arial","Tahoma","Courier New"], command=self.escolher_fonte, fg_color=t["card_active"], button_color=t["card_active"], button_hover_color=t["hover"], text_color=t["accent"]); self.font_menu.set(self.fonte_ui); self.font_menu.pack(side="left", expand=True, fill="x", padx=(0,5))
        self.lang_menu = ctk.CTkOptionMenu(prefs, values=["Português","English"], command=self.aplicar_idioma, fg_color=t["card_active"], button_color=t["card_active"], text_color=t["accent"]); self.lang_menu.set("Português" if pt else "English"); self.lang_menu.pack(side="left", expand=True, fill="x", padx=(5,0))
        colors = self._section_card(body, "CORES DO TEMA" if pt else "THEME COLORS", "Personalize uma área ou restaure o tema para voltar à identidade original." if pt else "Customize one area or restore the theme to return to its original identity.")
        self.theme_color_buttons = {}
        labels = [("bg","Fundo do app" if pt else "App background"),("sidebar","Barra lateral" if pt else "Sidebar"),("panel","Painel principal" if pt else "Main panel"),("card","Dentro das caixas" if pt else "Card interior"),("card_active","Caixa ativa" if pt else "Active card"),("icon_bg","Caixa do ícone" if pt else "Icon box"),("accent","Cor de destaque" if pt else "Accent"),("hover","Hover principal" if pt else "Main hover"),("text","Texto" if pt else "Text"),("border","Bordas" if pt else "Borders")]
        for k,label in labels:
            rr=ctk.CTkFrame(colors,fg_color="transparent"); rr.pack(fill="x",padx=16,pady=3)
            ctk.CTkLabel(rr,text=label,width=220,anchor="w",text_color=t["text"]).pack(side="left")
            b=ctk.CTkButton(rr,text=TEMAS[self.tema_atual].get(k,"#000000"),width=150,fg_color=TEMAS[self.tema_atual].get(k,t["card_active"]),hover_color=t["hover"],text_color="#FFFFFF",command=lambda key=k:self.escolher_cor_parte_tema(key)); b.pack(side="right"); self.theme_color_buttons[k]=b
        ctk.CTkButton(colors,text="RESTAURAR TEMA" if pt else "RESTORE THEME",command=self.restaurar_tema_atual,fg_color="transparent",border_width=1,border_color=t["accent"],text_color=t["text"]).pack(fill="x",padx=16,pady=(10,14))
        self.btn_custom_color=ctk.CTkButton(colors,text="COR DE DESTAQUE RÁPIDA",command=self.escolher_cor_destaque); self.btn_custom_color.pack_forget()

        # AUDIO STUDIO
        _, abody = self._page_shell("audio", "ÁUDIO // SOUND STUDIO" if pt else "AUDIO // SOUND STUDIO", "Escolha a identidade sonora do ZKStrap. Música e efeitos podem ser controlados separadamente." if pt else "Choose ZKStrap's sound identity. Music and effects can be controlled separately.")
        ahero = self._section_card(abody, "ZK AUDIO ENGINE", "10 packs locais, 2 trilhas melódicas por pack e efeitos diferentes para navegação, scroll, sliders, tema, Combo Planner, avisos e carregamento." if pt else "10 local packs, 2 melodic background tracks per pack and distinct effects for navigation, scroll, sliders, themes, Combo Planner, alerts and loading.")
        ar=ctk.CTkFrame(ahero,fg_color="transparent"); ar.pack(fill="x",padx=16,pady=(4,8))
        self.audio_current_label=ctk.CTkLabel(ar,text=f"PACK ATIVO  //  {self.sound_pack}",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")); self.audio_current_label.pack(side="left")
        self.audio_master_button=ctk.CTkButton(ar,text=("DESATIVAR ÁUDIO" if self.sounds_enabled else "ATIVAR ÁUDIO"),width=160,height=36,command=self._audio_master_toggle,fg_color=t["accent"] if self.sounds_enabled else t["card_active"],hover_color=t["hover"],text_color="#050505" if self.sounds_enabled else t["text"]); self.audio_master_button.pack(side="right")
        swr=ctk.CTkFrame(ahero,fg_color="transparent"); swr.pack(fill="x",padx=16,pady=(2,14))
        self.audio_music_switch=ctk.CTkSwitch(swr,text="MÚSICA DE FUNDO" if pt else "BACKGROUND MUSIC",command=self._audio_toggle_music,progress_color=t["accent"],fg_color="#44484F",text_color=t["text"]); self.audio_music_switch.pack(side="left",padx=(0,22))
        self.audio_sfx_switch=ctk.CTkSwitch(swr,text="EFEITOS / SFX" if pt else "EFFECTS / SFX",command=self._audio_toggle_sfx,progress_color=t["accent"],fg_color="#44484F",text_color=t["text"]); self.audio_sfx_switch.pack(side="left")
        if self.music_enabled: self.audio_music_switch.select()
        if self.sfx_enabled: self.audio_sfx_switch.select()
        vr=ctk.CTkFrame(ahero,fg_color="transparent"); vr.pack(fill="x",padx=16,pady=(0,14))
        ctk.CTkLabel(vr,text="VOLUME DA MÚSICA" if pt else "MUSIC VOLUME",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),width=145,anchor="w").pack(side="left")
        self.audio_music_volume_slider=ctk.CTkSlider(vr,from_=0.0,to=0.65,number_of_steps=65,command=self._audio_music_volume_preview,progress_color=t["accent"],button_color=t["accent"],button_hover_color=t["hover"]); self.audio_music_volume_slider.pack(side="left",fill="x",expand=True,padx=(8,10)); self.audio_music_volume_slider.set(float(getattr(self,"music_volume",0.22)))
        self.audio_music_volume_label=ctk.CTkLabel(vr,text=f"{int(round(float(getattr(self,'music_volume',0.22))*100))}%",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),width=46); self.audio_music_volume_label.pack(side="right")
        self.audio_music_volume_slider.bind("<ButtonRelease-1>",self._audio_music_volume_apply)
        svr=ctk.CTkFrame(ahero,fg_color="transparent"); svr.pack(fill="x",padx=16,pady=(0,14))
        ctk.CTkLabel(svr,text="VOLUME DOS EFEITOS" if pt else "SFX VOLUME",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),width=145,anchor="w").pack(side="left")
        self.audio_sfx_volume_slider=ctk.CTkSlider(svr,from_=0.0,to=1.5,number_of_steps=75,command=self._audio_sfx_volume_preview,progress_color=t["accent"],button_color=t["accent"],button_hover_color=t["hover"]); self.audio_sfx_volume_slider.pack(side="left",fill="x",expand=True,padx=(8,10)); self.audio_sfx_volume_slider.set(float(getattr(self,"sfx_volume",1.0)))
        self.audio_sfx_volume_label=ctk.CTkLabel(svr,text=f"{int(round(float(getattr(self,'sfx_volume',1.0))*100))}%",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),width=46); self.audio_sfx_volume_label.pack(side="right")
        self.audio_sfx_volume_slider.bind("<ButtonRelease-1>",self._audio_sfx_volume_apply)
        ctk.CTkLabel(ahero,text="100% = volume original • até 150% = boost dos barulhos da interface",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w").pack(fill="x",padx=16,pady=(0,12))
        packs=self._section_card(abody,"PACKS DE SOM" if pt else "SOUND PACKS","Cada pack usa composição, ritmo e harmonia próprios. Use TESTAR para ouvir a assinatura antes de trocar." if pt else "Each pack uses its own composition, rhythm and harmony. Use TEST to hear its signature before switching.")
        pgrid=ctk.CTkFrame(packs,fg_color="transparent"); pgrid.pack(fill="x",padx=10,pady=(3,12)); pgrid.grid_columnconfigure(0,weight=1,uniform="aud"); pgrid.grid_columnconfigure(1,weight=1,uniform="aud")
        self.audio_pack_buttons={}
        for i,(pname,meta) in enumerate(AUDIO_PACKS.items()):
            selected=(pname==self.sound_pack)
            pc=ctk.CTkFrame(pgrid,fg_color=t["card"],corner_radius=13,border_width=2 if selected else 1,border_color=t["accent"] if selected else t["card_active"]); pc.grid(row=i//2,column=i%2,sticky="nsew",padx=6,pady=6)
            ph=ctk.CTkFrame(pc,fg_color="transparent"); ph.pack(fill="x",padx=12,pady=(10,3))
            ctk.CTkLabel(ph,text=pname,text_color=t["text"],font=ctk.CTkFont(size=12,weight="bold")).pack(side="left")
            ctk.CTkLabel(ph,text=f"0{i+1:02d}",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="right")
            ctk.CTkLabel(pc,text=meta.get("desc",""),text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w").pack(fill="x",padx=12,pady=(1,8))
            br=ctk.CTkFrame(pc,fg_color="transparent"); br.pack(fill="x",padx=10,pady=(0,10))
            ctk.CTkButton(br,text="▶ TESTAR" if pt else "▶ TEST",width=100,height=32,command=lambda n=pname:self._audio_test_pack(n),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"]).pack(side="left",padx=(0,5))
            use=ctk.CTkButton(br,text="ATIVO ✓" if selected else ("USAR PACK" if pt else "USE PACK"),height=32,command=lambda n=pname:self._audio_select_pack(n),fg_color=t["accent"] if selected else t["card_active"],hover_color=t["hover"],text_color="#050505" if selected else t["text"]); use.pack(side="left",fill="x",expand=True,padx=(5,0)); self.audio_pack_buttons[pname]=use
        events=self._section_card(abody,"EVENTOS SONOROS" if pt else "SOUND EVENTS","O ZKStrap usa variações para não repetir o mesmo clique." if pt else "ZKStrap uses variants so the same click is not repeated constantly.")
        er=ctk.CTkFrame(events,fg_color="transparent"); er.pack(fill="x",padx=12,pady=(3,12))
        for i,(label,event) in enumerate([("CLICK","click"),("NAVEGAÇÃO","nav"),("SCROLL","scroll"),("SLIDER","slider"),("CONFIRMAR","confirm"),("TEMA","theme"),("SUCESSO","success"),("AVISO","warning")]):
            ctk.CTkButton(er,text=label,height=31,command=lambda ev=event:self._play_ui_sound(ev,0),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],font=ctk.CTkFont(size=8,weight="bold")).grid(row=i//4,column=i%4,sticky="ew",padx=4,pady=4); er.grid_columnconfigure(i%4,weight=1,uniform="evt")

        # PERFORMANCE CENTER — ações de desempenho separadas de limpeza/rollback.
        _, body = self._page_shell("maintenance", "CENTRAL DE DESEMPENHO" if pt else "PERFORMANCE CENTER", "Prepare o Windows e a sessão do Roblox sem misturar boost com limpeza ou restauração." if pt else "Prepare Windows and the Roblox session without mixing performance tools with cleanup or rollback.")

        quick = self._section_card(body, "PAINEL DE PERFORMANCE" if pt else "PERFORMANCE DASHBOARD", "Diagnóstico rápido antes de mudar qualquer coisa. CPU/RAM altos podem indicar concorrência real por recursos." if pt else "Run a quick diagnostic before changing anything. High CPU/RAM can reveal real resource contention.")
        qrow=ctk.CTkFrame(quick,fg_color="transparent"); qrow.pack(fill="x",padx=14,pady=(4,8))
        self.lbl_perf_diag = ctk.CTkLabel(qrow, text="Clique em ANALISAR para ler CPU, RAM, Roblox e captura em segundo plano." if pt else "Click ANALYZE to read CPU, RAM, Roblox and background capture.", text_color=t.get("muted","gray"), justify="left", anchor="w", font=ctk.CTkFont(family="Consolas", size=9), wraplength=820)
        self.lbl_perf_diag.pack(side="left",fill="x",expand=True)
        ctk.CTkButton(qrow,text="ANALISAR" if pt else "ANALYZE",width=150,height=38,corner_radius=10,command=self.diagnostico_performance,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",font=ctk.CTkFont(size=9,weight="bold")).pack(side="right",padx=(12,0))

        winperf = self._section_card(body, "WINDOWS PARA JOGOS" if pt else "WINDOWS FOR GAMING", "Use recursos nativos do Windows para reduzir gravação em segundo plano e escolher a GPU do Roblox. Nada aqui desativa segurança." if pt else "Use native Windows features to reduce background recording and choose the Roblox GPU. Nothing here disables security.")
        wr = ctk.CTkFrame(winperf, fg_color="transparent"); wr.pack(fill="x", padx=14, pady=(4,6))
        ctk.CTkButton(wr, text="MODO DE JOGO" if pt else "GAME MODE", command=self.abrir_game_mode_settings, fg_color=t["card_active"], hover_color=t["hover"], text_color=t["accent"],height=40,corner_radius=10).pack(side="left", expand=True, fill="x", padx=(0,5))
        ctk.CTkButton(wr, text="GPU DO ROBLOX" if pt else "ROBLOX GPU", command=self.abrir_graphics_settings, fg_color=t["card_active"], hover_color=t["hover"], text_color=t["accent"],height=40,corner_radius=10).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(wr, text="ENERGIA" if pt else "POWER", command=self.abrir_power_settings, fg_color=t["card_active"], hover_color=t["hover"], text_color=t["accent"],height=40,corner_radius=10).pack(side="left", expand=True, fill="x", padx=(5,0))
        self.switch_bg_capture = ctk.CTkSwitch(winperf, text="DESATIVAR CAPTURA/GRAVAÇÃO EM SEGUNDO PLANO" if pt else "DISABLE BACKGROUND CAPTURE/RECORDING", command=self.evento_background_capture, progress_color=t["accent"], fg_color="#44484F", text_color=t["text"])
        self.switch_bg_capture.pack(anchor="w", padx=16, pady=(7,14))
        if self.game_dvr_background_disabled(): self.switch_bg_capture.select()

        focus = self._section_card(body, "FOCO NO ROBLOX" if pt else "ROBLOX FOCUS", "Ações temporárias para dar mais espaço à sessão do jogo. Prioridade volta ao normal quando o Roblox fecha; encerrar apps sempre pede confirmação." if pt else "Temporary actions to give the game session more room. Priority resets when Roblox closes; closing apps always asks first.")
        frow=ctk.CTkFrame(focus,fg_color="transparent"); frow.pack(fill="x",padx=14,pady=(4,6))
        ctk.CTkButton(frow,text="PRIORIDADE ACIMA DO NORMAL" if pt else "ABOVE-NORMAL PRIORITY",command=self.aplicar_prioridade_roblox,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=40,corner_radius=10).pack(side="left",expand=True,fill="x",padx=(0,5))
        ctk.CTkButton(frow,text="FECHAR OVERLAYS" if pt else "CLOSE OVERLAYS",command=self.fechar_overlays,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=40,corner_radius=10).pack(side="left",expand=True,fill="x",padx=(5,0))
        frow2=ctk.CTkFrame(focus,fg_color="transparent"); frow2.pack(fill="x",padx=14,pady=(4,14))
        self.btn_fechar_pesados=ctk.CTkButton(frow2,text=self.tr[self.idioma]['fechar_pesados'],command=self.fechar_apps_pesados,fg_color="#D79A36",hover_color="#B9822F",text_color="#111111",height=40,corner_radius=10)
        self.btn_fechar_pesados.pack(side="left",expand=True,fill="x",padx=(0,5))
        ctk.CTkButton(frow2,text="PREPARAR SESSÃO" if pt else "PREPARE SESSION",command=self.preparar_sessao_roblox,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=40,corner_radius=10).pack(side="left",expand=True,fill="x",padx=(5,0))

        energy = self._section_card(body, "ENERGIA & INICIALIZAÇÃO" if pt else "POWER & STARTUP", "Plano Alto Desempenho pode ajudar a evitar economia agressiva de CPU em alguns PCs. Em notebooks, ele também pode aumentar consumo e temperatura." if pt else "High Performance can reduce aggressive CPU power saving on some PCs. On laptops it can also increase power draw and temperature.")
        erow=ctk.CTkFrame(energy,fg_color="transparent"); erow.pack(fill="x",padx=14,pady=(4,6))
        ctk.CTkButton(erow,text="ATIVAR ALTO DESEMPENHO" if pt else "ENABLE HIGH PERFORMANCE",command=self.ativar_plano_alto_desempenho,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=40,corner_radius=10).pack(side="left",expand=True,fill="x",padx=(0,5))
        ctk.CTkButton(erow,text="APPS DE INICIALIZAÇÃO" if pt else "STARTUP APPS",command=self.abrir_startup_apps_settings,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=40,corner_radius=10).pack(side="left",expand=True,fill="x",padx=(5,0))
        ctk.CTkLabel(energy,text="Dica: desative manualmente da inicialização só programas que você reconhece e não precisa abrindo com o Windows." if pt else "Tip: disable only startup apps you recognize and do not need launching with Windows.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9),anchor="w",justify="left").pack(fill="x",padx=16,pady=(5,14))

        # RECOVERY — limpeza e rollback em página própria.
        _, rbody = self._page_shell("recovery", "RECUPERAÇÃO & LIMPEZA" if pt else "RECOVERY & CLEANUP", "Backups, arquivos temporários e retorno ao original ficam separados das ferramentas de desempenho." if pt else "Backups, temporary files and rollback are kept separate from performance tools.")

        clean = self._section_card(rbody, "LIMPEZA SEGURA" if pt else "SAFE CLEANUP", "Remove logs e downloads temporários do Roblox. Isso libera organização/espaço, mas não é tratado como aumento mágico de FPS." if pt else "Removes Roblox logs and temporary downloads. This helps cleanup/storage, not magic FPS.")
        self.btn_limpar_logs=ctk.CTkButton(clean,text=self.tr[self.idioma]['limpar_logs'],command=self.limpar_arquivos_temp,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=42,corner_radius=10)
        self.btn_limpar_logs.pack(fill="x",padx=14,pady=(5,8))
        ctk.CTkButton(clean,text="ABRIR PASTA LOCAL DO ROBLOX" if pt else "OPEN ROBLOX LOCAL FOLDER",command=self.abrir_pasta_local_roblox,fg_color="transparent",border_width=1,border_color=t["border"],hover_color=t["card_active"],text_color=t["text"],height=38,corner_radius=10).pack(fill="x",padx=14,pady=(0,14))

        restore = self._section_card(rbody, "RESTAURAR ALTERAÇÕES" if pt else "RESTORE CHANGES", "Volte cada área ao original sem misturar essa ação com os botões de boost. O reset completo remove as configurações gerenciadas pelo ZKStrap." if pt else "Restore each area without mixing rollback with boost controls. Full reset removes settings managed by ZKStrap.")
        rr=ctk.CTkFrame(restore,fg_color="transparent"); rr.pack(fill="x",padx=14,pady=(4,6))
        ctk.CTkButton(rr,text="CURSOR ORIGINAL" if pt else "ORIGINAL CURSOR",command=self.restaurar_cursor_original,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38,corner_radius=10).pack(side="left",expand=True,fill="x",padx=(0,5))
        ctk.CTkButton(rr,text="FONTES ORIGINAIS" if pt else "ORIGINAL FONTS",command=self.restaurar_fonte_jogo,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38,corner_radius=10).pack(side="left",expand=True,fill="x",padx=5)
        ctk.CTkButton(rr,text="PLANO EQUILIBRADO" if pt else "BALANCED POWER",command=self.restaurar_plano_equilibrado,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],height=38,corner_radius=10).pack(side="left",expand=True,fill="x",padx=(5,0))
        self.btn_reset=ctk.CTkButton(restore,text=self.tr[self.idioma]['resetar'],command=self.resetar_roblox,fg_color="#D73A49",hover_color="#B52D39",height=42,corner_radius=10)
        self.btn_reset.pack(fill="x",padx=14,pady=(6,6))
        ctk.CTkButton(restore,text="ROLLBACK COMPLETO — CURSOR + FONTES + CONFIG" if pt else "FULL ROLLBACK — CURSOR + FONTS + CONFIG",command=self.rollback_completo,fg_color="transparent",hover_color=t["card_active"],border_width=1,border_color="#D73A49",text_color="#FF6978",height=40,corner_radius=10).pack(fill="x",padx=14,pady=(0,14))
        self.btn_apply=self.header_apply_button
        self.lbl_desc_manut=ctk.CTkLabel(restore,text="",font=ctk.CTkFont(size=1)); self.lbl_desc_manut.pack_forget()
        self.lbl_desc_reset=ctk.CTkLabel(restore,text="",font=ctk.CTkFont(size=1)); self.lbl_desc_reset.pack_forget()
        self.lbl_recursos=ctk.CTkLabel(restore,text="",font=ctk.CTkFont(size=1)); self.lbl_recursos.pack_forget()

        # UPDATES / CHANGELOG — v3.18.0 Update Center
        _, body = self._page_shell("updates", "ATUALIZAÇÕES // UPDATE CENTER" if pt else "UPDATES // UPDATE CENTER", "Atualize sem baixar um novo ZIP pelo Discord a cada versão." if pt else "Update without downloading a new Discord ZIP for every version.")
        hero_up=self._section_card(body, f"ZKSTRAP v{APP_VERSION}", "Canal oficial: GitHub • download verificado por SHA-256 • backup antes de instalar." if pt else "Official GitHub channel • SHA-256 verified downloads • backup before install.")
        top=ctk.CTkFrame(hero_up,fg_color="transparent"); top.pack(fill="x",padx=16,pady=(4,7))
        self.update_status_label=ctk.CTkLabel(top,text="● PRONTO PARA VERIFICAR" if pt else "● READY TO CHECK",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold"),anchor="w")
        self.update_status_label.pack(side="left",fill="x",expand=True)
        allowed_channels=["stable","beta"] + (["dev"] if _owner_key_valid_global() else [])
        self.update_channel_menu=ctk.CTkOptionMenu(top,values=allowed_channels,command=self._update_set_channel,width=120,fg_color=t["card_active"],button_color=t["accent"],button_hover_color=t["hover"])
        self.update_channel_menu.set(self.update_channel if self.update_channel in allowed_channels else allowed_channels[0]); self.update_channel_menu.pack(side="right")
        self.update_info_label=ctk.CTkLabel(hero_up,text=("Canal: " + self.update_channel.upper() + "  •  versão instalada: v" + APP_VERSION),text_color=t.get("muted","gray"),justify="left",anchor="w",wraplength=900)
        self.update_info_label.pack(fill="x",padx=16,pady=(2,8))
        self.update_progress=ctk.CTkProgressBar(hero_up,height=10,progress_color=t["accent"],fg_color=t["card_active"]); self.update_progress.pack(fill="x",padx=16,pady=(2,4)); self.update_progress.set(0)
        self.update_progress_label=ctk.CTkLabel(hero_up,text="",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=9),anchor="w"); self.update_progress_label.pack(fill="x",padx=16,pady=(0,7))
        actions=ctk.CTkFrame(hero_up,fg_color="transparent"); actions.pack(fill="x",padx=16,pady=(2,8))
        self.btn_update_check=ctk.CTkButton(actions,text="VERIFICAR ATUALIZAÇÕES" if pt else "CHECK FOR UPDATES",command=lambda:self._update_check_async(silent=False),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"]); self.btn_update_check.pack(side="left",expand=True,fill="x",padx=(0,4))
        self.btn_update_install=ctk.CTkButton(actions,text="ATUALIZAR AGORA" if pt else "UPDATE NOW",command=self._update_download_async,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",state="disabled"); self.btn_update_install.pack(side="left",expand=True,fill="x",padx=4)
        ctk.CTkButton(actions,text="GITHUB",command=lambda:webbrowser.open(UPDATE_REPO_URL),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],width=120).pack(side="left",padx=(4,0))
        opts=ctk.CTkFrame(hero_up,fg_color="transparent"); opts.pack(fill="x",padx=16,pady=(0,12))
        self.update_auto_switch=ctk.CTkSwitch(opts,text="VERIFICAR AUTOMATICAMENTE AO ABRIR" if pt else "CHECK AUTOMATICALLY ON STARTUP",command=self._update_toggle_auto,progress_color=t["accent"],fg_color=t["card_active"],text_color=t["text"]); self.update_auto_switch.pack(side="left")
        if self.update_auto_check: self.update_auto_switch.select()
        self.btn_update_rollback=ctk.CTkButton(opts,text="RESTAURAR VERSÃO ANTERIOR" if pt else "RESTORE PREVIOUS VERSION",command=self._update_restore_previous,fg_color="transparent",border_width=1,border_color=t["card_active"],hover_color=t["card_active"],text_color=t["text"]); self.btn_update_rollback.pack(side="right")
        def _version_key(row):
            nums=[int(n) for n in re.findall(r"\d+", row[0])]
            return tuple(nums)
        for ver,title,items in sorted(CHANGELOG, key=_version_key, reverse=True):
            card=self._section_card(body, f"{ver}  •  {title}")
            txt="\n".join("  ✓ "+item for item in items)
            ctk.CTkLabel(card,text=txt,text_color=t.get("muted","gray"),justify="left",anchor="w",font=ctk.CTkFont(family="Segoe UI",size=9),wraplength=820).pack(fill="x",padx=16,pady=(4,14))

        # FEEDBACK / BUGS — página própria
        _, body = self._page_shell("feedback", "SUGESTÕES & BUGS" if pt else "FEEDBACK & BUGS", "Uma central de feedback mais clara para separar ideia nova de problema real." if pt else "A clearer feedback center to separate new ideas from actual bugs.")
        hero = self._section_card(body, "AJUDE A EVOLUIR O ZKSTRAP" if pt else "HELP IMPROVE ZKSTRAP", "Descreva o que você gostaria de ver ou explique exatamente o que aconteceu. Quanto mais claro, mais fácil reproduzir." if pt else "Describe what you'd like to see or exactly what happened. Clear reports are easier to reproduce.")
        type_row = ctk.CTkFrame(hero, fg_color="transparent"); type_row.pack(fill="x", padx=16, pady=(2,10))
        self.btn_sug_idea = ctk.CTkButton(type_row, text="✦  SUGESTÃO" if pt else "✦  SUGGESTION", command=lambda: self._set_sug_tipo_ui("Sugestão" if pt else "Suggestion"), fg_color=t["accent"], hover_color=t["hover"], text_color="#050505", height=42)
        self.btn_sug_idea.pack(side="left", expand=True, fill="x", padx=(0,5))
        self.btn_sug_bug = ctk.CTkButton(type_row, text="⚠  REPORTAR BUG" if pt else "⚠  REPORT BUG", command=lambda: self._set_sug_tipo_ui("Reportar Bug" if pt else "Report Bug"), fg_color=t["card_active"], hover_color=t["hover"], text_color=t["text"], height=42)
        self.btn_sug_bug.pack(side="left", expand=True, fill="x", padx=(5,0))
        vals = self.tr[self.idioma]['sug_type_vals']; self.sug_tipo = vals[0]
        self.sug_type_menu = ctk.CTkOptionMenu(hero, values=vals); self.sug_type_menu.pack_forget()

        form = self._section_card(body, "DETALHES" if pt else "DETAILS", "Evite só escrever 'não funciona'. Em bugs, diga a função usada e o que você esperava acontecer." if pt else "Avoid only writing 'it doesn't work'. For bugs, mention the feature used and expected behavior.")
        self.entry_sug_title = ctk.CTkEntry(form, placeholder_text="Título curto — ex.: Cursor não aplica após update" if pt else "Short title — e.g. Cursor not applied after update", height=40)
        self.entry_sug_title.pack(fill="x", padx=16, pady=(4,7))
        self.txt_sug = ctk.CTkTextbox(form, height=180, fg_color="#080A0D", text_color="#FFFFFF", border_width=1, border_color=t["card_active"], font=ctk.CTkFont(family="Segoe UI", size=10))
        self.txt_sug.pack(fill="x", padx=16, pady=5)
        self.txt_sug.bind("<KeyRelease>", self._update_sug_counter)
        self._bind_outer_scroll(self.txt_sug, "feedback")
        self.lbl_sug_counter = ctk.CTkLabel(form, text="0 caracteres" if pt else "0 characters", text_color=t.get("muted","gray"), font=ctk.CTkFont(family="Consolas", size=8))
        self.lbl_sug_counter.pack(anchor="e", padx=16, pady=(0,4))
        self.switch_feedback_diag=ctk.CTkSwitch(form,text="INCLUIR DIAGNÓSTICO DO APP" if pt else "INCLUDE APP DIAGNOSTICS",progress_color=t["accent"],fg_color="#44484F",text_color=t["text"]); self.switch_feedback_diag.pack(anchor="w",padx=16,pady=(2,6)); self.switch_feedback_diag.select()
        self.btn_enviar_sug = ctk.CTkButton(form, text="ENVIAR FEEDBACK" if pt else "SEND FEEDBACK", command=self.enviar_sugestao, fg_color=t["accent"], hover_color=t["hover"], text_color="#050505", height=42)
        self.btn_enviar_sug.pack(fill="x", padx=16, pady=(4,14))

        tips = self._section_card(body, "ANTES DE REPORTAR UM BUG" if pt else "BEFORE REPORTING A BUG", "✓ reinicie o Roblox  •  ✓ confira a version-* detectada  •  ✓ veja o log inferior  •  ✓ diga qual tema/Windows está usando" if pt else "✓ restart Roblox  •  ✓ check detected version-*  •  ✓ inspect the bottom log  •  ✓ mention your theme/Windows version")
        self.lbl_feedback_mode = ctk.CTkLabel(tips, text=("MODO DE ENVIO: endpoint seguro quando configurado; caso contrário, copia para a área de transferência." if pt else "SEND MODE: secure endpoint when configured; otherwise copies to clipboard."), text_color=t.get("muted","gray"), wraplength=820, justify="left")
        self.lbl_feedback_mode.pack(anchor="w", padx=16, pady=(2,14))

        # SUPPORT HUB v3.18.4
        _, body = self._page_shell(
            "support",
            "APOIAR // ZKSTRAP" if pt else "SUPPORT // ZKSTRAP",
            "Uma forma opcional de fortalecer o projeto sem colocar dados de pagamento dentro do app." if pt else "An optional way to support the project without storing payment data inside the app."
        )
        hero = self._section_card(
            body,
            "💚 FORTALEÇA O PROJETO" if pt else "💚 SUPPORT THE PROJECT",
            "O ZKStrap continua gratuito. Se ele te ajuda e você quiser apoiar, a contribuição é totalmente opcional." if pt else "ZKStrap stays free. If it helps you and you want to support it, contributions are completely optional."
        )
        ctk.CTkLabel(
            hero,
            text=(
                "O pagamento acontece em uma página externa. O ZKStrap não pede, recebe ou armazena senha bancária, cartão, CPF, chave Pix ou credenciais de pagamento."
                if pt else
                "Payment happens on an external page. ZKStrap does not request, receive or store bank passwords, card data, tax IDs, Pix keys or payment credentials."
            ),
            text_color=t["text"],
            wraplength=860,
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=16, pady=(8,14))
        srow=ctk.CTkFrame(hero,fg_color="transparent"); srow.pack(fill="x",padx=16,pady=(0,14))
        ctk.CTkButton(
            srow,
            text="ABRIR PÁGINA DE APOIO" if pt else "OPEN SUPPORT PAGE",
            command=self._open_support_page,
            fg_color="#1ED760",
            hover_color="#18B953",
            text_color="#06150B",
            height=46,
            corner_radius=11,
            font=ctk.CTkFont(size=11,weight="bold")
        ).pack(side="left",expand=True,fill="x",padx=(0,5))
        ctk.CTkButton(
            srow,
            text="COPIAR LINK" if pt else "COPY LINK",
            command=self._copy_support_link,
            fg_color=t["card_active"],
            hover_color=t["hover"],
            text_color=t["accent"],
            height=46,
            corner_radius=11,
            font=ctk.CTkFont(size=11,weight="bold")
        ).pack(side="left",expand=True,fill="x",padx=(5,0))

        privacy_support = self._section_card(
            body,
            "PRIVACIDADE" if pt else "PRIVACY",
            "O botão apenas abre o site oficial de apoio do ZKStrap no navegador." if pt else "The button only opens the official ZKStrap support site in your browser."
        )
        ctk.CTkLabel(
            privacy_support,
            text=(
                "✓ nenhum dado bancário fica salvo no ZKStrap\n✓ o app não lê pagamentos\n✓ o app não pede login do banco\n✓ antes de pagar, confira os dados mostrados pelo próprio provedor"
                if pt else
                "✓ no banking data is stored in ZKStrap\n✓ the app does not read payments\n✓ the app never asks for bank login\n✓ before paying, verify the details shown by the payment provider"
            ),
            text_color=t.get("muted","gray"),
            font=ctk.CTkFont(family="Consolas",size=9),
            justify="left",
            anchor="w"
        ).pack(fill="x",padx=16,pady=(6,14))

        # ABOUT 2.0
        _, body = self._page_shell("about", "SOBRE // ABOUT 2.0" if pt else "ABOUT // 2.0", "De uma ferramenta de flags para uma central completa do jogador." if pt else "From a flags utility to a complete player hub.")
        intensive_start_dt=datetime(2026,9,10,0,0,0); project_start=datetime(2026,7,1).date(); now_dt=datetime.now(); today=now_dt.date()
        intense_days=max(0,(today-intensive_start_dt.date()).days); project_days=max(0,(today-project_start).days)
        intense_hours=max(0,int((now_dt-intensive_start_dt).total_seconds()//3600))
        intro=self._section_card(body,"ZKSTRAP","Central de otimização, personalização e ferramentas para Roblox, com foco especial na experiência de quem joga Blox Fruits." if pt else "Optimization, customization and Roblox tools, with special focus on Blox Fruits players.")
        about_text=("O ZKStrap nasceu porque o zkvez usava FastFlags em um PC fraco e viu como pequenos ajustes podiam ajudar. A ideia evoluiu para um launcher separado do Roblox: ele organiza ajustes locais, desempenho, personalização e ferramentas úteis sem pedir senha do Roblox.\n\nHoje o objetivo é ser algo que o jogador tenha motivo para abrir de novo: Combo Planner, Blox Hub, Creator Mode, áudio, temas, diagnóstico, recuperação e outras ferramentas em evolução." if pt else "ZKStrap started because zkvez used FastFlags on a weak PC and saw how small adjustments could help. It evolved into a launcher separate from Roblox: local settings, performance, customization and useful tools without asking for a Roblox password.\n\nThe goal now is to be something players actually want to reopen: Combo Planner, Blox Hub, Creator Mode, audio, themes, diagnostics, recovery and more.")
        self.txt_about=ctk.CTkLabel(intro,text=about_text,fg_color="transparent",text_color=t["text"],justify="left",anchor="w",wraplength=880); self.txt_about.pack(fill="x",padx=16,pady=(8,14))
        timeline=self._section_card(body,"LINHA DO TEMPO" if pt else "TIMELINE")
        tl=(f"01/07/2026  •  início do projeto  •  {project_days} dias desde o começo\n10/09/2026  •  início da reconstrução intensiva do Strap\nHOJE  •  {intense_days} dias nesta fase  •  ~{intense_hours} horas de tempo decorrido desde o início" if pt else f"07/01/2026  •  project start  •  {project_days} days total\n09/10/2026  •  intensive rebuild phase started\nTODAY  •  {intense_days} days refining this ZKStrap generation")
        ctk.CTkLabel(timeline,text=tl,text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=10,weight="bold"),justify="left",anchor="w").pack(fill="x",padx=16,pady=(6,14))
        privacy=self._section_card(body,"PRIVACIDADE & CONTROLE" if pt else "PRIVACY & CONTROL","Configurações ficam locais. O app não pede senha do Roblox. Integrações externas usam autorização oficial quando disponível." if pt else "Settings stay local. The app does not ask for a Roblox password. External integrations use official authorization when available.")
        ctk.CTkLabel(privacy,text=("Spotify/Mídia usa somente controles locais do Windows: sem login, Client ID, OAuth, API ou senha." if pt else "Spotify/Media uses local Windows media controls only: no login, Client ID, OAuth, API or password."),text_color=t["text"],wraplength=860,justify="left").pack(fill="x",padx=16,pady=(6,14))
        future=self._section_card(body,"FUTURO DO ZKSTRAP" if pt else "ZKSTRAP FUTURE","PvP Coach mais avançado, análise de sessão, Creator tools, integrações oficiais e novos recursos do Blox Hub — sem prometer funções antes de estarem prontas." if pt else "More advanced PvP Coach, session analysis, creator tools, official integrations and new Blox Hub features — without promising features before they are ready.")
        author=self._section_card(body,"FEITO PELO ZKVEZ" if pt else "MADE BY ZKVEZ")
        self.author_box=ctk.CTkLabel(author,text=("Criado por zkvez, criador de conteúdo de Blox Fruits. Muitas ideias do app vêm do uso real, de vídeos e das sugestões dos inscritos.\n\nDe uma ferramenta de flags para uma central completa do jogador." if pt else "Created by zkvez, a Blox Fruits content creator. Many features come from real use, videos and subscriber suggestions.\n\nFrom a flags utility to a complete player hub."),fg_color="transparent",text_color=t["text"],justify="left",anchor="w",wraplength=860); self.author_box.pack(fill="x",padx=16,pady=(8,12))
        self.yt_link=ctk.CTkLabel(author,text="https://www.youtube.com/@zkvez",text_color="#FF5555",font=ctk.CTkFont(family="Segoe UI",size=10,underline=True)); self.yt_link.pack(anchor="w",padx=16,pady=(0,12)); self.yt_link.bind("<Button-1>",lambda e:webbrowser.open("https://www.youtube.com/@zkvez"))

        # Compatibilidade com funções antigas que esperavam estas referências.
        self.tab_config = self.pages["home"]; self.tab_performance = self.pages["fps"]; self.tab_fastflags = self.pages["fps"]; self.tab_cursor = self.pages["cursor"]; self.tab_manutencao = self.pages["maintenance"]; self.tab_recuperacao = self.pages.get("recovery")
        self.right_tabview = self.content_host
        self.more_tabview = self.content_host

        if self.current_page_key not in self.pages: self.current_page_key = "home"
        self.show_page(self.current_page_key, animate=False)
        try: self.aplicar_fonte_widgets(self)
        except Exception: pass

    # ------------------------------------------------------------------
    # COMBO PLANNER v3.5
    # ------------------------------------------------------------------
    def _combo_catalog(self):
        # Catálogos visuais usados pelo Planner e Build Roulette.
        styles = [
            "Combat", "Advanced Combat (Combat V2)", "Dark Step", "Electric", "Water Kung Fu", "Dragon Breath", "Superhuman",
            "Death Step", "Sharkman Karate", "Electric Claw", "Dragon Talon", "Godhuman", "Sanguine Art"
        ]
        fruits = [
            "Rocket","Spin","Blade","Spring","Bomb","Smoke","Spike","Flame","Ice","Sand","Dark","Eagle",
            "Diamond","Light","Rubber","Ghost","Magma","Quake","Buddha","Love","Creation","Spider","Sound",
            "Phoenix","Portal","Lightning","Pain","Blizzard","Gravity","Mammoth","T-Rex","Dough","Shadow",
            "Venom","Gas","Spirit","Tiger","Yeti","Magnet","Kitsune","Control","Dragon"
        ]
        swords = [
            "Cutlass","Dual Katana","Katana","Iron Mace","Shark Saw","Triple Katana","Twin Hooks",
            "Dragon Trident","Dual-Headed Blade","Flail","Gravity Blade","Longsword","Pipe","Soul Cane","Trident","Wardens Sword",
            "Bisento","Buddy Sword","Canvander","Dark Dagger","Dragonheart","Fox Lamp","Koko","Midnight Blade","Oroshi",
            "Pole (1st Form)","Pole (2nd Form)","Rengoku","Saber","Saishi","Shark Anchor","Shizu","Spikey Trident","Tushita","Yama",
            "Cursed Dual Katana","Dark Blade","Dog Blade","Hallow Scythe","True Triple Katana"
        ]
        guns = [
            "Slingshot","Flintlock","Musket","Acidum Rifle","Bizarre Revolver","Cannon","Dual Flintlock",
            "Magma Blaster","Refined Slingshot","Bazooka","Dragonstorm","Kabucha","Venom Bow","Skull Guitar"
        ]
        return {"style": styles, "fruit": fruits, "sword": swords, "gun": guns}

    def _combo_sources(self):
        return [
            ("Blox Fruits — página oficial no Roblox", "https://www.roblox.com/games/2753915549/Blox-Fruits"),
            ("Blox Fruits Wiki/Fandom — Natural", "https://blox-fruits.fandom.com/wiki/Natural"),
            ("Blox Fruits Wiki/Fandom — Elemental", "https://blox-fruits.fandom.com/wiki/Elemental"),
            ("Blox Fruits Wiki/Fandom — Beast", "https://blox-fruits.fandom.com/wiki/Beast"),
            ("Blox Fruits Wiki/Fandom — Fighting Styles", "https://blox-fruits.fandom.com/wiki/Fighting_Styles"),
            ("Blox Fruits Wiki/Fandom — Swords", "https://blox-fruits.fandom.com/wiki/Swords"),
            ("Blox Fruits Wiki/Fandom — Guns", "https://blox-fruits.fandom.com/wiki/Guns"),
        ]

    def _combo_cache_dir(self, category=None):
        # v3.14 invalida apenas os catálogos que receberam o pipeline novo.
        # Outras categorias mantêm o cache legado sem serem reprocessadas.
        # v3.14.8: invalida o cache de Fruits de novo. A 3.14.7 podia deixar um
        # placeholder/arquivo antigo preso no cache depois de uma tentativa ruim.
        # As outras categorias mantêm o cache anterior para não baixar tudo de novo.
        folder = "thumbs_v16_fruit_cdn" if category == "fruit" else ("thumbs_v11_weapon_strict" if category in ("sword", "gun") else ("thumbs_v10_full" if category == "style" else "thumbs_v5"))
        p = os.path.join(os.path.dirname(self.config_path), "combo_planner", folder)
        os.makedirs(p, exist_ok=True)
        return p

    def _combo_slug(self, text):
        return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")

    def _combo_cache_path(self, category, name):
        return os.path.join(self._combo_cache_dir(category), f"{category}_{self._combo_slug(name)}.png")

    def _combo_exact_title(self, category, name):
        aliases = {
            ("style", "Advanced Combat (Combat V2)"): "Advanced Combat",
            ("style", "Advanced Combat"): "Advanced Combat",
            ("style", "Godhuman"): "Godhuman",
            ("style", "Sanguine Art"): "Sanguine Art",
            ("fruit", "Lightning"): "Lightning",
        }
        return aliases.get((category, name), str(name))

    def _combo_file_candidates(self, category, name):
        title=self._combo_exact_title(category,name)
        clean=str(title).strip()
        if category=="fruit":
            # Fruit precisa mostrar o modelo/objeto da fruta, não o ícone de habilidade.
            # Nunca usamos "<nome> Icon.png" sozinho: esse fallback foi a causa
            # de Flame/Light/Dark etc. aparecerem como símbolo em vez da fruta física.
            return [
                f"{clean} Physical Fruit.png",
                f"Physical {clean} Fruit.png",
                f"{clean} Fruit Model.png",
                f"{clean} Fruit.png",
                f"{clean} Fruit Icon.png",
                f"Icon {clean} Fruit.png",
            ]
        if category=="style":
            return [f"{clean} Icon.png", f"{clean}_Icon.png", f"{clean} Fighting Style Icon.png"]
        if category in ("sword","gun"):
            specials = {
                "Pole (1st Form)": ["Pole (1st Form).png", "Pole 1st Form.png", "Pole V1.png", "Pole V1 Icon.png", "Pole (1st Form) Icon.png"],
                "Pole (2nd Form)": ["Pole (2nd Form).png", "Pole 2nd Form.png", "Pole V2.png", "Pole V2 Icon.png", "Pole (2nd Form) Icon.png"],
                "Dog Blade": ["Dog Blade.png", "Dog Blade Icon.png"],
                "Dual-Headed Blade": ["Dual-Headed Blade.png", "Dual-Headed Blade Icon.png"],
                "Flail": ["Flail.png", "Flail Icon.png"],
                "Refined Slingshot": ["Refined Slingshot.png", "Refined Slingshot Icon.png"],
                "Slingshot": ["Slingshot.png", "Slingshot Icon.png"],
            }
            out=[]
            for fn in specials.get(clean, []):
                if fn not in out:
                    out.append(fn)
            for fn in [f"{clean}.png", f"{clean} Icon.png", f"{clean}_Icon.png", f"Icon {clean}.png"]:
                if fn not in out:
                    out.append(fn)
            return out
        return []

    def _combo_save_image_bytes(self, raw, cache, strict_square=False):
        try:
            from PIL import Image
            im=Image.open(BytesIO(raw)).convert("RGBA")
            if im.width < 24 or im.height < 24:
                return False
            # Remove margens transparentes antes de avaliar a forma real do ícone.
            alpha=im.getchannel("A")
            bbox=alpha.getbbox()
            if bbox:
                im=im.crop(bbox)
            if im.width < 24 or im.height < 24:
                return False
            if strict_square:
                ratio=float(im.width)/max(1.0,float(im.height))
                # Ícones reais do inventário são essencialmente quadrados; banners/cards
                # que causaram Superhuman/Spin/Spring errados são muito horizontais.
                if ratio < 0.76 or ratio > 1.32:
                    return False
            im.thumbnail((256,256),Image.Resampling.LANCZOS)
            canvas=Image.new("RGBA",(256,256),(0,0,0,0))
            x=(256-im.width)//2; y=(256-im.height)//2
            canvas.alpha_composite(im,(x,y))
            canvas.save(cache,"PNG")
            return True
        except Exception:
            return False

    def _fruit_category_pages(self):
        # ÚNICAS fontes aceitas para imagens de Fruit no v3.14.6.
        # A página individual e pageimage/og:image foram removidas do pipeline de Fruits
        # porque podiam devolver player, skill, transformação, modelo antigo ou screenshot.
        return [
            "https://blox-fruits.fandom.com/wiki/Natural",
            "https://blox-fruits.fandom.com/wiki/Elemental",
            "https://blox-fruits.fandom.com/wiki/Beast",
        ]

    def _fruit_rarity_for_file(self, name):
        # Rarity usada no nome dos arquivos da tabela da wiki (ex.: RocketCommon).
        groups = {
            "Common": {"Rocket","Spin","Blade","Spring","Bomb","Smoke","Spike"},
            "Uncommon": {"Flame","Ice","Sand","Dark","Eagle","Diamond"},
            "Rare": {"Light","Rubber","Ghost","Magma"},
            "Legendary": {"Quake","Buddha","Love","Creation","Spider","Sound","Phoenix","Portal","Lightning","Pain","Blizzard"},
            "Mythical": {"Gravity","Mammoth","T-Rex","Dough","Shadow","Venom","Gas","Spirit","Tiger","Yeti","Magnet","Kitsune","Control","Dragon"},
        }
        for rarity, names in groups.items():
            if name in names:
                return rarity
        return ""

    def _fruit_direct_file_candidates(self, name):
        # A própria tabela da wiki expõe os assets como Nome+Raridade
        # (RocketCommon, FlameUncommon, LightRare...). Em vez de raspar HTML,
        # apontamos direto para o arquivo exato.
        rarity = self._fruit_rarity_for_file(name)
        if not rarity:
            return []
        bases = [f"{name}{rarity}"]
        # Alguns títulos podem ter variação de pontuação no nome do arquivo.
        if name == "T-Rex":
            bases += ["TRexMythical", "T-RexMythical"]
        if name == "Lightning":
            bases += ["LightningLegendary"]
        # Magnet é recente; tentamos também a alternativa caso a wiki tenha
        # mantido um rótulo de raridade diferente no arquivo.
        if name == "Magnet":
            bases += ["MagnetMythical"]
        out=[]
        for b in bases:
            for ext in (".png", ".webp"):
                fn=b+ext
                if fn not in out:
                    out.append(fn)
        return out

    def _combo_fruit_primary_url(self, name):
        """Primary CDN for Fruit thumbnails, independent from Fandom HTML/API."""
        special = {
            "Magnet": "https://wikiassets.net/bloxfruits-3bec24/images/896b3a0f6578535ac56efed826bbe1b1.webp",
        }
        if name in special:
            return special[name]
        safe = str(name).replace("/", "-")
        return f"https://raw.githubusercontent.com/blackxscripts/blox-fruits/main/{safe}_Fruit.png"

    def _combo_try_fruit_primary_cdn(self, name, headers, cache):
        try:
            url=self._combo_fruit_primary_url(name)
            ih=dict(headers)
            ih["Accept"]="image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
            r=requests.get(url,headers=ih,timeout=10,allow_redirects=True)
            ctype=(r.headers.get("content-type") or "").lower()
            if not (r.ok and len(r.content)>300 and "image" in ctype):
                return False
            return self._combo_save_image_bytes(r.content,cache,strict_square=True)
        except Exception:
            return False

    def _combo_try_fruit_api_file(self, name, headers, cache):
        """Resolve o arquivo exato da Fruit via MediaWiki API.

        A 3.14.7 dependia primeiro de ``Special:Redirect/file``. Em algumas redes
        esse endpoint devolve challenge/HTML, mesmo quando a API normal da wiki
        continua funcionando. Aqui consultamos somente os nomes de arquivo exatos
        gerados por ``_fruit_direct_file_candidates`` e pedimos a URL original do
        asset. Não há busca por screenshot, player, skill ou transformação.
        """
        api="https://blox-fruits.fandom.com/api.php"
        try:
            for filename in self._fruit_direct_file_candidates(name):
                try:
                    r=requests.get(
                        api,
                        params={
                            "action":"query",
                            "format":"json",
                            "titles":"File:"+filename,
                            "prop":"imageinfo",
                            "iiprop":"url|mime|size",
                            "iiurlwidth":384,
                            "redirects":1,
                        },
                        headers=headers,
                        timeout=10,
                    )
                    if not r.ok:
                        continue
                    pages=(r.json().get("query",{}).get("pages",{}) or {}).values()
                    for page in pages:
                        if page.get("missing") is not None:
                            continue
                        info=(page.get("imageinfo") or [])
                        if not info:
                            continue
                        meta=info[0] or {}
                        image_url=meta.get("thumburl") or meta.get("url")
                        if not image_url:
                            continue
                        ih=dict(headers)
                        ih["Referer"]="https://blox-fruits.fandom.com/wiki/Blox_Fruits"
                        ir=requests.get(image_url,headers=ih,timeout=12,allow_redirects=True)
                        ctype=(ir.headers.get("content-type") or "").lower()
                        if not (ir.ok and len(ir.content)>300 and "image" in ctype):
                            continue
                        if self._combo_save_image_bytes(ir.content,cache,strict_square=True):
                            return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def _combo_try_fruit_direct_file(self, name, headers, cache):
        """Baixa o asset exato da fruta pela própria wiki, sem analisar screenshots."""
        try:
            from urllib.parse import quote
            for filename in self._fruit_direct_file_candidates(name):
                # Special:Redirect/file resolve para o arquivo original no CDN da Fandom.
                urls = [
                    "https://blox-fruits.fandom.com/wiki/Special:Redirect/file/" + quote(filename, safe=""),
                    "https://blox-fruits.fandom.com/wiki/Special:FilePath/" + quote(filename, safe=""),
                ]
                for url in urls:
                    try:
                        ih=dict(headers)
                        ih["Referer"]="https://blox-fruits.fandom.com/wiki/Blox_Fruits"
                        ih["Accept"]="image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
                        r=requests.get(url,headers=ih,timeout=12,allow_redirects=True)
                        ctype=(r.headers.get("content-type") or "").lower()
                        if not (r.ok and len(r.content)>300 and "image" in ctype):
                            continue
                        if self._combo_save_image_bytes(r.content,cache,strict_square=True):
                            return True
                    except Exception:
                        pass
            return False
        except Exception:
            return False

    def _fruit_image_name_matches(self, fruit_name, meta):
        """Reconhece APENAS a miniatura da fruta nas páginas Natural/Elemental/Beast.

        A tabela atual do Fandom costuma usar alt/textos como ``RocketCommon`` ou
        ``FlameUncommon``. A v3.14.5 exigia a palavra "fruit" e por isso rejeitava
        todas essas imagens válidas. Aqui removemos apenas sufixos de raridade/tipo
        e continuamos bloqueando screenshot, player, skill, transformação e mídia old.
        """
        try:
            def norm(v):
                v=urllib.parse.unquote(str(v or ""))
                # separa CamelCase usado pela tabela: RocketCommon -> Rocket Common
                v=re.sub(r"(?<=[a-z0-9])(?=[A-Z])"," ",v)
                v=v.replace("_"," ").replace("-"," ")
                v=re.sub(r"\.(png|webp|jpg|jpeg|gif)(\?.*)?$","",v,flags=re.I)
                v=re.sub(r"\b(image|file|thumbnail|thumb|wiki|fandom)\b"," ",v,flags=re.I)
                v=re.sub(r"[^a-z0-9]+"," ",v.lower()).strip()
                return re.sub(r"\s+"," ",v)

            fruit=norm(fruit_name)
            m=norm(meta)
            if not fruit or not m:
                return False

            bad=("player","user","using","showcase","gameplay","screenshot","awakening","awakened",
                 "transformation","transformed","moveset","move","skill","ability","held","inventory screen",
                 "old","legacy","previous","revamp comparison","admin","avatar","character")
            if any(b in m for b in bad):
                return False

            # Remove apenas palavras esperadas na célula da tabela/caminho do asset.
            cleaned=re.sub(
                r"\b(common|uncommon|rare|legendary|mythical|natural|elemental|beast|fruit|physical|model|original|current|latest|revision|scale|width|height|png|webp|jpg|jpeg)\b",
                " ",m
            )
            cleaned=re.sub(r"\b\d+\b"," ",cleaned)
            cleaned=re.sub(r"\s+"," ",cleaned).strip()
            if cleaned == fruit:
                return True

            # Em URLs do static.wikia podem sobrar hashes/caminhos. Nesse caso,
            # basta o alt/title exato ter o nome da fruta + raridade.
            parts=m.split()
            if fruit in m:
                rest=m.replace(fruit," ",1)
                rest=re.sub(
                    r"\b(common|uncommon|rare|legendary|mythical|natural|elemental|beast|fruit|physical|model|original|current|latest)\b",
                    " ",rest
                )
                rest=re.sub(r"\b\d+\b"," ",rest)
                rest=re.sub(r"[^a-z]+","",rest)
                if not rest:
                    return True
            return False
        except Exception:
            return False

    def _fruit_category_extract_urls(self, fruit_name, html_text, page_url):
        """Extrai a imagem do item diretamente da tabela das 3 páginas de categoria."""
        try:
            from urllib.parse import urljoin
            found=[]
            for tag in re.findall(r"<img\b[^>]*>",str(html_text or ""),re.I):
                attrs={}
                for k,v1,v2 in re.findall(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')",tag):
                    attrs[k.lower()]=v1 or v2

                meta=" ".join([
                    attrs.get("alt",""), attrs.get("title",""),
                    attrs.get("data-image-name",""), attrs.get("data-file-name","")
                ])
                if not self._fruit_image_name_matches(fruit_name,meta):
                    continue

                candidates=[]
                for key in ("data-src","data-lazy-src","data-original","src"):
                    v=(attrs.get(key) or "").strip()
                    if v and not v.startswith("data:"):
                        candidates.append(v)
                for key in ("data-srcset","srcset"):
                    raw=(attrs.get(key) or "").strip()
                    if raw:
                        for part in raw.split(","):
                            u=part.strip().split(" ",1)[0].strip()
                            if u and not u.startswith("data:"):
                                candidates.append(u)

                for src in reversed(candidates):
                    u=urljoin(page_url,src.replace("&amp;","&"))
                    # Tenta baixar a versão original, sem thumbnail reduzida.
                    u=re.sub(r"/revision/latest/(?:scale-to-width-down|scale-to-height-down)/\d+.*$","/revision/latest",u)
                    if u not in found:
                        found.append(u)
            return found[:8]
        except Exception:
            return []

    def _fruit_category_html(self, page_url, headers):
        """Baixa cada página no máximo uma vez por sessão e tenta a API da MESMA página como fallback."""
        if not hasattr(self,"_fruit_category_html_cache"):
            self._fruit_category_html_cache={}
        if not hasattr(self,"_fruit_category_html_lock"):
            self._fruit_category_html_lock=threading.Lock()

        with self._fruit_category_html_lock:
            if page_url in self._fruit_category_html_cache:
                return self._fruit_category_html_cache[page_url]

            html=""
            try:
                r=requests.get(page_url,headers=headers,timeout=12,allow_redirects=True)
                if r.ok and "<img" in r.text.lower():
                    html=r.text
            except Exception:
                pass

            # Mesmo conteúdo/página via MediaWiki API; ajuda quando o HTML normal
            # entrega challenge/consent em vez da tabela.
            if not html:
                try:
                    title=urllib.parse.unquote(page_url.rstrip("/").split("/")[-1]).replace("_"," ")
                    api="https://blox-fruits.fandom.com/api.php"
                    ar=requests.get(api,params={"action":"parse","format":"json","page":title,"prop":"text","redirects":1},headers=headers,timeout=12)
                    if ar.ok:
                        html=((((ar.json().get("parse") or {}).get("text") or {}).get("*")) or "")
                except Exception:
                    pass

            self._fruit_category_html_cache[page_url]=html
            return html

    def _combo_try_fruit_category_image(self, name, headers, cache):
        """Busca Fruit SOMENTE em Natural/Elemental/Beast, usando o ícone da tabela."""
        for page_url in self._fruit_category_pages():
            try:
                html=self._fruit_category_html(page_url,headers)
                if not html:
                    continue
                for image_url in self._fruit_category_extract_urls(name,html,page_url):
                    try:
                        ih=dict(headers); ih["Referer"]=page_url
                        ir=requests.get(image_url,headers=ih,timeout=12,allow_redirects=True)
                        ctype=(ir.headers.get("content-type") or "").lower()
                        if not (ir.ok and len(ir.content)>300 and "image" in ctype):
                            continue
                        if self._combo_save_image_bytes(ir.content,cache,strict_square=True):
                            return True
                    except Exception:
                        pass
            except Exception:
                pass
        return False

    def _combo_try_exact_fandom_file(self, category, name, headers, cache):
        # Special:Redirect/file devolve o arquivo original quando o nome existe.
        # Isso evita usar og:image genérico ou screenshot/card da página.
        try:
            from urllib.parse import quote
            for filename in self._combo_file_candidates(category,name):
                url="https://blox-fruits.fandom.com/wiki/Special:Redirect/file/"+quote(filename,safe="")
                r=requests.get(url,headers=headers,timeout=8,allow_redirects=True)
                ctype=(r.headers.get("content-type") or "").lower()
                if r.ok and len(r.content)>300 and "image" in ctype:
                    if self._combo_save_image_bytes(r.content,cache,strict_square=(category in ("style","fruit","sword","gun"))):
                        return True
        except Exception:
            pass
        return False

    def _combo_try_infobox_icon(self, category, name, headers, cache):
        """Resolve o ícone atual pela infobox da página exata e rejeita mídia de showcase."""
        if category not in ("style","fruit","sword","gun"):
            return False
        try:
            title=self._combo_exact_title(category,name)
            api="https://blox-fruits.fandom.com/api.php"
            r=requests.get(api,params={"action":"parse","format":"json","page":title,"prop":"wikitext","redirects":1},headers=headers,timeout=7)
            if not r.ok:return False
            wt=(((r.json().get("parse") or {}).get("wikitext") or {}).get("*") or "")
            if not wt:return False
            target=re.sub(r"[^a-z0-9]+","",str(title).lower())
            bad=("old","previous","legacy","showcase","move","moveset","held","in-game","ingame","aura","banner","logo","awakening","awakened","transformation","user","using","gameplay","screenshot","render")
            candidates=[]
            for m in re.finditer(r"(?im)^\s*\|\s*([a-z0-9 _-]{1,32})\s*=\s*(?:\[\[)?(?:File|Image):([^\]|\n]+)",wt):
                field=(m.group(1) or "").strip().lower(); fn=(m.group(2) or "").strip()
                low=fn.lower(); flat=re.sub(r"[^a-z0-9]+","",low)
                if any(x in low for x in bad):continue
                score=0
                if category=="fruit":
                    # O campo/arquivo precisa identificar a FRUTA física. Um campo chamado
                    # apenas "Icon" costuma ser o símbolo da habilidade/shop.
                    fruitish=("fruit" in field or "physical" in field or "fruit" in low or "physical" in low or "model" in low)
                    if not fruitish:
                        continue
                    if "fruit icon" in field or "physical" in field: score+=30
                    if "fruit" in low: score+=18
                    if "physical" in low or "model" in low: score+=16
                    if "fruit icon" in low: score+=10
                    if target and target in flat: score+=18
                else:
                    if field in ("icon","inventory icon","image","style icon","weapon icon"):score+=24
                    if "icon" in field:score+=18
                    if "icon" in low:score+=14
                    if target and target in flat:score+=18
                    if category=="style" and ("style" in low or "combat" in low):score+=4
                    if category=="sword" and "sword" in low:score+=5
                    if category=="gun" and "gun" in low:score+=5
                if score>=24:candidates.append((score,fn))
            if not candidates:
                for fn in re.findall(r"(?i)\[\[(?:File|Image):([^\]|\n]+)",wt[:12000]):
                    low=fn.lower(); flat=re.sub(r"[^a-z0-9]+","",low)
                    if any(x in low for x in bad):continue
                    if category=="fruit":
                        if "fruit" not in low and "physical" not in low and "model" not in low:
                            continue
                        score=(20 if "fruit" in low else 0)+(16 if "physical" in low or "model" in low else 0)+(18 if target and target in flat else 0)
                    else:
                        score=(18 if "icon" in low else 0)+(18 if target and target in flat else 0)
                    if score>=30:candidates.append((score,fn.strip()))
            candidates.sort(key=lambda x:x[0],reverse=True)
            seen=set()
            for _,fn in candidates:
                if fn in seen:continue
                seen.add(fn)
                qr=requests.get(api,params={"action":"query","format":"json","titles":"File:"+fn,"prop":"imageinfo","iiprop":"url","iiurlwidth":384},headers=headers,timeout=7)
                if not qr.ok:continue
                for page in (qr.json().get("query",{}).get("pages",{}) or {}).values():
                    ii=(page.get("imageinfo") or [])
                    if not ii:continue
                    url=ii[0].get("thumburl") or ii[0].get("url")
                    if not url:continue
                    ir=requests.get(url,headers=headers,timeout=8,allow_redirects=True)
                    if ir.ok and len(ir.content)>300 and "image" in (ir.headers.get("content-type") or "").lower():
                        if self._combo_save_image_bytes(ir.content,cache,strict_square=True):return True
        except Exception:
            pass
        return False

    def _combo_try_fandom_parse_icon(self, category, name, headers, cache):
        """Find a page-specific icon file and reject screenshots/cards.

        This v3.14 path is intentionally limited to Fighting Styles and Fruits.
        """
        if category not in ("style", "fruit", "sword", "gun"):
            return False
        try:
            title=self._combo_exact_title(category,name)
            api="https://blox-fruits.fandom.com/api.php"
            pr=requests.get(api,params={"action":"parse","format":"json","page":title,"prop":"images","redirects":1},headers=headers,timeout=8)
            data=pr.json() if pr.ok else {}
            images=((data.get("parse") or {}).get("images") or [])
            compact=re.sub(r"[^a-z0-9]+","",str(name).lower())
            ranked=[]
            for fn in images:
                low=str(fn).lower(); flat=re.sub(r"[^a-z0-9]+","",low)
                if not low.endswith((".png",".webp",".jpg",".jpeg")):
                    continue
                if any(b in low for b in ("showcase","move","held","in-game","ingame","aura","banner","logo","gif","thumbnail","old","previous","legacy","awakening","awakened","transformation","gameplay","screenshot")):
                    continue
                score=0
                if compact and compact in flat: score+=12
                if category=="fruit":
                    # Para Fruit, plain "Icon" não serve. Exigimos referência clara à fruta física.
                    if "fruit" not in low and "physical" not in low and "model" not in low:
                        continue
                    if "fruit" in low: score+=18
                    if "physical" in low or "model" in low: score+=16
                    if "fruit icon" in low: score+=8
                else:
                    if "icon" in low: score+=14
                    if category=="style" and ("style" in low or "combat" in low): score+=4
                    if category=="sword" and "sword" in low: score+=5
                    if category=="gun" and "gun" in low: score+=5
                if score>=14: ranked.append((score,fn))
            ranked.sort(reverse=True)
            for _,fn in ranked[:8]:
                qr=requests.get(api,params={"action":"query","format":"json","titles":"File:"+fn,"prop":"imageinfo","iiprop":"url"},headers=headers,timeout=8)
                qd=qr.json() if qr.ok else {}
                for page in (qd.get("query",{}).get("pages",{}) or {}).values():
                    ii=(page.get("imageinfo") or [])
                    if not ii: continue
                    url=ii[0].get("thumburl") or ii[0].get("url")
                    if not url: continue
                    ir=requests.get(url,headers=headers,timeout=9,allow_redirects=True)
                    if ir.ok and len(ir.content)>300 and "image" in (ir.headers.get("content-type") or "").lower():
                        if self._combo_save_image_bytes(ir.content,cache,strict_square=True):
                            return True
        except Exception:
            pass
        return False

    def _combo_try_exact_mediawiki(self, category, name, headers, cache):
        # Consulta o título EXATO em vez de fazer busca aproximada.
        try:
            title=self._combo_exact_title(category,name)
            api="https://blox-fruits.fandom.com/api.php"
            params={"action":"query","format":"json","redirects":1,"titles":title,"prop":"pageimages","piprop":"thumbnail","pithumbsize":512}
            r=requests.get(api,params=params,headers=headers,timeout=8)
            data=r.json() if r.ok else {}
            pages=(data.get("query",{}).get("pages",{}) or {}).values()
            for page in pages:
                if page.get("missing") is not None:
                    continue
                thumb=(page.get("thumbnail") or {}).get("source")
                if not thumb:
                    continue
                ir=requests.get(thumb,headers=headers,timeout=9,allow_redirects=True)
                ctype=(ir.headers.get("content-type") or "").lower()
                if ir.ok and len(ir.content)>300 and "image" in ctype:
                    if self._combo_save_image_bytes(ir.content,cache,strict_square=(category in ("style","fruit","sword","gun"))):
                        return True
        except Exception:
            pass
        return False

    def _combo_page_is_specific(self, html_text, name):
        try:
            plain=re.sub(r"<[^>]+>"," ",str(html_text or ""))
            plain=re.sub(r"\s+"," ",plain).lower()
            target=str(name).strip().lower()
            return bool(target and (f">{target}<" in str(html_text or "").lower() or target in plain[:7000]))
        except Exception:
            return False

    def _combo_html_icon_candidates(self, category, name, html_text, page_url):
        # Para estilos/frutas, prioriza <img> que realmente pareça ser o ícone do item.
        # Não usa banner/og:image como primeira opção.
        if category not in ("style","fruit","sword","gun"):
            return []
        try:
            from urllib.parse import urljoin
            target=re.sub(r"[^a-z0-9]+"," ",str(name).lower()).strip()
            target_compact=re.sub(r"[^a-z0-9]+","",str(name).lower())
            found=[]
            for tag in re.findall(r"<img\b[^>]*>",str(html_text or ""),re.I):
                attrs={}
                for k,v1,v2 in re.findall(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')",tag):
                    attrs[k.lower()]=v1 or v2
                src=attrs.get("data-src") or attrs.get("data-lazy-src") or attrs.get("data-original") or attrs.get("src") or ""
                if not src or src.startswith("data:"):
                    continue
                meta=" ".join([attrs.get("alt",""),attrs.get("title",""),attrs.get("class",""),src]).lower()
                compact=re.sub(r"[^a-z0-9]+","",meta)
                bad=("logo","banner","header","screenshot","wallpaper","avatar","site-icon","favicon","shop-card","social")
                if any(x in meta for x in bad):
                    continue
                score=0
                if target and target in meta: score+=7
                if target_compact and target_compact in compact: score+=6
                if category=="fruit":
                    # Aceita somente mídia que se identifique como Fruit/Physical/Model.
                    if "fruit" not in meta and "physical" not in meta and "model" not in meta:
                        continue
                    if "fruit icon" in meta: score+=12
                    if "physical" in meta or "model" in meta: score+=10
                    if "fruit" in meta: score+=6
                else:
                    if category=="style" and ("fighting style" in meta or "style icon" in meta): score+=7
                    if category=="sword" and "sword" in meta: score+=7
                    if category=="gun" and "gun" in meta: score+=7
                    if re.search(r"(^|[ _-])icon([ _.-]|$)",meta): score+=5
                if score < 7:
                    continue
                found.append((score,urljoin(page_url,src.replace("&amp;","&"))))
            found.sort(key=lambda x:x[0],reverse=True)
            out=[]
            for _,url in found:
                if url not in out: out.append(url)
            return out[:10]
        except Exception:
            return []

    def _combo_try_page_icon(self, category, name, page_url, headers, cache):
        if category not in ("style","fruit","sword","gun"):
            return False
        try:
            r=requests.get(page_url,headers=headers,timeout=8,allow_redirects=True)
            if not r.ok or not self._combo_page_is_specific(r.text,name):
                return False
            for candidate in self._combo_html_icon_candidates(category,name,r.text,r.url or page_url):
                try:
                    ih=dict(headers); ih["Referer"]=r.url or page_url
                    ir=requests.get(candidate,headers=ih,timeout=9,allow_redirects=True)
                    ctype=(ir.headers.get("content-type") or "").lower()
                    if ir.ok and len(ir.content)>300 and "image" in ctype:
                        if self._combo_save_image_bytes(ir.content,cache,strict_square=True):
                            return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def _combo_source_pages(self, category, name):
        slug=self._combo_slug(name)
        if category=="fruit":
            return self._fruit_category_pages()
        if category=="style":
            title=self._combo_exact_title(category,name)
            return [
                f"https://blox-fruits.fandom.com/wiki/{urllib.parse.quote(str(title).replace(' ', '_'))}",
                f"https://bloxfruitswiki.org/wiki/{self._combo_slug(title)}/",
            ]
        if category in ("sword","gun"):
            title=self._combo_exact_title(category,name)
            return [
                f"https://blox-fruits.fandom.com/wiki/{urllib.parse.quote(str(title).replace(' ', '_'))}",
                f"https://bloxfruitswiki.org/wiki/{self._combo_slug(title)}/",
            ]
        return []

    def _combo_source_page(self, category, name):
        pages=self._combo_source_pages(category,name)
        return pages[0] if pages else ""

    def _combo_fetch_thumb_worker(self, category, name, callback=None):
        if category not in ("style","fruit","sword","gun"):
            return
        key=(category,name)
        if key in self._combo_fetching: return
        self._combo_fetching.add(key)
        try:
            with self._combo_fetch_sem:
                cache=self._combo_cache_path(category,name)
                if not os.path.isfile(cache):
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/apng,*/*;q=0.8",
                    }
                    if category == "fruit":
                        # v3.15: CDN independente primeiro; Fandom fica apenas como fallback.
                        if not self._combo_try_fruit_primary_cdn(name,headers,cache):
                            if not self._combo_try_fruit_api_file(name,headers,cache):
                                if not self._combo_try_fruit_direct_file(name,headers,cache):
                                    self._combo_try_fruit_category_image(name,headers,cache)
                    else:
                        # v3.14.9: weapons no longer use the broad page/parse fallbacks that
                        # could pull player screenshots, arena shots or legacy media. If an
                        # exact file / infobox icon is not found, the app now prefers a blank
                        # placeholder instead of a wrong image.
                        if not os.path.isfile(cache):
                            if not self._combo_try_exact_fandom_file(category,name,headers,cache):
                                self._combo_try_infobox_icon(category,name,headers,cache)
                if callback:
                    try: self.after(0, callback)
                    except Exception: pass
        finally:
            self._combo_fetching.discard(key)

    def _combo_local_icon_path(self, category, name):
        """Return a bundled Combo Planner icon from the user-provided local pack.

        v3.15.3 uses exact bundled assets for all four Combo Planner catalogs.
        Fruit, Style, Sword and Gun thumbnails are fully local and never depend on
        wiki/API availability or stale online cache entries.
        """
        if category not in ("fruit", "style", "sword", "gun"):
            return ""
        try:
            fn=f"{self._combo_slug(name)}.webp"
            p=_resource_path("zkstrap_assets","combo_icons",category,fn)
            return p if os.path.isfile(p) else ""
        except Exception:
            return ""

    def _combo_load_local_ctk_thumb(self, category, name, size):
        p=self._combo_local_icon_path(category,name)
        if not p:
            return None
        try:
            from PIL import Image
            im=Image.open(p).convert("RGBA")
            im.thumbnail((size,size),Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=im,dark_image=im,size=(size,size))
        except Exception:
            return None

    def _combo_get_ctk_thumb(self, category, name, size=72, callback=None, allow_network=False):
        key=(category,name,size)
        if key in self._combo_thumb_cache: return self._combo_thumb_cache[key]
        local=self._combo_load_local_ctk_thumb(category,name,size)
        if local is not None:
            self._combo_thumb_cache[key]=local
            return local
        # All four catalogs are strict-local in v3.15.3. If an asset is missing,
        # show the neutral placeholder instead of using cache or an online image.
        if category in ("fruit","style","sword","gun"):
            return None
        p=self._combo_cache_path(category,name)
        if os.path.isfile(p):
            try:
                from PIL import Image
                im=Image.open(p).convert("RGBA")
                im.thumbnail((size,size),Image.Resampling.LANCZOS)
                photo=ctk.CTkImage(light_image=im,dark_image=im,size=(size,size))
                self._combo_thumb_cache[key]=photo
                return photo
            except Exception:
                pass
        if allow_network and getattr(self,"_combo_online_thumbs",False) and (category,name) not in self._combo_fetching:
            threading.Thread(target=self._combo_fetch_thumb_worker,args=(category,name,callback),daemon=True).start()
        return None

    def _combo_prefetch_category(self, category, names, refresh_callback=None):
        if category in ("style","fruit","sword","gun"):
            return
        if category not in ("style","fruit","sword","gun") or not getattr(self,"_combo_online_thumbs",False): return
        token=(category,tuple(names))
        if token in getattr(self,"_combo_prefetching",set()): return
        self._combo_prefetching.add(token)
        workers=4 if category in ("style","fruit","sword","gun") else 1
        queue=[n for n in names if not self._combo_local_icon_path(category,n) and not os.path.isfile(self._combo_cache_path(category,n))]
        lock=threading.Lock(); last=[time.monotonic()]
        def runner():
            while True:
                with lock:
                    if not queue: return
                    name=queue.pop(0)
                self._combo_fetch_thumb_worker(category,name,callback=None)
                if refresh_callback:
                    now=time.monotonic()
                    with lock:
                        if now-last[0]>.35:
                            last[0]=now
                            try:self.after(0,refresh_callback)
                            except Exception:pass
        def worker():
            try:
                pool=[]
                for _ in range(max(1,workers)):
                    th=threading.Thread(target=runner,daemon=True); th.start(); pool.append(th)
                for th in pool: th.join()
            finally:
                self._combo_prefetching.discard(token)
                if refresh_callback:
                    try:self.after(0,refresh_callback)
                    except Exception:pass
        threading.Thread(target=worker,daemon=True).start()

    def _combo_warm_cache_safe(self):
        try:
            cat=self._combo_catalog()
            self._combo_prefetch_category("style",cat.get("style",[])[:6],None)
            self._combo_prefetch_category("fruit",cat.get("fruit",[])[:8],None)
        except Exception:
            pass

    def combo_abrir_fontes(self):
        t=TEMAS[self.tema_atual]; pt=self.idioma=="pt"
        win=ctk.CTkToplevel(self); win.title("Combo Planner — Fontes"); self._center_child_window(win,650,430); win.transient(self)
        box=ctk.CTkFrame(win,fg_color=t["panel"],corner_radius=14,border_width=1,border_color=t["border"]); box.pack(fill="both",expand=True,padx=14,pady=14)
        ctk.CTkLabel(box,text="FONTES & CRÉDITOS",font=ctk.CTkFont(size=20,weight="bold"),text_color=t["text"]).pack(anchor="w",padx=18,pady=(18,4))
        msg=("O catálogo textual usa a página oficial do Blox Fruits e guias públicos da comunidade. Miniaturas são carregadas sob demanda e armazenadas apenas em cache local. Os nomes e imagens pertencem aos respectivos criadores/detentores." if pt else "The text catalog uses the official Blox Fruits page and public community guides. Thumbnails are loaded on demand and stored only in local cache. Names and images belong to their respective creators/owners.")
        ctk.CTkLabel(box,text=msg,wraplength=590,justify="left",anchor="w",text_color=t.get("muted","gray")).pack(fill="x",padx=18,pady=(2,14))
        for label,url in self._combo_sources():
            ctk.CTkButton(box,text=label,command=lambda u=url:webbrowser.open(u),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],anchor="w").pack(fill="x",padx=18,pady=4)
        ctk.CTkButton(box,text="FECHAR" if pt else "CLOSE",command=win.destroy,fg_color=t["accent"],text_color="#050505").pack(fill="x",padx=18,pady=(16,18))

    def combo_refresh_library(self):
        frame=getattr(self,"combo_library_frame",None)
        if frame is None: return
        for w in frame.winfo_children():
            try:w.destroy()
            except Exception:pass
        t=TEMAS[self.tema_atual]; pt=self.idioma=="pt"
        if not self.combo_entries:
            ctk.CTkLabel(frame,text="Nenhum combo salvo ainda. Clique em ＋ NOVO COMBO." if pt else "No saved combos yet. Click ＋ NEW COMBO.",text_color=t.get("muted","gray")).pack(fill="x",padx=8,pady=22)
            return
        for entry in reversed(self.combo_entries):
            if not isinstance(entry, dict):
                continue
            card=ctk.CTkFrame(frame,fg_color=t["card"],corner_radius=12,border_width=1,border_color=t["card_active"]); card.pack(fill="x",padx=2,pady=6)
            head=ctk.CTkFrame(card,fg_color="transparent"); head.pack(fill="x",padx=12,pady=(10,4))
            ctk.CTkLabel(head,text=str(entry.get("name") or "Combo"),font=ctk.CTkFont(size=13,weight="bold"),text_color=t["text"]).pack(side="left")
            buttons=ctk.CTkFrame(head,fg_color="transparent"); buttons.pack(side="right")
            ctk.CTkButton(buttons,text="EDITAR" if pt else "EDIT",width=66,height=28,command=lambda e=entry:self.combo_editar(e),fg_color=t["card_active"],text_color=t["accent"]).pack(side="left",padx=2)
            ctk.CTkButton(buttons,text="DUP",width=48,height=28,command=lambda e=entry:self.combo_duplicar(e),fg_color=t["card_active"],text_color=t["text"]).pack(side="left",padx=2)
            ctk.CTkButton(buttons,text="×",width=34,height=28,command=lambda e=entry:self.combo_excluir(e),fg_color="#7A2431",hover_color="#A52E40").pack(side="left",padx=2)
            load=ctk.CTkFrame(card,fg_color=t["card_active"],corner_radius=9); load.pack(fill="x",padx=12,pady=5)
            for cat,key,label in (("style","style","ESTILO" if pt else "STYLE"),("fruit","fruit","FRUTA" if pt else "FRUIT"),("sword","sword","SWORD"),("gun","gun","GUN")):
                slot=ctk.CTkFrame(load,fg_color="transparent"); slot.pack(side="left",expand=True,fill="x",padx=6,pady=7)
                value=entry.get(key,"") or (entry.get("slot3","") if key=="sword" else (entry.get("slot4","") if key=="gun" else ""))
                im=self._combo_get_ctk_thumb(cat,value,42,callback=None,allow_network=False) if value else None
                ctk.CTkLabel(slot,text=("" if im else "◇"),image=im,text_color=t["accent"],width=46).pack(side="left",padx=(0,5))
                ctk.CTkLabel(slot,text=f"{label}\n{value or '—'}",justify="left",anchor="w",font=ctk.CTkFont(size=8,weight="bold"),text_color=t["text"]).pack(side="left")
            preview=str(entry.get("combo","")).strip().replace("\n","  →  ")
            if len(preview)>150: preview=preview[:147]+"..."
            ctk.CTkLabel(card,text=(preview or ("Sem sequência escrita." if pt else "No sequence written.")),text_color=t.get("muted","gray"),justify="left",anchor="w",wraplength=790).pack(fill="x",padx=14,pady=(4,11))

    def combo_novo(self):
        self._combo_open_editor(None)

    def combo_editar(self, entry):
        self._combo_open_editor(entry)

    def combo_duplicar(self, entry):
        cp=dict(entry); cp["id"]=uuid.uuid4().hex; cp["name"]=(str(cp.get("name") or "Combo")+" — cópia")
        self.combo_entries.append(cp)
        if len(self.combo_entries)>=5:self._unlock_secret_theme("Architect","5 builds salvas no Combo Planner")
        self.salvar_config_app(); self.combo_refresh_library()

    def combo_excluir(self, entry):
        if not messagebox.askyesno("Combo Planner","Excluir este combo?" if self.idioma=="pt" else "Delete this combo?"): return
        eid=entry.get("id"); self.combo_entries=[e for e in self.combo_entries if e.get("id")!=eid]; self.salvar_config_app(); self.combo_refresh_library()

    def _combo_open_editor(self, existing=None):
        t=TEMAS[self.tema_atual]; pt=self.idioma=="pt"; data=dict(existing or {})
        data.setdefault("id",uuid.uuid4().hex); data.setdefault("name",""); data.setdefault("style",""); data.setdefault("fruit",""); data.setdefault("sword", str(data.get("sword", data.get("slot3", "")) or "")); data.setdefault("gun", str(data.get("gun", data.get("slot4", "")) or "")); data.setdefault("combo","")
        win=ctk.CTkToplevel(self); win.title("Combo Planner — Editor"); self._center_child_window(win,900,690); win.transient(self)
        root=ctk.CTkFrame(win,fg_color=t["panel"],corner_radius=14,border_width=1,border_color=t["border"]); root.pack(fill="both",expand=True,padx=12,pady=12)
        title=ctk.CTkLabel(root,text="NOVO COMBO" if not existing and pt else ("NEW COMBO" if not existing else ("EDITAR COMBO" if pt else "EDIT COMBO")),font=ctk.CTkFont(size=20,weight="bold"),text_color=t["text"]); title.pack(anchor="w",padx=16,pady=(14,4))
        step=ctk.CTkLabel(root,text="",font=ctk.CTkFont(family="Consolas",size=9,weight="bold"),text_color=t["accent"]); step.pack(anchor="w",padx=16,pady=(0,6))
        area=ctk.CTkFrame(root,fg_color="transparent"); area.pack(fill="both",expand=True,padx=14,pady=4)
        footer=ctk.CTkFrame(root,fg_color="transparent"); footer.pack(fill="x",padx=14,pady=(4,12))
        state={"idx":0}; steps=["style","fruit","sword","gun","combo"]

        def clear():
            for w in area.winfo_children():
                try:w.destroy()
                except Exception:pass
        def choose_grid(category):
            clear(); names=self._combo_catalog()[category]
            search=ctk.CTkEntry(area,placeholder_text="Pesquisar..." if pt else "Search..."); search.pack(fill="x",padx=4,pady=(2,8))
            sc=ctk.CTkScrollableFrame(area,fg_color=t["card"],corner_radius=10); sc.pack(fill="both",expand=True,padx=4,pady=2); self._install_smooth_scroll(sc,1)
            grid=ctk.CTkFrame(sc,fg_color="transparent"); grid.pack(fill="x",expand=True)
            def render(*_,prefetch=True):
                for w in grid.winfo_children(): w.destroy()
                q=search.get().strip().lower(); shown=[n for n in names if q in n.lower()]
                for i,n in enumerate(shown):
                    grid.grid_columnconfigure(i%5,weight=1,uniform="combo")
                    selected=(data.get(category)==n); img=self._combo_get_ctk_thumb(category,n,64,callback=None,allow_network=False)
                    card=ctk.CTkButton(grid,text=n,image=img,compound="top",height=122,width=130,fg_color=t["accent"] if selected else t["card_active"],hover_color=t["hover"],text_color="#050505" if selected else t["text"],command=lambda name=n:(self._play_ui_sound("combo_select",0),data.__setitem__(category,name),render(prefetch=False)))
                    card.grid(row=i//5,column=i%5,padx=5,pady=5,sticky="nsew")
                if prefetch and shown: self._combo_prefetch_category(category,shown,lambda:render(prefetch=False))
            search.bind("<KeyRelease>",lambda e:render(prefetch=True)); render(prefetch=True)


        def combo_text():
            clear(); ctk.CTkLabel(area,text="FINALIZAR BUILD" if pt else "FINISH BUILD",font=ctk.CTkFont(size=16,weight="bold"),text_color=t["text"]).pack(anchor="w",padx=8,pady=(8,4))
            ent=ctk.CTkEntry(area,placeholder_text="Nome da build — ex.: Gravity Main" if pt else "Build name — e.g. Gravity Main",height=42); ent.insert(0,str(data.get("name",""))); ent.pack(fill="x",padx=8,pady=(6,8))
            ctk.CTkLabel(area,text="SEQUÊNCIA DO COMBO" if pt else "COMBO SEQUENCE",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(anchor="w",padx=8,pady=(8,3))
            txt=ctk.CTkTextbox(area,height=260,fg_color=t["card"],border_width=1,border_color=t["card_active"],text_color=t["text"]); txt.pack(fill="both",expand=True,padx=8,pady=(2,8)); txt.insert("0.0",str(data.get("combo","")))
            def sync_name(*_): data["name"]=ent.get().strip()
            def sync_txt(*_): data["combo"]=txt.get("0.0","end").strip()
            ent.bind("<KeyRelease>",sync_name); txt.bind("<KeyRelease>",sync_txt)
        def render_step():
            idx=state["idx"]; key=steps[idx]
            labels_pt=["1/5 • ESTILO DE LUTA","2/5 • FRUTA","3/5 • SWORD","4/5 • GUN","5/5 • ESCREVER COMBO"]
            labels_en=["1/5 • FIGHTING STYLE","2/5 • FRUIT","3/5 • SWORD","4/5 • GUN","5/5 • WRITE COMBO"]
            step.configure(text=(labels_pt if pt else labels_en)[idx])
            if key in ("style","fruit","sword","gun"): choose_grid(key)
            else: combo_text()
            back.configure(state="normal" if idx>0 else "disabled")
            nextb.configure(text=("SALVAR BUILD" if pt else "SAVE BUILD") if idx==len(steps)-1 else ("PRÓXIMO  →" if pt else "NEXT  →"))
        def prev(): self._play_ui_sound("back",0); state["idx"]=max(0,state["idx"]-1); render_step()
        def nxt():
            self._play_ui_sound("combo_next",0)
            key=steps[state["idx"]]
            if key in ("style","fruit","sword","gun") and not data.get(key):
                messagebox.showwarning("Combo Planner","Escolha uma opção antes de continuar." if pt else "Choose an option before continuing."); return
            if state["idx"]<len(steps)-1: state["idx"]+=1; render_step(); return
            if not str(data.get("name","")).strip(): data["name"]="Minha build" if pt else "My build"
            data["slot3"] = str(data.get("sword", "") or "")
            data["slot4"] = str(data.get("gun", "") or "")
            if existing:
                for i,e in enumerate(self.combo_entries):
                    if e.get("id")==existing.get("id"): self.combo_entries[i]=dict(data); break
            else: self.combo_entries.append(dict(data))
            if len(self.combo_entries)>=5:self._unlock_secret_theme("Architect","5 builds salvas no Combo Planner")
            self._play_ui_sound("combo_save",0); self.salvar_config_app(); self.combo_refresh_library(); win.destroy()
        back=ctk.CTkButton(footer,text="← VOLTAR" if pt else "← BACK",command=prev,fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],width=140); back.pack(side="left")
        nextb=ctk.CTkButton(footer,text="PRÓXIMO  →" if pt else "NEXT  →",command=nxt,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",width=180); nextb.pack(side="right")
        render_step()



    # ------------------------------------------------------------------
    # BLOX HUB v3.14 — Roulette / Creator / Setups / Spotify
    # ------------------------------------------------------------------
    def _roulette_catalog_safe(self):
        cat=self._combo_catalog()
        return {k:list(cat.get(k,[])) for k in ("style","fruit","sword","gun")}

    def _fruit_rarity_groups(self):
        return {
            "COMMON":["Rocket","Spin","Blade","Spring","Bomb","Smoke","Spike"],
            "UNCOMMON":["Flame","Ice","Sand","Dark","Eagle","Diamond"],
            "RARE":["Light","Rubber","Ghost","Magma"],
            "LEGENDARY":["Quake","Buddha","Love","Creation","Spider","Sound","Phoenix","Portal","Lightning","Pain","Blizzard"],
            "MYTHICAL":["Gravity","Mammoth","T-Rex","Dough","Shadow","Venom","Gas","Spirit","Tiger","Yeti","Magnet","Kitsune","Control","Dragon"],
        }

    def _sword_rarity_groups(self):
        return {
            "COMMON":["Cutlass","Dual Katana","Katana"],
            "UNCOMMON":["Iron Mace","Shark Saw","Triple Katana","Twin Hooks"],
            "RARE":["Dragon Trident","Dual-Headed Blade","Flail","Gravity Blade","Longsword","Pipe","Soul Cane","Trident","Wardens Sword"],
            "LEGENDARY":["Bisento","Buddy Sword","Canvander","Dark Dagger","Dragonheart","Fox Lamp","Koko","Midnight Blade","Oroshi","Pole (1st Form)","Pole (2nd Form)","Rengoku","Saber","Saishi","Shark Anchor","Shizu","Spikey Trident","Tushita","Yama"],
            "MYTHICAL":["Cursed Dual Katana","Dark Blade","Dog Blade","Hallow Scythe","True Triple Katana"],
        }

    def _gun_rarity_groups(self):
        return {
            "COMMON":["Slingshot"],
            "UNCOMMON":["Flintlock","Musket"],
            "RARE":["Acidum Rifle","Bizarre Revolver","Cannon","Dual Flintlock","Magma Blaster","Refined Slingshot"],
            "LEGENDARY":["Bazooka","Dragonstorm","Kabucha","Venom Bow"],
            "MYTHICAL":["Skull Guitar"],
        }

    def _roulette_rarity_groups(self, category):
        if category=="fruit": return self._fruit_rarity_groups()
        if category=="sword": return self._sword_rarity_groups()
        if category=="gun": return self._gun_rarity_groups()
        return {}

    def _roulette_allowed(self, category):
        names=list(self._roulette_catalog_safe().get(category,[]))
        inv=getattr(self,"roulette_inventory",{}) or {}
        data=inv.get(category,{}) if isinstance(inv.get(category,{}),dict) else {}
        if bool(data.get("all",False)):
            return names
        allowed=data.get("allowed")
        if isinstance(allowed,list) and allowed:
            chosen=[n for n in names if n in set(allowed)]
            return chosen or names
        return names

    def roulette_inventory_dialog(self):
        """Inventário estável da Roulette.

        v3.14.3 remove o caminho baseado em tk.BooleanVar/CTkCheckBox que podia
        abortar a montagem da janela no Windows e deixar somente um painel vazio.
        Os itens agora são botões de estado simples, todos mantidos em sets Python.
        """
        t=TEMAS[self.tema_atual]; pt=self.idioma=="pt"
        win=ctk.CTkToplevel(self); win.title("Build Roulette — Inventário"); self._center_child_window(win,860,720); win.transient(self)
        closed=[False]
        def close_inventory(*_):
            if closed[0]: return
            closed[0]=True
            try:self._play_ui_sound("close",0)
            except Exception:pass
            try:win.destroy()
            except Exception:pass
        win.protocol("WM_DELETE_WINDOW",close_inventory); win.bind("<Escape>",close_inventory)

        root=ctk.CTkFrame(win,fg_color=t["panel"],corner_radius=14,border_width=1,border_color=t["border"]); root.pack(fill="both",expand=True,padx=12,pady=12)
        head=ctk.CTkFrame(root,fg_color="transparent"); head.pack(fill="x",padx=16,pady=(12,2))
        ctk.CTkLabel(head,text="INVENTÁRIO DA ROLETA" if pt else "ROULETTE INVENTORY",font=ctk.CTkFont(size=20,weight="bold"),text_color=t["text"]).pack(side="left")
        ctk.CTkButton(head,text="×",width=42,height=34,command=close_inventory,fg_color=t["card_active"],hover_color="#7A2431",text_color=t["text"]).pack(side="right")
        desc=("Isso só filtra o sorteio. Desative o que você não quer que apareça. Em Fruits, isso também serve para não gastar uma fruta difícil de conseguir ou a única unidade que você tem." if pt else "This only filters the roll. Disable anything you do not want to appear. For Fruits, this also avoids spending a rare or single copy you want to keep.")
        ctk.CTkLabel(root,text=desc,wraplength=790,justify="left",anchor="w",text_color=t.get("muted","gray")).pack(fill="x",padx=16,pady=(0,8))

        catalog=self._roulette_catalog_safe(); inv=getattr(self,"roulette_inventory",{}) or {}
        selected={}
        for cat in ("style","fruit","sword","gun"):
            names=list(catalog.get(cat,[])); cfg=inv.get(cat,{}) if isinstance(inv.get(cat,{}),dict) else {}
            raw=cfg.get("allowed") if isinstance(cfg.get("allowed"),list) else None
            selected[cat]=set(names if (cfg.get("all",True) or raw is None) else [n for n in raw if n in names])
            if not selected[cat]: selected[cat]=set(names)

        tabbar=ctk.CTkFrame(root,fg_color="transparent"); tabbar.pack(fill="x",padx=14,pady=(2,5))
        content=ctk.CTkFrame(root,fg_color="transparent"); content.pack(fill="both",expand=True,padx=14,pady=4)
        state={"cat":"style"}; item_buttons={}

        def item_style(cat,name):
            on=name in selected.get(cat,set())
            return {"fg_color":t["accent"] if on else t["card_active"], "text_color":"#050505" if on else t["text"]}

        def render_category(cat):
            state["cat"]=cat
            for w in content.winfo_children():
                try:w.destroy()
                except Exception:pass
            item_buttons.clear()
            names=list(catalog.get(cat,[]))
            tools=ctk.CTkFrame(content,fg_color="transparent"); tools.pack(fill="x",pady=(2,7))
            ctk.CTkLabel(tools,text={"style":"FIGHTING STYLES","fruit":"FRUITS","sword":"SWORDS","gun":"GUNS"}.get(cat,cat.upper()),text_color=t["accent"],font=ctk.CTkFont(size=13,weight="bold")).pack(side="left")
            def set_all(value):
                selected[cat]=set(names) if value else set()
                render_category(cat)
            ctk.CTkButton(tools,text="TODOS" if pt else "ALL",width=76,height=28,command=lambda:set_all(True),fg_color=t["card_active"],text_color=t["accent"]).pack(side="right",padx=2)
            ctk.CTkButton(tools,text="NENHUM" if pt else "NONE",width=82,height=28,command=lambda:set_all(False),fg_color=t["card_active"],text_color=t["text"]).pack(side="right",padx=2)
            if cat in ("fruit","sword","gun"):
                rar=ctk.CTkFrame(content,fg_color="transparent"); rar.pack(fill="x",pady=(0,7))
                ctk.CTkLabel(rar,text="SELEÇÃO EM MASSA POR RARIDADE",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left",padx=(0,6))
                def toggle_group(rn):
                    group=set(self._roulette_rarity_groups(cat).get(rn,[])) & set(names)
                    if group and group.issubset(selected[cat]): selected[cat]-=group
                    else: selected[cat]|=group
                    render_category(cat)
                for rn in self._roulette_rarity_groups(cat):
                    ctk.CTkButton(rar,text=rn,width=78,height=26,command=lambda r=rn:toggle_group(r),fg_color=t["card_active"],text_color=t["accent"],font=ctk.CTkFont(size=7,weight="bold")).pack(side="left",padx=2)

            scroll=ctk.CTkScrollableFrame(content,fg_color=t["card"],corner_radius=12); scroll.pack(fill="both",expand=True)
            grid=ctk.CTkFrame(scroll,fg_color="transparent"); grid.pack(fill="x",expand=True,padx=8,pady=8)
            def toggle(name):
                if name in selected[cat]: selected[cat].discard(name)
                else: selected[cat].add(name)
                b=item_buttons.get(name)
                if b:
                    try:b.configure(**item_style(cat,name))
                    except Exception:pass
            for i,name in enumerate(names):
                st=item_style(cat,name)
                b=ctk.CTkButton(grid,text=name,height=38,corner_radius=9,command=lambda n=name:toggle(n),fg_color=st["fg_color"],hover_color=t["hover"],text_color=st["text_color"],font=ctk.CTkFont(size=9,weight="bold"))
                b.grid(row=i//3,column=i%3,sticky="ew",padx=5,pady=5); grid.grid_columnconfigure(i%3,weight=1,uniform="inv")
                item_buttons[name]=b

        def select_tab(cat):
            try:self._play_ui_sound("nav",.02)
            except Exception:pass
            render_category(cat)
            for key,b in tab_buttons.items():
                try:b.configure(fg_color=t["accent"] if key==cat else t["card_active"],text_color="#050505" if key==cat else t["text"])
                except Exception:pass
        tab_buttons={}
        for cat,label in (("style","FIGHTING STYLES"),("fruit","FRUITS"),("sword","SWORDS"),("gun","GUNS")):
            b=ctk.CTkButton(tabbar,text=label,height=36,command=lambda c=cat:select_tab(c),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"])
            b.pack(side="left",expand=True,fill="x",padx=3); tab_buttons[cat]=b

        def save():
            for cat in ("style","fruit","sword","gun"):
                if not selected.get(cat):
                    messagebox.showwarning("Build Roulette","Escolha pelo menos uma opção em cada categoria."); return
            out={}
            for cat in ("style","fruit","sword","gun"):
                names=list(catalog.get(cat,[])); allowed=[n for n in names if n in selected[cat]]
                out[cat]={"all":len(allowed)==len(names),"allowed":allowed}
            self.roulette_inventory=out; self.salvar_config_app(); self._play_ui_sound("confirm",0); close_inventory()

        foot=ctk.CTkFrame(root,fg_color="transparent"); foot.pack(fill="x",padx=14,pady=(5,14))
        ctk.CTkButton(foot,text="CANCELAR" if pt else "CANCEL",command=close_inventory,fg_color=t["card_active"],text_color=t["text"],height=42,width=150).pack(side="left",padx=(0,5))
        ctk.CTkButton(foot,text="SALVAR FILTROS" if pt else "SAVE FILTERS",command=save,fg_color=t["accent"],text_color="#050505",height=42).pack(side="left",expand=True,fill="x")
        select_tab("style")
        try:win.after(80,lambda:(win.lift(),win.focus_force()))
        except Exception:pass

    def _roulette_set_visual(self, category, name, final=False):
        slot=getattr(self,"roulette_slots",{}).get(category)
        if not slot: return
        img_lbl,name_lbl=slot
        size=78
        im=self._combo_get_ctk_thumb(category,name,size,callback=None,allow_network=False)
        if im is None:
            # Request in background; when ready only refresh the current item.
            def cb(cat=category,n=name):
                try:
                    current=getattr(self,"_roulette_current_names",{}).get(cat)
                    if current==n:self._roulette_set_visual(cat,n,final=final)
                except Exception: pass
            self._combo_get_ctk_thumb(category,name,size,callback=cb,allow_network=True)
        try:
            img_lbl.configure(text="" if im else "◇",image=im,text_color=TEMAS[self.tema_atual]["accent"])
            img_lbl.image=im
            name_lbl.configure(text=name)
            if final:
                img_lbl.configure(fg_color=TEMAS[self.tema_atual].get("card","transparent"),corner_radius=12)
                self.after(180,lambda l=img_lbl: l.configure(fg_color="transparent"))
        except Exception: pass

    def roulette_start(self):
        if bool(getattr(self,"_roulette_running",False)): return
        catalogs={c:self._roulette_allowed(c) for c in ("style","fruit","sword","gun")}
        try: mode=str(self.roulette_mode.get())
        except Exception: mode="ALEATÓRIO TOTAL"
        if mode=="RARIDADE BAIXA":
            low=set(self._fruit_rarity_groups().get("COMMON",[])+self._fruit_rarity_groups().get("UNCOMMON",[])+self._fruit_rarity_groups().get("RARE",[]))
            filtered=[n for n in catalogs.get("fruit",[]) if n in low]
            if filtered:catalogs["fruit"]=filtered
        if any(not v for v in catalogs.values()):
            messagebox.showwarning("Build Roulette","Configure o inventário da roleta primeiro."); return
        result={c:random.choice(v) for c,v in catalogs.items()}
        self._roulette_running=True; self._roulette_current_names={}
        order=["style","fruit","sword","gun"]
        def reveal(index=0):
            if index>=len(order):
                self._roulette_running=False
                self.last_roulette_build=dict(result)
                item={"id":uuid.uuid4().hex,"time":datetime.now().isoformat(timespec="seconds"),**result}
                self.roulette_history=(list(getattr(self,"roulette_history",[]))+[item])[-60:]
                self.roulette_roll_count=int(getattr(self,"roulette_roll_count",0) or 0)+1
                if self.roulette_roll_count>=20:self._unlock_secret_theme("Jackpot","20 builds sorteadas na Roulette")
                self.salvar_config_app(); self.roulette_refresh_history(); self._play_ui_sound("success",0)
                self.show_toast("BUILD SORTEADA","Fighting Style + Fruit + Sword + Gun definidos.",kind="success",duration=2600)
                return
            cat=order[index]; names=catalogs[cat]; frames=18
            def tick(i=0):
                if i<frames:
                    # Accelerated roll: random thumbnails, then decelerate near the end.
                    n=random.choice(names); self._roulette_current_names[cat]=n; self._roulette_set_visual(cat,n,False)
                    delay=45+int((i/max(1,frames-1))**2*105)
                    self.after(delay,lambda:tick(i+1))
                else:
                    n=result[cat]; self._roulette_current_names[cat]=n; self._roulette_set_visual(cat,n,True); self._play_ui_sound("combo_select",0)
                    self.after(360,lambda:reveal(index+1))
            tick()
        self._play_ui_sound("open",0); reveal(0)

    def roulette_favorite_current(self):
        b=dict(getattr(self,"last_roulette_build",{}) or {})
        if not b:
            self.show_toast("BUILD ROULETTE","Sorteie uma build primeiro.",kind="info"); return
        favs=list(getattr(self,"roulette_favorites",[]))
        key=tuple(b.get(k) for k in ("style","fruit","sword","gun"))
        if any(tuple(x.get(k) for k in ("style","fruit","sword","gun"))==key for x in favs if isinstance(x,dict)):
            self.show_toast("BUILD ROULETTE","Essa combinação já está nos favoritos.",kind="info"); return
        b["id"]=uuid.uuid4().hex; b["time"]=datetime.now().isoformat(timespec="seconds"); favs.append(b)
        self.roulette_favorites=favs[-60:]; self.salvar_config_app(); self._play_ui_sound("confirm",0); self.roulette_refresh_history()

    def roulette_save_to_combo(self):
        b=dict(getattr(self,"last_roulette_build",{}) or {})
        if not b:
            self.show_toast("BUILD ROULETTE","Sorteie primeiro.",kind="info"); return
        entry={"id":uuid.uuid4().hex,"name":f"Roulette • {b.get('fruit','Build')}","style":b.get("style",""),"fruit":b.get("fruit",""),"sword":b.get("sword",""),"gun":b.get("gun",""),"slot3":b.get("sword",""),"slot4":b.get("gun",""),"combo":""}
        self.combo_entries.append(entry)
        if len(self.combo_entries)>=5:self._unlock_secret_theme("Architect","5 builds salvas no Combo Planner")
        self.salvar_config_app(); self.combo_refresh_library(); self._play_ui_sound("combo_save",0)
        self.show_toast("SALVO NO COMBO PLANNER","A build completa foi salva; abra o Planner para escrever ou ajustar a sequência.",kind="success",duration=3800)

    def roulette_create_challenge(self):
        b=dict(getattr(self,"last_roulette_build",{}) or {})
        if not b:
            self.show_toast("BUILD ROULETTE","Sorteie primeiro.",kind="info"); return
        self._creator_context_build=b
        self.show_page("creator",animate=True)
        try:self.creator_generate_challenges(context_build=b)
        except Exception: pass

    def roulette_refresh_history(self):
        frame=getattr(self,"roulette_history_frame",None)
        if not frame:return
        try:
            for w in frame.winfo_children():w.destroy()
        except Exception:return
        t=TEMAS[self.tema_atual]; pt=self.idioma=="pt"
        items=list(getattr(self,"roulette_history",[]))[-8:][::-1]
        if not items:
            ctk.CTkLabel(frame,text="Nenhuma build sorteada ainda." if pt else "No rolls yet.",text_color=t.get("muted","gray")).pack(padx=16,pady=14); return
        for x in items:
            row=ctk.CTkFrame(frame,fg_color=t["card_active"],corner_radius=10); row.pack(fill="x",padx=12,pady=4)
            ctk.CTkLabel(row,text=f"{x.get('style','—')}  •  {x.get('fruit','—')}  •  {x.get('sword','—')}  •  {x.get('gun','—')}",text_color=t["text"],font=ctk.CTkFont(size=10,weight="bold")).pack(side="left",padx=12,pady=9)

    # ---------------- Creator Mode ----------------
    def _creator_ideas(self):
        return [
            "BUILD ROULETTE — Sorteie uma build e continue usando ela até conseguir uma vitória.",
            "SHORTS — Use uma build da Build Roulette e grave um Shorts mostrando um combo bonito que funcione em player real.",
            "BUILD ESQUECIDA — Use a Build Roulette para gerar uma combinação que você quase nunca usaria e tente fazer ela funcionar no PvP.",
            "BUILD ROULETTE — Pegue uma build estranha sorteada pela roleta e ajuste a sequência até criar um combo funcional.",
            "3 BUILDS, 3 CHANCES — Gere 3 builds diferentes na Build Roulette. Faça exatamente 1 PvP com cada build, sem rerollar antes de usar cada uma.",
            "ROLETA PROGRESSIVA — Comece com uma build da Build Roulette e, depois de cada vitória, troque apenas uma parte da combinação.",
            "BOUNTY HUNT — Escolha uma limitação do Creator Mode e faça uma sessão de bounty hunting obedecendo ela.",
            "CAÇADA POR FRUTA — Use uma build sorteada pela Build Roulette e tente vencer um jogador que esteja usando Portal, Dragon ou Kitsune.",
            "WIN STREAK — Use uma combinação que você quase nunca joga e tente manter uma sequência de vitórias.",
            "BUILD ROULETTE / RARIDADE BAIXA — Gere uma build priorizando opções de raridade mais baixa e veja até onde consegue levar ela no PvP.",
            "BUILD ROULETTE — Continue sorteando builds até conseguir um clip realmente bonito em player real.",
            "COMBO LAB — Crie um full combo e um mini combo diferentes usando a mesma Fruit + Fighting Style.",
            "HIGHLIGHTS — Use uma build sorteada pela Build Roulette durante 30 minutos e salve os melhores momentos.",
            "BUILD ROULETTE — Pegue uma build que parece ruim e transforme ela em uma ideia de vídeo que realmente funcione.",
        ]

    def creator_generate_idea(self):
        ideas=self._creator_ideas(); used=set(getattr(self,"creator_used_ideas",[])); pool=[x for x in ideas if x not in used]
        if not pool:
            used=set(); pool=list(ideas); self.creator_used_ideas=[]
        idea=random.choice(pool); self.creator_used_ideas.append(idea); self._creator_current_idea=idea
        try:self.creator_idea_label.configure(text=idea)
        except Exception:pass
        self.salvar_config_app(); self._play_ui_sound("select",0)

    def creator_reset_used_ideas(self):
        self.creator_used_ideas=[]; self.salvar_config_app(); self.show_toast("CREATOR MODE","Histórico de ideias resetado.",kind="success")

    def creator_save_current_project(self):
        idea=str(getattr(self,"_creator_current_idea","") or "").strip()
        if not idea:
            self.show_toast("CREATOR MODE","Gere uma ideia primeiro.",kind="info"); return
        name=ctk.CTkInputDialog(text="Nome do projeto:",title="Creator Mode").get_input()
        if not name:return
        self.creator_projects.append({"id":uuid.uuid4().hex,"name":name.strip()[:80],"idea":idea,"status":"Planejado","created":datetime.now().isoformat(timespec="seconds")})
        self.creator_projects=self.creator_projects[-80:]; self.salvar_config_app(); self.creator_refresh_projects(); self._play_ui_sound("confirm",0)

    def creator_delete_project(self,pid):
        self.creator_projects=[x for x in self.creator_projects if isinstance(x,dict) and x.get("id")!=pid]; self.salvar_config_app(); self.creator_refresh_projects()

    def creator_refresh_projects(self):
        frame=getattr(self,"creator_projects_frame",None)
        if not frame:return
        try:
            # Preserve section header/subtitle labels by only destroying rows tagged manually.
            for w in list(frame.winfo_children()):
                if getattr(w,"_zk_project_row",False):w.destroy()
        except Exception:return
        t=TEMAS[self.tema_atual]
        for p in list(getattr(self,"creator_projects",[]))[::-1][:12]:
            row=ctk.CTkFrame(frame,fg_color=t["card_active"],corner_radius=10); row._zk_project_row=True; row.pack(fill="x",padx=12,pady=4)
            ctk.CTkLabel(row,text=f"{p.get('name','Projeto')}\n{p.get('idea','')}",justify="left",anchor="w",text_color=t["text"],wraplength=700).pack(side="left",fill="x",expand=True,padx=12,pady=8)
            ctk.CTkButton(row,text="×",width=34,command=lambda pid=p.get("id"):self.creator_delete_project(pid),fg_color="#7A2431",hover_color="#A52E40").pack(side="right",padx=8)

    def _creator_templates(self):
        """Pool final aprovada para v3.16. SECRET não aparece no seletor; cai raramente."""
        return [
            # FÁCIL
            {"difficulty":"Fácil","title":"3 KILLS","desc":"Consiga 3 kills em PvP.","type":"kills","target":3},
            {"difficulty":"Fácil","title":"WIN STREAK 3","desc":"Consiga 3 vitórias seguidas. Só contam players de 5M+; 2.5M não conta.","type":"streak","target":3,"min_bounty":5000000},
            {"difficulty":"Fácil","title":"+50K BOUNTY","desc":"Ganhe +50k de bounty.","type":"bounty","target":50000},
            {"difficulty":"Fácil","title":"STARTER DE STYLE","desc":"Consiga uma kill iniciando a luta/entrada com o Fighting Style.","type":"manual","target":1},
            {"difficulty":"Fácil","title":"SWORD NO COMBO","desc":"Consiga uma kill usando a Sword como parte importante do combo.","type":"manual","target":1},
            {"difficulty":"Fácil","title":"2 KILLS SEM V4","desc":"Consiga 2 kills sem usar V4.","type":"kills","target":2},
            {"difficulty":"Fácil","title":"15 MIN SEM MORRER","desc":"Fique 15 minutos indo PvP sem morrer.","type":"timer","target":900,"reset_on_death":True},
            {"difficulty":"Fácil","title":"3 KILLS / COMBOS DIFERENTES","desc":"Consiga 3 kills usando combos diferentes. Se vier vinculada a uma build da Roulette, passa a contar como Médio.","type":"kills","target":3,"roulette_bump":"Médio"},
            {"difficulty":"Fácil","title":"VIRADA","desc":"Vença uma luta depois de começar tomando o primeiro combo.","type":"manual","target":1},

            # MÉDIO
            {"difficulty":"Médio","title":"5 KILLS","desc":"Consiga 5 kills.","type":"kills","target":5},
            {"difficulty":"Médio","title":"WIN STREAK 5","desc":"Consiga 5 vitórias seguidas. Só contam players de 5M+; 2.5M não conta.","type":"streak","target":5,"min_bounty":5000000},
            {"difficulty":"Médio","title":"+100K BOUNTY","desc":"Ganhe +100k de bounty.","type":"bounty","target":100000},
            {"difficulty":"Médio","title":"3 KILLS EM 10 MIN","desc":"Consiga 3 kills em até 10 minutos.","type":"timed_kills","target":3,"time_limit":600},
            {"difficulty":"Médio","title":"30 MIN SEM V4","desc":"Jogue por 30 minutos sem usar V4.","type":"timer","target":1800},
            {"difficulty":"Médio","title":"2 COUNTER KILLS","desc":"Consiga 2 kills entrando de counter-attack em vez de avançar primeiro.","type":"kills","target":2},
            {"difficulty":"Médio","title":"3 KILLS SEM MORRER","desc":"Consiga 3 kills sem morrer.","type":"kills","target":3,"reset_on_death":True},

            # DIFÍCIL
            {"difficulty":"Difícil","title":"10 KILLS","desc":"Consiga 10 kills.","type":"kills","target":10},
            {"difficulty":"Difícil","title":"+200K BOUNTY","desc":"Ganhe +200k de bounty.","type":"bounty","target":200000},
            {"difficulty":"Difícil","title":"WIN STREAK 7","desc":"Consiga 7 vitórias seguidas. Só contam players de 5M+; 2.5M não conta.","type":"streak","target":7,"min_bounty":5000000},
            {"difficulty":"Difícil","title":"5 KILLS SEM MORRER","desc":"Consiga 5 kills sem morrer.","type":"kills","target":5,"reset_on_death":True},
            {"difficulty":"Difícil","title":"5 KILLS EM 15 MIN","desc":"Consiga 5 kills em até 15 minutos.","type":"timed_kills","target":5,"time_limit":900},
            {"difficulty":"Difícil","title":"5 COMBOS / 5 KILLS","desc":"Consiga 5 kills usando 5 sequências de combo diferentes.","type":"kills","target":5},
            {"difficulty":"Difícil","title":"+100K SEM MORRER","desc":"Ganhe +100k de bounty sem morrer.","type":"bounty","target":100000,"reset_on_death":True},
            {"difficulty":"Difícil","title":"30 MIN SEM MORRER / PVP","desc":"Fique 30 minutos sem morrer enquanto realmente vai PvP. Ficar parado não vale.","type":"timer","target":1800,"reset_on_death":True},
            {"difficulty":"Difícil","title":"GUN CLICK STARTER x5","desc":"Consiga 5 kills usando o click da Gun como starter.","type":"kills","target":5},
            {"difficulty":"Difícil","title":"3 KILLS SEM REPETIR COMBO","desc":"Consiga 3 kills sem repetir o mesmo combo. Com build da Roulette, este desafio é sempre Difícil.","type":"kills","target":3},
            {"difficulty":"Difícil","title":"10 KILLS SEM MORRER","desc":"Consiga 10 kills sem morrer.","type":"kills","target":10,"reset_on_death":True},

            # INSANO
            {"difficulty":"Insano","title":"+500K BOUNTY","desc":"Ganhe +500k de bounty.","type":"bounty","target":500000},
            {"difficulty":"Insano","title":"WIN STREAK 10","desc":"Consiga 10 vitórias seguidas. Só contam players de 5M+; 2.5M não conta.","type":"streak","target":10,"min_bounty":5000000},
            {"difficulty":"Insano","title":"20 KILLS SEM MORRER","desc":"Consiga 20 kills sem morrer.","type":"kills","target":20,"reset_on_death":True},
            {"difficulty":"Insano","title":"+250K SEM MORRER","desc":"Ganhe +250k de bounty sem morrer.","type":"bounty","target":250000,"reset_on_death":True},
            {"difficulty":"Insano","title":"5 KILLS / COMBOS DIFERENTES","desc":"Consiga 5 kills usando combos diferentes com a mesma build.","type":"kills","target":5},
            {"difficulty":"Insano","title":"45 MIN SEM V4","desc":"Jogue por 45 minutos sem usar V4 — vale bounty hunt, team, script ou war.","type":"timer","target":2700},
            {"difficulty":"Insano","title":"5 KILLS EM 10 MIN / SEM MORRER","desc":"Consiga 5 kills em até 10 minutos sem morrer.","type":"timed_kills","target":5,"time_limit":600,"reset_on_death":True},
            {"difficulty":"Insano","title":"5 ABERTURAS DIFERENTES","desc":"Consiga 5 kills sem iniciar duas lutas da mesma maneira.","type":"kills","target":5},
            {"difficulty":"Insano","title":"+300K EM 30 MIN","desc":"Ganhe +300k de bounty em até 30 minutos. Você pode pausar o cronômetro para registrar o bounty exato.","type":"timed_bounty","target":300000,"time_limit":1800},
        ]

    def _creator_secret_templates(self):
        return [
            {"difficulty":"SECRET","title":"NO DASH x3","desc":"Consiga 3 kills sem usar dash durante as lutas.","type":"kills","target":3,"secret_theme":"No Dash"},
            {"difficulty":"SECRET","title":"PURE COMBAT","desc":"Mate alguém usando apenas o Fighting Style da build aleatória.","type":"manual","target":1,"secret_theme":"Pure Combat","needs_roulette":True},
            {"difficulty":"SECRET","title":"SETE DÍGITOS","desc":"Ganhe +1.000.000 de bounty durante o desafio.","type":"bounty","target":1000000,"secret_theme":"Millionaire"},
            {"difficulty":"SECRET","title":"30 KILL STREAK","desc":"Faça uma sequência de 30 kills sem perder. Só contam players de 5M+; 2.5M não conta.","type":"streak","target":30,"min_bounty":5000000,"secret_theme":"Untouchable"},
            {"difficulty":"SECRET","title":"20 KILLS // SEM MORRER","desc":"Consiga 20 kills sem morrer. O cronômetro mede quanto tempo você levou.","type":"timer_kills","target":20,"reset_on_death":True,"secret_theme":"Endurance"},
        ]

    def _creator_new_runtime(self, template, context_build=None):
        x=dict(template)
        now=time.time()
        x.update({"id":uuid.uuid4().hex,"value":0,"done":False,"failed":False,"running":False,"started_at":None,"elapsed":0,"created":now,"completed_at":None,"attempts":1,"swaps_used":0,"archived":False,"timer_started_once":False})
        if context_build:
            x["context_build"]=dict(context_build)
            if x.get("roulette_bump"):
                x["difficulty"]=x.get("roulette_bump")
        if x.get("difficulty")=="SECRET" and x.get("needs_roulette") and not x.get("context_build"):
            lb=dict(getattr(self,"last_roulette_build",{}) or {})
            if lb:x["context_build"]=lb
        return x

    def creator_generate_challenges(self, context_build=None):
        diff=str(self.creator_diff.get()) if hasattr(self,"creator_diff") else "Médio"
        try:count=max(1,min(5,int(self.creator_count.get())))
        except Exception:count=3
        pool=self._creator_templates()
        if diff!="Misturar":
            pool=[x for x in pool if x.get("difficulty")==diff or (context_build and x.get("roulette_bump")==diff)]
        if not pool:return
        picked=random.sample(pool,k=min(count,len(pool)))
        out=[]; secret_titles=[]; used_secret=set()
        force_secret=bool(self._owner_key_valid() and dict(getattr(self,"_owner_state",{}) or {}).get("force_secret_challenges",False))
        for t in picked:
            chosen=t
            # SECRET: ~3% normally. Owner Lab can force it for local testing only.
            if force_secret or random.random()<0.03:
                secrets=[z for z in self._creator_secret_templates() if z.get("title") not in used_secret]
                if secrets:
                    chosen=random.choice(secrets); used_secret.add(chosen.get("title")); secret_titles.append(chosen.get("title"))
            out.append(self._creator_new_runtime(chosen,context_build=context_build))
        self.creator_challenges=out
        self._creator_session_started_at=time.time(); self._creator_session_initial_count=len(out); self._creator_celebration_open=False
        self.creator_refresh_challenges(); self._play_ui_sound("confirm",0)
        if secret_titles:self.after(180,lambda titles=list(secret_titles):self._creator_secret_reveal(titles))

    def _creator_find(self,cid):
        return next((x for x in getattr(self,"creator_challenges",[]) if isinstance(x,dict) and x.get("id")==cid),None)

    def _creator_active_elapsed(self,x):
        elapsed=float(x.get("elapsed",0) or 0)
        if x.get("running") and x.get("started_at"):
            elapsed+=max(0,time.time()-float(x.get("started_at")))
        return elapsed

    def _creator_pause_runtime(self,x):
        if x.get("running") and x.get("started_at"):
            x["elapsed"]=int(self._creator_active_elapsed(x)); x["running"]=False; x["started_at"]=None

    def _creator_value(self,x):
        typ=x.get("type")
        if typ=="timer":return self._creator_active_elapsed(x)
        if typ=="timer_kills":return float(x.get("value",0) or 0)
        return float(x.get("value",0) or 0)

    def _creator_is_complete(self,x):
        typ=x.get("type")
        if typ=="timer": return self._creator_active_elapsed(x)>=float(x.get("target",1) or 1)
        if typ=="timer_kills": return float(x.get("value",0) or 0)>=float(x.get("target",1) or 1)
        if typ in ("timed_kills","timed_bounty"):
            return bool(x.get("timer_started_once")) and float(x.get("value",0) or 0)>=float(x.get("target",1) or 1) and self._creator_active_elapsed(x)<=float(x.get("time_limit",1) or 1)
        return float(x.get("value",0) or 0)>=float(x.get("target",1) or 1)

    def _creator_update_done(self,x):
        if not x or x.get("done"):return
        typ=x.get("type")
        if typ in ("timed_kills","timed_bounty") and x.get("running") and self._creator_active_elapsed(x)>float(x.get("time_limit",1) or 1) and float(x.get("value",0) or 0)<float(x.get("target",1) or 1):
            self._creator_pause_runtime(x); x["failed"]=True; self._play_ui_sound("warning",0); return
        if self._creator_is_complete(x):
            self._creator_pause_runtime(x); x["done"]=True; x["failed"]=False; x["completed_at"]=time.time()
            if typ=="timer":x["elapsed"]=int(x.get("target",1) or 1)
            elif typ=="timer_kills":
                # O cronômetro é apenas informativo: registra quanto tempo levou até 20/20.
                x["elapsed"]=max(0,int(x.get("elapsed",0) or 0))
                x["value"]=int(x.get("target",1) or 1)
            self._creator_archive_completed(x)

    def _creator_archive_completed(self,x):
        if x.get("archived"):return
        x["archived"]=True
        self.creator_total_completed=int(getattr(self,"creator_total_completed",0) or 0)+1
        build=dict(x.get("context_build",{}) or {})
        final_progress=self._creator_format_progress(x)
        record={
            "id":uuid.uuid4().hex,"title":x.get("title","DESAFIO"),"difficulty":x.get("difficulty",""),
            "completed":datetime.now().isoformat(timespec="seconds"),"duration":max(0,int(time.time()-float(x.get("created",time.time()) or time.time()))),
            "attempts":int(x.get("attempts",1) or 1),"progress":final_progress,"build":build,
        }
        self.creator_history=(list(getattr(self,"creator_history",[]))+[record])[-300:]
        unlocked_now=[]
        secret_theme=x.get("secret_theme")
        if secret_theme and self._unlock_secret_theme(secret_theme,f"SECRET // {x.get('title','')}"):
            unlocked_now.append(secret_theme)
        if self.creator_total_completed>=5 and self._unlock_secret_theme("Party","5 desafios concluídos no total",announce=False):
            unlocked_now.append("Party")
        x["unlocked_now"]=unlocked_now
        self.salvar_config_app(); self._play_ui_sound("challenge_complete",0)
        try:self.creator_refresh_history()
        except Exception:pass
        self.after(250,self._creator_session_complete_if_ready)

    def creator_add(self,cid,amount=1):
        x=self._creator_find(cid)
        if not x or x.get("done"):return
        x["failed"]=False
        # Nos SECRET de kills cronometradas, o relógio começa sozinho na primeira kill.
        if x.get("type")=="timer_kills" and int(amount)>0 and not x.get("timer_started_once"):
            x["running"]=True; x["started_at"]=time.time(); x["timer_started_once"]=True
            self._creator_ensure_tick()
        value=max(0,int(x.get("value",0) or 0)+int(amount))
        if x.get("type")=="timer_kills":
            value=min(value,int(x.get("target",1) or 1))
        x["value"]=value
        self._creator_update_done(x); self.creator_refresh_challenges()

    def creator_add_bounty(self,cid):
        x=self._creator_find(cid)
        if not x or x.get("done"):return
        was_running=bool(x.get("running"));
        if was_running:self._creator_pause_runtime(x)
        raw=ctk.CTkInputDialog(text="Quanto de bounty você ganhou?\nEx.: 12450\n\nO cronômetro fica pausado enquanto você digita.",title="Creator Mode").get_input()
        if raw is None:
            if was_running and not x.get("done"):x["running"]=True;x["started_at"]=time.time();self._creator_ensure_tick()
            self.creator_refresh_challenges(); return
        try:n=int(re.sub(r"[^0-9]","",raw)); assert n>=0
        except Exception:
            messagebox.showwarning("Creator Mode","Digite um valor válido.")
            if was_running:x["running"]=True;x["started_at"]=time.time();self._creator_ensure_tick()
            return
        x["failed"]=False; x["value"]=max(0,int(x.get("value",0) or 0)+n); self._creator_update_done(x)
        if was_running and not x.get("done") and not x.get("failed"):
            x["running"]=True;x["started_at"]=time.time();self._creator_ensure_tick()
        self.creator_refresh_challenges()

    def creator_reset_value(self,cid):
        x=self._creator_find(cid)
        if not x:return
        x["value"]=0; x["done"]=False; x["failed"]=False; x["running"]=False; x["started_at"]=None; x["elapsed"]=0; x["timer_started_once"]=False; x["attempts"]=int(x.get("attempts",1) or 1)+1
        self.creator_refresh_challenges()

    def creator_mark_done(self,cid):
        x=self._creator_find(cid)
        if not x or x.get("done"):return
        x["value"]=int(x.get("target",1) or 1); self._creator_update_done(x); self.creator_refresh_challenges()

    def creator_toggle_timer(self,cid):
        x=self._creator_find(cid)
        if not x or x.get("done"):return
        if x.get("running"):
            self._creator_pause_runtime(x)
        else:
            if x.get("failed"):
                x["failed"]=False; x["value"]=0; x["elapsed"]=0; x["attempts"]=int(x.get("attempts",1) or 1)+1
            x["running"]=True; x["started_at"]=time.time(); x["timer_started_once"]=True
        self._creator_update_done(x); self.creator_refresh_challenges(); self._creator_ensure_tick()

    def creator_streak(self,cid,won=True):
        x=self._creator_find(cid)
        if not x or x.get("done"):return
        if won:x["value"]=int(x.get("value",0) or 0)+1
        else:
            x["value"]=0; x["attempts"]=int(x.get("attempts",1) or 1)+1; self._play_ui_sound("warning",0)
        self._creator_update_done(x); self.creator_refresh_challenges()

    def creator_death(self,cid):
        x=self._creator_find(cid)
        if not x or x.get("done"):return
        if x.get("reset_on_death"):
            x["value"]=0; x["done"]=False; x["failed"]=False; x["running"]=False; x["started_at"]=None; x["elapsed"]=0; x["timer_started_once"]=False; x["attempts"]=int(x.get("attempts",1) or 1)+1
            self.creator_refresh_challenges(); self._play_ui_sound("warning",0)

    def _creator_format_seconds(self,sec):
        sec=max(0,int(sec)); return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"

    def _creator_format_progress(self,x):
        typ=x.get("type"); v=float(x.get("value",0) or 0); target=float(x.get("target",1) or 1)
        if typ=="timer":return f"{self._creator_format_seconds(self._creator_active_elapsed(x))} / {self._creator_format_seconds(target)}"
        if typ=="timer_kills":
            kills=min(int(v),int(target))
            elapsed=self._creator_active_elapsed(x)
            return f"{kills}/{int(target)} kills  •  TEMPO {self._creator_format_seconds(elapsed)}"
        if typ in ("timed_kills","timed_bounty"):
            remain=max(0,float(x.get("time_limit",0) or 0)-self._creator_active_elapsed(x))
            unit=(f"+{int(v):,}/+{int(target):,} bounty".replace(",",".") if typ=="timed_bounty" else f"{int(v)}/{int(target)} kills")
            return f"{unit}  •  RESTANTE {self._creator_format_seconds(remain)}"
        if typ=="bounty":return f"+{int(v):,} / +{int(target):,} bounty".replace(",",".")
        if typ=="streak":return f"{int(v)} / {int(target)} sequência  •  só 5M+"
        if typ=="kills":return f"{int(v)} / {int(target)} kills"
        return "CONCLUÍDO" if x.get("done") else "PENDENTE"

    def creator_swap_challenge(self,cid):
        old=self._creator_find(cid)
        if not old or old.get("done"):return
        used_swaps=int(old.get("swaps_used",0) or 0)
        if used_swaps>=2:
            self.show_toast("LIMITE DE TROCAS","Esse desafio já usou as 2 trocas disponíveis.",kind="warning",duration=3000); return
        diff=old.get("difficulty","Médio"); used={x.get("title") for x in self.creator_challenges if isinstance(x,dict)}
        source=self._creator_secret_templates() if diff=="SECRET" else self._creator_templates()
        pool=[x for x in source if x.get("difficulty")==diff and x.get("title") not in used]
        if not pool:
            self.show_toast("CREATOR MODE","Não há outro desafio diferente nessa categoria agora.",kind="info"); return
        repl=self._creator_new_runtime(random.choice(pool),context_build=old.get("context_build")); repl["swaps_used"]=used_swaps+1
        self.creator_challenges=[repl if x.get("id")==cid else x for x in self.creator_challenges]; self.creator_refresh_challenges(); self._play_ui_sound("select",0)
        if repl.get("difficulty")=="SECRET":self.after(120,lambda:self._creator_secret_reveal([repl.get("title")]))

    def _creator_ensure_tick(self):
        if getattr(self,"_creator_timer_job",None):return
        def tick():
            self._creator_timer_job=None; active=False
            for x in getattr(self,"creator_challenges",[]):
                if isinstance(x,dict) and x.get("running") and not x.get("done"):
                    active=True; self._creator_update_done(x)
            try:self.creator_refresh_challenges(light=True)
            except Exception:pass
            if active:self._creator_timer_job=self.after(500,tick)
        self._creator_timer_job=self.after(500,tick)

    def creator_refresh_challenges(self,light=False):
        frame=getattr(self,"creator_challenge_frame",None)
        if not frame:return
        t=TEMAS[self.tema_atual]
        if light:
            widgets=getattr(self,"_creator_progress_widgets",{}) or {}
            for x in getattr(self,"creator_challenges",[]):
                if not isinstance(x,dict):continue
                refs=widgets.get(x.get("id"));
                if not refs:continue
                try:
                    typ=x.get("type"); val=float(x.get("value",0) or 0); target=max(1.0,float(x.get("target",1) or 1))
                    if typ=="timer": ratio=min(1.0,self._creator_active_elapsed(x)/target)
                    elif typ=="timer_kills": ratio=min(1.0,val/target)
                    else: ratio=min(1.0,val/target)
                    refs["bar"].set(max(0,ratio))
                    text="✓ DESAFIO CONCLUÍDO" if x.get("done") else ("TEMPO ESGOTADO — RESET PARA TENTAR DE NOVO" if x.get("failed") else self._creator_format_progress(x))
                    refs["label"].configure(text=text,text_color=t["accent"] if x.get("done") else ("#FF6B6B" if x.get("failed") else t.get("muted","gray")))
                    if refs.get("timer"):
                        if typ in ("timed_kills","timed_bounty"):
                            sec=max(0,float(x.get("time_limit",0) or 0)-self._creator_active_elapsed(x))
                            refs["timer"].configure(text=self._creator_format_seconds(sec))
                        elif typ=="timer":refs["timer"].configure(text=self._creator_format_seconds(self._creator_active_elapsed(x)))
                        elif typ=="timer_kills":refs["timer"].configure(text=self._creator_format_seconds(self._creator_active_elapsed(x)))
                except Exception:pass
            return
        try:
            for w in frame.winfo_children():w.destroy()
        except Exception:return
        self._creator_progress_widgets={}
        challenges=list(getattr(self,"creator_challenges",[]))
        if not challenges:
            empty=ctk.CTkFrame(frame,fg_color=t["card_active"],corner_radius=12); empty.pack(fill="x",padx=2,pady=6)
            ctk.CTkLabel(empty,text="Nenhum desafio ativo.",text_color=t["text"],font=ctk.CTkFont(size=12,weight="bold")).pack(anchor="w",padx=14,pady=(12,2))
            ctk.CTkLabel(empty,text="Escolha dificuldade + quantidade e clique em GERAR DESAFIOS.",text_color=t.get("muted","gray"),font=ctk.CTkFont(size=9)).pack(anchor="w",padx=14,pady=(0,12))
            return
        for x in challenges:
            if not isinstance(x,dict):continue
            is_secret=x.get("difficulty")=="SECRET"; done=bool(x.get("done")); border=("#FF4FD8" if is_secret else (t["accent"] if done else t["border"]))
            card=ctk.CTkFrame(frame,fg_color=t["card_active"],corner_radius=13,border_width=2 if is_secret or done else 1,border_color=border); card.pack(fill="x",padx=2,pady=6)
            head=ctk.CTkFrame(card,fg_color="transparent"); head.pack(fill="x",padx=12,pady=(9,3))
            title_prefix="??? // SECRET" if is_secret else str(x.get("difficulty",""))
            ctk.CTkLabel(head,text=f"{title_prefix}  //  {x.get('title','DESAFIO')}",text_color="#FF6FE5" if is_secret else t["accent"],font=ctk.CTkFont(family="Consolas",size=9,weight="bold")).pack(side="left")
            if not done:
                remain=max(0,2-int(x.get("swaps_used",0) or 0))
                ctk.CTkButton(head,text=f"TROCAR  {remain}/2",width=88,height=25,command=lambda cid=x.get("id"):self.creator_swap_challenge(cid),state="normal" if remain>0 else "disabled",fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["text"]).pack(side="right")
            ctk.CTkLabel(card,text=x.get("desc",""),text_color=t["text"],justify="left",anchor="w",wraplength=790).pack(fill="x",padx=12,pady=(1,5))
            build=dict(x.get("context_build",{}) or {})
            if build:
                line="  •  ".join(str(build.get(k,"—")) for k in ("style","fruit","sword","gun"))
                ctk.CTkLabel(card,text="BUILD VINCULADA  //  "+line,text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7),anchor="w",wraplength=800).pack(fill="x",padx=12,pady=(0,5))
            typ=x.get("type")
            timer_lbl=None
            if typ in ("timer","timed_kills","timed_bounty","timer_kills"):
                shown=(max(0,float(x.get("time_limit",0) or 0)-self._creator_active_elapsed(x)) if typ in ("timed_kills","timed_bounty") else self._creator_active_elapsed(x))
                timerbox=ctk.CTkFrame(card,fg_color=t["card"],corner_radius=10); timerbox.pack(fill="x",padx=12,pady=(2,7))
                ctk.CTkLabel(timerbox,text="TEMPO RESTANTE" if typ in ("timed_kills","timed_bounty") else "CRONÔMETRO",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="left",padx=10,pady=9)
                timer_lbl=ctk.CTkLabel(timerbox,text=self._creator_format_seconds(shown),text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=21,weight="bold")); timer_lbl.pack(side="right",padx=12,pady=7)
            target=max(1.0,float(x.get("target",1) or 1)); val=min(target,float(x.get("value",0) or 0)); bar=ctk.CTkProgressBar(card,height=8,progress_color="#FF4FD8" if is_secret else t["accent"]); bar.set(max(0,min(1,val/target))); bar.pack(fill="x",padx=12,pady=(2,3))
            status_text="✓ DESAFIO CONCLUÍDO" if done else ("TEMPO ESGOTADO — RESET PARA TENTAR DE NOVO" if x.get("failed") else self._creator_format_progress(x))
            progress_lbl=ctk.CTkLabel(card,text=status_text,text_color=t["accent"] if done else ("#FF6B6B" if x.get("failed") else t.get("muted","gray")),font=ctk.CTkFont(family="Consolas",size=9 if typ in ("timer","timed_kills","timed_bounty","timer_kills") else 8,weight="bold")); progress_lbl.pack(anchor="w",padx=12,pady=(0,6))
            self._creator_progress_widgets[x.get("id")]={"bar":bar,"label":progress_lbl,"timer":timer_lbl}
            # Important: DONE cards stay compact. No empty action frame is created.
            if done:continue
            actions=ctk.CTkFrame(card,fg_color="transparent"); actions.pack(fill="x",padx=10,pady=(0,9)); cid=x.get("id")
            if typ in ("kills","timed_kills","timer_kills"):
                ctk.CTkButton(actions,text="−1",width=48,command=lambda c=cid:self.creator_add(c,-1),fg_color=t["card"],text_color=t["text"]).pack(side="left",padx=2)
                kill_target=int(x.get("target",1) or 1)
                kill_done=(typ=="timer_kills" and int(x.get("value",0) or 0)>=kill_target)
                ctk.CTkButton(actions,text=("KILLS ✓" if kill_done else "+1 KILL"),width=82,command=lambda c=cid:self.creator_add(c,1),state="disabled" if kill_done else "normal",fg_color=t["card_active"] if kill_done else t["accent"],text_color=t.get("muted","gray") if kill_done else "#050505").pack(side="left",padx=2)
            elif typ in ("bounty","timed_bounty"):
                ctk.CTkButton(actions,text="+ ADICIONAR BOUNTY",command=lambda c=cid:self.creator_add_bounty(c),fg_color=t["accent"],text_color="#050505").pack(side="left",padx=2)
            elif typ=="streak":
                ctk.CTkButton(actions,text="+1 VITÓRIA 5M+",command=lambda c=cid:self.creator_streak(c,True),fg_color=t["accent"],text_color="#050505").pack(side="left",padx=2)
                ctk.CTkButton(actions,text="PERDI — RESET",command=lambda c=cid:self.creator_streak(c,False),fg_color=t["card"],text_color=t["text"]).pack(side="left",padx=2)
            else:
                ctk.CTkButton(actions,text="MARCAR CONCLUÍDO",command=lambda c=cid:self.creator_mark_done(c),fg_color=t["accent"],text_color="#050505").pack(side="left",padx=2)
            if typ in ("timer","timed_kills","timed_bounty","timer_kills"):
                ctk.CTkButton(actions,text="PAUSAR TEMPO" if x.get("running") else "INICIAR TEMPO",command=lambda c=cid:self.creator_toggle_timer(c),fg_color=t["card"],text_color=t["accent"]).pack(side="left",padx=2)
            if x.get("reset_on_death"):
                ctk.CTkButton(actions,text="MORRI — RESET",command=lambda c=cid:self.creator_death(c),fg_color="#7A2431",hover_color="#A52E40").pack(side="left",padx=2)
            ctk.CTkButton(actions,text="RESET",width=64,command=lambda c=cid:self.creator_reset_value(c),fg_color="transparent",border_width=1,border_color=t["card_active"],text_color=t["text"]).pack(side="right",padx=2)
        self._creator_ensure_tick()

    def creator_refresh_history(self):
        frame=getattr(self,"creator_history_frame",None)
        if not frame:return
        try:
            for w in frame.winfo_children():w.destroy()
        except Exception:return
        t=TEMAS[self.tema_atual]; items=list(getattr(self,"creator_history",[]))[-20:][::-1]
        if not items:
            ctk.CTkLabel(frame,text="Nenhum desafio concluído ainda.",text_color=t.get("muted","gray")).pack(padx=12,pady=14); return
        for rec in items:
            secret=rec.get("difficulty")=="SECRET"; row=ctk.CTkFrame(frame,fg_color=t["card_active"],corner_radius=10,border_width=1,border_color="#FF4FD8" if secret else t["border"]); row.pack(fill="x",padx=2,pady=4)
            left=ctk.CTkFrame(row,fg_color="transparent"); left.pack(side="left",fill="x",expand=True,padx=10,pady=8)
            ctk.CTkLabel(left,text=f"{rec.get('difficulty','')} // {rec.get('title','')}",text_color="#FF6FE5" if secret else t["accent"],font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w").pack(fill="x")
            build=dict(rec.get("build",{}) or {}); build_txt=(" • ".join(str(build.get(k,"—")) for k in ("style","fruit","sword","gun")) if build else "Livre / sem build vinculada")
            ctk.CTkLabel(left,text=build_txt,text_color=t["text"],font=ctk.CTkFont(size=8),anchor="w",wraplength=610).pack(fill="x",pady=(2,0))
            ctk.CTkLabel(left,text=str(rec.get("progress") or ""),text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7),anchor="w").pack(fill="x",pady=(2,0))
            dur=self._creator_format_seconds(rec.get("duration",0)); attempts=int(rec.get("attempts",1) or 1)
            dt=str(rec.get("completed") or "").replace("T"," ")[:16]
            ctk.CTkLabel(row,text=f"{dt}\n{dur}  •  {attempts} tentativa(s)",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=7),justify="right").pack(side="right",padx=10,pady=8)

    def _creator_secret_reveal(self,titles):
        if getattr(self,"_creator_secret_reveal_open",False):return
        self._creator_secret_reveal_open=True; self._play_ui_sound("secret_reveal",0); t=TEMAS[self.tema_atual]
        win=ctk.CTkToplevel(self); win.title("??? // SECRET"); self._center_child_window(win,520,250); win.transient(self); win.attributes("-topmost",True)
        root=ctk.CTkFrame(win,fg_color="#120817",corner_radius=16,border_width=2,border_color="#FF4FD8"); root.pack(fill="both",expand=True,padx=10,pady=10)
        lab=ctk.CTkLabel(root,text="??? // SECRET DISCOVERED",text_color="#FF6FE5",font=ctk.CTkFont(family="Consolas",size=18,weight="bold")); lab.pack(pady=(28,8))
        ctk.CTkLabel(root,text="\n".join(str(x) for x in titles),text_color="#FFFFFF",font=ctk.CTkFont(size=14,weight="bold"),wraplength=440).pack(pady=4)
        ctk.CTkLabel(root,text="Isso não aparece sempre. Concluir pode esconder algo além do histórico.",text_color="#BA9CBF",font=ctk.CTkFont(size=9),wraplength=430).pack(pady=(6,12))
        def close():
            self._creator_secret_reveal_open=False
            try:win.destroy()
            except Exception:pass
        ctk.CTkButton(root,text="ACEITAR DESAFIO",command=close,fg_color="#FF4FD8",hover_color="#FF83EA",text_color="#130015").pack(pady=(0,18))
        win.protocol("WM_DELETE_WINDOW",close)
        pulse=["#FF4FD8","#8C5CFF","#FF85E9","#FF4FD8"]
        for i,c in enumerate(pulse):
            self.after(150*i,lambda col=c: lab.configure(text_color=col) if self._widget_alive(lab) else None)

    def _creator_session_complete_if_ready(self):
        items=[x for x in getattr(self,"creator_challenges",[]) if isinstance(x,dict)]
        if not items or getattr(self,"_creator_celebration_open",False):return
        if not all(bool(x.get("done")) for x in items):return
        self._creator_celebration_open=True; self._creator_show_session_complete(items)

    def _creator_show_session_complete(self,items):
        t=TEMAS[self.tema_atual]; unlocked=[]
        for x in items:unlocked.extend(list(x.get("unlocked_now",[]) or []))
        unlocked=list(dict.fromkeys(unlocked))
        self._play_ui_sound("challenge_session",0)
        win=ctk.CTkToplevel(self); win.title("Creator Mode // Session Complete"); self._center_child_window(win,760,560); win.transient(self); win.attributes("-topmost",True)
        canvas=Canvas(win,bg=t["bg"],highlightthickness=0,bd=0); canvas.place(x=0,y=0,relwidth=1,relheight=1)
        panel=ctk.CTkFrame(win,fg_color=t["panel"],corner_radius=18,border_width=2,border_color=t["accent"]); panel.place(relx=.5,rely=.5,anchor="center",relwidth=.86,relheight=.80)
        ctk.CTkLabel(panel,text="SESSION COMPLETE",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=23,weight="bold")).pack(pady=(28,4))
        ctk.CTkLabel(panel,text=f"{len(items)}/{len(items)} desafios concluídos",text_color=t["text"],font=ctk.CTkFont(size=14,weight="bold")).pack(pady=(0,10))
        names="\n".join("✓  "+str(x.get("title","DESAFIO")) for x in items)
        ctk.CTkLabel(panel,text=names,text_color=t["text"],font=ctk.CTkFont(size=10),justify="left",wraplength=560).pack(padx=24,pady=8)
        elapsed=max(0,int(time.time()-float(getattr(self,"_creator_session_started_at",time.time()) or time.time())))
        ctk.CTkLabel(panel,text=f"TEMPO DA SESSÃO  {self._creator_format_seconds(elapsed)}   •   TOTAL CONCLUÍDO  {int(getattr(self,'creator_total_completed',0))}",text_color=t.get("muted","gray"),font=ctk.CTkFont(family="Consolas",size=8,weight="bold")).pack(pady=(8,6))
        if unlocked:
            ctk.CTkLabel(panel,text="NEW THEME UNLOCKED  //  "+" + ".join(unlocked),text_color="#FFD166",font=ctk.CTkFont(family="Consolas",size=11,weight="bold"),wraplength=600).pack(pady=(4,8))
        def finish():
            self.creator_challenges=[]; self._creator_celebration_open=False; self._creator_session_started_at=0.0; self._creator_session_initial_count=0
            try:win.destroy()
            except Exception:pass
            self.creator_refresh_challenges(); self.creator_refresh_history(); self.salvar_config_app()
        ctk.CTkButton(panel,text="CONTINUAR",command=finish,fg_color=t["accent"],hover_color=t["hover"],text_color="#050505",height=42,width=220,font=ctk.CTkFont(size=11,weight="bold")).pack(pady=(10,22))
        win.protocol("WM_DELETE_WINDOW",finish)
        # Confetti: lightweight Canvas rectangles, no generated images/assets.
        pieces=[]; colors=[t["accent"],t.get("border",t["accent"]),"#FFD166","#FF73B3","#67E8F9","#6EE7B7"]
        import random as _r
        for _ in range(70):
            x=_r.randint(5,750); y=_r.randint(-500,-10); w=_r.randint(4,9); h=_r.randint(8,16); col=_r.choice(colors); speed=_r.randint(3,8)
            rid=canvas.create_rectangle(x,y,x+w,y+h,fill=col,outline=""); pieces.append([rid,speed])
        def fall():
            if not self._widget_alive(win):return
            try:
                for rid,sp in pieces:
                    canvas.move(rid,0,sp); coords=canvas.coords(rid)
                    if coords and coords[1]>570: canvas.move(rid,_r.randint(-120,120),-_r.randint(620,900))
                win.after(35,fall)
            except Exception:pass
        fall()

    # ---------------- SETUPS ----------------
    def _capture_setup(self):
        return {
            "modules":dict(getattr(self,"module_states",{})),
            "advanced_values":dict(getattr(self,"advanced_values",{})),
            "micro_fps_target":str(getattr(self,"micro_fps_target","144")),
            "game_resolution":str(getattr(self,"resolucao_jogo","1280x720")),
            "custom_width":int(getattr(self,"custom_width",1280)),"custom_height":int(getattr(self,"custom_height",720)),
            "theme":str(getattr(self,"tema_atual","ZKStrap Core")),"accent_color":str(getattr(self,"cor_personalizada","")),
            "font":str(getattr(self,"fonte_ui","Segoe UI")),"cursor_pack":str(getattr(self,"cursor_pack","Roblox Padrão")),
            "cursor_visual_size":int(getattr(self,"cursor_visual_size",24)),"cursor_auto_remove_white":bool(getattr(self,"cursor_auto_remove_white",True)),
            "cursor_anchor_mode":str(getattr(self,"cursor_anchor_mode","Ponta no centro")),"game_font_source":str(getattr(self,"game_font_source","")),
            "sound_pack":str(getattr(self,"sound_pack",DEFAULT_AUDIO_PACK)),"music_enabled":bool(getattr(self,"music_enabled",True)),
            "sfx_enabled":bool(getattr(self,"sfx_enabled",True)),"music_volume":float(getattr(self,"music_volume",0.22)),
        }

    def _refresh_setup_edit_indicator(self):
        sid=str(getattr(self,"setup_edit_id","") or ""); name=""
        if sid:
            for s in getattr(self,"zk_setups",[]):
                if isinstance(s,dict) and s.get("id")==sid:name=s.get("name","Setup");break
        text=f"EDITANDO SETUP: {name}" if name else ""
        for attr in ("setup_edit_banner","header_setup_edit_label"):
            try:getattr(self,attr).configure(text=text)
            except Exception:pass
        try:
            ctrl=getattr(self,"setup_edit_controls",None)
            if ctrl is not None:
                if name:
                    if not ctrl.winfo_manager():ctrl.pack(fill="x",padx=16,pady=(2,8))
                else:ctrl.pack_forget()
        except Exception:pass

    def save_current_as_setup(self):
        if len(getattr(self,"zk_setups",[]))>=5:
            messagebox.showwarning("SETUPS","Você já salvou 5 setups. Exclua um antes de criar outro.");return
        name=ctk.CTkInputDialog(text="Nome do setup:",title="Salvar como Setup").get_input()
        if not name:return
        self.zk_setups.append({"id":uuid.uuid4().hex,"name":name.strip()[:60],"data":self._capture_setup(),"created":datetime.now().isoformat(timespec="seconds")})
        self.salvar_config_app(); self.refresh_setups_page(); self._play_ui_sound("confirm",0)

    def _apply_setup_data(self,data):
        if not isinstance(data,dict):return False
        self.module_states=dict(data.get("modules",self.module_states)); self.advanced_values=dict(data.get("advanced_values",self.advanced_values))
        self.micro_fps_target=str(data.get("micro_fps_target",self.micro_fps_target)); self.resolucao_jogo=str(data.get("game_resolution",self.resolucao_jogo))
        self.custom_width=int(data.get("custom_width",self.custom_width)); self.custom_height=int(data.get("custom_height",self.custom_height))
        self.cor_personalizada=str(data.get("accent_color",self.cor_personalizada)); self.fonte_ui=str(data.get("font",self.fonte_ui))
        self.cursor_pack=str(data.get("cursor_pack",self.cursor_pack)); self.cursor_visual_size=int(data.get("cursor_visual_size",self.cursor_visual_size)); self.cursor_auto_remove_white=bool(data.get("cursor_auto_remove_white",self.cursor_auto_remove_white)); self.cursor_anchor_mode=str(data.get("cursor_anchor_mode",self.cursor_anchor_mode)); self.game_font_source=str(data.get("game_font_source",self.game_font_source))
        self.sound_pack=str(data.get("sound_pack",self.sound_pack)); self.music_enabled=bool(data.get("music_enabled",self.music_enabled)); self.sfx_enabled=bool(data.get("sfx_enabled",self.sfx_enabled)); self.music_volume=float(data.get("music_volume",self.music_volume))
        try:
            mgr=self._sound_manager; mgr.set_pack(self.sound_pack); mgr.set_music_enabled(self.music_enabled); mgr.set_sfx_enabled(self.sfx_enabled); mgr.set_music_volume(self.music_volume)
        except Exception:pass
        self.salvar_config_app(); self.restaurar_estado_interface()
        try:self.atualizar_estilos_cards()
        except Exception:pass
        return True

    def apply_saved_setup(self,sid):
        setup=next((s for s in self.zk_setups if isinstance(s,dict) and s.get("id")==sid),None)
        if not setup:return
        data=setup.get("data",{}); changes=[]; current=self._capture_setup()
        for key,label in (("modules","módulos/flags"),("advanced_values","ajustes avançados"),("theme","tema"),("sound_pack","áudio"),("cursor_pack","cursor"),("font","fonte")):
            if current.get(key)!=data.get(key):changes.append(label)
        summary=", ".join(changes) if changes else "nenhuma diferença detectada"
        if not messagebox.askyesno("Aplicar Setup",f"Aplicar '{setup.get('name','Setup')}'?\n\nMudanças: {summary}\n\nUm snapshot da configuração atual será salvo para recuperação."):return
        self.last_setup_snapshot=current; old_theme=self.tema_atual
        self._apply_setup_data(data)
        ok=self.aplicar_configuracoes()
        new_theme=str(data.get("theme",old_theme))
        if new_theme in TEMAS and new_theme!=old_theme:
            self.mudar_tema_interface(new_theme)
        self.show_toast("SETUP APLICADO",setup.get("name","Setup"),kind="success" if ok else "warning")

    def edit_saved_setup(self,sid):
        if not any(isinstance(x,dict) and x.get("id")==sid for x in self.zk_setups):return
        self.setup_edit_id=sid; self._refresh_setup_edit_indicator(); self.refresh_setups_page(); self.show_toast("MODO DE EDIÇÃO","Você está editando este setup. Faça as mudanças no app e use SALVAR ALTERAÇÕES ou PARAR DE EDITAR no topo de SETUPS.",kind="info",duration=5500)

    def save_setup_edits(self,sid):
        for s in self.zk_setups:
            if isinstance(s,dict) and s.get("id")==sid:s["data"]=self._capture_setup();s["updated"]=datetime.now().isoformat(timespec="seconds");break
        self.setup_edit_id=""; self.salvar_config_app(); self.refresh_setups_page(); self._refresh_setup_edit_indicator(); self._play_ui_sound("confirm",0)

    def save_current_setup_edits(self):
        sid=str(getattr(self,"setup_edit_id","") or "")
        if not sid:
            self.show_toast("SETUPS","Nenhum setup está sendo editado.",kind="info"); return
        self.save_setup_edits(sid)
        self.show_toast("SETUP ATUALIZADO","Alterações salvas no setup.",kind="success")

    def cancel_setup_edit(self):
        if not str(getattr(self,"setup_edit_id","") or ""):
            return
        self.setup_edit_id=""
        self.salvar_config_app(); self.refresh_setups_page(); self._refresh_setup_edit_indicator()
        self.show_toast("EDIÇÃO ENCERRADA","Nenhuma alteração adicional será salva no setup.",kind="info")

    def rename_saved_setup(self,sid):
        setup=next((s for s in self.zk_setups if isinstance(s,dict) and s.get("id")==sid),None)
        if not setup:return
        name=ctk.CTkInputDialog(text="Novo nome:",title="Renomear Setup").get_input()
        if not name:return
        setup["name"]=name.strip()[:60]; self.salvar_config_app(); self.refresh_setups_page(); self._refresh_setup_edit_indicator()

    def delete_saved_setup(self,sid):
        if not messagebox.askyesno("SETUPS","Excluir este setup?"):return
        self.zk_setups=[s for s in self.zk_setups if not(isinstance(s,dict) and s.get("id")==sid)]
        if self.setup_edit_id==sid:self.setup_edit_id=""
        self.salvar_config_app(); self.refresh_setups_page(); self._refresh_setup_edit_indicator()

    def compare_saved_setup(self,sid):
        setup=next((x for x in self.zk_setups if isinstance(x,dict) and x.get("id")==sid),None)
        if not setup:return
        a=self._capture_setup(); b=setup.get("data",{}) if isinstance(setup.get("data",{}),dict) else {}
        labels={"modules":"Módulos/flags","advanced_values":"Ajustes avançados","micro_fps_target":"Limite FPS","game_resolution":"Resolução","theme":"Tema","font":"Fonte UI","cursor_pack":"Cursor","sound_pack":"Pack de áudio","music_enabled":"Música","sfx_enabled":"SFX","music_volume":"Volume música","sfx_volume":"Volume efeitos"}
        lines=[]
        for key,label in labels.items():
            if a.get(key)!=b.get(key):
                if key=="modules":
                    aa=a.get(key,{}) or {}; bb=b.get(key,{}) or {}; changed=[k for k in sorted(set(aa)|set(bb)) if bool(aa.get(k))!=bool(bb.get(k))]
                    lines.append(f"{label}: "+(", ".join(changed) if changed else "alterado"))
                elif key=="advanced_values":
                    aa=a.get(key,{}) or {}; bb=b.get(key,{}) or {}; changed=[k for k in sorted(set(aa)|set(bb)) if aa.get(k)!=bb.get(k)]
                    lines.append(f"{label}: "+(", ".join(changed) if changed else "alterado"))
                else: lines.append(f"{label}: atual={a.get(key)!r}  →  setup={b.get(key)!r}")
        messagebox.showinfo(f"Comparar — {setup.get('name','Setup')}","Nenhuma diferença detectada." if not lines else "Mudanças ao aplicar:\n\n"+"\n".join(lines[:18]))

    def refresh_setups_page(self):
        frame=getattr(self,"setups_list_frame",None)
        if not frame:return
        t=TEMAS[self.tema_atual]
        try:
            for w in frame.winfo_children():w.destroy()
        except Exception:return
        if not self.zk_setups:
            ctk.CTkLabel(frame,text="Nenhum setup salvo ainda.",text_color=t.get("muted","gray")).pack(pady=10); self._refresh_setup_edit_indicator(); return
        for s in self.zk_setups:
            row=ctk.CTkFrame(frame,fg_color=t["card_active"],corner_radius=10,border_width=1,border_color=t["accent"] if s.get("id")==self.setup_edit_id else t["border"]); row.pack(fill="x",pady=4)
            ctk.CTkLabel(row,text=s.get("name","Setup"),text_color=t["text"],font=ctk.CTkFont(size=11,weight="bold")).pack(side="left",padx=10,pady=10)
            if s.get("id")==self.setup_edit_id:
                ctk.CTkButton(row,text="SALVAR ALTERAÇÕES",command=lambda sid=s.get("id"):self.save_setup_edits(sid),fg_color=t["accent"],text_color="#050505",width=132).pack(side="right",padx=3)
            for lab,fn in (("APLICAR",self.apply_saved_setup),("COMPARAR",self.compare_saved_setup),("EDITAR",self.edit_saved_setup),("RENOMEAR",self.rename_saved_setup),("EXCLUIR",self.delete_saved_setup)):
                ctk.CTkButton(row,text=lab,command=lambda sid=s.get("id"),f=fn:f(sid),fg_color=t["card"],hover_color=t["hover"],text_color=t["accent"] if lab!="EXCLUIR" else "#FF8798",width=78).pack(side="right",padx=2)
        self._refresh_setup_edit_indicator()

    def _offer_close_heavy_apps(self):
        names={"medal.exe","medalencoder.exe","obs64.exe","overwolf.exe","gamebar.exe","nvidia share.exe","chrome.exe","msedge.exe","firefox.exe","brave.exe","opera.exe"}
        found=[]
        for proc in psutil.process_iter(["pid","name","memory_info"]):
            try:
                n=(proc.info.get("name") or "").lower()
                if n in names:
                    mem=(proc.info.get("memory_info").rss/1024/1024) if proc.info.get("memory_info") else 0
                    found.append((proc.info["pid"],proc.info.get("name") or n,mem))
            except Exception:pass
        if not found:return
        found.sort(key=lambda x:x[2],reverse=True)
        listing="\n".join(f"{name} — {mem:.0f} MB" for _,name,mem in found[:14])
        if not messagebox.askyesno("PC Fraco — liberar recursos",f"Encontrei programas conhecidos usando recursos:\n\n{listing}\n\nQuer fechar esses processos agora?\n\nAtenção: navegador/gravador pode ter trabalho ou gravação em andamento. Nada será fechado sem esta confirmação."):return
        for pid,name,_ in found:
            try:psutil.Process(pid).terminate()
            except Exception as e:self.log_output(f"[-] Não foi possível fechar {name}: {e}")

    def apply_builtin_setup(self,kind):
        current=self._capture_setup(); self.last_setup_snapshot=current
        data=dict(current); data["modules"]=dict(current.get("modules",{})); data["advanced_values"]=dict(current.get("advanced_values",{}))
        if kind=="fps_max":
            data["modules"].update({"performance_boost":True,"gray_sky":True,"fps_unlock":True,"micro_opt":True})
            data["advanced_values"].update({"texture":"0","msaa":"0","frm":"1","grass":"0","lod":"0"}); data["micro_fps_target"]="240"
            msg="FPS MÁXIMO prioriza as configurações mais leves/agressivas disponíveis no ZKStrap. O ganho real depende do hardware e do jogo. Aplicar?"
        else:
            data["modules"].update({"performance_boost":True,"gray_sky":True,"fps_unlock":True,"micro_opt":True})
            data["advanced_values"].update({"texture":"1","msaa":"0","frm":"2","grass":"0","lod":"1"}); data["micro_fps_target"]="60"
            msg="PC FRACO reduz efeitos e consumo para buscar estabilidade e uma experiência próxima de 60 FPS quando o hardware permitir. Aplicar?"
        if not messagebox.askyesno("SETUPS",msg):return
        self._apply_setup_data(data); self.aplicar_configuracoes()
        if kind=="weak_pc" and messagebox.askyesno("PC FRACO","Quer verificar gravadores, overlays e navegadores pesados e escolher se fecha?\n\nNada será encerrado sem confirmação."):
            self._offer_close_heavy_apps()
        self.salvar_config_app(); self.refresh_setups_page()

    # ---------------- Spotify / Windows Now Playing ----------------
    def _spotify_section_card(self,parent,title,description=""):
        card=ctk.CTkFrame(parent,fg_color="#181818",corner_radius=16,border_width=1,border_color="#2D2D2D")
        card.pack(fill="x",padx=6,pady=10)
        ctk.CTkFrame(card,width=4,fg_color="#1ED760",corner_radius=3).place(x=0,y=14,relheight=.70)
        content=ctk.CTkFrame(card,fg_color="transparent");content.pack(fill="both",expand=True,padx=22,pady=(16,18))
        head=ctk.CTkFrame(content,fg_color="transparent");head.pack(fill="x")
        ctk.CTkLabel(head,text=title,text_color="#FFFFFF",font=ctk.CTkFont(family="Segoe UI",size=15,weight="bold"),anchor="w").pack(side="left")
        ctk.CTkLabel(head,text="SPOTIFY  //  LOCAL",height=23,corner_radius=8,fg_color="#242424",text_color="#1ED760",font=ctk.CTkFont(family="Consolas",size=6,weight="bold")).pack(side="right")
        if description:
            ctk.CTkLabel(content,text=description,text_color="#B3B3B3",font=ctk.CTkFont(size=9),anchor="w",justify="left",wraplength=860).pack(fill="x",pady=(6,0))
        return content

    def _spotify_brand_header(self,parent):
        card=ctk.CTkFrame(parent,fg_color="#1ED760",corner_radius=18,border_width=0);card.pack(fill="x",padx=6,pady=(2,10))
        row=ctk.CTkFrame(card,fg_color="transparent");row.pack(fill="x",padx=18,pady=16)
        cv=Canvas(row,width=58,height=58,bg="#1ED760",highlightthickness=0,bd=0);cv.pack(side="left",padx=(0,14))
        cv.create_oval(4,4,54,54,fill="#0B0B0B",outline="")
        for box,w in [((14,18,45,35),3),((16,24,43,40),3),((18,30,40,44),2)]:
            cv.create_arc(*box,start=25,extent=135,style="arc",outline="#1ED760",width=w)
        txt=ctk.CTkFrame(row,fg_color="transparent");txt.pack(side="left",fill="x",expand=True)
        ctk.CTkLabel(txt,text="SPOTIFY // ZK DECK",text_color="#050505",font=ctk.CTkFont(size=20,weight="bold"),anchor="w").pack(fill="x")
        ctk.CTkLabel(txt,text="Now Playing • playback • volume • busca",text_color="#14351F",font=ctk.CTkFont(family="Consolas",size=8,weight="bold"),anchor="w").pack(fill="x",pady=(3,0))
        return card

    def spotify_open_tutorial(self):
        try:
            self.show_page("spotify", animate=True)
            self._spotify_set_status("use o Now Playing; nenhuma conta precisa ser conectada", "info")
        except Exception:
            pass

    def _spotify_set_status(self, text, kind="info"):
        try:
            t=TEMAS[self.tema_atual]
            colors={"ok":"#1ED760","success":"#1ED760","warning":"#F0C75E","error":"#FF6B7A","info":"#B3B3B3"}
            if getattr(self,"spotify_status_label",None):
                self.spotify_status_label.configure(text="Status: "+str(text),text_color=colors.get(kind,t.get("muted","gray")))
        except Exception:
            pass

    def _spotify_status_async(self, text, kind="info"):
        try:self.after(0,lambda msg=str(text),k=str(kind):self._spotify_set_status(msg,k))
        except Exception:pass

    @staticmethod
    def _spotify_seconds(value):
        try:
            if value is None:return 0.0
            if hasattr(value,"total_seconds"):return max(0.0,float(value.total_seconds()))
            if hasattr(value,"duration"):return max(0.0,float(value.duration)/10000000.0)
            return max(0.0,float(getattr(value,"seconds",value)))
        except Exception:return 0.0

    @staticmethod
    def _spotify_source_name(source):
        s=str(source or "").lower()
        if "spotify" in s:return "Spotify Desktop"
        if "chrome" in s:return "Spotify Web / Chrome"
        if "msedge" in s or "edge" in s:return "Spotify Web / Edge"
        if "firefox" in s:return "Spotify Web / Firefox"
        if "brave" in s:return "Spotify Web / Brave"
        if "opera" in s:return "Spotify Web / Opera"
        return str(source or "Spotify / Windows")

    @staticmethod
    def _spotify_enum_int(value, default=-1):
        try:return int(value)
        except Exception:
            try:return int(getattr(value,"value"))
            except Exception:return default

    async def _spotify_media_backend(self):
        """Return WinRT classes used by the Spotify-targeted media layer."""
        try:
            from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
            from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions
            return MediaManager,DataReader,Buffer,InputStreamOptions,"pywinrt"
        except Exception as first:
            try:
                from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
                from winsdk.windows.storage.streams import DataReader, Buffer, InputStreamOptions
                return MediaManager,DataReader,Buffer,InputStreamOptions,"winsdk"
            except Exception as second:
                raise RuntimeError(f"WinRT indisponível: {first} | fallback: {second}")

    def _spotify_browser_window_hint(self, browser_source=""):
        """Confirma Spotify Web pelo título da janela do MESMO navegador da sessão.
        Evita usar uma aba Spotify do Firefox para autorizar uma sessão do Chrome, por exemplo.
        """
        if os.name != "nt": return False
        src=str(browser_source or "").lower()
        wanted=set()
        for token,exe in (("chrome","chrome.exe"),("msedge","msedge.exe"),("edge","msedge.exe"),("firefox","firefox.exe"),("brave","brave.exe"),("opera","opera.exe")):
            if token in src:wanted.add(exe)
        cache_key=tuple(sorted(wanted)) or ("any",)
        now=time.monotonic(); cache=getattr(self,"_spotify_window_hint_cache",{})
        if isinstance(cache,dict) and cache_key in cache and now-float(cache[cache_key][0])<1.25:
            return bool(cache[cache_key][1])
        found=False
        try:
            user32=ctypes.windll.user32
            EnumWindowsProc=ctypes.WINFUNCTYPE(ctypes.c_bool,wintypes.HWND,wintypes.LPARAM)
            def cb(hwnd,lparam):
                nonlocal found
                try:
                    if not user32.IsWindowVisible(hwnd): return True
                    n=user32.GetWindowTextLengthW(hwnd)
                    if n<=0:return True
                    buf=ctypes.create_unicode_buffer(n+1); user32.GetWindowTextW(hwnd,buf,n+1)
                    title=str(buf.value or "").lower()
                    if "spotify" not in title:return True
                    pid=wintypes.DWORD(); user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
                    try:name=psutil.Process(int(pid.value)).name().lower()
                    except Exception:name=""
                    browsers={"chrome.exe","msedge.exe","firefox.exe","brave.exe","opera.exe"}
                    if name in browsers and (not wanted or name in wanted):
                        found=True; return False
                except Exception: pass
                return True
            user32.EnumWindows(EnumWindowsProc(cb),0)
        except Exception: found=False
        if not isinstance(cache,dict):cache={}
        cache[cache_key]=(now,found); self._spotify_window_hint_cache=cache
        return found

    async def _spotify_pick_session_async(self, manager):
        """Pick a Spotify session without ever guessing a random browser tab.

        Spotify Desktop is unambiguous because Windows exposes Spotify in the
        source application id. Browser tabs are different: Chrome/Edge may expose
        YouTube, Spotify Web and other sites under the SAME browser app id.  We
        therefore accept a browser session only when Windows exposes a strong
        music signature: PlaybackType=MUSIC plus title, artist and album metadata.
        If that proof is missing, the session is kept only for diagnostics and is
        NEVER controlled.
        """
        sessions=list(manager.get_sessions() or [])
        current=manager.get_current_session()
        rows=[]
        for idx,session in enumerate(sessions):
            try:source=str(getattr(session,"source_app_user_model_id","") or "")
            except Exception:source=""
            low=source.lower()
            browser=any(x in low for x in ("chrome","msedge","edge","firefox","brave","opera"))
            desktop="spotify" in low
            if not (desktop or browser):
                continue
            try:playback=session.get_playback_info()
            except Exception:playback=None
            ptype=self._spotify_enum_int(getattr(playback,"playback_type",None),-1) if playback else -1
            try:props=await session.try_get_media_properties_async()
            except Exception:props=None
            title=str(getattr(props,"title","") or "") if props else ""
            artist=str(getattr(props,"artist","") or "") if props else ""
            album=str(getattr(props,"album_title","") or "") if props else ""
            album_artist=str(getattr(props,"album_artist","") or "") if props else ""
            track_no=int(getattr(props,"track_number",0) or 0) if props else 0

            score=-10000
            why=[]
            proven=False
            if desktop:
                score=1000
                proven=True
                why.append("spotify-desktop")
            elif browser:
                # Browser sessions are accepted only with a Spotify-specific signal.
                # 1) Windows declares MUSIC + title/artist, or
                # 2) the visible browser window itself says Spotify + title/artist.
                # VIDEO remains rejected, so an ordinary YouTube tab is never selected.
                spotify_window=self._spotify_browser_window_hint(source)
                if ptype==2:
                    why.append("video-rejected")
                elif not title:
                    why.append("no-title-rejected")
                elif not artist:
                    why.append("no-artist-rejected")
                elif ptype==1 or spotify_window or bool(album):
                    # Alguns navegadores/versões do Windows deixam PlaybackType como UNKNOWN
                    # no Spotify Web. Título + artista + álbum é uma assinatura musical forte
                    # o bastante para aceitar a sessão sem depender do título da janela.
                    proven=True
                    if spotify_window:
                        score=780; why.append("spotify-window-proven")
                    elif ptype==1:
                        score=740; why.append("browser-music-proven")
                    else:
                        score=720; why.append("browser-rich-metadata-proven")
                    if album:score+=25
                    if album_artist:score+=15
                    if track_no>0:score+=10
                    if session is current:score+=8
                else:
                    why.append("browser-ambiguous-rejected")
            rows.append({
                "session":session,"props":props,"playback":playback,
                "source":source,"title":title,"artist":artist,"album":album,
                "ptype":ptype,"score":score,"why":why,"proven":proven,
                "browser":browser,"desktop":desktop,
            })
        usable=[r for r in rows if r.get("proven") and r["score"]>0]
        if not usable:
            return None,rows
        usable.sort(key=lambda r:r["score"],reverse=True)
        return usable[0],rows

    async def _spotify_read_art_async(self, props, DataReader, Buffer, InputStreamOptions):
        art=b""
        thumb=getattr(props,"thumbnail",None) if props else None
        if thumb is None:return art
        try:
            stream=await thumb.open_read_async()
            size=int(getattr(stream,"size",0) or 0)
            capacity=max(65536,min(5_000_000,size if size>0 else 5_000_000))
            buff=Buffer(capacity)
            result=await stream.read_async(buff,buff.capacity,InputStreamOptions.READ_AHEAD)
            target=result if result is not None else buff
            # PyWinRT buffers support the buffer protocol on recent versions.
            try:
                art=bytes(bytearray(target))
            except Exception:
                reader=DataReader.from_buffer(target)
                length=int(getattr(target,"length",0) or 0)
                out=bytearray(length)
                if length:
                    reader.read_bytes(out)
                art=bytes(out)
        except Exception:
            art=b""
        return art

    async def _spotify_winrt_snapshot_async(self):
        """Read the Spotify-targeted SMTC session; unrelated media is ignored."""
        try:
            MediaManager,DataReader,Buffer,InputStreamOptions,backend=await self._spotify_media_backend()
            manager=await MediaManager.request_async()
            picked,rows=await self._spotify_pick_session_async(manager)
            if picked is None:
                summaries=[]
                browser_rows=[r for r in rows if r.get("browser")]
                for r in rows[:6]:
                    why=",".join(r.get("why") or [])
                    title=(r.get("title") or "")[:48]
                    summaries.append(f"{r.get('source') or '?'} type={r.get('ptype')} why={why} title={title}")
                reason="browser_ambiguous" if browser_rows else "no_spotify_session"
                return {"ok":False,"reason":reason,"error":" | ".join(summaries),"backend":backend}
            session=picked["session"]
            props=picked.get("props")
            if props is None:
                props=await session.try_get_media_properties_async()
            playback=session.get_playback_info()
            timeline=session.get_timeline_properties()
            title=str(getattr(props,"title","") or "") if props else ""
            artist=str(getattr(props,"artist","") or "") if props else ""
            album=str(getattr(props,"album_title","") or "") if props else ""
            status_obj=getattr(playback,"playback_status",None) if playback else None
            status=str(getattr(status_obj,"name",status_obj) or "").upper()
            position=self._spotify_seconds(getattr(timeline,"position",None)) if timeline else 0.0
            start_sec=self._spotify_seconds(getattr(timeline,"start_time",None)) if timeline else 0.0
            end_sec=self._spotify_seconds(getattr(timeline,"end_time",None)) if timeline else 0.0
            duration=max(0.0,end_sec-start_sec) if end_sec>start_sec else end_sec
            art=await self._spotify_read_art_async(props,DataReader,Buffer,InputStreamOptions)
            return {"ok":True,"source":picked.get("source","") ,"title":title,"artist":artist,"album":album,"status":status,"position":position,"duration":duration,"art":art,"backend":backend,"target_score":picked.get("score",0)}
        except Exception as exc:
            return {"ok":False,"reason":"winrt_error","error":f"{type(exc).__name__}: {exc}"}

    async def _spotify_winrt_command_async(self,cmd):
        """Control the chosen Spotify session directly, never global media keys."""
        try:
            MediaManager,_,_,_,backend=await self._spotify_media_backend()
            manager=await MediaManager.request_async()
            picked,rows=await self._spotify_pick_session_async(manager)
            if picked is None:
                browser_rows=[r for r in rows if r.get("browser")]
                reason="browser_ambiguous" if browser_rows else "no_spotify_session"
                msg=("O navegador está expondo mídia, mas o Windows não provou que ela é Spotify Web. Controle bloqueado para proteger YouTube e outras abas." if browser_rows else "Spotify não apareceu nas sessões de mídia do Windows.")
                return {"ok":False,"reason":reason,"backend":backend,"error":msg}
            session=picked["session"]
            command=str(cmd or "").lower()
            if command=="toggle":
                ok=await session.try_toggle_play_pause_async()
                if not ok:
                    playback=session.get_playback_info()
                    st=str(getattr(getattr(playback,"playback_status",None),"name",getattr(playback,"playback_status",None)) or "").upper()
                    if "PAUSED" in st or "STOPPED" in st:
                        ok=await session.try_play_async()
                    elif "PLAYING" in st:
                        ok=await session.try_pause_async()
            elif command=="next":ok=await session.try_skip_next_async()
            elif command=="previous":ok=await session.try_skip_previous_async()
            elif command=="play":ok=await session.try_play_async()
            elif command=="pause":ok=await session.try_pause_async()
            else:return {"ok":False,"reason":"bad_command","error":command}
            return {"ok":bool(ok),"reason":"ok" if ok else "rejected","source":picked.get("source",""),"backend":backend}
        except Exception as exc:
            return {"ok":False,"reason":"winrt_error","error":f"{type(exc).__name__}: {exc}"}

    def _spotify_snapshot_worker(self):
        if self._spotify_snapshot_busy:return
        self._spotify_snapshot_busy=True
        def worker():
            try:
                import asyncio
                snap=asyncio.run(self._spotify_winrt_snapshot_async()) if os.name=="nt" else {"ok":False,"reason":"not_windows"}
            except Exception as exc:
                snap={"ok":False,"reason":"worker_error","error":f"{type(exc).__name__}: {exc}"}
            finally:
                self._spotify_snapshot_busy=False
            try:self.after(0,lambda s=snap:self._spotify_apply_snapshot(s))
            except Exception:pass
        threading.Thread(target=worker,daemon=True).start()

    def _spotify_format_time(self,seconds):
        try:
            seconds=max(0,int(seconds)); return f"{seconds//60}:{seconds%60:02d}"
        except Exception:return "0:00"

    def _spotify_make_art(self,raw,size):
        if not raw:return None
        try:
            from PIL import Image, ImageOps
            im=Image.open(BytesIO(raw)).convert("RGB")
            im=ImageOps.fit(im,(size,size),method=Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=im,dark_image=im,size=(size,size))
        except Exception:return None

    def _spotify_apply_snapshot(self,snap):
        self._spotify_current=dict(snap or {})
        ok=bool(snap.get("ok"))
        if ok:
            title=str(snap.get("title") or "Spotify")
            artist=str(snap.get("artist") or "Artista não informado")
            album=str(snap.get("album") or "")
            source=self._spotify_source_name(snap.get("source"))
            playing="PLAYING" in str(snap.get("status") or "").upper()
            pos=float(snap.get("position") or 0); dur=float(snap.get("duration") or 0)
            self._spotify_set_status(("tocando" if playing else "pausado")+f" • {source}","ok")
            try:self.spotify_source_label.configure(text=("● TOCANDO  •  " if playing else "Ⅱ PAUSADO  •  ")+source.upper())
            except Exception:pass
            try:self.spotify_title_label.configure(text=title)
            except Exception:pass
            try:self.spotify_artist_label.configure(text=artist)
            except Exception:pass
            try:self.spotify_album_label.configure(text=("ÁLBUM  •  "+album) if album else "")
            except Exception:pass
            try:self.spotify_progress.set(max(0.0,min(1.0,pos/dur if dur>0 else 0.0)))
            except Exception:pass
            try:self.spotify_time_label.configure(text=self._spotify_format_time(pos)); self.spotify_duration_label.configure(text=self._spotify_format_time(dur))
            except Exception:pass
            try:
                art=self._spotify_make_art(snap.get("art") or b"",132)
                self._spotify_art_ctk=art
                self.spotify_art_label.configure(image=art,text="" if art else "♫")
            except Exception:pass
            try:
                if getattr(self,"spotify_now_label",None):self.spotify_now_label.configure(text=f"Alvo: {source}  •  {title} — {artist}  •  backend {snap.get('backend','WinRT')}")
            except Exception:pass
            try:
                if self._spotify_mini_frame and self._spotify_mini_frame.winfo_exists():
                    self._spotify_mini_title.configure(text=title)
                    self._spotify_mini_artist.configure(text=artist)
                    mart=self._spotify_make_art(snap.get("art") or b"",54); self._spotify_mini_art_ctk=mart
                    if getattr(self,"_spotify_mini_art_label",None):self._spotify_mini_art_label.configure(image=mart,text="" if mart else "♫")
            except Exception:pass
            try:
                now=time.monotonic()
                if now-float(getattr(self,"_spotify_last_volume_probe",0.0))>4.5:
                    self._spotify_last_volume_probe=now
                    self._spotify_volume_async("read",None,True)
            except Exception:pass
        else:
            reason=str(snap.get("reason") or "")
            error=str(snap.get("error") or "").strip()
            if reason=="browser_ambiguous":
                self._spotify_set_status("mídia do navegador detectada, mas não é possível provar que é Spotify Web; controles bloqueados para não pausar YouTube","warning")
            elif reason=="no_spotify_session":
                self._spotify_set_status("Spotify não encontrado nas sessões do Windows; YouTube e outros players serão ignorados","warning")
                detail="Dê play uma vez no Spotify Desktop/Web. Depois ele pode ficar pausado que o ZKStrap continua mirando a sessão dele."
            elif reason=="not_windows":
                self._spotify_set_status("Now Playing disponível somente no Windows","warning"); detail=""
            else:
                self._spotify_set_status("falha no leitor do Spotify/Windows; veja o diagnóstico abaixo","error")
                detail=error or "Sessão não disponível."
            try:self.spotify_source_label.configure(text="SPOTIFY // SESSÃO ALVO")
            except Exception:pass
            try:self.spotify_title_label.configure(text="Spotify não detectado")
            except Exception:pass
            try:self.spotify_artist_label.configure(text="Use Spotify Desktop para controle 100% exclusivo. No navegador, sessões ambíguas são bloqueadas.")
            except Exception:pass
            try:self.spotify_album_label.configure(text="")
            except Exception:pass
            try:self.spotify_progress.set(0); self.spotify_time_label.configure(text="0:00"); self.spotify_duration_label.configure(text="0:00")
            except Exception:pass
            try:self.spotify_art_label.configure(image=None,text="♫"); self._spotify_art_ctk=None
            except Exception:pass
            try:
                if getattr(self,"spotify_now_label",None):self.spotify_now_label.configure(text=("Diagnóstico: "+detail) if detail else "")
            except Exception:pass

    def spotify_search_web(self):
        try:q=str(self.spotify_search_entry.get() or "").strip()
        except Exception:q=""
        if not q:
            self._spotify_set_status("digite uma música, artista ou álbum para pesquisar","warning"); return
        try:
            webbrowser.open("https://open.spotify.com/search/"+urllib.parse.quote(q,safe=""))
            self._spotify_set_status(f"pesquisando no Spotify: {q}","ok")
        except Exception as exc:self._spotify_set_status(f"não consegui abrir a pesquisa: {exc}","error")

    def spotify_open_app(self):
        if os.name!="nt":
            self._spotify_set_status("abrir Spotify automaticamente está disponível somente no Windows","warning"); return False
        try:
            os.startfile("spotify:"); self._spotify_set_status("abrindo Spotify…","ok"); self._play_ui_sound("open",0); self.after(1200,self.spotify_poll_now); return True
        except Exception:
            try:webbrowser.open("https://open.spotify.com")
            except Exception:pass
            self._spotify_set_status("app não localizado; abri o Spotify Web","warning"); return False

    def _spotify_toggle_web_volume(self):
        try:self.spotify_web_volume_optin=bool(self.spotify_web_volume_switch.get())
        except Exception:self.spotify_web_volume_optin=not bool(getattr(self,"spotify_web_volume_optin",False))
        self.salvar_config_app()
        if self.spotify_web_volume_optin:
            self._spotify_set_status("volume Web liberado: ele controla o processo do navegador e pode afetar outras abas", "warning")
        else:
            self._spotify_set_status("volume Web protegido; apenas Spotify Desktop terá volume isolado", "ok")
        self._spotify_volume_async("read",None,True)

    def _spotify_audio_volume_worker(self, action="read", value=None):
        """Read/change ONLY the Spotify audio session using Windows Core Audio.

        Desktop Spotify is isolated by process name. Browser audio is never changed
        just because it comes from chrome.exe/msedge.exe: that could also mute YouTube.
        A browser session is accepted only if its Core Audio metadata itself contains
        an explicit Spotify identifier.
        """
        if os.name != "nt":
            return {"ok":False,"reason":"not_windows","error":"Windows required"}
        coinited=False
        try:
            try:
                import comtypes
                try:
                    comtypes.CoInitialize()
                    coinited=True
                except Exception:
                    pass
            except Exception:
                comtypes=None
            from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
            sessions=AudioUtilities.GetAllSessions()
            targets=[]
            browser_names={"chrome.exe","msedge.exe","firefox.exe","brave.exe","opera.exe"}
            spotify_pids=set()
            try:
                for pr in psutil.process_iter(["pid","name"]):
                    name=str(pr.info.get("name") or "").lower()
                    if name=="spotify.exe" or name.startswith("spotify"):
                        spotify_pids.add(int(pr.info.get("pid") or 0))
            except Exception:pass
            for sess in sessions:
                proc_name=""; proc_pid=0
                try:
                    proc=sess.Process
                    if proc is not None:
                        proc_name=str(proc.name() or "").lower(); proc_pid=int(getattr(proc,"pid",0) or 0)
                except Exception:
                    proc_name=""; proc_pid=0
                if not proc_pid:
                    try:proc_pid=int(getattr(sess,"ProcessId",0) or 0)
                    except Exception:proc_pid=0
                fields=[]
                for attr in ("DisplayName","Identifier","InstanceIdentifier"):
                    try: fields.append(str(getattr(sess,attr," ") or ""))
                    except Exception: pass
                meta=" ".join(fields).lower()
                is_desktop=(proc_name=="spotify.exe" or proc_pid in spotify_pids or "spotify.exe" in meta or "spotifyab.spotifymusic" in meta or "spotify" in meta and proc_name not in browser_names)
                is_web=(proc_name in browser_names and ("open.spotify" in meta or "spotify" in meta))
                if not (is_desktop or is_web):
                    continue
                try:
                    ctl=sess._ctl.QueryInterface(ISimpleAudioVolume)
                except Exception:
                    try: ctl=sess.SimpleAudioVolume
                    except Exception: continue
                targets.append((ctl,"desktop" if is_desktop else "web",proc_name,meta))
            if not targets and bool(getattr(self,"spotify_web_volume_optin",False)) and self._spotify_browser_window_hint():
                # Explicit opt-in only: Core Audio exposes browser audio per process, not per tab.
                # Therefore this can affect other tabs in the same browser and the UI says so.
                for sess in sessions:
                    try:
                        proc=sess.Process; proc_name=str(proc.name() or "").lower() if proc is not None else ""
                    except Exception: proc_name=""
                    if proc_name not in browser_names: continue
                    try: ctl=sess._ctl.QueryInterface(ISimpleAudioVolume)
                    except Exception:
                        try: ctl=sess.SimpleAudioVolume
                        except Exception: continue
                    targets.append((ctl,"web-browser",proc_name,"spotify window opt-in"))
            if not targets:
                return {"ok":False,"reason":"no_isolated_audio_session","error":"Spotify Desktop audio session not found; browser volume is protected unless Web volume opt-in is enabled."}

            levels=[]; mutes=[]
            for ctl,kind,proc,meta in targets:
                try: levels.append(float(ctl.GetMasterVolume()))
                except Exception: pass
                try: mutes.append(bool(ctl.GetMute()))
                except Exception: pass
            current=max(levels) if levels else 1.0
            muted=bool(mutes and all(mutes))

            act=str(action or "read").lower()
            if act=="set":
                target=max(0.0,min(1.0,float(value)))
                for ctl,_,_,_ in targets:
                    try: ctl.SetMasterVolume(target,None)
                    except Exception: pass
                current=target
                if target>0 and muted:
                    for ctl,_,_,_ in targets:
                        try: ctl.SetMute(0,None)
                        except Exception: pass
                    muted=False
            elif act=="delta":
                target=max(0.0,min(1.0,current+float(value or 0)))
                for ctl,_,_,_ in targets:
                    try: ctl.SetMasterVolume(target,None)
                    except Exception: pass
                current=target
                if target>0 and muted:
                    for ctl,_,_,_ in targets:
                        try: ctl.SetMute(0,None)
                        except Exception: pass
                    muted=False
            elif act=="mute_toggle":
                new_mute=not muted
                for ctl,_,_,_ in targets:
                    try: ctl.SetMute(1 if new_mute else 0,None)
                    except Exception: pass
                muted=new_mute
            kinds={k for _,k,_,_ in targets}
            if "web-browser" in kinds: out_kind="web-browser"
            elif kinds=={"web"}: out_kind="web"
            else: out_kind="desktop"
            return {"ok":True,"volume":current,"muted":muted,"target_count":len(targets),"kind":out_kind}
        except Exception as exc:
            return {"ok":False,"reason":"pycaw_error","error":f"{type(exc).__name__}: {exc}"}
        finally:
            if coinited:
                try: comtypes.CoUninitialize()
                except Exception: pass

    def _spotify_apply_volume_result(self,result,quiet=False):
        r=dict(result or {})
        if r.get("ok"):
            pct=int(round(float(r.get("volume",1.0))*100))
            muted=bool(r.get("muted"))
            kind=str(r.get("kind") or "desktop")
            try:
                self.spotify_volume_slider.set(pct)
                self.spotify_volume_value_label.configure(text=("MUDO" if muted else f"{pct}%"))
                if kind=="desktop": state="SPOTIFY DESKTOP • volume isolado"
                elif kind=="web-browser": state="SPOTIFY WEB • volume do navegador (outras abas podem mudar)"
                else: state="SPOTIFY WEB • sessão isolada"
                self.spotify_volume_state_label.configure(text=state,text_color="#1ED760")
            except Exception: pass
            if not quiet:
                self._spotify_set_status(("Spotify mutado" if muted else f"volume do Spotify: {pct}%"),"ok")
            return True
        reason=str(r.get("reason") or "")
        err=str(r.get("error") or "")
        try:
            if reason=="no_isolated_audio_session":
                self.spotify_volume_state_label.configure(text="VOLUME EXCLUSIVO • abra o Spotify Desktop",text_color="#F0C75E")
                self.spotify_volume_value_label.configure(text="—")
            else:
                self.spotify_volume_state_label.configure(text="VOLUME EXCLUSIVO • indisponível",text_color="#FF6B7A")
                self.spotify_volume_value_label.configure(text="—")
        except Exception: pass
        if not quiet:
            if reason=="no_isolated_audio_session":
                self._spotify_set_status("volume exclusivo não encontrado; o navegador não será alterado para não afetar YouTube","warning")
            else:
                self._spotify_set_status("falha no volume exclusivo: "+(err or reason),"error")
        return False

    def _spotify_volume_async(self,action="read",value=None,quiet=False):
        def worker():
            result=self._spotify_audio_volume_worker(action,value)
            try:self.after(0,lambda r=result,q=quiet:self._spotify_apply_volume_result(r,q))
            except Exception:pass
        threading.Thread(target=worker,daemon=True).start()

    def _spotify_volume_preview(self,value):
        try:
            pct=max(0,min(100,int(round(float(value)))))
            if getattr(self,"spotify_volume_value_label",None):self.spotify_volume_value_label.configure(text=f"{pct}%")
        except Exception:pass

    def _spotify_volume_apply_slider(self):
        try:value=float(self.spotify_volume_slider.get())/100.0
        except Exception:return
        self._spotify_volume_async("set",value,False)

    def spotify_local_command(self,cmd):
        command=str(cmd or "").lower()
        if os.name!="nt":self._spotify_set_status("controle local disponível somente no Windows","warning"); return False
        # Volume is isolated to Spotify audio sessions; never touch Windows master
        # volume and never change an unidentified browser session.
        if command in ("spotify_mute","mute"):
            self._spotify_volume_async("mute_toggle",None,False); self._play_ui_sound("click",0); return True
        if command in ("spotify_volume_down","volume_down"):
            self._spotify_volume_async("delta",-0.05,False); self._play_ui_sound("click",0); return True
        if command in ("spotify_volume_up","volume_up"):
            self._spotify_volume_async("delta",0.05,False); self._play_ui_sound("click",0); return True
        if command not in ("previous","toggle","next","play","pause"):
            return False
        self._spotify_set_status("enviando comando direto para a sessão do Spotify…","info")
        def worker():
            try:
                import asyncio
                result=asyncio.run(self._spotify_winrt_command_async(command))
            except Exception as exc:
                result={"ok":False,"reason":"worker_error","error":f"{type(exc).__name__}: {exc}"}
            def finish(r=result):
                if r.get("ok"):
                    self._spotify_set_status(f"comando enviado • {self._spotify_source_name(r.get('source'))}","ok")
                    self._play_ui_sound("click",0)
                    self.after(220,self.spotify_poll_now)
                else:
                    reason=str(r.get("reason") or "")
                    if reason=="browser_ambiguous":
                        self._spotify_set_status("controle bloqueado: o Chrome/Edge não separou Spotify Web de outras abas; nenhum player foi controlado","warning")
                    elif reason=="no_spotify_session":
                        self._spotify_set_status("Spotify não encontrado; nenhum outro player foi controlado","warning")
                    else:
                        self._spotify_set_status("comando recusado: "+str(r.get("error") or reason),"error")
            try:self.after(0,finish)
            except Exception:pass
        threading.Thread(target=worker,daemon=True).start()
        return True

    def spotify_command(self,cmd):
        if cmd in ("previous","toggle","next","spotify_mute","spotify_volume_down","spotify_volume_up","mute","volume_down","volume_up"):return self.spotify_local_command(cmd)
        return False

    def spotify_connect(self):self.spotify_open_app()
    def spotify_disconnect(self):self.spotify_auth={}; self.spotify_client_id=""; self._spotify_set_status("nenhuma conta fica conectada nesta versão","ok")
    def spotify_test_connection(self):self.spotify_poll_now()
    def spotify_set_volume(self,value):
        try:self._spotify_volume_async("set",max(0.0,min(1.0,float(value)/100.0 if float(value)>1 else float(value))),False)
        except Exception:self._spotify_set_status("não consegui ajustar o volume exclusivo do Spotify","error")

    def spotify_poll_now(self):
        self._spotify_snapshot_worker()
        if getattr(self,"_spotify_poll_job",None):
            try:self.after_cancel(self._spotify_poll_job)
            except Exception:pass
        try:
            page_open=(getattr(self,"current_page_key","")=="spotify")
            mini_open=bool(self._spotify_mini_frame and self._spotify_mini_frame.winfo_exists())
            self._spotify_poll_job=self.after(1800,self.spotify_poll_now) if (page_open or mini_open) else None
        except Exception:self._spotify_poll_job=None
        return True

    def _spotify_render_now(self):self.spotify_poll_now()

    def _spotify_show_mini(self,user_action=False):
        self.spotify_mini_hidden=False; self.salvar_config_app()
        if self._spotify_mini_frame is not None:
            try:
                if self._spotify_mini_frame.winfo_exists():self._spotify_mini_frame.lift(); return
            except Exception:pass
        t=TEMAS[self.tema_atual]
        f=ctk.CTkFrame(self,width=360,height=112,fg_color="#181818",corner_radius=14,border_width=1,border_color="#1ED760")
        f.place(x=-390,rely=1.0,y=-15,anchor="sw"); f.pack_propagate(False); self._spotify_mini_frame=f
        art=ctk.CTkFrame(f,width=64,height=64,fg_color="#242424",corner_radius=10); art.pack(side="left",padx=(10,8),pady=10); art.pack_propagate(False)
        self._spotify_mini_art_label=ctk.CTkLabel(art,text="♫",text_color="#1ED760",font=ctk.CTkFont(size=20,weight="bold")); self._spotify_mini_art_label.pack(fill="both",expand=True)
        left=ctk.CTkFrame(f,fg_color="transparent"); left.pack(side="left",fill="both",expand=True,padx=(0,4),pady=9)
        self._spotify_mini_title=ctk.CTkLabel(left,text="Spotify",text_color="#FFFFFF",font=ctk.CTkFont(size=10,weight="bold"),anchor="w"); self._spotify_mini_title.pack(fill="x")
        self._spotify_mini_artist=ctk.CTkLabel(left,text="Now Playing do Windows",text_color="#B3B3B3",font=ctk.CTkFont(size=8),anchor="w"); self._spotify_mini_artist.pack(fill="x")
        rr=ctk.CTkFrame(left,fg_color="transparent"); rr.pack(fill="x",pady=(5,0))
        for lab,cmd in (("⏮","previous"),("▶/⏸","toggle"),("⏭","next")):
            ctk.CTkButton(rr,text=lab,width=58,height=26,command=lambda c=cmd:self.spotify_local_command(c),fg_color=t["card_active"],text_color=t["accent"]).pack(side="left",padx=2)
        ctk.CTkButton(f,text="×",width=28,height=28,command=self._spotify_hide_mini,fg_color="transparent",hover_color=t["card_active"],text_color=t["text"]).pack(side="right",anchor="n",padx=6,pady=6)
        self._play_ui_sound("open",0)
        def anim(x=-390):
            if self._spotify_mini_frame is not f:return
            nx=min(15,x+46); f.place_configure(x=nx)
            if nx<15:self.after(15,lambda:anim(nx))
        anim(); self.spotify_poll_now()

    def _spotify_hide_mini(self):
        f=getattr(self,"_spotify_mini_frame",None); self.spotify_mini_hidden=True; self.salvar_config_app(); self._play_ui_sound("close",0)
        if not f:return
        def anim(x=15):
            try:
                nx=x-48; f.place_configure(x=nx)
                if nx>-405:self.after(14,lambda:anim(nx))
                else:f.destroy();self._spotify_clear_mini_ref()
            except Exception:self._spotify_clear_mini_ref()
        anim()

    def _spotify_clear_mini_ref(self):
        self._spotify_mini_frame=None
        self._spotify_mini_art_label=None

    # ------------------------------------------------------------------
    # ZK AI v3.10 — Dialogue Engine guiado (sem IA generativa).
    # ------------------------------------------------------------------
    def _zkai_nick(self):
        nick=str(getattr(self,"onboarding_username","") or "").strip().lstrip("@")
        if not nick:
            try: nick=str(getattr(self,"linked_profile",{}).get("name","") or "").strip().lstrip("@")
            except Exception: nick=""
        return nick or "player"

    def _zkai_add_bubble(self, role, text, actions=None):
        host=getattr(self,"zkai_chat_frame",None)
        if host is None or not self._widget_alive(host): return
        t=TEMAS[self.tema_atual]; st=self._theme_style()
        is_user=(role=="user")
        row=ctk.CTkFrame(host,fg_color="transparent")
        row.pack(fill="x",pady=6,padx=10)
        bubble=ctk.CTkFrame(row,fg_color=t["card_active"] if is_user else t["card"],corner_radius=max(10,st["nav_radius"]),border_width=1,border_color=t["border"] if is_user else t["accent"])
        bubble.pack(side="right" if is_user else "left",anchor="e" if is_user else "w",padx=(110,0) if is_user else (0,110))
        head=ctk.CTkFrame(bubble,fg_color="transparent"); head.pack(fill="x",padx=12,pady=(8,2))
        ctk.CTkLabel(head,text=("VOCÊ  /  INPUT" if is_user else "ZK ASSIST  /  APP HELP"),text_color=t.get("muted","gray") if is_user else t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold"),anchor="w").pack(side="left")
        ctk.CTkLabel(head,text="●",text_color=t["accent"] if not is_user else t.get("muted","gray"),font=ctk.CTkFont(size=8)).pack(side="right")
        ctk.CTkLabel(bubble,text=str(text),wraplength=650,justify="left",anchor="w",text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=10)).pack(fill="x",padx=12,pady=(4,10))
        if actions:
            ar=ctk.CTkFrame(bubble,fg_color="transparent"); ar.pack(fill="x",padx=10,pady=(0,10))
            for label,action in actions[:4]:
                ctk.CTkButton(ar,text=label,command=lambda a=action:self._zkai_action(a),height=31,corner_radius=max(6,st["nav_radius"]-2),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["accent"],border_width=1,border_color=t["border"],font=ctk.CTkFont(size=8,weight="bold")).pack(side="left",padx=3,pady=2)

    def _zkai_action(self, action):
        if not action: return
        if action.startswith("page:"):
            self.show_page(action.split(":",1)[1],animate=True); return
        if action=="apply": self.aplicar_configuracoes(); return
        if action=="tutorial": self.abrir_tutorial(False); return
        if action.startswith("url:"):
            try:webbrowser.open(action.split(":",1)[1])
            except Exception:pass

    def _zkdialog_clear(self):
        for name in ("zkai_chat_frame","zkai_options_frame"):
            host=getattr(self,name,None)
            if host is not None and self._widget_alive(host):
                for w in host.winfo_children():
                    try:w.destroy()
                    except Exception:pass

    def _zkdialog_set_options(self, options):
        host=getattr(self,"zkai_options_frame",None)
        if host is None or not self._widget_alive(host): return
        for w in host.winfo_children():
            try:w.destroy()
            except Exception:pass
        t=TEMAS[self.tema_atual]; st=self._theme_style()
        if not options: return
        title=ctk.CTkFrame(host,fg_color="transparent"); title.pack(fill="x",pady=(2,6))
        ctk.CTkLabel(title,text="PRÓXIMA DECISÃO",text_color=t["text"],font=ctk.CTkFont(family="Segoe UI",size=10,weight="bold")).pack(side="left")
        ctk.CTkLabel(title,text=f"{len(options)} CAMINHOS",text_color=t["accent"],font=ctk.CTkFont(family="Consolas",size=7,weight="bold")).pack(side="right")
        grid=ctk.CTkFrame(host,fg_color="transparent"); grid.pack(fill="x")
        for i,opt in enumerate(options):
            if len(opt)==2: label,target=opt; user_text=label
            else: label,target,user_text=opt
            display_label="\n".join(textwrap.wrap(str(label),width=31,break_long_words=False,break_on_hyphens=False)) or str(label)
            button_height=52 if "\n" in display_label else 42
            b=ctk.CTkButton(grid,text=display_label,height=button_height,corner_radius=max(7,st["nav_radius"]),command=lambda l=user_text,tg=target:self._zkdialog_choose(l,tg),fg_color=t["card_active"],hover_color=t["hover"],text_color=t["text"],border_width=1,border_color=t["border"],font=ctk.CTkFont(family="Segoe UI",size=8,weight="bold"))
            b.grid(row=i//2,column=i%2,sticky="ew",padx=4,pady=4)
            grid.grid_columnconfigure(i%2,weight=1,uniform="zkopt")

    def _zkdialog_choose(self, user_text, target):
        self._zkai_add_bubble("user",user_text)
        # Pequeno delay visual de mensageiro; a resposta já está pronta localmente.
        self.after(180,lambda:self._zkdialog_go(target))

    def _zkdialog_render_topics(self):
        host=getattr(self,"zkai_topic_frame",None)
        if host is None or not self._widget_alive(host):return
        for w in host.winfo_children():
            try:w.destroy()
            except Exception:pass
        t=TEMAS[self.tema_atual]
        topics=[
            ("⚙  APLICAR / ROBLOX","app:cat_apply","Flags, pasta, vincular, reiniciar"),
            ("⚡  FPS / PING","app:cat_performance","FPS, gráficos e rede"),
            ("✦  VISUAL / ÁUDIO","app:cat_visual","Tema, cursor, fonte, sons"),
            ("🎮  BLOX TOOLS","app:cat_tools","Roulette, Planner, Creator"),
            ("🛠  ERROS / RECUPERAÇÃO","app:cat_recovery","Logs, backup, rollback, manutenção"),
            ("ⓘ  APP / TUTORIAL","app:cat_info","Status, atualizações, tutorial"),
        ]
        for i,(label,target,sub) in enumerate(topics):
            card=ctk.CTkFrame(host,fg_color=t["card_active"],corner_radius=10,border_width=1,border_color=t["border"]); card.grid(row=i//2,column=i%2,sticky="nsew",padx=5,pady=5)
            ctk.CTkButton(card,text=label,height=38,command=lambda tg=target:self._zkdialog_topic_click(tg),fg_color="transparent",hover_color=t["hover"],text_color=t["accent"],font=ctk.CTkFont(size=9,weight="bold"),anchor="w").pack(fill="x",padx=4,pady=(4,0))
            ctk.CTkLabel(card,text=sub,text_color=t.get("muted","gray"),font=ctk.CTkFont(size=8),anchor="w").pack(fill="x",padx=10,pady=(0,8))
            host.grid_columnconfigure(i%2,weight=1,uniform="zkcat")

    def _zkassist_search(self):
        try:q=str(self.zkai_search_entry.get() or "").strip().lower()
        except Exception:q=""
        if not q:
            self._zkdialog_topic_click("app:home"); return
        routes=[
            (("aplica","aplicar","flag","clientsettings","não aplica","nao aplica"),"app:not_apply"),
            (("roblox","pasta","version","vincular"),"app:roblox"),
            (("fps","lag","gráfico","grafico","desempenho"),"app:fps"),
            (("ping","latência","latencia","dns","rede"),"app:ping"),
            (("resolução","resolucao","stretch"),"app:resolution"),
            (("cursor","mouse"),"app:cursor"),
            (("fonte","font"),"app:fonts"),
            (("tema","cor","visual"),"app:themes"),
            (("som","audio","áudio","música","musica"),"app:audio"),
            (("combo","planner"),"app:combo"),
            (("roleta","roulette"),"app:roulette"),
            (("desafio","creator"),"app:creator"),
            (("spotify","mídia","midia"),"app:spotify"),
            (("log","erro","bug","falha"),"app:logs"),
            (("backup","restaurar","recuperação","recuperacao"),"app:recovery"),
            (("tutorial","como usa","como usar"),"app:tutorial"),
            (("atualização","atualizacao","versão","versao"),"app:updates"),
        ]
        for keys,target in routes:
            if any(k in q for k in keys):
                self._zkdialog_topic_click(target); return
        self._zkdialog_clear(); self._zkai_add_bubble("assistant",f"Não encontrei uma função exata para ‘{q}’. Escolha uma das 6 áreas acima; elas são mais fáceis de navegar do que a lista antiga.")
        self._zkdialog_set_options([("APLICAR / ROBLOX","app:cat_apply"),("FPS / PING","app:cat_performance"),("VISUAL / ÁUDIO","app:cat_visual"),("ERROS / RECUPERAÇÃO","app:cat_recovery")])

    def _zkdialog_topic_click(self,target):
        self._zkdialog_clear(); self._zkdialog_go(target)

    def _zkai_set_mode(self, mode):
        # Nesta versão só o Assistente ZKStrap está liberado.
        if mode=="pvp":
            try:self.show_toast("IA EM DESENVOLVIMENTO","O ZK AI/PvP Coach será liberado em uma atualização futura quando estiver estável.",kind="info",duration=3000)
            except Exception:pass
            self.zkai_mode="zkstrap"
            self._zkai_refresh_mode_ui(render=False)
            return
        self.zkai_mode="zkstrap"
        self._zkai_refresh_mode_ui(render=True)

    def _zkai_refresh_mode_ui(self, render=False):
        self.zkai_mode="zkstrap"
        try:
            self.zkai_mode_label.configure(text="MODO // ASSISTENTE LOCAL")
            self.zkai_context_label.configure(text="Estado real do app • atalhos diretos • sem conversa livre")
        except Exception:pass
        self._zkdialog_render_topics()
        if render:
            self._zkdialog_clear(); self._zkdialog_go("app:home")

    def _zkdialog_app_status(self):
        states=getattr(self,"module_states",{})
        labels={"performance_boost":"FPS/gráficos","gray_sky":"céu cinza","fps_unlock":"FPS unlock","ping_boost":"rede/ping","telemetry_off":"telemetria off","micro_opt":"micro-otimização","draco_aura":"Draco V4"}
        ativos=[labels.get(k,k) for k,v in states.items() if v]
        return "Ativos agora: " + (", ".join(ativos) if ativos else "nenhum módulo principal") + f". Alvo de FPS: {getattr(self,'micro_fps_target','144')}. Watchdog: {'ligado' if getattr(self,'config_watchdog_enabled',False) else 'desligado'}."

    def _zkdialog_nodes(self):
        # Árvore principal do PvP Coach. As respostas abaixo são fechadas e baseadas
        # exclusivamente no material curado do ZKVEZ para esta versão.
        return {
            "greeting": ("Eae mano. Antes de liberar o Coach, escolhe uma saudação pra gente começar kkkkk.", [
                ("EAE MANO","greet_eae"),("OI, TUDO BEM?","greet_tudo"),("COMO CÊ TÁ?","greet_como"),("BOA?","greet_boa")]),
            "greet_eae": ("Eae meu parcero kkkkk, tudo dboa?",[("TO DBOA","greet_finish"),("MAIS OU MENOS","greet_mid"),("BORA PRO PVP","greet_finish")]),
            "greet_tudo": ("Tudo dboa kkkkk, e você?",[("TO DBOA","greet_finish"),("MAIS OU MENOS","greet_mid"),("BORA PRO PVP","greet_finish")]),
            "greet_como": ("Tô dboa, pronto pra analisar teu PvP sem inventar moda kkkkk. E você?",[("TO DBOA","greet_finish"),("MAIS OU MENOS","greet_mid")]),
            "greet_boa": ("Boa demais kkkkk. Tá suave por aí?",[("SUAVE","greet_finish"),("MAIS OU MENOS","greet_mid")]),
            "greet_mid": ("Aí é foda kkkkk. Bora focar no PvP então; escolhe um tópico e a gente vai por partes.",[("BORA","greet_finish")]),
            "greet_finish": ("Fechou. Saudações concluídas. Agora as áreas do Coach estão liberadas; escolhe qualquer uma ali em cima.",[("NÃO SEI O QUE MELHORAR","diag_start"),("MOVIMENTAÇÃO","movement_start"),("COMBO","combo_start")]),
            "pvp_home": ("Escolhe uma área nos tópicos acima. Se você não souber o problema, usa ‘NÃO SEI O QUE MELHORAR’ e eu vou confirmando hipótese por hipótese.",[("NÃO SEI O QUE MELHORAR","diag_start"),("MOVIMENTAÇÃO","movement_start"),("MIRA","aim_start"),("COMBO","combo_start")]),

            # Diagnóstico geral: suspeita -> confirmação -> conselho.
            "diag_start": ("Vamos descobrir sem chutar. Você toma combo com frequência?",[("SIM","diag_takes"),("NÃO","diag_attack")]),
            "diag_takes": ("Quando isso acontece, qual opção parece mais com você?",[("ME MOVIMENTO POUCO","diag_move"),("NÃO SEI QUANDO ELE VAI AVANÇAR","diag_gamesense"),("OS DOIS","diag_both"),("NÃO É ISSO","diag_attack")]),
            "diag_move": ("Então movement é um ponto forte pra treinar. Você precisa variar direção, ground/air e aprender Soul Dash; parado ou lento demais fica previsível. Isso bate com suas lutas?",[("SIM, É ISSO","movement_start"),("NÃO","diag_attack")]),
            "diag_gamesense": ("Isso já puxa game sense: não adianta só se mover; você precisa ler a entrada antes dela acontecer. Qual dessas situações parece mais com o que acontece com você?",[("ELE ENTRA ANTES DE EU REAGIR","gs_react"),("AVANÇO E TOMO COUNTER","gs_countered"),("EU RECUO DEMAIS","gs_too_passive"),("NÃO É ISSO","diag_attack")]),
            "diag_both": ("Parece MOVEMENT + GAME SENSE: movimentação pouco variada e dificuldade de ler a entrada do adversário. Quer trabalhar qual primeiro?",[("MOVIMENTAÇÃO","movement_start"),("GAME SENSE","gamesense_start")]),
            "diag_attack": ("Você consegue iniciar seus próprios combos?",[("ERRO O STARTER","aim_starter"),("ACERTO, MAS O COMBO QUEBRA","combo_break"),("ACERTO E DEMORO PRA MATAR","combo_slow"),("ESSA PARTE TÁ BOA","diag_predict")]),
            "diag_predict": ("Quando tenta avançar, você sente que o adversário já sabe onde você vai estar?",[("SIM","predict_start"),("NÃO","training_start")]),

            # Movement / tracking.
            "movement_start": ("Qual situação combina mais com você?",[("ME MOVIMENTO BEM, MAS NÃO ACERTO O COMBO","move_good_combo"),("ME MOVIMENTO MAL, MAS QUANDO COMBO EU MATO","move_bad_kill"),("ME MOVIMENTO MAL E MINHA MIRA É RUIM","move_aim"),("PERCO O INIMIGO DA TELA","tracking"),("TOMO COMBO MESMO ME MOVIMENTANDO","move_take_combo"),("NÃO SEI SOUL DASH","souldash")]),
            "move_good_combo": ("Se o movement já está bom mas você não encaixa combo, eu investigaria MIRA + COMBO. Você perde mais o starter ou quebra no meio?",[("ERRO O STARTER","aim_starter"),("QUEBRA NO MEIO","combo_break")]),
            "move_bad_kill": ("Seu dano/execução parece suficiente quando entra. Então o foco é chegar melhor na oportunidade: variar direção, ground/air, Soul Dash e não ficar lento/previsível.",[("COMO MELHORO MOVEMENT?","movement_core"),("NÃO SEI SOUL DASH","souldash")]),
            "move_aim": ("Aqui eu juntaria MOVEMENT + MIRA. Primeiro pare de ficar previsível; depois treine acompanhar o alvo e acertar a skill no momento certo em PvP real.",[("EU PERCO ELE DA TELA","tracking"),("EU VEJO, MAS ERRO A SKILL","aim_skill"),("QUERO MOVEMENT","movement_core")]),
            "tracking": ("Quando perder o cara, abre mais a câmera/FOV pra enxergar uma área maior. Achou ele? Diminui e volta a focar. Usa também o som do dash e das skills pra localizar onde ele está.",[("EU NÃO USO MUITO O SOM","audio"),("ENTENDI","movement_start")]),
            "movement_core": ("Movement bom é imprevisível: varia direção, lateral/vertical, ground/air, usa dash normal e Soul Dash pra reposicionar. Soru/TP serve pra escapar de combo ou fechar distância; não fica repetindo sempre a mesma rota.",[("SOUL DASH","souldash"),("QUANDO O CARA AVANÇA?","gamesense_advance"),("VOLTAR","movement_start")]),
            "souldash": ("Soul Dash é click da Soul Guitar + dash e jump praticamente juntos. É ótimo pra movement, escapar e ficar imprevisível. Só não usa no meio do seu próprio combo, senão você se joga pra longe do cara kkkkk.",[("ABRIR TUTORIAL DO ZKVEZ","url:https://youtu.be/YUQNjDriM1c?si=lmBtR5Z_I8bwZckm"),("VOLTAR","movement_start")]),
            "move_take_combo": ("Se você se movimenta bem e ainda toma combo, movement não é tudo. O próximo ponto é saber quando o inimigo vai avançar em você e reagir antes da entrada.",[("TREINAR ISSO","gamesense_advance"),("VER OBSERVATION","obs_start")]),

            # Mira / tracking / starter.
            "aim_start": ("Primeiro separa MIRA de PREDICT. Mira é acertar skill/click que exige precisão; predict é saber onde o player vai estar pela movimentação. Qual é seu caso?",[("PERCO O INIMIGO DA TELA","tracking"),("VEJO ELE, MAS ERRO A SKILL","aim_skill"),("ERRO O STARTER","aim_starter"),("QUERO ENTENDER PREDICT","predict_start")]),
            "aim_skill": ("Se você acompanha o alvo mas erra a skill, treina isso em PvP real. Player ‘skill’ precisa de boa mira justamente porque usa skill pequena, pouco range ou gun. Não tenta compensar jogando skill aleatória.",[("ERRO POR REAÇÃO LENTA","aim_reaction"),("QUERO TREINAR PREDICT","predict_start")]),
            "aim_reaction": ("Às vezes o problema é tempo de reação. Boa noção de jogo ajuda porque você reage antes: lê movimento, item na mão e o momento em que ele vai entrar, em vez de esperar tudo acontecer pra só depois mirar.",[("GAME SENSE","gamesense_start"),("VOLTAR PRA MIRA","aim_start")]),
            "aim_starter": ("Starter pode falhar por mira, predict ou timing ruim. Se você é lento pra reagir, trabalha game sense; se vê o alvo e erra a posição, trabalha mira; se ele sempre já saiu dali, trabalha predict.",[("MIRA","aim_skill"),("PREDICT","predict_start"),("TIMING / GAME SENSE","gamesense_advance")]),

            # Combo / ken trick / endlag.
            "combo_start": ("O que acontece com seu combo?",[("ERRO O STARTER","aim_starter"),("O CARA ESCAPA","combo_break"),("QUEBRA NO MEIO","combo_break"),("NO DUMMY FUNCIONA, EM PLAYER NÃO","combo_dummy"),("DEMORO MUITO PRA MATAR","combo_slow"),("ELE DESVIA MUITO","combo_mini")]),
            "combo_break": ("Reveja o combo e ache exatamente onde dá pra escapar. Normalmente você precisa olhar partes ken-trickáveis e o endlag entre skills; muda a sequência da forma correta até fechar essa abertura.",[("ELE USA OBS E SAI","combo_obs"),("ELE DÁ TP PRA FORA","combo_endlag"),("NÃO SEI ONDE ESCAPA","combo_review")]),
            "combo_dummy": ("Dummy não usa Observation nem TP. Se funciona nele e falha em player, procura skills que dão pra desviar e endlag entre elas; é aí que o cara consegue sair.",[("REVER ABERTURAS","combo_review"),("OBSERVATION / KEN-TRICK","obs_start")]),
            "combo_review": ("Treina no dummy pra decorar a sequência, mas depois testa com amigo/player. Repete até achar a abertura real e cria variações pra quando uma skill estiver faltando.",[("FULL OU MINI?","combo_mini"),("VOLTAR","combo_start")]),
            "combo_endlag": ("Se o cara dá TP no meio, existe uma abertura: timing lento, endlag entre skills ou skill que não prende. Ajusta essa parte; não precisa trocar a build inteira por causa disso.",[("REVER COMBO","combo_review"),("ENDLAG","endlag")]),
            "combo_slow": ("Demorar pra matar pode ser combo fraco, mini-combo demais, enrolar pra iniciar, contra-atacar pouco ou correr demais. Primeiro veja se seu combo realmente fecha dano quando entra.",[("MEU COMBO DÁ DANO","combo_speed"),("ACHO ELE FRACO","combo_review")]),
            "combo_speed": ("Se o dano existe, então para de enrolar: aproveita openings, contra-ataca quando o inimigo erra e não transforma toda oportunidade em fuga. Mini-combo é ferramenta, não desculpa pra nunca finalizar.",[("GAME SENSE","gamesense_start"),("VOLTAR","combo_start")]),
            "combo_mini": ("Se o player desvia muito bem, mini-combo é mais seguro. Num full combo ele pode ken-trickar, contra-atacar e te ferrar; com mini você tira recurso, dano e volta pro neutro.",[("OBSERVATION","obs_start"),("FULL COMBO","combo_review")]),
            "combo_obs": ("Se ele ken-tricka a mesma parte sempre, recua ou encaixa uma skill que quebre Observation e continua quando fizer sentido. O importante é não repetir a mesma abertura toda luta.",[("COMO TIRAR OBS?","obs_start"),("VOLTAR","combo_start")]),
            "endlag": ("Endlag é quando você fica preso depois da própria skill/ataque. Se o inimigo sabe disso, ele pode entrar justamente nessa janela. Movimenta e escolhe melhor quando gastar skills que te deixam vulnerável.",[("GAME SENSE","gamesense_start"),("COMBO","combo_start")]),

            # Observation / bait.
            "obs_start": ("Você não consegue saber com certeza quando a Observation do outro está ativa. Vai tirando com algumas skills, click da Soul Guitar e mini-combos; ele provavelmente vai tentar desviar e gastar haki.",[("COMO BAITAR?","bait_start"),("ELE DESVIA MEU COMBO","combo_obs")]),
            "bait_start": ("Bait é quando ele tenta fazer você gastar sua entrada numa oportunidade falsa. Sinais comuns: ele recua numa distância perfeita pro seu starter, mantém a câmera em você e parece pronto pra responder assim que você avançar. Em vez de entregar tudo, testa com pressão curta e vê a reação.",[("COMO EU FAÇO UM BAIT?","bait_self"),("AVANÇO E TOMO COUNTER","gs_countered"),("VOLTAR","gamesense_start")]),
            "bait_self": ("Pra baitar sem se entregar, mostra uma abertura controlada: muda a distância ou finge recuo, mas guarda uma resposta. Se ele gastar o starter tentando aproveitar, você pune a animação/cooldown. Se ele não entrar, você simplesmente reseta a posição.",[("COMO PUNIR DEPOIS?","gs_miss_punish"),("TREINAR LEITURA","gs_read_train"),("VOLTAR","gamesense_start")]),

            # Predict / game sense / adaptação.
            "predict_start": ("Predict é prever onde o cara vai estar com base na movimentação e nos padrões. Observa pra onde ele costuma ir, como reage quando você avança e como inicia combo.",[("COMO TREINAR?","predict_train"),("PREDICT AVANÇADO","predict_advanced"),("O CARA DÁ MUITO TP","tp_enemy")]),
            "predict_train": ("Treina no próprio PvP. Repara padrões e tenta antecipar uma coisa por vez. Se ele sempre vai pro ar, dá TP + stun ou recua do mesmo jeito, na próxima você já muda sua resposta.",[("AVANÇADO","predict_advanced"),("GAME SENSE","gamesense_start")]),
            "predict_advanced": ("Um predict mais avançado é usar o knockback pra prever onde o adversário vai cair, dar TP nele e estender. Isso vem de repetir muito e assistir/recriar jogadas boas.",[("TREINO","training_start"),("VOLTAR","predict_start")]),
            "tp_enemy": ("Depende de onde ele dá TP. Se aparece atrás, já fica atento: sobe pro ar ou dá TP pra longe também. O principal é não continuar olhando pra frente como se nada tivesse acontecido.",[("TRACKING","tracking"),("GAME SENSE","gamesense_start")]),
            "gamesense_start": ("Game sense é ler a situação antes de apertar skill. Escolhe o problema que realmente acontece na luta:",[("ELE ENTRA ANTES DE EU REAGIR","gs_react"),("AVANÇO E TOMO COUNTER","gs_countered"),("NÃO PUNISHO QUANDO ELE ERRA","gs_miss_punish"),("ELE ME BAITA","bait_start"),("PERCO ELE DA CÂMERA","audio"),("QUERO LER PADRÕES","patterns")]),
            "gs_react": ("Se ele entra antes de você reagir, para de esperar a skill aparecer na tela. Repara no item que ele equipa, na direção do movimento, na distância e no jeito que ele costuma iniciar. A reação começa nesses sinais, não depois do hit.",[("COMO TREINAR ESSA LEITURA?","gs_read_train"),("E SE ELE FINGIR A ENTRADA?","bait_start"),("VOLTAR","gamesense_start")]),
            "gs_read_train": ("Treina uma coisa por vez: durante algumas lutas, esquece bounty e tenta identificar só o starter do adversário. Antes de cada entrada, pensa rápido: distância, item na mão e direção. Depois confere se sua leitura bateu. Repetindo isso, você começa a reagir antes.",[("QUERO TREINAR PUNISH","gs_punish_train"),("LER PADRÕES","patterns"),("VOLTAR","gamesense_start")]),
            "gs_countered": ("Se você avança e toma counter, provavelmente está tratando qualquer erro dele como abertura. Antes de entrar, confirma três coisas: ele gastou uma skill importante, está numa posição ruim e você consegue alcançar sem se jogar reto no próximo ataque.",[("COMO SEI SE É ABERTURA REAL?","gs_real_opening"),("COMO IDENTIFICAR BAIT?","bait_start"),("VOLTAR","gamesense_start")]),
            "gs_too_passive": ("Se você recua demais, o problema pode ser deixar abertura passar. Você não precisa virar full agressivo: quando ele erra algo importante e fica mal posicionado, entra com um punish curto e reposiciona. Isso já força respeito sem se jogar no risco.",[("TREINAR PUNISH","gs_punish_train"),("ABERTURA REAL","gs_real_opening"),("VOLTAR","gamesense_start")]),
            "gs_miss_punish": ("Quando ele erra uma skill, não olha só o cooldown. Olha onde ele terminou a animação, a distância entre vocês e se ele ainda tem uma resposta rápida. Se estiver exposto, pune; se o recuo parecer preparado, testa com pressão curta em vez de entregar seu starter.",[("TREINAR PUNISH","gs_punish_train"),("COMO IDENTIFICAR BAIT?","bait_start"),("VOLTAR","gamesense_start")]),
            "gs_real_opening": ("Uma abertura fica bem mais confiável quando três sinais aparecem juntos: ele gastou uma ferramenta importante, terminou mal posicionado e não consegue te atingir antes da sua entrada. Um erro sozinho não significa que você tem que avançar.",[("TREINAR ISSO","gs_punish_train"),("E SE FOR BAIT?","bait_start"),("VOLTAR","gamesense_start")]),
            "gs_punish_train": ("No treino, escolhe um único erro pra punir — por exemplo, quando o starter de range dele erra. Não tenta punir tudo. Espera esse erro, entra com uma sequência curta e sai. Quando isso ficar automático, adiciona outra situação.",[("COMBO CURTO / MINI-COMBO","combo_mini"),("LER PADRÕES","patterns"),("VOLTAR","gamesense_start")]),
            "gamesense_advance": ("Pra decidir avançar ou recuar, não usa uma regra fixa. Junta cooldown, posição, distância e comportamento. Se ele gastou uma ferramenta importante e terminou exposto, pressiona; se recuou já olhando pra sua entrada ou guardando resposta, não corre reto.",[("ABERTURA REAL","gs_real_opening"),("ELE ME BAITA","bait_start"),("VOLTAR","gamesense_start")]),
            "cooldown": ("Cooldown ajuda, mas sozinho não decide a jogada. O melhor punish vem quando o cooldown gasto coincide com posição ruim e distância favorável. Se só uma dessas coisas aconteceu, você pode pressionar sem comprometer seu starter.",[("TREINAR PUNISH","gs_punish_train"),("ABERTURA REAL","gs_real_opening"),("VOLTAR","gamesense_start")]),
            "patterns": ("Pra ler padrão, procura repetição: pra qual lado ele escapa, quando sobe pro ar, qual skill usa depois do dash e o que faz depois de errar. Quando você notar uma repetição, muda sua resposta só na próxima vez em vez de tentar adivinhar tudo de uma vez.",[("ELE SE ADAPTOU A MIM","adaptation"),("COMO TREINAR LEITURA?","gs_read_train"),("VOLTAR","gamesense_start")]),
            "adaptation": ("Se ele percebeu seu padrão, muda uma variável por vez: direção de entrada, altura, timing ou distância. Não precisa trocar a build nem virar outro player; o objetivo é impedir que sua próxima ação seja óbvia.",[("LER PADRÕES","patterns"),("MOVIMENTAÇÃO","movement_core"),("VOLTAR","gamesense_start")]),
            "audio": ("Se você perde o player da câmera, o áudio vira pista extra: direção, dash e algumas skills entregam onde ele está. Usa isso junto com tracking; não tenta depender só do som.",[("TREINAR TRACKING","tracking"),("MOVIMENTAÇÃO","movement_core"),("VOLTAR","gamesense_start")]),

            # Estilos e raças.
            "style_start": ("Você escolhe como quer jogar; não existe um modo automaticamente melhor. Quer ver o que cada estilo significa?",[("SIM, EXPLICA","style_explain"),("JÁ SEI, QUERO ESCOLHER RAÇA","race_start")]),
            "style_explain": ("PASSIVO espera mais a oportunidade. AGRESSIVO pressiona e procura entrada. PASSIVO-AGRESSIVO alterna pressão e recuo. COUNTER espera erro/exposição pra responder. Player experiente consegue variar, mas a preferência é sua.",[("SOU PASSIVO","style_passive"),("SOU AGRESSIVO","style_aggressive"),("SOU PASSIVO-AGRESSIVO","style_mix"),("SOU COUNTER","style_counter")]),
            "style_passive": ("Fechou. Pra raça, um estilo passivo combina bem com Fish e também pode usar Angel; eu priorizaria Fish pela defesa do V3.",[("VER RAÇAS","race_passive"),("VOLTAR","style_start")]),
            "style_aggressive": ("Pra agressivo eu olharia primeiro Ghoul ou Cyborg. Human depende muito de estar com pouca vida; Draco também pode encaixar, mas Ghoul/Cyborg são escolhas mais constantes.",[("VER RAÇAS","race_aggressive"),("VOLTAR","style_start")]),
            "style_mix": ("Passivo-agressivo combina bem com Mink ou Ghoul: velocidade pra alternar distância ou versatilidade/cooldown pra pressionar quando aparece a chance.",[("VER RAÇAS","race_mix"),("VOLTAR","style_start")]),
            "style_counter": ("Counter combina bem com Draco, Cyborg ou Fish. A ideia é sobreviver/segurar pressão e responder quando o inimigo entrega a abertura.",[("VER RAÇAS","race_counter"),("VOLTAR","style_start")]),
            "race_start": ("Pra recomendar raça eu prefiro saber seu estilo, não decorar build por build. Qual combina mais com você?",[("PASSIVO","race_passive"),("AGRESSIVO","race_aggressive"),("PASSIVO-AGRESSIVO","race_mix"),("COUNTER","race_counter")]),
            "race_passive": ("PASSIVO: Fish é minha principal escolha pela defesa do V3. Angel também entra como opção de sustain/recuperação.",[("QUANDO USAR V4?","v4_use"),("VOLTAR","race_start")]),
            "race_aggressive": ("AGRESSIVO: Ghoul ou Cyborg. Ghoul é versátil, recupera vida e o V3 ajuda nos cooldowns; Cyborg causa dano de lightning e quebra Observation. Human é mais situacional com pouca vida.",[("QUANDO USAR V4?","v4_use"),("VOLTAR","race_start")]),
            "race_mix": ("PASSIVO-AGRESSIVO: Mink ou Ghoul. Mink é velocidade; Ghoul é mais versátil e ajuda a manter pressão/recuperação.",[("QUANDO USAR V4?","v4_use"),("VOLTAR","race_start")]),
            "race_counter": ("COUNTER: Draco, Cyborg ou Fish. Draco pode cancelar ataque com V3 bem usado; Cyborg pune com lightning/Observation; Fish aguenta muita pressão.",[("QUANDO USAR V4?","v4_use"),("VOLTAR","race_start")]),
            "v4_use": ("Não recomendo ativar V4 sem motivo. Bons motivos: 2v1+, cheater/xitado ou alguém abusando muito de spam. Ativar só porque não quer morrer pode funcionar, mas você provavelmente vai ouvir que apelou kkkkk.",[("2V1+","multi_start"),("VOLTAR","race_start")]),

            # 2v1+.
            "multi_start": ("Qual situação?",[("2V1","multi_2"),("3V1 / 4V1","multi_34"),("TÔ COMBANDO E O OUTRO CHEGOU","multi_interrupt")]),
            "multi_2": ("No 2v1, separa os dois com movement: muda posição, ground/air e faz um chegar primeiro. Pode matar o mais fraco antes porque é mais rápido; se sua skill tem range alto, dá até pra pegar os dois juntos.",[("COMO SEPARAR MELHOR?","multi_separate"),("QUEM MATO PRIMEIRO?","multi_target"),("V4?","v4_use")]),
            "multi_separate": ("Não fica parado tentando tankar os dois. Movimenta, troca altura e direção até um deles se adiantar. Aí você cria uma janela de 1v1 temporária e comba rápido antes do segundo alcançar.",[("O SEGUNDO CHEGOU","multi_interrupt"),("VOLTAR","multi_start")]),
            "multi_target": ("Matar o mais fraco costuma ser mais rápido porque ele não acompanha seu movement. Também dá pra esperar quem chega primeiro. O habilidoso exige mais tempo, então não fica preso nele enquanto o outro bate de graça.",[("VOLTAR","multi_2")]),
            "multi_interrupt": ("Se o segundo chega enquanto você comba, eu abandonaria o combo e recuaria um pouco, ou daria uma mini-combo no que chegou e reposicionaria. Não fica preso no hitkill enquanto toma skill por trás.",[("MINI-COMBO","combo_mini"),("VOLTAR","multi_start")]),
            "multi_34": ("3v1/4v1 exige ainda mais movement e game sense. Separa sempre que possível, não fica no mesmo plano/altura e foca em ativar V4 quando houver motivo pra ter chance real.",[("SEPARAR","multi_separate"),("V4","v4_use")]),

            # Treino / evolução / tilt / build.
            "training_start": ("O que você quer organizar no treino?",[("TREINAR UMA MECÂNICA","train_mechanic"),("TENHO SÓ 30 MINUTOS","train_30"),("COM QUEM TREINAR?","train_opponents"),("NÃO QUERO PERDER BOUNTY","train_no_bounty"),("TÔ TILTADO","tilt"),("TROCAR DE BUILD?","build_switch")]),
            "train_mechanic": ("Fica um dia inteiro ou até mais numa mecânica se precisar. Depende do quanto você aprende rápido; melhor corrigir uma coisa de verdade do que trocar de foco a cada dez minutos.",[("MOVEMENT","movement_start"),("MIRA","aim_start"),("PREDICT","predict_start")]),
            "train_30": ("Com pouco tempo, eu faria um foco por dia: passa boa parte dos 30 minutos numa coisa só e só troca quando ela começar a ficar natural. Não tenta treinar tudo ao mesmo tempo.",[("ESCOLHER MECÂNICA","train_mechanic"),("VOLTAR","training_start")]),
            "train_opponents": ("Treina com gente do seu nível ou um pouco melhor. Quando já está num nível alto/20M+, procura player realmente bom e variado; só lutar contra gente fraca para de ensinar.",[("NÃO QUERO PERDER BOUNTY","train_no_bounty"),("VOLTAR","training_start")]),
            "train_no_bounty": ("Usa servidor privado com PvP amigável ou o Coliseu, entrando nos quadrados dos lados pra virar friendly PvP. Assim dá pra treinar sem transformar bounty em preocupação.",[("TREINO DE MECÂNICA","train_mechanic"),("VOLTAR","training_start")]),
            "tilt": ("Para um pouco, reveja o que errou e tenta de novo. Se falhar novamente, não desiste: você não melhora do dia pra noite. O erro é continuar tiltado no automático ou trocar de build toda derrota.",[("REVER ERRO","diag_start"),("VOLTAR","training_start")]),
            "build_switch": ("Pode usar a build que quiser, só não escolhe item que não encaixa nada com nada. Trocar toda hora atrasa porque você nunca domina combo, variações e jeito de jogar. E copiar build de 30M não copia a habilidade dele.",[("MINHA BUILD É RUIM?","build_bad"),("VOLTAR","training_start")]),
            "build_bad": ("A build vira problema quando os itens realmente não encaixam: fruta ruim pro plano, estilo que não conversa com ela, gun random e espada sem função. Fora isso, primeiro olha execução e game sense.",[("COMBO","combo_start"),("ESTILO","style_start")]),
        }

    def _zkdialog_go(self, target):
        # Ações diretas não geram texto falso na conversa.
        if target.startswith("url:"):
            self._zkai_action(target); return
        if target.startswith("page:"):
            self._zkai_action(target); return
        if target in ("tutorial","apply"):
            self._zkai_action(target); return

        # Assistente do app: respostas fechadas e calculadas do estado real.
        if target.startswith("app:"):
            kind=target.split(":",1)[1]
            states=getattr(self,"module_states",{})
            roblox_dir=getattr(self,"pasta_roblox_salva","") or ""
            roblox_running=bool(self._roblox_pids())
            font_name=os.path.basename(getattr(self,"game_font_source","") or "") or "padrão"
            cursor_name=getattr(self,"cursor_pack","Roblox Padrão") or "Roblox Padrão"
            res_name=getattr(self,"resolucao_jogo","1280x720") or "1280x720"
            watchdog=bool(getattr(self,"config_watchdog_enabled",False))
            fps_target=getattr(self,"micro_fps_target","144")
            if kind=="home":
                msg="Escolhe uma das 6 áreas acima ou pesquisa o que você quer fazer. Se você não sabe onde está o problema, usa DIAGNÓSTICO RÁPIDO."
                opts=[("DIAGNÓSTICO RÁPIDO","app:status"),("APLICAR / ROBLOX","app:cat_apply"),("FPS / PING","app:cat_performance"),("VISUAL / ÁUDIO","app:cat_visual")]
            elif kind=="cat_apply":
                msg="Aplicação e Roblox: aqui ficam as causas mais comuns de uma configuração não entrar no jogo."
                opts=[("POR QUE NÃO APLICA?","app:not_apply"),("VINCULAR ROBLOX","app:link_roblox"),("PASTA / STATUS ROBLOX","app:roblox"),("APLICAR AGORA","app:apply"),("REINICIAR ROBLOX?","app:restart"),("VOLTAR","app:home")]
            elif kind=="cat_performance":
                msg="Desempenho reúne FPS, gráficos, ping/latência, resolução e o painel de diagnóstico."
                opts=[("FPS & GRÁFICOS","app:fps"),("PING & LATÊNCIA","app:ping"),("RESOLUÇÃO","app:resolution"),("CENTRAL DE DESEMPENHO","app:maintenance"),("VOLTAR","app:home")]
            elif kind=="cat_visual":
                msg="Personalização do ZKStrap e do Roblox: tema, cursor, fonte e áudio."
                opts=[("TEMAS","app:themes"),("CURSOR","app:cursor"),("FONTES","app:fonts"),("ÁUDIO / SONS","app:audio"),("VOLTAR","app:home")]
            elif kind=="cat_tools":
                msg="Ferramentas de Blox Fruits: Build Roulette, Combo Planner, Creator Challenges e mídia."
                opts=[("BUILD ROULETTE","app:roulette"),("COMBO PLANNER","app:combo"),("CREATOR CHALLENGES","app:creator"),("SPOTIFY / MÍDIA","app:spotify"),("VOLTAR","app:home")]
            elif kind=="cat_recovery":
                msg="Se algo quebrou ou ficou estranho, comece pelos logs. Depois use recuperação/backup quando precisar desfazer algo."
                opts=[("LOGS / ERROS","app:logs"),("RECUPERAÇÃO","app:recovery"),("BACKUP / RESTAURAR","app:backup"),("DESEMPENHO","app:maintenance"),("VOLTAR","app:home")]
            elif kind=="cat_info":
                msg="Informações do app: estado atual, tutorial e atualizações."
                opts=[("CONFIG ATUAL","app:config_full"),("TUTORIAL","app:tutorial"),("ATUALIZAÇÕES","app:updates"),("VOLTAR","app:home")]
            elif kind=="status":
                msg=self._zkdialog_app_status(); opts=[("VER CONFIG COMPLETA","app:config_full"),("ABRIR FPS & GRÁFICOS","page:fps"),("APLICAR AGORA","app:apply"),("VOLTAR","app:home")]
            elif kind=="config_full":
                labels={"performance_boost":"FPS/gráficos","gray_sky":"céu cinza","fps_unlock":"FPS unlock","ping_boost":"rede/ping","telemetry_off":"telemetria off","micro_opt":"micro-otimização","draco_aura":"Draco V4"}
                ativos=[labels.get(k,k) for k,v in states.items() if v]
                msg=(f"Config atual: tema {self.tema_atual}; alvo {fps_target} FPS; resolução {res_name}; cursor {cursor_name}; fonte {font_name}; watchdog {'ligado' if watchdog else 'desligado'}; Roblox {'aberto' if roblox_running else 'fechado'}; pasta {'detectada' if roblox_dir else 'não detectada'}. Módulos ativos: "+(", ".join(ativos) if ativos else "nenhum" )+".")
                opts=[("FPS & GRÁFICOS","page:fps"),("RESOLUÇÃO","page:resolution"),("CURSOR","page:cursor"),("FONTES","page:fonts"),("TEMAS","page:theme"),("VOLTAR","app:home")]
            elif kind=="not_apply":
                reasons=[]
                if not roblox_dir: reasons.append("o diretório do Roblox ainda não está vinculado")
                elif not os.path.isdir(roblox_dir): reasons.append("a pasta salva do Roblox não existe mais")
                if roblox_running: reasons.append("o Roblox está aberto; alguns assets/configs só aparecem após fechar e abrir de novo")
                if not any(bool(v) for v in states.values()): reasons.append("nenhum módulo principal está marcado")
                if not reasons: reasons.append("o app parece vinculado; reaplique e confira o log inferior para ver se alguma etapa foi ignorada")
                msg="Se não está aplicando, eu verificaria nesta ordem: " + "; ".join(reasons) + "."
                opts=[("VINCULAR ROBLOX","app:link_roblox"),("APLICAR AGORA","app:apply"),("ABRIR LOG","app:logs"),("FPS & GRÁFICOS","page:fps"),("VOLTAR","app:home")]
            elif kind=="fps":
                msg=f"FPS & Gráficos: alvo atual {fps_target} FPS. Modo FPS/gráficos {'ativo' if states.get('performance_boost') else 'desativado'}; FPS unlock {'ativo' if states.get('fps_unlock') else 'desativado'}; micro-otimização {'ativa' if states.get('micro_opt') else 'desativada'}; céu cinza {'ativo' if states.get('gray_sky') else 'desativado'}."
                opts=[("ABRIR FPS & GRÁFICOS","page:fps"),("APLICAR CONFIG","app:apply"),("VER CONFIG ATUAL","app:config_full"),("VOLTAR","app:home")]
            elif kind=="ping":
                msg=f"Ping & Latência tem teste de rota Roblox, jitter, limpeza segura de DNS e atalhos para reduzir gargalos locais. O pack antigo de FastFlags está {'ativo' if states.get('ping_boost') else 'desativado'}, mas pode ser ignorado pelo Roblox atual. Distância e rota do provedor ainda são os principais limites do ping real."
                opts=[("ABRIR PING & LATÊNCIA","page:ping"),("APLICAR CONFIG","app:apply"),("VOLTAR","app:home")]
            elif kind=="roblox":
                msg=f"Roblox {'está aberto' if roblox_running else 'não está aberto agora'}. Pasta detectada: {roblox_dir or 'não detectada'}. Watchdog: {'ligado' if watchdog else 'desligado'}."
                opts=[("VINCULAR / LOCALIZAR","app:link_roblox"),("IR PARA INÍCIO","page:home"),("VOLTAR","app:home")]
            elif kind=="link_roblox":
                msg="Para o ZKStrap aplicar configs, ele precisa saber qual version-* do Roblox é a instalação atual. Use VINCULAR ROBLOX no topo/início e escolha ou deixe o app detectar a pasta correta. Depois aplique novamente."
                opts=[("IR PARA INÍCIO","page:home"),("APLICAR DEPOIS","app:apply_help"),("VOLTAR","app:home")]
            elif kind=="apply_help":
                msg="Aplicar configurações grava as opções selecionadas no ClientSettings e reaplica assets quando necessário. Se cursor, fonte ou resolução não aparecerem, feche completamente o Roblox e abra de novo após aplicar."
                opts=[("APLICAR AGORA","app:apply"),("POR QUE NÃO APLICA?","app:not_apply"),("REINICIAR ROBLOX?","app:restart"),("VOLTAR","app:home")]
            elif kind=="resolution":
                msg=f"Resolução selecionada agora: {res_name}. Abra RESOLUÇÃO, escolha um preset ou personalizada e use APLICAR NO ROBLOX. Se o jogo já estiver aberto, pode ser necessário reiniciar o cliente."
                opts=[("ABRIR RESOLUÇÃO","page:resolution"),("VOLTAR","app:home")]
            elif kind=="cursor":
                msg=f"Cursor atual: {cursor_name}. Para trocar: abra CURSOR, escolha um pack ou importe PNG/pack, ajuste o tamanho e aplique. O original fica protegido por backup para restauração."
                opts=[("ABRIR CURSOR","page:cursor"),("RESTAURAR?","app:backup"),("VOLTAR","app:home")]
            elif kind=="fonts":
                msg=f"Fonte atual: {font_name}. Para usar outra: abra FONTES, escolha um .TTF/.OTF e clique APLICAR NO JOGO. Os arquivos originais são preservados em backup."
                opts=[("ABRIR FONTES","page:fonts"),("RESTAURAR?","app:backup"),("VOLTAR","app:home")]
            elif kind=="themes":
                msg=f"Tema atual: {self.tema_atual}. Os temas mudam apenas a interface do ZKStrap; não alteram gráficos do Roblox. Abra PERSONALIZAR para trocar atmosfera e cores."
                opts=[("ABRIR TEMAS","page:theme"),("VOLTAR","app:home")]
            elif kind=="combo":
                msg="Combo Planner salva builds e sequências localmente para consulta. Ele não executa macro nem automatiza o jogo."
                opts=[("ABRIR COMBO PLANNER","page:combo"),("VOLTAR","app:home")]
            elif kind=="roulette":
                msg="Build Roulette sorteia Fighting Style + Fruit + Sword + Gun usando os catálogos locais. Você pode ajustar o inventário, favoritar, salvar no Planner e mandar a build direto para os desafios."
                opts=[("ABRIR BUILD ROULETTE","page:roulette"),("CREATOR CHALLENGES","page:creator"),("COMBO PLANNER","page:combo"),("VOLTAR","app:cat_tools")]
            elif kind=="creator":
                msg=f"Creator Challenges: {len(getattr(self,'creator_challenges',[]))} ativo(s), {int(getattr(self,'creator_total_completed',0))} concluído(s) no total. Ativos somem ao fechar o app; concluídos ficam no histórico. SECRET pode aparecer raramente."
                opts=[("ABRIR CREATOR","page:creator"),("BUILD ROULETTE","page:roulette"),("TEMAS SECRETOS","page:theme"),("VOLTAR","app:cat_tools")]
            elif kind=="spotify":
                msg="Spotify/Mídia usa as sessões de mídia do Windows. Desktop tem controle mais confiável; navegador só é controlado quando o ZKStrap consegue identificar a sessão sem arriscar pausar YouTube."
                opts=[("ABRIR SPOTIFY / MÍDIA","page:spotify"),("ÁUDIO DO ZKSTRAP","page:audio"),("VOLTAR","app:cat_tools")]
            elif kind=="watchdog":
                msg=f"Watchdog está {'ligado' if watchdog else 'desligado'}. Quando ligado, ele verifica periodicamente se a pasta/configuração do Roblox mudou e mantém a sincronização."
                opts=[("IR PARA INÍCIO","page:home"),("VOLTAR","app:home")]
            elif kind=="audio":
                text="Na aba ÁUDIO você escolhe entre 10 packs locais e controla música ambiente e SFX separadamente. Scroll, slider, navegação, temas e Combo Planner têm sons próprios."
                opts=[("ABRIR ÁUDIO","page:audio"),("PERSONALIZAR","page:theme"),("VOLTAR","app:home")]
            elif kind=="maintenance":
                msg="CENTRAL DE DESEMPENHO reúne diagnóstico, Modo de Jogo, preferência de GPU, plano de energia, prioridade do Roblox e ferramentas de foco da sessão. Limpeza e rollback ficam separados em RECUPERAÇÃO."
                opts=[("ABRIR DESEMPENHO","page:maintenance"),("RECUPERAÇÃO","page:recovery"),("VOLTAR","app:home")]
            elif kind=="recovery":
                msg="RECUPERAÇÃO é a área para limpar logs/cache temporário e desfazer alterações: cursor, fontes, plano de energia e reset completo do ZKStrap."
                opts=[("ABRIR RECUPERAÇÃO","page:recovery"),("CURSOR","page:cursor"),("FONTES","page:fonts"),("VOLTAR","app:home")]
            elif kind=="backup":
                msg="Cursor e fontes mantêm backups dos arquivos originais. A página RECUPERAÇÃO concentra limpeza e rollback geral, sem misturar isso com boost de desempenho."
                opts=[("CURSOR","page:cursor"),("FONTES","page:fonts"),("RECUPERAÇÃO","page:recovery"),("VOLTAR","app:home")]
            elif kind=="logs":
                msg="Use ABRIR LOG no rodapé para ver o que o ZKStrap detectou/aplicou. Se algo falhar, procure linhas com [!], [-] ou mensagens sobre diretório/ClientSettings e use isso para identificar a etapa que falhou."
                opts=[("RECUPERAÇÃO","page:recovery"),("DESEMPENHO","page:maintenance"),("POR QUE NÃO APLICA?","app:not_apply"),("VOLTAR","app:home")]
            elif kind=="tutorial":
                msg="O tutorial mostra as áreas principais sem cobrir os controles. Você pode reabrir o guia pelo botão ? TUTORIAL na lateral."
                opts=[("ABRIR TUTORIAL","tutorial"),("VOLTAR","app:home")]
            elif kind=="updates":
                msg="A página ATUALIZAÇÕES mostra o changelog da build atual e o que mudou em cada versão do ZKStrap."
                opts=[("ABRIR ATUALIZAÇÕES","page:updates"),("VOLTAR","app:home")]
            elif kind=="bloxstrap":
                msg="Quando o Bloxstrap é detectado, o ZKStrap também tenta espelhar cursor/fonte nas pastas usadas por ele para que os assets sobrevivam melhor às atualizações do Roblox."
                opts=[("CURSOR","page:cursor"),("FONTES","page:fonts"),("VOLTAR","app:home")]
            elif kind=="restart":
                msg=f"Roblox {'está aberto' if roblox_running else 'já está fechado'}. Para assets como cursor/fonte e algumas mudanças visuais, feche todas as instâncias do Roblox e abra novamente depois de aplicar."
                opts=[("APLICAR ANTES","app:apply"),("VOLTAR","app:home")]
            elif kind=="visual":
                msg=f"Tema atual: {self.tema_atual}. Cursor: {cursor_name}. Fonte do jogo: {font_name}."
                opts=[("ABRIR TEMAS","page:theme"),("ABRIR CURSOR","page:cursor"),("ABRIR FONTES","page:fonts"),("VOLTAR","app:home")]
            elif kind=="navigation":
                msg="Escolha uma área e eu abro direto."
                opts=[("FPS & GRÁFICOS","page:fps"),("PING & LATÊNCIA","page:ping"),("RESOLUÇÃO","page:resolution"),("CURSOR","page:cursor"),("FONTES","page:fonts"),("DESEMPENHO","page:maintenance"),("RECUPERAÇÃO","page:recovery")]
            elif kind=="apply":
                self.aplicar_configuracoes(); msg="A ação normal de aplicar configurações foi executada. Confira o log inferior e reinicie o Roblox se a mudança precisar recarregar assets."; opts=[("VER STATUS","app:status"),("ABRIR LOG","app:logs"),("VOLTAR","app:home")]
            else:
                msg="Escolha uma dúvida do Assistente ZKStrap."; opts=[("VOLTAR","app:home")]
            self._zkai_add_bubble("assistant",msg); self._zkdialog_set_options(opts); return

        nodes=self._zkdialog_nodes()
        data=nodes.get(target)
        if data is None:
            self._zkai_add_bubble("assistant","Esse caminho ainda não existe nesta versão. Volta pros tópicos e escolhe outra área.")
            self._zkdialog_set_options([("VOLTAR AO INÍCIO","pvp_home")]); return
        msg,opts=data
        self.zkai_dialog_node=target
        self._zkai_add_bubble("assistant",msg)
        if target=="greet_finish":
            self.zkai_greeting_done=True
            self._zkdialog_render_topics()
        self._zkdialog_set_options(opts)

    def show_page(self, key, animate=True):
        """Troca de página + estado sincronizado na navegação principal."""
        pages=getattr(self,"pages",{})
        if key not in pages: return
        if key in ("combo","roulette"):
            try:self.after(250,self._combo_warm_cache_safe)
            except Exception:pass
        if key=="theme":
            try:
                builder=getattr(self,"_build_theme_gallery_once",None)
                if callable(builder): builder()
            except Exception as exc:
                try: self.log_output(f"[!] Galeria de temas: {exc}")
                except Exception: pass
        t=TEMAS[self.tema_atual]
        for k,b in getattr(self,"nav_buttons",{}).items():
            try:
                b.configure(fg_color=t["card_active"] if k==key else "transparent",
                            text_color=t["accent"] if k==key else t["text"],
                            border_width=1,
                            border_color=t["accent"] if k==key else self._mix_hex(t.get("sidebar",t["card"]),t.get("border",t["accent"]),.25))
            except Exception: pass
        for k,b in getattr(self,"nav_rail_buttons",{}).items():
            try:
                b.configure(fg_color=t["icon_bg"] if k==key else "transparent",
                            border_width=1 if k==key else 0,border_color=t["accent"])
            except Exception: pass

        job=getattr(self,"_page_anim_job",None)
        if job is not None:
            try: self.after_cancel(job)
            except Exception: pass
            self._page_anim_job=None
            pending=getattr(self,"_pending_page",None)
            if pending in pages:
                try:
                    for k,p in pages.items():
                        if k!=pending: p.place_forget()
                    pages[pending].place(relx=0,rely=0,relwidth=1,relheight=1); pages[pending].lift()
                except Exception: pass
                self._visible_page=pending
            self._pending_page=None

        old_key=getattr(self,"_visible_page",None); old=pages.get(old_key) if old_key else None; new=pages[key]
        if old_key==key:
            try: new.place(relx=0,rely=0,relwidth=1,relheight=1); new.lift()
            except Exception: pass
            self.current_page_key=key; return
        if not animate or old is None:
            try:
                if old is not None: old.place_forget()
                new.place(relx=0,rely=0,relwidth=1,relheight=1); new.lift()
            except Exception: pass
            self._visible_page=key; self._pending_page=None; self.current_page_key=key
            try: self.salvar_config_app()
            except Exception: pass
            return

        self._pending_page=key
        try:
            old.place(relx=0,rely=0,relwidth=1,relheight=1)
            new.place(relx=.012,rely=0,relwidth=1,relheight=1); new.lift()
        except Exception:
            try: old.place_forget(); new.place(relx=0,rely=0,relwidth=1,relheight=1); new.lift()
            except Exception: pass
            self._visible_page=key; self._pending_page=None; self.current_page_key=key; return
        steps=14
        def finish():
            try: old.place_forget(); new.place(relx=0,rely=0,relwidth=1,relheight=1); new.lift()
            except Exception: pass
            self._visible_page=key; self._pending_page=None; self._page_anim_job=None; self.current_page_key=key
            try: self.salvar_config_app()
            except Exception: pass
        def tick(i=0):
            if i>=steps: finish(); return
            p=i/max(1,steps-1); e=p*p*(3-2*p)
            try:
                new.place_configure(relx=.012*(1-e)); old.place_configure(relx=-.002*e)
            except Exception:
                finish(); return
            self._page_anim_job=self.after(10,lambda:tick(i+1))
        tick(0)

    def reconstruir_interface(self):
        try: self._fechar_busca_universal()
        except Exception: pass
        try: self._tutorial_close(mark_complete=False, voltar_home=False)
        except Exception: pass
        try:
            self.main_container.destroy()
        except Exception:
            pass
        self.criar_interface()
        self.restaurar_estado_interface()

    def _set_sug_tipo_ui(self, tipo):
        self.sug_tipo = tipo
        t = TEMAS[self.tema_atual]
        try:
            is_bug = "bug" in str(tipo).lower()
            self.btn_sug_idea.configure(fg_color=t["card_active"] if is_bug else t["accent"], text_color=t["text"] if is_bug else "#050505")
            self.btn_sug_bug.configure(fg_color=t["accent"] if is_bug else t["card_active"], text_color="#050505" if is_bug else t["text"])
        except Exception:
            pass

    def _update_sug_counter(self, event=None):
        try:
            n=len(self.txt_sug.get("0.0","end").rstrip("\n"))
            self.lbl_sug_counter.configure(text=(f"{n} caracteres" if self.idioma=="pt" else f"{n} characters"))
        except Exception:
            pass

    def enviar_sugestao(self):
        msg = self.txt_sug.get("0.0", "end").strip()
        title = ""
        try:
            title = self.entry_sug_title.get().strip()
        except Exception:
            pass

        if len(msg) < 5:
            messagebox.showwarning(
                self.tr[self.idioma]['msg_warning'],
                self.tr[self.idioma]['short_message_warning']
            )
            return

        tipo = getattr(self, "sug_tipo", self.tr[self.idioma]['sug_type_vals'][0])
        WEBHOOK_URL = 'https://discord.com/api/webhooks/1521648703537021060/ef_0NSR2DhCkivFbf0lMfX02PnyytKLvOE4pnT5KsFe0YNfF0jUTla7MJJmaiXqgjiXi'

        # Payload direto para o webhook do Discord, como nas builds antigas.
        cabecalho = f"**{tipo} ZKSTRAP**"
        if title:
            cabecalho += f"\n**Título:** {title}"
        diag = ""
        try:
            if getattr(self, "switch_feedback_diag", None) is not None and self.switch_feedback_diag.get():
                snap=self._snapshot_sistema()
                diag=(f"\n`ZKStrap {APP_VERSION} | {self.tema_atual} | CPU {snap['cpu']:.0f}% | RAM {snap['ram_pct']:.0f}% | Roblox {'ON' if snap['roblox_count'] else 'OFF'}`")
        except Exception:
            pass
        payload = {
            "content": f"{cabecalho}\n```{msg}```{diag}"
        }

        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=8)
            if response.status_code in (200, 204):
                self._legacy_info(
                    self.tr[self.idioma]['msg_ok'],
                    self.tr[self.idioma]['sug_sent']
                )
                self.txt_sug.delete("0.0", "end")
                try:
                    self.entry_sug_title.delete(0, "end")
                except Exception:
                    pass
                self._update_sug_counter()
                self.log_output(f"[*] {tipo} enviado via Discord webhook.")
            else:
                messagebox.showerror(
                    self.tr[self.idioma]['msg_error'],
                    f"{self.tr[self.idioma]['webhook_fail']} ({response.status_code})"
                )
                self.log_output(f"[-] Falha webhook: {response.status_code}")
        except Exception as e:
            messagebox.showerror(
                self.tr[self.idioma]['msg_error'],
                f"{self.tr[self.idioma]['webhook_fail']}\n{e}"
            )
            self.log_output(f"[-] Exceção webhook: {e}")

    def _snapshot_sistema(self):
        """Snapshot leve e honesto: CPU/RAM/processos/Roblox. Não tenta estimar FPS."""
        try:
            cpu=float(psutil.cpu_percent(interval=0.18))
        except Exception: cpu=0.0
        try:
            vm=psutil.virtual_memory(); ram_pct=float(vm.percent); ram_free=float(vm.available)/(1024**3)
        except Exception: ram_pct=0.0; ram_free=0.0
        proc_count=0; roblox_count=0; roblox_mem=0.0
        try:
            for proc in psutil.process_iter(['name','memory_info']):
                proc_count += 1
                try:
                    if (proc.info.get('name') or '').lower() == 'robloxplayerbeta.exe':
                        roblox_count += 1
                        mi=proc.info.get('memory_info')
                        if mi: roblox_mem += float(mi.rss)/(1024**2)
                except Exception: pass
        except Exception: pass
        return {"time":datetime.now().isoformat(timespec="seconds"),"cpu":cpu,"ram_pct":ram_pct,"ram_free_gb":ram_free,"processes":proc_count,"roblox_count":roblox_count,"roblox_mem_mb":roblox_mem}

    def refresh_dashboard(self):
        try:
            labels=getattr(self,'dashboard_labels',{})
            if not labels: return
            active=sum(1 for k in MAIN_MODULE_KEYS if self.module_states.get(k,False))
            client_ok=bool(self.pasta_roblox_salva and os.path.isdir(self.pasta_roblox_salva))
            labels['client'].configure(text="ONLINE" if client_ok else "NÃO LOCALIZADO", text_color=TEMAS[self.tema_atual]['accent'] if client_ok else "#FF6B6B")
            labels['modules'].configure(text=f"{active} ATIVAS")
            assets=[]
            if self.cursor_pack != "Roblox Padrão": assets.append("CURSOR")
            if self.game_font_source: assets.append("FONTE")
            labels['assets'].configure(text=" + ".join(assets) if assets else "PADRÃO")
            labels['restart'].configure(text="SIM" if self._roblox_esta_aberto() and active else "NÃO")
            if getattr(self,'dashboard_path_label',None): self.dashboard_path_label.configure(text=self.pasta_roblox_salva or "ClientSettings ainda não vinculado")
        except Exception:
            pass

    def executar_benchmark(self):
        pt=self.idioma=='pt'; t=TEMAS[self.tema_atual]
        try:
            if getattr(self,'lbl_benchmark',None): self.lbl_benchmark.configure(text="Medindo..." if pt else "Measuring...",text_color=t['accent'])
        except Exception: pass
        def worker():
            snap=self._snapshot_sistema(); before=self.last_benchmark.get('current') if isinstance(self.last_benchmark,dict) else None
            self.last_benchmark={"previous":before or {},"current":snap}; self.salvar_config_app()
            def finish():
                prev=self.last_benchmark.get('previous') or {}
                lines=[f"CPU: {snap['cpu']:.0f}%",f"RAM: {snap['ram_pct']:.0f}%  •  livre {snap['ram_free_gb']:.1f} GB",f"Processos: {snap['processes']}",f"Roblox: {'ON' if snap['roblox_count'] else 'OFF'}  •  {snap['roblox_mem_mb']:.0f} MB"]
                if prev:
                    lines.append(f"Δ CPU: {snap['cpu']-float(prev.get('cpu',snap['cpu'])):+.0f} pp  •  Δ RAM: {snap['ram_pct']-float(prev.get('ram_pct',snap['ram_pct'])):+.0f} pp")
                txt="\n".join(lines)
                try:
                    if getattr(self,'lbl_benchmark',None): self.lbl_benchmark.configure(text=txt,text_color=t.get('muted','gray'))
                except Exception: pass
                self.log_output("[BENCH] "+" | ".join(lines[:4]))
            self.after(0,finish)
        threading.Thread(target=worker,daemon=True).start()

    def _flags_preview(self):
        flags={}
        for key,data in FLAG_MODULES.items():
            if bool(self.module_states.get(key,False)):
                flags.update(self._flags_do_modulo(key,data))
        flags.update(self.obter_flags_avancadas())
        return self._corrigir_tipos_flags(flags)

    def mostrar_comparador_config(self):
        pt=self.idioma=='pt'; t=TEMAS[self.tema_atual]; st=self._theme_style()
        flags=self._flags_preview(); active=[]
        for key in MAIN_MODULE_KEYS:
            if self.module_states.get(key,False): active.append(FLAG_MODULES[key]['pt' if pt else 'en'])
        win=ctk.CTkToplevel(self); win.title("ZKStrap // Comparador"); win.geometry("760x610"); win.minsize(660,520); win.configure(fg_color=t['bg']); win.transient(self)
        box=ctk.CTkFrame(win,fg_color=t['panel'],corner_radius=st['radius'],border_width=1,border_color=t['border']); box.pack(fill='both',expand=True,padx=18,pady=18)
        ctk.CTkLabel(box,text="CONFIGURAÇÃO ATUAL  →  CONFIGURAÇÃO A APLICAR" if pt else "CURRENT CONFIG  →  CONFIG TO APPLY",text_color=t['text'],font=ctk.CTkFont(size=18,weight='bold')).pack(anchor='w',padx=18,pady=(16,4))
        summary=(f"Módulos ativos: {len(active)}  •  Flags resultantes: {len(flags)}\nCéu cinza: {'ON' if self.module_states.get('gray_sky') else 'OFF'}  •  Alvo FPS: {self.micro_fps_target}" if pt else f"Active modules: {len(active)}  •  Resulting flags: {len(flags)}\nGray sky: {'ON' if self.module_states.get('gray_sky') else 'OFF'}  •  FPS target: {self.micro_fps_target}")
        ctk.CTkLabel(box,text=summary,text_color=t['accent'],justify='left',anchor='w',font=ctk.CTkFont(family='Consolas',size=10)).pack(fill='x',padx=18,pady=(2,10))
        txt=ctk.CTkTextbox(box,fg_color=t['card'],text_color=t['text'],border_width=1,border_color=t['card_active'],font=ctk.CTkFont(family='Consolas',size=9)); txt.pack(fill='both',expand=True,padx=18,pady=(0,10))
        lines=[]
        lines.append("[MÓDULOS]" if pt else "[MODULES]")
        lines.extend("  ✓ "+x for x in active); lines.append("")
        lines.append("[FLAGS GERENCIADAS]" if pt else "[MANAGED FLAGS]")
        for k in sorted(flags): lines.append(f"  {k} = {flags[k]!r}")
        txt.insert('0.0','\n'.join(lines)); txt.configure(state='disabled')
        ctk.CTkButton(box,text="APLICAR AGORA" if pt else "APPLY NOW",command=lambda:(win.destroy(),self.aplicar_configuracoes()),fg_color=t['accent'],hover_color=t['hover'],text_color='#050505',height=42).pack(fill='x',padx=18,pady=(0,16))

    def aplicar_configuracoes(self):
        self._play_ui_sound("apply",.0)
        before=self._snapshot_sistema()
        ok=self._salvar_flags_compiladas(mostrar_popup=False,usar_editor=False)
        after=self._snapshot_sistema()
        active=sum(1 for k in MAIN_MODULE_KEYS if self.module_states.get(k,False))
        flags=len(self._flags_preview())
        restart=bool(self._roblox_esta_aberto())
        self.last_apply_summary={"ok":bool(ok),"active":active,"flags":flags,"restart":restart,"time":datetime.now().isoformat(timespec='seconds')}
        if ok and flags>0:self._unlock_secret_theme("Flagborn","uma configuração com flags foi aplicada")
        self.salvar_config_app(); self.refresh_dashboard()
        self.mostrar_resultado_aplicacao(ok,active,flags,restart,before,after)
        return ok

    def otimizar_um_clique(self):
        pt=self.idioma=='pt'
        if not self.module_states.get('performance_boost',False):
            if not messagebox.askyesno("ZKStrap", "Ativar o Modo FPS / gráficos no mínimo e aplicar?\n\nO ZKStrap não fechará seus programas e não ativará automaticamente opções experimentais." if pt else "Enable FPS Mode / minimum graphics and apply?\n\nZKStrap will not close your programs or automatically enable experimental options."):
                return
            self.module_states['performance_boost']=True
            try:
                sw=self.module_switches.get('performance_boost'); sw.select()
            except Exception: pass
        ok=self.aplicar_configuracoes()
        if ok and self._roblox_esta_aberto():
            try:
                for proc in psutil.process_iter(['name']):
                    if (proc.info.get('name') or '').lower()=='robloxplayerbeta.exe' and os.name=='nt': proc.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
                self.log_output('[+] Prioridade do Roblox ajustada para ABOVE_NORMAL nesta sessão.')
            except Exception as e: self.log_output(f'[i] Prioridade não alterada: {e}')

    def mostrar_resultado_aplicacao(self,ok,active,flags,restart,before=None,after=None):
        pt=self.idioma=='pt'
        if ok:
            title="CONFIGURAÇÕES APLICADAS" if pt else "SETTINGS APPLIED"
            if restart:
                msg=(f"{active} módulos • {flags} flags gerenciadas. Reinicie o Roblox para carregar tudo." if pt else f"{active} modules • {flags} managed flags. Restart Roblox to load everything.")
            else:
                msg=(f"{active} módulos • {flags} flags gerenciadas. Configuração verificada no disco." if pt else f"{active} modules • {flags} managed flags. Configuration verified on disk.")
            self.show_toast(title,msg,kind="success",duration=4200)
        else:
            self.show_toast("FALHA AO APLICAR" if pt else "APPLY FAILED",
                            "Veja o System Log para os detalhes." if pt else "Check System Log for details.",kind="error",duration=4800)

    # ------------------------------------------------------------------
    # UPDATE CENTER v3.18.0
    # ------------------------------------------------------------------
    @staticmethod
    def _update_version_tuple(value):
        try:
            nums=[int(x) for x in re.findall(r"\d+", str(value or ""))[:4]]
            return tuple(nums + [0]*(4-len(nums)))
        except Exception:
            return (0,0,0,0)

    def _update_base_dir(self):
        base=os.path.dirname(self.config_path)
        p=os.path.join(base,"updates")
        os.makedirs(p,exist_ok=True)
        return p

    def _update_install_dir(self):
        if getattr(sys,"frozen",False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _update_set_status(self, text, color=None):
        try:
            if getattr(self,"update_status_label",None):
                self.update_status_label.configure(text=text, text_color=color or TEMAS[self.tema_atual]["accent"])
        except Exception:
            pass

    def _update_set_channel(self, value):
        value=str(value or "stable").lower()
        if value=="dev" and not _owner_key_valid_global(): value="beta"
        if value not in UPDATE_MANIFEST_URLS: value="stable"
        self.update_channel=value
        self._update_manifest={}
        try: self.btn_update_install.configure(state="disabled")
        except Exception: pass
        try: self.update_info_label.configure(text=f"Canal: {value.upper()}  •  versão instalada: v{APP_VERSION}")
        except Exception: pass
        self.salvar_config_app()
        self._update_check_async(silent=False)

    def _update_toggle_auto(self):
        try: self.update_auto_check=bool(self.update_auto_switch.get())
        except Exception: self.update_auto_check=True
        self.salvar_config_app()

    def _update_fetch_manifest(self, channel=None):
        channel=str(channel or self.update_channel or "stable").lower()
        url=UPDATE_MANIFEST_URLS.get(channel, UPDATE_MANIFEST_URLS["stable"])
        r=requests.get(url,timeout=12,headers={"User-Agent":f"ZKStrap/{APP_VERSION}"})
        r.raise_for_status()
        data=r.json()
        if not isinstance(data,dict): raise ValueError("manifest inválido")
        if str(data.get("channel","")).lower()!=channel:
            raise ValueError("canal do manifest não confere")
        version=str(data.get("version","") or "").strip()
        if not version: raise ValueError("manifest sem versão")
        return data

    def _update_check_async(self, silent=False):
        if getattr(self,"_update_check_busy",False): return
        self._update_check_busy=True
        if not silent: self._update_set_status("● VERIFICANDO GITHUB…")
        def worker():
            try:
                data=self._update_fetch_manifest()
                self.after(0,lambda d=data:self._update_apply_manifest(d,silent))
            except Exception as e:
                msg=str(e)
                self.after(0,lambda m=msg:self._update_check_failed(m,silent))
            finally:
                self._update_check_busy=False
        threading.Thread(target=worker,daemon=True).start()

    def _update_check_failed(self, message, silent=False):
        self._update_set_status("● NÃO FOI POSSÍVEL VERIFICAR", "#FFB347")
        try: self.update_progress_label.configure(text=message[:160])
        except Exception: pass
        if not silent:
            try: self.show_toast("UPDATE CENTER", "Não foi possível consultar o GitHub agora.", kind="warning")
            except Exception: pass

    def _update_apply_manifest(self, data, silent=False):
        self._update_manifest=dict(data or {})
        remote=str(data.get("version","") or "")
        notes=data.get("notes",[]) if isinstance(data.get("notes",[]),list) else []
        package=str(data.get("package_url","") or "").strip()
        sha=str(data.get("sha256","") or "").strip().lower()
        newer=self._update_version_tuple(remote) > self._update_version_tuple(APP_VERSION)
        if newer:
            self._update_set_status(f"● NOVA VERSÃO v{remote}", TEMAS[self.tema_atual]["accent"])
            info=f"v{APP_VERSION} → v{remote}  •  canal {self.update_channel.upper()}"
            if notes: info += "\n" + "  •  ".join(str(x) for x in notes[:5])
            if not package or len(sha)!=64:
                info += "\nRelease ainda sem pacote/hash publicado."
                state="disabled"
            else:
                state="normal"
            try:
                self.update_info_label.configure(text=info)
                self.btn_update_install.configure(state=state)
                self.update_progress_label.configure(text="Atualização opcional." if not bool(data.get("mandatory",False)) else "Atualização marcada como obrigatória pelo canal.")
            except Exception: pass
            if not silent:
                try:self.show_toast("UPDATE DISPONÍVEL",f"ZKStrap v{remote} está disponível.",kind="info")
                except Exception:pass
        else:
            self._update_set_status("● VOCÊ ESTÁ ATUALIZADO", "#41D17D")
            try:
                self.update_info_label.configure(text=f"v{APP_VERSION} é a versão mais recente do canal {self.update_channel.upper()}.")
                self.update_progress_label.configure(text="Nenhum download necessário.")
                self.btn_update_install.configure(state="disabled")
            except Exception: pass

    def _update_download_async(self):
        if getattr(self,"_update_download_busy",False): return
        data=dict(getattr(self,"_update_manifest",{}) or {})
        url=str(data.get("package_url","") or "").strip(); expected=str(data.get("sha256","") or "").strip().lower()
        version=str(data.get("version","") or "update")
        if not url or len(expected)!=64:
            messagebox.showwarning("ZKStrap","Este canal ainda não publicou um pacote válido para esta versão.")
            return
        self._update_download_busy=True; self._update_download_cancel=False
        try:self.btn_update_install.configure(state="disabled")
        except Exception:pass
        self._update_set_status("● BAIXANDO ATUALIZAÇÃO…")
        def worker():
            try:
                ddir=os.path.join(self._update_base_dir(),"downloads"); os.makedirs(ddir,exist_ok=True)
                dest=os.path.join(ddir,f"ZKStrap-v{version}.zip")
                h=hashlib.sha256(); done=0
                with requests.get(url,stream=True,timeout=(12,45),headers={"User-Agent":f"ZKStrap/{APP_VERSION}"}) as r:
                    r.raise_for_status(); total=int(r.headers.get("content-length",0) or 0)
                    with open(dest,"wb") as f:
                        for chunk in r.iter_content(chunk_size=262144):
                            if self._update_download_cancel: raise RuntimeError("download cancelado")
                            if not chunk: continue
                            f.write(chunk); h.update(chunk); done+=len(chunk)
                            self.after(0,lambda d=done,t=total:self._update_progress_ui(d,t))
                actual=h.hexdigest().lower()
                if actual!=expected:
                    try: os.remove(dest)
                    except Exception: pass
                    raise RuntimeError("SHA-256 não confere; download descartado")
                self.after(0,lambda:self._update_launch_installer(dest,expected,version))
            except Exception as e:
                msg=str(e); self.after(0,lambda m=msg:self._update_download_failed(m))
            finally:
                self._update_download_busy=False
        threading.Thread(target=worker,daemon=True).start()

    def _update_progress_ui(self, done, total):
        try:
            frac=(done/total) if total>0 else 0
            self.update_progress.set(max(0,min(1,frac)))
            mb=done/(1024*1024); totalmb=total/(1024*1024) if total else 0
            self.update_progress_label.configure(text=(f"{mb:.1f} MB / {totalmb:.1f} MB  •  {frac*100:.0f}%" if total else f"{mb:.1f} MB baixados"))
        except Exception: pass

    def _update_download_failed(self, message):
        self._update_set_status("● FALHA NO DOWNLOAD", "#FF6978")
        try:
            self.update_progress_label.configure(text=message[:180]); self.btn_update_install.configure(state="normal")
        except Exception:pass
        try:self.show_toast("UPDATE CENTER",message[:120],kind="error")
        except Exception:pass

    def _update_updater_source(self):
        install=self._update_install_dir()
        exe=os.path.join(install,"ZKUpdater.exe")
        py=os.path.join(install,"ZKUpdater.py")
        if os.path.isfile(exe): return exe
        if os.path.isfile(py): return py
        return ""

    def _update_launch_installer(self, package, expected_sha, version):
        src=self._update_updater_source()
        if not src:
            self._update_download_failed("ZKUpdater não foi encontrado nesta instalação.")
            return
        if not messagebox.askyesno("ZKStrap Update Center",f"v{version} foi baixada e verificada.\n\nO ZKStrap será fechado, a versão atual será salva em backup e a atualização será instalada. Continuar?"):
            try:self.btn_update_install.configure(state="normal")
            except Exception:pass
            return
        temp_dir=os.path.join(tempfile.gettempdir(),"ZKStrapUpdater"); os.makedirs(temp_dir,exist_ok=True)
        ext=".exe" if src.lower().endswith(".exe") else ".py"
        temp_updater=os.path.join(temp_dir,"ZKUpdater"+ext)
        shutil.copy2(src,temp_updater)
        install=self._update_install_dir(); backup=os.path.join(self._update_base_dir(),"backups")
        exe_name=os.path.basename(sys.executable) if getattr(sys,"frozen",False) else "ZKStrap.exe"
        args=[temp_updater,"--apply",package,"--sha256",expected_sha,"--install-dir",install,"--backup-dir",backup,"--wait-pid",str(os.getpid()),"--relaunch",exe_name,"--from-version",APP_VERSION,"--to-version",version]
        if ext==".py": args=[sys.executable]+args
        subprocess.Popen(args,close_fds=True)
        self._owner_skip_shutdown_save=False
        self.after(180,self._shutdown_app)

    def _update_latest_backup(self):
        bdir=os.path.join(self._update_base_dir(),"backups")
        if not os.path.isdir(bdir): return ""
        files=[os.path.join(bdir,x) for x in os.listdir(bdir) if x.lower().endswith(".zip")]
        return max(files,key=os.path.getmtime) if files else ""

    def _update_restore_previous(self):
        backup=self._update_latest_backup()
        if not backup:
            messagebox.showinfo("ZKStrap","Nenhum backup de versão anterior foi encontrado ainda.")
            return
        src=self._update_updater_source()
        if not src:
            messagebox.showwarning("ZKStrap","ZKUpdater não foi encontrado nesta instalação.")
            return
        name=os.path.basename(backup)
        if not messagebox.askyesno("Restaurar versão",f"Restaurar o backup mais recente?\
\
{name}\
\
Seus dados pessoais em LOCALAPPDATA não serão apagados."):
            return
        temp_dir=os.path.join(tempfile.gettempdir(),"ZKStrapUpdater"); os.makedirs(temp_dir,exist_ok=True)
        ext=".exe" if src.lower().endswith(".exe") else ".py"; temp_updater=os.path.join(temp_dir,"ZKUpdater"+ext); shutil.copy2(src,temp_updater)
        install=self._update_install_dir(); exe_name=os.path.basename(sys.executable) if getattr(sys,"frozen",False) else "ZKStrap.exe"
        args=[temp_updater,"--restore",backup,"--install-dir",install,"--wait-pid",str(os.getpid()),"--relaunch",exe_name]
        if ext==".py": args=[sys.executable]+args
        subprocess.Popen(args,close_fds=True); self.after(180,self._shutdown_app)

    def rollback_completo(self):
        pt=self.idioma=='pt'
        if not messagebox.askyesno("ZKStrap // Rollback", "Restaurar ClientSettings, cursor e fontes originais e desligar todos os módulos do ZKStrap?" if pt else "Restore original ClientSettings, cursor and fonts and disable all ZKStrap modules?"):
            return
        self.config_watchdog_enabled=False
        try: self.restaurar_cursor_original(silencioso=True)
        except Exception: pass
        try: self.restaurar_fonte_jogo(silencioso=True)
        except Exception: pass
        try:
            self.atualizar_pasta_roblox_atual()
            if self.pasta_roblox_salva:
                cs=os.path.join(self.pasta_roblox_salva,'ClientSettings')
                if os.path.isdir(cs): shutil.rmtree(cs)
        except Exception as e: self.log_output(f'[!] Rollback ClientSettings: {e}')
        for key in list(self.module_states): self.module_states[key]=False
        for k in list(self.advanced_values): self.advanced_values[k]='Auto'
        try:
            for sw in self.module_switches.values(): sw.deselect()
            if getattr(self,'switch_config_watchdog',None): self.switch_config_watchdog.deselect()
        except Exception: pass
        if self.bg_capture_changed_by_app and self.game_dvr_background_disabled() and os.name=='nt':
            try:
                import winreg
                for path,name in [(r"System\GameConfigStore","GameDVR_Enabled"),(r"Software\Microsoft\Windows\CurrentVersion\GameDVR","AppCaptureEnabled")]:
                    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,path,0,winreg.KEY_SET_VALUE) as k: winreg.SetValueEx(k,name,0,winreg.REG_DWORD,1)
                self.bg_capture_changed_by_app=False
            except Exception: pass
        self.salvar_config_app(); self.atualizar_estilos_cards(); self.refresh_dashboard()
        self.log_output('[+] Rollback completo finalizado.')
        self._legacy_info("ZKStrap", "Rollback concluído. ClientSettings do ZKStrap removido e assets restaurados quando havia backup." if pt else "Rollback complete. ZKStrap ClientSettings removed and assets restored when backups existed.")

    def abrir_modo_compacto(self):
        pt=self.idioma=='pt'; t=TEMAS[self.tema_atual]; st=self._theme_style()
        win=ctk.CTkToplevel(self); win.title(f"ZKStrap Compact v{APP_VERSION}"); win.geometry("470x550"); win.resizable(False,False); win.configure(fg_color=t['bg']); win.transient(self)
        try: self.withdraw()
        except Exception: pass
        def close():
            try: win.destroy(); self.deiconify(); self.lift()
            except Exception: pass
        win.protocol('WM_DELETE_WINDOW',close)
        shell=ctk.CTkFrame(win,fg_color=t['panel'],corner_radius=st['radius'],border_width=1,border_color=t['border']); shell.pack(fill='both',expand=True,padx=16,pady=16)
        ctk.CTkLabel(shell,text="ZKSTRAP // COMPACT",text_color=t['text'],font=ctk.CTkFont(size=20,weight='bold')).pack(anchor='w',padx=18,pady=(18,2))
        ctk.CTkLabel(shell,text=f"v{APP_VERSION}  •  {THEME_DECOR.get(self.tema_atual,THEME_DECOR['Clean'])['tag']}",text_color=t['accent'],font=ctk.CTkFont(family='Consolas',size=9)).pack(anchor='w',padx=18,pady=(0,16))
        status=ctk.CTkFrame(shell,fg_color=t['card'],corner_radius=st['nav_radius'],border_width=1,border_color=t['card_active']); status.pack(fill='x',padx=18,pady=4)
        ctk.CTkLabel(status,text=("ROBLOX: ONLINE" if self._roblox_esta_aberto() else "ROBLOX: OFFLINE"),text_color=t['accent'],font=ctk.CTkFont(size=12,weight='bold')).pack(anchor='w',padx=14,pady=12)
        def toggle(key):
            self.module_states[key]=not self.module_states.get(key,False); self.salvar_config_app(); refresh_btns()
        btns={}
        for key,label in [('performance_boost','MODO FPS'),('gray_sky','CÉU CINZA')]:
            b=ctk.CTkButton(shell,text='',command=lambda k=key:toggle(k),height=44); b.pack(fill='x',padx=18,pady=5); btns[key]=b
        def refresh_btns():
            for k,b in btns.items():
                on=self.module_states.get(k,False); b.configure(text=f"{('●' if on else '○')}  {('MODO FPS' if k=='performance_boost' else 'CÉU CINZA')}  —  {('ON' if on else 'OFF')}",fg_color=t['accent'] if on else t['card_active'],hover_color=t['hover'],text_color='#050505' if on else t['text'])
        refresh_btns()
        ctk.CTkButton(shell,text="⚡ APLICAR CONFIGURAÇÕES",command=self.aplicar_configuracoes,fg_color=t['accent'],hover_color=t['hover'],text_color='#050505',height=48,font=ctk.CTkFont(size=11,weight='bold')).pack(fill='x',padx=18,pady=(16,5))
        ctk.CTkButton(shell,text="ABRIR CLIENTSETTINGS",command=self.abrir_pasta_clientsettings,fg_color=t['card_active'],hover_color=t['hover'],text_color=t['accent'],height=40).pack(fill='x',padx=18,pady=5)
        ctk.CTkButton(shell,text="VOLTAR AO ZKSTRAP",command=close,fg_color='transparent',border_width=1,border_color=t['card_active'],text_color=t['text'],height=40).pack(fill='x',padx=18,pady=(5,18))

    def selecionar_preset_grafico(self, preset, salvar=True):
        if preset not in PERFORMANCE_PRESETS:
            preset = "Padrão"
        self.preset_grafico = preset
        descricoes_pt = {
            "Padrão": "Não adiciona flags de qualidade pelo preset.",
            "Clean": "Reduz grama e antialiasing, mas preserva mais qualidade de textura.",
            "FPS": "Prioriza FPS: textura baixa, LOD agressivo, sem MSAA e sem grama distante.",
            "Batata": "Máximo foco em desempenho usando apenas flags locais permitidas pelo modo seguro.",
        }
        descricoes_en = {
            "Padrão": "Does not add graphics flags from the preset.",
            "Clean": "Reduces grass and antialiasing while preserving more texture quality.",
            "FPS": "Prioritizes FPS: low textures, aggressive LOD, no MSAA and no distant grass.",
            "Batata": "Maximum performance focus using only local flags accepted by safe mode.",
        }
        try:
            self.lbl_preset_info.configure(text=(descricoes_pt if self.idioma == "pt" else descricoes_en)[preset])
        except Exception:
            pass
        if salvar:
            self.salvar_config_app()
            self.log_output(f"[*] Preset gráfico: {preset}")

    def selecionar_resolucao(self, valor):
        self.resolucao_jogo = valor
        self.salvar_config_app()

    def _resolver_resolucao_escolhida(self):
        valor = getattr(self, "resolucao_jogo", "1280x720")
        custom_names = {"Personalizada", "Custom"}
        if valor in custom_names:
            try:
                w = int(self.entry_res_w.get().strip())
                h = int(self.entry_res_h.get().strip())
            except Exception:
                raise ValueError("Largura e altura precisam ser números inteiros.")
        else:
            try:
                w, h = [int(x) for x in valor.lower().split("x", 1)]
            except Exception:
                w, h = 1280, 720
        if not (320 <= w <= 7680 and 240 <= h <= 4320):
            raise ValueError("Resolução fora do intervalo aceito (320x240 até 7680x4320).")
        self.custom_width, self.custom_height = w, h
        return w, h

    def encontrar_janela_roblox(self):
        if sys.platform != "win32":
            return None
        pids = set()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if (proc.info.get('name') or '').lower() == 'robloxplayerbeta.exe':
                    pids.add(int(proc.info['pid']))
            except Exception:
                pass
        if not pids:
            return None

        user32 = ctypes.windll.user32
        encontrados = []
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def callback(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in pids:
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    encontrados.append((hwnd, buf.value))
            return True

        user32.EnumWindows(EnumWindowsProc(callback), 0)
        if not encontrados:
            return None
        for hwnd, titulo in encontrados:
            if "roblox" in titulo.lower():
                return hwnd
        return encontrados[0][0]

    def aplicar_resolucao_roblox(self):
        if sys.platform != "win32":
            messagebox.showwarning("Windows", "Esta função de resolução usa a API de janelas do Windows.")
            return
        try:
            w, h = self._resolver_resolucao_escolhida()
        except ValueError as e:
            messagebox.showwarning(self.tr[self.idioma]['msg_warning'], str(e))
            return

        hwnd = self.encontrar_janela_roblox()
        if not hwnd:
            messagebox.showwarning(self.tr[self.idioma]['msg_warning'], "Abra o Roblox primeiro para aplicar a resolução.")
            return

        try:
            user32 = ctypes.windll.user32
            GWL_STYLE = -16
            GWL_EXSTYLE = -20
            SW_RESTORE = 9
            SWP_NOZORDER = 0x0004
            SWP_SHOWWINDOW = 0x0040
            user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.GetWindowLongW.restype = ctypes.c_long
            user32.AdjustWindowRectEx.argtypes = [ctypes.POINTER(wintypes.RECT), wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            user32.AdjustWindowRectEx.restype = wintypes.BOOL
            user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.ShowWindow.restype = wintypes.BOOL
            user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
            user32.SetWindowPos.restype = wintypes.BOOL
            style = user32.GetWindowLongW(wintypes.HWND(hwnd), GWL_STYLE)
            exstyle = user32.GetWindowLongW(wintypes.HWND(hwnd), GWL_EXSTYLE)
            rect = wintypes.RECT(0, 0, w, h)
            user32.AdjustWindowRectEx(ctypes.byref(rect), style, False, exstyle)
            outer_w = rect.right - rect.left
            outer_h = rect.bottom - rect.top
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)
            x = max(0, (screen_w - outer_w) // 2)
            y = max(0, (screen_h - outer_h) // 2)
            user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)
            ok = user32.SetWindowPos(wintypes.HWND(hwnd), wintypes.HWND(0), x, y, outer_w, outer_h, SWP_NOZORDER | SWP_SHOWWINDOW)
            if not ok:
                raise ctypes.WinError()
            self.resolucao_jogo = f"{w}x{h}" if f"{w}x{h}" != "1080x1080" else "1080x1080"
            self.salvar_config_app()
            self.log_output(f"[+] Janela do Roblox ajustada para área cliente ~{w}x{h}.")
            self.show_toast("RESOLUÇÃO APLICADA",f"Área do Roblox ajustada para aproximadamente {w}x{h}.",kind="success",duration=2600)
        except Exception as e:
            self.log_output(f"[-] Falha ao redimensionar Roblox: {e}")
            messagebox.showerror(self.tr[self.idioma]['msg_error'], str(e))

    def get_client_settings_paths(self):
        if not self.pasta_roblox_salva:
            return None, None
        pasta = os.path.join(self.pasta_roblox_salva, "ClientSettings")
        arquivo = os.path.join(pasta, "ClientAppSettings.json")
        return pasta, arquivo

    def abrir_pasta_clientsettings(self):
        self.atualizar_pasta_roblox_atual()
        if not self.pasta_roblox_salva or not os.path.exists(self.pasta_roblox_salva):
            messagebox.showwarning(self.tr[self.idioma]['msg_warning'], self.tr[self.idioma]['no_dir_warning'])
            return
        pasta, _ = self.get_client_settings_paths()
        try:
            os.makedirs(pasta, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(pasta)
            else:
                webbrowser.open("file://" + pasta)
            self.log_output(f"[*] Pasta ClientSettings aberta: {pasta}")
        except Exception as e:
            messagebox.showerror(self.tr[self.idioma]['msg_error'], str(e))

    def _ler_json_editor(self):
        texto = self.txt_custom_flags.get("0.0", "end").strip() if hasattr(self, "txt_custom_flags") else "{}"
        if not texto:
            return {}
        dados = json.loads(texto)
        if not isinstance(dados, dict):
            raise ValueError("O JSON precisa ter um objeto { chave: valor } na raiz.")
        return dados

    def validar_flags_editor(self, mostrar=True):
        try:
            dados = self._ler_json_editor()
        except Exception as e:
            if mostrar:
                messagebox.showerror(self.tr[self.idioma]['msg_error'], f"JSON inválido:\n{e}")
            return None
        conhecidas = sorted(k for k in dados if k in ROBLOX_LOCAL_FFLAG_ALLOWLIST)
        fora = sorted(k for k in dados if k not in ROBLOX_LOCAL_FFLAG_ALLOWLIST)
        # v2.2: não remove flags customizadas. O arquivo recebe exatamente o JSON;
        # quem decide se uma flag é reconhecida é o próprio cliente Roblox.
        self.custom_flags = dict(dados)
        self.salvar_config_app()
        if mostrar:
            msg = f"JSON válido: {len(dados)} flag(s).\n\nConhecidas na allowlist: {len(conhecidas)}"
            if fora:
                msg += f"\nFora da allowlist conhecida: {len(fora)}"
                msg += "\n\nEssas flags também serão gravadas, mas o Roblox atual pode ignorá-las."
            if "DFIntDebugDynamicRenderKiloPixels" in dados:
                msg += "\n\nAviso: DFIntDebugDynamicRenderKiloPixels (resolução interna) não está funcional na allowlist atual; gravar a chave não faz o cliente obedecer."
            self._legacy_info("FastFlags", msg)
        return dict(dados)

    def aplicar_json_agora(self):
        dados = self.validar_flags_editor(mostrar=False)
        if dados is None:
            messagebox.showerror(self.tr[self.idioma]['msg_error'], "Corrija o JSON antes de aplicar.")
            return
        self.custom_flags = dados
        self._salvar_flags_compiladas(mostrar_popup=True, usar_editor=False)

    def carregar_flags_atuais_no_editor(self):
        self.atualizar_pasta_roblox_atual()
        if not self.pasta_roblox_salva:
            messagebox.showwarning(self.tr[self.idioma]['msg_warning'], self.tr[self.idioma]['no_dir_warning'])
            return
        _, arquivo = self.get_client_settings_paths()
        try:
            dados = {}
            if os.path.exists(arquivo):
                with open(arquivo, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    dados = loaded
            self.txt_custom_flags.delete("0.0", "end")
            self.txt_custom_flags.insert("0.0", json.dumps(dados, indent=4, ensure_ascii=False))
            self.log_output(f"[*] ClientAppSettings carregado no editor ({len(dados)} chaves).")
        except Exception as e:
            messagebox.showerror(self.tr[self.idioma]['msg_error'], str(e))

    def resetar_roblox(self):
        if not self.pasta_roblox_salva:
            self.log_output("[!] Erro: Nenhum diretório selecionado.")
            messagebox.showwarning(self.tr[self.idioma]['msg_warning'], self.tr[self.idioma]['no_dir_warning'])
            return

        # Se o watchdog continuar ligado, ele recriaria o ClientAppSettings cinco segundos depois.
        self.config_watchdog_enabled = False
        try:
            if getattr(self, "switch_config_watchdog", None) is not None:
                self.switch_config_watchdog.deselect()
        except Exception:
            pass

        # Restaura também o cursor local caso a v2.3 tenha feito backup dele.
        try:
            self.restaurar_cursor_original(silencioso=True)
        except Exception:
            pass
        try:
            self.restaurar_fonte_jogo(silencioso=True)
        except Exception:
            pass

        client_settings = os.path.join(self.pasta_roblox_salva, 'ClientSettings')
        try:
            if os.path.exists(client_settings):
                shutil.rmtree(client_settings)
            for key, sw in getattr(self, "module_switches", {}).items():
                sw.deselect()
                self.module_states[key] = False
            for key, menu in getattr(self, "advanced_menus", {}).items():
                menu.set("Auto")
                self.advanced_values[key] = "Auto"
            self.custom_flags = {}
            self.last_custom_keys = set()
            if hasattr(self, "txt_custom_flags"):
                self.txt_custom_flags.delete("0.0", "end")
                self.txt_custom_flags.insert("0.0", "{}")
            self.salvar_config_app()
            self.atualizar_estilos_cards()
            self.log_output("[!] ClientSettings removido, watchdog desligado e cursor restaurado quando havia backup.")
            self._legacy_info(self.tr[self.idioma]['msg_ok'], self.tr[self.idioma]['reset_success'])
        except Exception as e:
            self.log_output(f"[!] Erro ao resetar: {str(e)}")
            messagebox.showerror(self.tr[self.idioma]['msg_error'], str(e))

    def limpar_arquivos_temp(self):
        paths = [os.path.expandvars(r'%LOCALAPPDATA%\Roblox\logs'), os.path.expandvars(r'%LOCALAPPDATA%\Roblox\Downloads')]
        self.log_output("[*] Iniciando limpeza...")
        apagados = 0
        for path in paths:
            if os.path.exists(path):
                for item in os.listdir(path):
                    try:
                        caminho_item = os.path.join(path, item)
                        if os.path.isfile(caminho_item) or os.path.islink(caminho_item):
                            os.unlink(caminho_item); apagados += 1
                        elif os.path.isdir(caminho_item):
                            shutil.rmtree(caminho_item); apagados += 1
                    except Exception as e:
                        self.log_output(f"[!] Falha ao apagar {item}: {e}")
        self.log_output(f"[+] Limpeza concluída. {apagados} itens removidos.")
        self._legacy_info(self.tr[self.idioma]['msg_ok'], self.tr[self.idioma]['clean_success'])

    def fechar_apps_pesados(self):
        heavy_names = ["chrome.exe", "discord.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe", "spotify.exe", "steam.exe", "epicgameslauncher.exe", "battle.net.exe", "origin.exe", "riotclientux.exe", "riotclientuxrender.exe"]
        encontrados = []
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            name = proc.info.get('name') or ""
            if name.lower() in heavy_names:
                if name.lower().startswith("roblox"):
                    continue
                encontrados.append((proc.info['pid'], name))
        if not encontrados:
            self._legacy_info(self.tr[self.idioma]['msg_ok'], self.tr[self.idioma]['clean_success'])
            return
        lista = "\n".join([f"{pid} - {name}" for pid, name in encontrados])
        confirmar = messagebox.askyesno(self.tr[self.idioma]['confirm_kill_title'], self.tr[self.idioma]['confirm_kill_body'].format(lista=lista))
        if not confirmar:
            self.log_output("[i] Usuário cancelou o fechamento de apps pesados.")
            return
        for pid, name in encontrados:
            try:
                p = psutil.Process(pid)
                p.terminate()
                try:
                    p.wait(timeout=3)
                    self.log_output(f"[+] Processo terminado: {name} (PID {pid})")
                except psutil.TimeoutExpired:
                    p.kill()
                    self.log_output(f"[+] Processo morto (kill): {name} (PID {pid})")
            except Exception as e:
                self.log_output(f"[-] Falha ao fechar {name} (PID {pid}): {e}")
        self._legacy_info(self.tr[self.idioma]['msg_ok'], self.tr[self.idioma]['clean_success'])

    def game_dvr_background_disabled(self):
        """Lê apenas configurações HKCU do usuário atual. False = não confirmamos como desativado."""
        if os.name != "nt":
            return False
        try:
            import winreg
            vals=[]
            for path,name in [
                (r"System\GameConfigStore","GameDVR_Enabled"),
                (r"Software\Microsoft\Windows\CurrentVersion\GameDVR","AppCaptureEnabled"),
            ]:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,path,0,winreg.KEY_READ) as k:
                        vals.append(int(winreg.QueryValueEx(k,name)[0]))
                except Exception:
                    vals.append(1)
            return all(v==0 for v in vals)
        except Exception:
            return False

    def evento_background_capture(self):
        desired_off = bool(getattr(self,"switch_bg_capture",None) and self.switch_bg_capture.get())
        if os.name != "nt":
            messagebox.showwarning("ZKStrap", "Esta opção é exclusiva do Windows.")
            return
        if desired_off:
            ok=messagebox.askyesno("Captura em segundo plano", "Desativar a captura/gravação em segundo plano do Xbox Game Bar?\n\nIsso pode liberar recursos em PCs onde a gravação de fundo está ativa, mas desativa recursos de clipes até você ligar novamente.")
            if not ok:
                try: self.switch_bg_capture.deselect()
                except Exception: pass
                return
        try:
            import winreg
            value = 0 if desired_off else 1
            for path,name in [
                (r"System\GameConfigStore","GameDVR_Enabled"),
                (r"Software\Microsoft\Windows\CurrentVersion\GameDVR","AppCaptureEnabled"),
            ]:
                with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,path,0,winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k,name,0,winreg.REG_DWORD,value)
            self.bg_capture_changed_by_app = True
            self.salvar_config_app()
            self.log_output(f"[+] Captura em segundo plano: {'desativada' if desired_off else 'ativada'}.")
            self._legacy_info("ZKStrap", "Configuração aplicada. Alguns componentes do Game Bar podem exigir sair/entrar na sessão do Windows ou reiniciar para refletir completamente.")
        except Exception as e:
            try:
                if desired_off: self.switch_bg_capture.deselect()
                else: self.switch_bg_capture.select()
            except Exception: pass
            messagebox.showerror("ZKStrap", f"Não foi possível alterar a captura em segundo plano:\n{e}")

    def abrir_game_mode_settings(self):
        try:
            os.startfile("ms-settings:gaming-gamemode")
        except Exception as e:
            messagebox.showerror("ZKStrap", f"Não foi possível abrir o Modo de Jogo:\n{e}")

    def abrir_graphics_settings(self):
        try:
            os.startfile("ms-settings:display-advancedgraphics")
        except Exception:
            try: os.startfile("ms-settings:display")
            except Exception as e: messagebox.showerror("ZKStrap", f"Não foi possível abrir as Preferências de Gráficos:\n{e}")

    def abrir_power_settings(self):
        try:
            os.startfile("ms-settings:powersleep")
        except Exception:
            try:
                subprocess.Popen(["control.exe", "powercfg.cpl"], creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            except Exception as e:
                messagebox.showerror("ZKStrap", f"Não foi possível abrir as opções de energia:\n{e}")

    def abrir_startup_apps_settings(self):
        try:
            os.startfile("ms-settings:startupapps")
        except Exception as e:
            messagebox.showerror("ZKStrap", f"Não foi possível abrir Apps de Inicialização:\n{e}")

    def _set_power_scheme(self, scheme_alias, friendly_name):
        if os.name != "nt":
            messagebox.showwarning("ZKStrap", "Planos de energia desta tela são exclusivos do Windows.")
            return False
        try:
            flags=getattr(subprocess,"CREATE_NO_WINDOW",0)
            cp=subprocess.run(["powercfg","/setactive",scheme_alias],capture_output=True,text=True,timeout=8,creationflags=flags)
            if cp.returncode != 0:
                raise RuntimeError((cp.stderr or cp.stdout or "powercfg retornou erro").strip())
            self.log_output(f"[+] Plano de energia ativado: {friendly_name}.")
            self.show_toast("PLANO DE ENERGIA", f"{friendly_name} ativado.", kind="success", duration=2600)
            return True
        except Exception as e:
            self.log_output(f"[-] Falha ao trocar plano de energia: {e}")
            messagebox.showerror("ZKStrap", f"Não foi possível trocar o plano de energia:\n{e}")
            return False

    def ativar_plano_alto_desempenho(self):
        pt=self.idioma=="pt"
        msg=("Ativar o plano Alto Desempenho do Windows?\n\nEle pode reduzir economia agressiva de CPU, mas em notebooks pode aumentar consumo e temperatura."
             if pt else
             "Enable Windows High Performance power plan?\n\nIt can reduce aggressive CPU power saving, but may increase power use and temperature on laptops.")
        if not messagebox.askyesno("ZKStrap", msg):
            return
        self._set_power_scheme("SCHEME_MIN", "Alto Desempenho" if pt else "High Performance")

    def restaurar_plano_equilibrado(self):
        self._set_power_scheme("SCHEME_BALANCED", "Equilibrado" if self.idioma=="pt" else "Balanced")

    def abrir_pasta_local_roblox(self):
        path=os.path.expandvars(r"%LOCALAPPDATA%\Roblox")
        try:
            if os.path.isdir(path): os.startfile(path)
            else: messagebox.showwarning("ZKStrap", "A pasta local do Roblox ainda não foi encontrada.")
        except Exception as e:
            messagebox.showerror("ZKStrap", f"Não foi possível abrir a pasta do Roblox:\n{e}")

    def preparar_sessao_roblox(self):
        """Prepara uma sessão sem alterações permanentes: prioridade + opção de fechar overlays."""
        pt=self.idioma=="pt"
        if not self._roblox_esta_aberto():
            messagebox.showwarning("ZKStrap", "Abra o Roblox primeiro para preparar a sessão." if pt else "Open Roblox first to prepare the session.")
            return
        self.aplicar_prioridade_roblox()
        msg=("Quer verificar overlays/gravadores conhecidos e escolher se fecha?\n\nNada será encerrado sem uma segunda confirmação."
             if pt else
             "Check known overlays/recorders and choose whether to close them?\n\nNothing will be closed without another confirmation.")
        if messagebox.askyesno("ZKStrap", msg):
            self.fechar_overlays()
        self.log_output("[+] Sessão Roblox preparada: prioridade revisada e overlays verificados.")

    def aplicar_prioridade_roblox(self):
        if os.name != "nt":
            messagebox.showwarning("ZKStrap", "Prioridade de processo desta tela foi feita para Windows.")
            return
        encontrados=[]; falhas=[]
        for proc in psutil.process_iter(['pid','name']):
            try:
                if (proc.info.get('name') or '').lower() == 'robloxplayerbeta.exe':
                    proc.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
                    encontrados.append(proc.info['pid'])
            except Exception as e:
                falhas.append(str(e))
        if encontrados:
            self.log_output(f"[+] Roblox em prioridade ABOVE_NORMAL: PID(s) {', '.join(map(str,encontrados))}")
            self._legacy_info("ZKStrap", "Prioridade do Roblox definida como Acima do normal nesta sessão.\nEla volta ao padrão quando o processo é encerrado.")
        else:
            messagebox.showwarning("ZKStrap", "Abra o Roblox primeiro para aplicar a prioridade.")

    def fechar_overlays(self):
        names={
            'gamebar.exe','gamebarftserver.exe','xboxgamebarwidgets.exe',
            'overwolf.exe','medal.exe','medalencoder.exe','nvidia share.exe','obs64.exe'
        }
        found=[]
        for proc in psutil.process_iter(['pid','name']):
            try:
                n=(proc.info.get('name') or '').lower()
                if n in names: found.append((proc.info['pid'],proc.info.get('name') or n))
            except Exception: pass
        if not found:
            self._legacy_info("ZKStrap", "Nenhum overlay/gravador conhecido foi encontrado em execução.")
            return
        listing='\n'.join(f"{pid} - {name}" for pid,name in found)
        if not messagebox.askyesno("Fechar overlays / gravadores", "Foram encontrados:\n\n"+listing+"\n\nFechar agora? Se você estiver gravando, a gravação pode ser interrompida."):
            return
        closed=0
        for pid,name in found:
            try:
                p=psutil.Process(pid); p.terminate(); closed+=1
            except Exception as e:
                self.log_output(f"[-] Não foi possível fechar {name}: {e}")
        self.log_output(f"[+] Overlays/gravadores encerrados: {closed}")

    def _plano_energia_ativo(self):
        if os.name != "nt": return "N/D"
        try:
            flags=getattr(subprocess,"CREATE_NO_WINDOW",0)
            cp=subprocess.run(["powercfg","/getactivescheme"],capture_output=True,text=True,timeout=5,creationflags=flags)
            out=(cp.stdout or "").strip()
            if "(" in out and ")" in out:
                return out.rsplit("(",1)[-1].split(")",1)[0].strip()
            return out[-60:] if out else "N/D"
        except Exception:
            return "N/D"

    def diagnostico_performance(self):
        def worker():
            try:
                cpu=psutil.cpu_percent(interval=.35)
                vm=psutil.virtual_memory()
                roblox=[]
                for p in psutil.process_iter(['pid','name','memory_info']):
                    try:
                        if (p.info.get('name') or '').lower()=='robloxplayerbeta.exe':
                            mem=p.info.get('memory_info').rss/1024/1024 if p.info.get('memory_info') else 0
                            roblox.append((p.info['pid'],mem))
                    except Exception: pass
                dvr='OFF' if self.game_dvr_background_disabled() else 'ON / padrão'
                if roblox:
                    rb=' | '.join(f"PID {pid}: {mem:.0f} MB" for pid,mem in roblox)
                else:
                    rb='não aberto'
                plano=self._plano_energia_ativo()
                txt=(f"CPU agora: {cpu:.0f}%\nRAM: {vm.percent:.0f}% usada • {vm.available/1024/1024/1024:.1f} GB disponível\nThreads lógicas: {self.get_logical_processors()}\nRoblox: {rb}\nCaptura em segundo plano: {dvr}\nPlano de energia: {plano}")
                self.after(0, lambda: self.lbl_perf_diag.configure(text=txt, text_color=TEMAS[self.tema_atual]['text']))
            except Exception as e:
                err=str(e)
                self.after(0, lambda msg=err: self.lbl_perf_diag.configure(text=f"Falha no diagnóstico: {msg}"))
        threading.Thread(target=worker,daemon=True).start()

    def get_logical_processors(self):
        try:
            return max(1, int(psutil.cpu_count(logical=True) or os.cpu_count() or 1))
        except Exception:
            return max(1, int(os.cpu_count() or 1))

    def evento_micro_fps_changed(self, valor):
        self.micro_fps_target = str(valor)
        self.salvar_config_app()
        if (self.module_states.get("micro_opt", False) or self.module_states.get("fps_unlock", False)) and self.pasta_roblox_salva:
            self._salvar_flags_compiladas(mostrar_popup=False, usar_editor=False)

    def _flags_do_modulo(self, key, data):
        flags = dict(data.get("flags", {}))
        if key == "fps_unlock":
            try:
                target = int(self.micro_fps_target)
            except Exception:
                target = 144
            flags = {
                "DFIntTaskSchedulerTargetFps": target,
                "DFIntGraphicsOptimizationModeFRMFrameRateTarget": target,
            }
        elif key == "ping_boost":
            flags = dict(getattr(self, "flag_otimizar_ping", {}) or {})
        if key == "micro_opt":
            threads = self.get_logical_processors()
            for k in MICRO_THREAD_KEYS:
                flags[k] = threads
            try:
                flags["DFIntGraphicsOptimizationModeFRMFrameRateTarget"] = int(self.micro_fps_target)
            except Exception:
                flags["DFIntGraphicsOptimizationModeFRMFrameRateTarget"] = 144
        return flags

    def _roblox_pids(self):
        pids = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if (proc.info.get('name') or '').lower() == 'robloxplayerbeta.exe':
                    pids.append(int(proc.info['pid']))
        except Exception:
            pass
        return tuple(sorted(set(pids)))

    def _watchdog_capturar_json_editor(self):
        """Atualiza self.custom_flags com o JSON INTEIRO que está visível no editor.

        Se o usuário estiver no meio da digitação e o JSON ficar temporariamente
        inválido, o último JSON válido continua ativo e nenhum arquivo é destruído.
        """
        if not hasattr(self, "txt_custom_flags"):
            return False
        try:
            dados = self._ler_json_editor()
        except Exception as e:
            estado = f"invalid:{type(e).__name__}:{e}"
            if estado != self._watchdog_editor_state:
                self.log_output("[watchdog] JSON do editor está inválido/incompleto; mantendo o último JSON válido.")
                self._watchdog_editor_state = estado
            return False

        dados = self._corrigir_tipos_flags(dados)
        mudou = dados != getattr(self, "custom_flags", {})
        if mudou:
            self.custom_flags = dict(dados)
            self.salvar_config_app()
            self.log_output(f"[watchdog] JSON inteiro do editor atualizado: {len(dados)} flag(s).")
        self._watchdog_editor_state = "valid"
        return mudou

    def evento_watchdog_config(self):
        self.config_watchdog_enabled = bool(self.switch_config_watchdog.get())
        self.salvar_config_app()
        estado = "ativado" if self.config_watchdog_enabled else "desativado"
        self.log_output(f"[*] Watchdog ClientSettings {estado}. Intervalo: 5s.")
        if self.config_watchdog_enabled:
            self.watchdog_clientsettings_tick(run_once=True)
        self.show_toast("WATCHDOG " + ("ATIVADO" if self.config_watchdog_enabled else "DESATIVADO"),
                        "Sincronização automática a cada 5 segundos." if self.config_watchdog_enabled else "Sincronização automática pausada.",
                        kind="success" if self.config_watchdog_enabled else "info",duration=2500)

    def _montar_flags_estado(self):
        flags = {}
        for key, data in FLAG_MODULES.items():
            ativo = bool(self.module_states.get(key, False))
            sw = getattr(self, "module_switches", {}).get(key)
            if sw is not None:
                try:
                    ativo = bool(sw.get())
                    self.module_states[key] = ativo
                except Exception:
                    pass
            if ativo:
                flags.update(self._flags_do_modulo(key, data))
        flags.update(self.obter_flags_avancadas())
        return self._corrigir_tipos_flags(flags)

    def _clientsettings_precisa_sincronizar(self):
        self.atualizar_pasta_roblox_atual()
        if not self.pasta_roblox_salva or not os.path.isdir(self.pasta_roblox_salva):
            return False
        client_dir = os.path.join(self.pasta_roblox_salva, "ClientSettings")
        arquivo = os.path.join(client_dir, "ClientAppSettings.json")
        if not os.path.exists(arquivo):
            return True
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                atual = json.load(f)
            if not isinstance(atual, dict):
                return True
        except Exception:
            return True

        desejadas = self._montar_flags_estado()
        managed_keys = set(ADVANCED_MANAGED_KEYS) | set(self.last_custom_keys)
        for key, data in FLAG_MODULES.items():
            managed_keys.update(self._flags_do_modulo(key, data).keys())
        esperado = {k: v for k, v in atual.items() if k not in managed_keys}
        esperado.update(desejadas)
        return esperado != atual

    def watchdog_clientsettings_tick(self, run_once=False):
        try:
            if getattr(self, "config_watchdog_enabled", False):
                # 1) Usa somente o estado das opções do executor.
                editor_mudou = False

                # 2) Usa o ciclo de vida do processo (PID) como gatilho de ressincronização.
                # Isso NÃO lê/escreve memória do Roblox: apenas detecta abrir/fechar/reiniciar.
                pids = self._roblox_pids()
                processo_mudou = pids != getattr(self, "_watchdog_last_pids", tuple())
                if processo_mudou:
                    self._watchdog_last_pids = pids
                    if pids:
                        self.log_output(f"[watchdog] Roblox detectado/reiniciado (PID {pids[0]}). Conferindo flags...")
                    else:
                        self.log_output("[watchdog] Roblox fechado. Flags continuam preparadas para a próxima abertura.")

                # 3) Regrava somente quando o arquivo não contém exatamente o estado desejado,
                # quando o editor mudou ou quando houve reinício/update do Roblox.
                precisa = editor_mudou or processo_mudou or self._clientsettings_precisa_sincronizar()
                if precisa:
                    ok = self._salvar_flags_compiladas(mostrar_popup=False, usar_editor=False, criar_backup=False)
                    if ok:
                        msg = f"[watchdog] ClientAppSettings sincronizado ({len(self._montar_flags_estado())} flag(s) ativas)."
                        if msg != self._watchdog_last_message:
                            self.log_output(msg)
                            self._watchdog_last_message = msg

                # O mesmo watchdog reaplica o cursor escolhido apenas se os assets mudaram
                # (por exemplo, após uma atualização que criou uma nova version-*).
                if getattr(self, "cursor_pack", "Roblox Padrão") != "Roblox Padrão":
                    self.aplicar_cursor_pack(self.cursor_pack, silencioso=True, somente_se_precisar=True)
                if getattr(self, "game_font_source", ""):
                    self.aplicar_fonte_jogo(silencioso=True, somente_se_precisar=True)
        except Exception as e:
            msg = f"[watchdog] erro: {e}"
            if msg != self._watchdog_last_message:
                self.log_output(msg)
                self._watchdog_last_message = msg
        finally:
            if not run_once and getattr(self, "loop_verificar_jogo", True):
                self.after(5000, self.watchdog_clientsettings_tick)

    def get_cursor_packs_dir(self):
        pasta = os.path.join(os.path.dirname(self.config_path), "cursor_packs")
        os.makedirs(pasta, exist_ok=True)
        return pasta

    def get_cursor_backup_dir(self, roblox_dir=None):
        roblox_dir = roblox_dir or self.pasta_roblox_salva
        versao = os.path.basename(roblox_dir.rstrip("\\/")) if roblox_dir else "unknown"
        pasta = os.path.join(os.path.dirname(self.config_path), "cursor_backups", versao)
        os.makedirs(pasta, exist_ok=True)
        return pasta

    def listar_cursor_packs(self):
        values = ["Roblox Padrão"]
        try:
            base = self.get_cursor_packs_dir()
            for nome in sorted(os.listdir(base), key=str.lower):
                p = os.path.join(base, nome)
                if os.path.isdir(p) and os.path.isfile(os.path.join(p, "ArrowCursor.png")):
                    values.append(nome)
        except Exception:
            pass
        return values

    @staticmethod
    def _nome_pack_seguro(nome):
        nome = os.path.splitext(os.path.basename(nome))[0].strip() or "Cursor"
        nome = re.sub(r'[^A-Za-z0-9 _.-]+', '_', nome).strip(' ._')
        return nome[:48] or "Cursor"

    @staticmethod
    def _remover_fundo_branco_bordas(img, threshold=245):
        """Remove apenas branco/quase-branco conectado às bordas da imagem."""
        img = img.convert("RGBA").copy()
        w, h = img.size
        if w <= 0 or h <= 0:
            return img
        px = img.load()
        visited = bytearray(w * h)
        q = deque()
        def white(x, y):
            r, g, b, a = px[x, y]
            return a > 0 and r >= threshold and g >= threshold and b >= threshold
        def push(x, y):
            idx = y*w + x
            if not visited[idx] and white(x, y):
                visited[idx] = 1; q.append((x,y))
        for x in range(w): push(x,0); push(x,h-1)
        for y in range(h): push(0,y); push(w-1,y)
        removed = 0
        while q:
            x,y = q.popleft(); r,g,b,a = px[x,y]; px[x,y] = (r,g,b,0); removed += 1
            if x>0: push(x-1,y)
            if x+1<w: push(x+1,y)
            if y>0: push(x,y-1)
            if y+1<h: push(x,y+1)
        return img

    def evento_cursor_tamanho(self, valor):
        try:
            self.cursor_visual_size = max(8, min(48, int(round(float(valor)))))
        except Exception:
            self.cursor_visual_size = 24
        self._play_ui_sound("slider",.065)
        try:
            self.lbl_cursor_size.configure(text=f"Tamanho visível: {self.cursor_visual_size}px")
        except Exception:
            pass
        self.salvar_config_app()

    def evento_cursor_white_bg(self):
        try:
            self.cursor_auto_remove_white = bool(self.switch_cursor_white.get())
        except Exception:
            self.cursor_auto_remove_white = True
        self.salvar_config_app()
        self.show_toast("FUNDO BRANCO AUTOMÁTICO",
                        "Remoção automática ativada." if self.cursor_auto_remove_white else "Remoção automática desativada.",
                        kind="success" if self.cursor_auto_remove_white else "info",duration=2300)

    def _normalizar_cursor_png(self, origem, destino, tamanho=64, visual_size=None, anchor_mode=None):
        """Gera um cursor Roblox 64x64 sem transformar a arte inteira em um cursor gigante.

        O canvas fica 64x64. O tamanho visível é fixo em 24 px.
        Modos:
          - Ponta no centro: primeiro pixel visível/top-left da arte fica próximo do hotspot central.
          - Centro: arte fica centralizada; melhor para crosshair/círculo.
          - Preservar 64x64: se a origem já for 64x64, mantém pixels/posição exatamente.
        """
        try:
            from PIL import Image
        except Exception as e:
            raise RuntimeError("Pillow não está instalado. Instale com: pip install Pillow") from e

        visual_size = int(visual_size if visual_size is not None else getattr(self, "cursor_visual_size", 24))
        visual_size = max(8, min(48, visual_size))
        anchor_mode = str(anchor_mode or getattr(self, "cursor_anchor_mode", "Ponta no centro"))

        with Image.open(origem) as im0:
            original_size = tuple(im0.size)
            original_mode = str(im0.mode)
            try:
                im0.seek(0)
            except Exception:
                pass
            original_rgba = im0.convert("RGBA")
            if getattr(self, "cursor_auto_remove_white", True):
                original_rgba = self._remover_fundo_branco_bordas(original_rgba)

            # Para packs Roblox-ready, não destrói padding/hotspot já preparado.
            if anchor_mode == "Preservar 64x64" and original_rgba.size == (tamanho, tamanho):
                canvas = original_rgba.copy()
                alpha = canvas.getchannel("A")
                bbox = alpha.getbbox()
                if bbox is None:
                    raise ValueError("O cursor está totalmente transparente.")
                visible_bbox = bbox
                visible_size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
            else:
                alpha = original_rgba.getchannel("A")
                bbox = alpha.getbbox()
                if bbox is None:
                    raise ValueError("O cursor está totalmente transparente.")
                art = original_rgba.crop(bbox)
                if art.width <= 0 or art.height <= 0:
                    raise ValueError("Dimensões inválidas no cursor.")

                # Escala pelo TAMANHO VISÍVEL, não pelo canvas 64x64.
                escala = min(visual_size / art.width, visual_size / art.height)
                novo_w = max(1, int(round(art.width * escala)))
                novo_h = max(1, int(round(art.height * escala)))
                if (novo_w, novo_h) != art.size:
                    art = art.resize((novo_w, novo_h), Image.Resampling.LANCZOS)

                canvas = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
                if anchor_mode == "Centro":
                    x = (tamanho - novo_w) // 2
                    y = (tamanho - novo_h) // 2
                else:
                    # O hotspot de imagens de cursor do Roblox fica no centro do canvas.
                    # Para setas comuns, a ponta normalmente está no canto superior esquerdo
                    # da arte recortada; colocá-la no centro deixa clique e ponta alinhados.
                    x = tamanho // 2
                    y = tamanho // 2
                    # Se o usuário escolher um cursor enorme, evita cortar tudo na borda.
                    x = min(x, tamanho - novo_w)
                    y = min(y, tamanho - novo_h)
                canvas.alpha_composite(art, (x, y))
                visible_bbox = canvas.getchannel("A").getbbox()
                visible_size = (novo_w, novo_h)

            os.makedirs(os.path.dirname(destino), exist_ok=True)
            canvas.save(destino, format="PNG", optimize=True)

        with Image.open(destino) as check:
            if check.size != (tamanho, tamanho):
                raise IOError("Falha ao gerar canvas 64x64 do cursor.")
            rgba = check.convert("RGBA")
            if rgba.getchannel("A").getbbox() is None:
                raise IOError("Cursor final ficou totalmente transparente.")

        return {
            "original_size": original_size,
            "original_mode": original_mode,
            "final_size": (tamanho, tamanho),
            "final_mode": "RGBA",
            "visible_size": visible_size,
            "visible_bbox": visible_bbox,
            "anchor_mode": anchor_mode,
        }

    def _cursor_source_file(self, base, far=False):
        """Usa o PNG original quando disponível; packs antigos caem no Arrow*.png existente."""
        primary = os.path.join(base, "SourceFar.png" if far else "SourceArrow.png")
        fallback = os.path.join(base, "ArrowFarCursor.png" if far else "ArrowCursor.png")
        if os.path.isfile(primary):
            return primary
        if os.path.isfile(fallback):
            return fallback
        if far:
            p = os.path.join(base, "SourceArrow.png")
            if os.path.isfile(p):
                return p
            p = os.path.join(base, "ArrowCursor.png")
            if os.path.isfile(p):
                return p
        return ""

    def _regenerar_cursor_pack(self, pack):
        if not pack or pack == "Roblox Padrão":
            return None
        base = os.path.join(self.get_cursor_packs_dir(), pack)
        src_normal = self._cursor_source_file(base, far=False)
        src_far = self._cursor_source_file(base, far=True) or src_normal
        if not src_normal or not os.path.isfile(src_normal):
            raise FileNotFoundError("Fonte do cursor não encontrada no pack.")
        info_normal = self._normalizar_cursor_png(
            src_normal, os.path.join(base, "ArrowCursor.png"), 64,
            visual_size=self.cursor_visual_size, anchor_mode=self.cursor_anchor_mode
        )
        info_far = self._normalizar_cursor_png(
            src_far, os.path.join(base, "ArrowFarCursor.png"), 64,
            visual_size=self.cursor_visual_size, anchor_mode=self.cursor_anchor_mode
        )
        return info_normal, info_far

    def evento_cursor_ancora(self, valor):
        self.cursor_anchor_mode = str(valor)
        self.salvar_config_app()

    def importar_cursor_png(self):
        origem = filedialog.askopenfilename(title="Escolha o cursor PNG", filetypes=[("PNG", "*.png")])
        if not origem:
            return
        nome = self._nome_pack_seguro(os.path.basename(origem))
        destino = os.path.join(self.get_cursor_packs_dir(), nome)
        try:
            os.makedirs(destino, exist_ok=True)
            # Guarda o original para que mudar tamanho depois não redimensione um PNG já redimensionado.
            shutil.copy2(origem, os.path.join(destino, "SourceArrow.png"))
            shutil.copy2(origem, os.path.join(destino, "SourceFar.png"))
            self.cursor_pack = nome
            info, _ = self._regenerar_cursor_pack(nome)
            self.cursor_menu.configure(values=self.listar_cursor_packs())
            self.cursor_menu.set(nome)
            try:
                ow, oh = info["original_size"]
                vw, vh = info["visible_size"]
                self.lbl_cursor_status.configure(
                    text=f"Importado: {ow}x{oh} {info['original_mode']} → canvas 64x64 | arte visível {vw}x{vh}px | {self.cursor_anchor_mode}"
                )
            except Exception:
                pass
            self.salvar_config_app()
            self.log_output(
                f"[+] Cursor preparado: fonte {info['original_size'][0]}x{info['original_size'][1]} -> "
                f"canvas 64x64, arte {info['visible_size'][0]}x{info['visible_size'][1]} px."
            )
            self.aplicar_cursor_pack(nome)
        except Exception as e:
            messagebox.showerror(self.tr[self.idioma]['msg_error'], f"Falha ao importar cursor:\n{e}")

    def importar_cursor_pack_pasta(self):
        origem = filedialog.askdirectory(title="Pasta com ArrowCursor.png / ArrowFarCursor.png")
        if not origem:
            return
        normal = os.path.join(origem, "ArrowCursor.png")
        far = os.path.join(origem, "ArrowFarCursor.png")
        if not os.path.isfile(normal):
            messagebox.showwarning(self.tr[self.idioma]['msg_warning'], "O pack precisa ter ArrowCursor.png.")
            return
        nome = self._nome_pack_seguro(os.path.basename(origem))
        destino = os.path.join(self.get_cursor_packs_dir(), nome)
        try:
            os.makedirs(destino, exist_ok=True)
            shutil.copy2(normal, os.path.join(destino, "SourceArrow.png"))
            shutil.copy2(far if os.path.isfile(far) else normal, os.path.join(destino, "SourceFar.png"))
            self.cursor_pack = nome
            info_normal, info_far = self._regenerar_cursor_pack(nome)
            self.cursor_menu.configure(values=self.listar_cursor_packs())
            self.cursor_menu.set(nome)
            try:
                self.lbl_cursor_status.configure(
                    text=(f"Pack: canvas 64x64 | Arrow visível {info_normal['visible_size'][0]}x{info_normal['visible_size'][1]} | "
                          f"Far {info_far['visible_size'][0]}x{info_far['visible_size'][1]} | {self.cursor_anchor_mode}")
                )
            except Exception:
                pass
            self.salvar_config_app()
            self.log_output(f"[+] Pack de cursor '{nome}' importado e preparado.")
            self.aplicar_cursor_pack(nome)
        except Exception as e:
            messagebox.showerror(self.tr[self.idioma]['msg_error'], f"Falha ao importar pack:\n{e}")

    def _cursor_target_dir(self):
        self.atualizar_pasta_roblox_atual()
        if not self.pasta_roblox_salva:
            return ""
        return os.path.join(self.pasta_roblox_salva, "content", "textures", "Cursors", "KeyboardMouse")

    @staticmethod
    def _arquivos_iguais(a, b):
        try:
            if not os.path.isfile(a) or not os.path.isfile(b):
                return False
            if os.path.getsize(a) != os.path.getsize(b):
                return False
            with open(a, "rb") as fa, open(b, "rb") as fb:
                while True:
                    ba = fa.read(65536); bb = fb.read(65536)
                    if ba != bb:
                        return False
                    if not ba:
                        return True
        except Exception:
            return False

    def _bloxstrap_cursor_dir(self):
        """Retorna o diretório de modificações do Bloxstrap quando ele existe.

        Se o usuário usa Bloxstrap, ele pode reaplicar suas próprias modificações ao iniciar
        e sobrescrever o arquivo na version-*. Espelhar o cursor aqui evita esse conflito.
        """
        try:
            local = os.environ.get("LOCALAPPDATA", "")
            if not local:
                return ""
            root = os.path.join(local, "Bloxstrap")
            if not os.path.isdir(root):
                return ""
            return os.path.join(root, "Modifications", "content", "textures", "Cursors", "KeyboardMouse")
        except Exception:
            return ""

    def _aplicar_cursor_bloxstrap(self, src_normal, src_far):
        target = self._bloxstrap_cursor_dir()
        if not target:
            return False
        try:
            os.makedirs(target, exist_ok=True)
            backup = os.path.join(os.path.dirname(self.config_path), "cursor_backups", "bloxstrap")
            os.makedirs(backup, exist_ok=True)
            marker = os.path.join(backup, ".zkvez_created")
            for src, nome in ((src_normal, "ArrowCursor.png"), (src_far, "ArrowFarCursor.png")):
                dst = os.path.join(target, nome)
                bak = os.path.join(backup, nome)
                if os.path.isfile(dst) and not os.path.exists(bak):
                    shutil.copy2(dst, bak)
                elif not os.path.exists(dst):
                    try:
                        open(marker, "a", encoding="utf-8").close()
                    except Exception:
                        pass
                shutil.copy2(src, dst)
            return True
        except Exception as e:
            try:
                self.log_output(f"[!] Não foi possível espelhar cursor no Bloxstrap: {e}")
            except Exception:
                pass
            return False

    def aplicar_cursor_pack(self, pack, silencioso=False, somente_se_precisar=False):
        if pack == "Roblox Padrão":
            return self.restaurar_cursor_original(silencioso=silencioso)
        base = os.path.join(self.get_cursor_packs_dir(), pack)
        # Reprocessa no tamanho/hotspot selecionado sempre que o usuário clicar em aplicar.
        # O watchdog usa somente_se_precisar=True e não fica redimensionando a imagem a cada 5 s.
        if not somente_se_precisar:
            try:
                self._regenerar_cursor_pack(pack)
            except Exception as e:
                if not silencioso:
                    messagebox.showerror(self.tr[self.idioma]['msg_error'], f"Falha ao preparar cursor:\n{e}")
                return False
        src_normal = os.path.join(base, "ArrowCursor.png")
        src_far = os.path.join(base, "ArrowFarCursor.png")
        if not os.path.isfile(src_normal):
            if not silencioso:
                messagebox.showwarning(self.tr[self.idioma]['msg_warning'], "Pack de cursor não encontrado.")
            return False
        if not os.path.isfile(src_far):
            src_far = src_normal
        target_dir = self._cursor_target_dir()
        if not target_dir or not os.path.isdir(target_dir):
            if not silencioso:
                messagebox.showwarning(self.tr[self.idioma]['msg_warning'], "Pasta de cursores do Roblox não encontrada nesta versão.")
            return False
        dst_normal = os.path.join(target_dir, "ArrowCursor.png")
        dst_far = os.path.join(target_dir, "ArrowFarCursor.png")
        if somente_se_precisar and self._arquivos_iguais(src_normal, dst_normal) and self._arquivos_iguais(src_far, dst_far):
            return True
        try:
            backup = self.get_cursor_backup_dir(self.pasta_roblox_salva)
            bak_normal = os.path.join(backup, "ArrowCursor.png")
            bak_far = os.path.join(backup, "ArrowFarCursor.png")
            if os.path.isfile(dst_normal) and not os.path.exists(bak_normal):
                shutil.copy2(dst_normal, bak_normal)
            if os.path.isfile(dst_far) and not os.path.exists(bak_far):
                shutil.copy2(dst_far, bak_far)
            shutil.copy2(src_normal, dst_normal)
            shutil.copy2(src_far, dst_far)
            if not self._arquivos_iguais(src_normal, dst_normal) or not self._arquivos_iguais(src_far, dst_far):
                raise IOError("A cópia terminou, mas a verificação dos arquivos do Roblox falhou.")
            bloxstrap = self._aplicar_cursor_bloxstrap(src_normal, src_far)
            self.cursor_pack = pack
            self.salvar_config_app()
            try:
                extra = " + Bloxstrap" if bloxstrap else ""
                self.lbl_cursor_status.configure(
                    text=f"Aplicado e verificado em .../{os.path.basename(self.pasta_roblox_salva)}{extra}. Feche TODO o Roblox e abra novamente."
                )
            except Exception:
                pass
            if not silencioso:
                self.log_output(f"[+] Cursor '{pack}' aplicado nos assets reais do Roblox.")
                self._legacy_info(
                    self.tr[self.idioma]['msg_ok'],
                    "Cursor aplicado e conferido no disco.\n\nFeche TODAS as janelas/processos do Roblox e abra de novo. "
                    "Se uma experiência definir o próprio MouseIcon, ela pode substituir temporariamente o cursor padrão."
                )
            return True
        except Exception as e:
            if not silencioso:
                messagebox.showerror(self.tr[self.idioma]['msg_error'], f"Falha ao aplicar cursor:\n{e}")
            return False

    def evento_cursor_pack(self, valor):
        self.cursor_pack = str(valor)
        self.salvar_config_app()
        self.aplicar_cursor_pack(self.cursor_pack)

    def aplicar_cursor_selecionado(self):
        pack = self.cursor_menu.get() if getattr(self, "cursor_menu", None) is not None else self.cursor_pack
        self.cursor_pack = pack
        return self.aplicar_cursor_pack(pack)

    def restaurar_cursor_original(self, silencioso=False):
        self.atualizar_pasta_roblox_atual()
        if not self.pasta_roblox_salva:
            return False
        target_dir = self._cursor_target_dir()
        backup = self.get_cursor_backup_dir(self.pasta_roblox_salva)
        restored = 0
        try:
            for nome in ("ArrowCursor.png", "ArrowFarCursor.png"):
                src = os.path.join(backup, nome)
                dst = os.path.join(target_dir, nome)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    restored += 1
            # Restaura também a modificação do Bloxstrap, se a v2.4 tiver espelhado nela.
            try:
                bs_target = self._bloxstrap_cursor_dir()
                bs_backup = os.path.join(os.path.dirname(self.config_path), "cursor_backups", "bloxstrap")
                marker = os.path.join(bs_backup, ".zkvez_created")
                if bs_target:
                    for nome in ("ArrowCursor.png", "ArrowFarCursor.png"):
                        src_bs = os.path.join(bs_backup, nome)
                        dst_bs = os.path.join(bs_target, nome)
                        if os.path.isfile(src_bs):
                            os.makedirs(bs_target, exist_ok=True)
                            shutil.copy2(src_bs, dst_bs)
                        elif os.path.exists(marker) and os.path.isfile(dst_bs):
                            try:
                                os.remove(dst_bs)
                            except Exception:
                                pass
            except Exception:
                pass
            self.cursor_pack = "Roblox Padrão"
            try:
                self.cursor_menu.set("Roblox Padrão")
                self.lbl_cursor_status.configure(text="Cursor original restaurado." if restored else "Nenhum backup desta versão foi necessário/encontrado.")
            except Exception:
                pass
            self.salvar_config_app()
            if not silencioso:
                if restored:
                    self.log_output("[+] Cursor original restaurado.")
                    self._legacy_info(self.tr[self.idioma]['msg_ok'], "Cursor original restaurado.")
                else:
                    self._legacy_info(self.tr[self.idioma]['msg_ok'], "Não há backup de cursor para esta version-*; os arquivos atuais foram mantidos.")
            return True
        except Exception as e:
            if not silencioso:
                messagebox.showerror(self.tr[self.idioma]['msg_error'], f"Falha ao restaurar cursor:\n{e}")
            return False

    def evento_switch_modulo(self, key):
        sw = getattr(self, "module_switches", {}).get(key)
        if sw is None:
            return
        ativo = bool(sw.get())
        self.module_states[key] = ativo
        self._play_ui_sound("toggle_on" if ativo else "toggle_off",.0)
        nome = FLAG_MODULES.get(key, {}).get("pt" if self.idioma == "pt" else "en", key)
        self.log_output(f"[i] {nome}: {'Ativado' if ativo else 'Desativado'}")
        self.atualizar_estilos_cards()
        self.salvar_config_app()
        aplicado=False
        if self.pasta_roblox_salva:
            try:
                aplicado=bool(self._salvar_flags_compiladas(mostrar_popup=False, usar_editor=False))
            except Exception as e:
                self.log_output(f"[-] Auto-aplicar módulo falhou: {e}")
                self.show_toast("FALHA AO APLICAR" if self.idioma=="pt" else "APPLY FAILED", str(e), kind="error")
                return
        if self.idioma=="pt":
            titulo=f"{nome.upper()} {'ATIVADO' if ativo else 'DESATIVADO'}"
            msg=("Configuração aplicada automaticamente ao Roblox." if aplicado else "Estado salvo. Selecione/detecte o Roblox para gravar no ClientSettings.")
        else:
            titulo=f"{nome.upper()} {'ENABLED' if ativo else 'DISABLED'}"
            msg=("Setting applied automatically to Roblox." if aplicado else "State saved. Detect/select Roblox to write ClientSettings.")
        self.show_toast(titulo,msg,kind="success" if ativo else "info",duration=2700)

    def evento_advanced_changed(self, key, valor):
        self.advanced_values[key] = str(valor)
        self.salvar_config_app()

    def obter_flags_avancadas(self):
        vals = dict(getattr(self, "advanced_values", {}))
        try:
            for k, menu in getattr(self, "advanced_menus", {}).items():
                vals[k] = str(menu.get())
        except Exception:
            pass
        flags = {}
        if vals.get("texture", "Auto") != "Auto":
            flags["DFFlagTextureQualityOverrideEnabled"] = True
            flags["DFIntTextureQualityOverride"] = int(vals["texture"])
        if vals.get("msaa", "Auto") != "Auto":
            flags["FIntDebugForceMSAASamples"] = int(vals["msaa"])
        if vals.get("frm", "Auto") != "Auto":
            flags["DFIntDebugFRMQualityLevelOverride"] = int(vals["frm"])
        if vals.get("grass", "Auto") != "Auto":
            n = int(vals["grass"])
            flags["FIntFRMMaxGrassDistance"] = n
            flags["FIntFRMMinGrassDistance"] = n
        if vals.get("lod", "Auto") != "Auto":
            n = int(vals["lod"])
            flags["DFIntCSGLevelOfDetailSwitchingDistance"] = n
            flags["DFIntCSGLevelOfDetailSwitchingDistanceL12"] = n
            flags["DFIntCSGLevelOfDetailSwitchingDistanceL23"] = n
            flags["DFIntCSGLevelOfDetailSwitchingDistanceL34"] = n
        self.advanced_values = vals
        return flags

    def aplicar_ajustes_avancados(self):
        self.salvar_config_app()
        self._salvar_flags_compiladas(mostrar_popup=True, usar_editor=True)

    def atualizar_estilos_cards(self):
        t = TEMAS[self.tema_atual]
        try:
            for key, sw in getattr(self, "module_switches", {}).items():
                card = self.module_cards.get(key)
                sw.configure(progress_color=t["accent"])
                if card:
                    if sw.get():
                        card.configure(fg_color=t["card_active"], border_color=t["accent"])
                    else:
                        card.configure(fg_color="transparent", border_color=t["card_active"])
        except Exception:
            pass
        try:
            self.btn_apply.configure(text='APLICAR CONFIGURAÇÕES' if self.idioma=='pt' else 'APPLY SETTINGS')
            self.btn_reset.configure(text=self.tr[self.idioma]['resetar'])
            self.btn_limpar_logs.configure(text=self.tr[self.idioma]['limpar_logs'])
            self.btn_fechar_pesados.configure(text=self.tr[self.idioma]['fechar_pesados'])
            self.lbl_recursos.configure(text=self.tr[self.idioma]['modulos'])
        except Exception:
            pass
        try:
            self.txt_about.configure(text=self.texto_sobre[self.idioma], text_color=t["text"])
        except Exception:
            pass
        try:
            self.author_box.configure(text=self.author_texts[self.idioma], text_color=t["text"])
        except Exception:
            pass
        try:
            self.yt_link.configure(text="https://www.youtube.com/@zkvez")
        except Exception:
            pass

    def aplicar_idioma(self, escolha):
        self.idioma = 'pt' if escolha.lower().startswith('p') else 'en'
        self.salvar_config_app()
        self.log_output(f"[*] Idioma alterado para: {'Português' if self.idioma=='pt' else 'English'}")
        self.after(10, self.reconstruir_interface)

    def _unlock_secret_theme(self, name, reason="", announce=True):
        if name not in UNLOCKABLE_THEME_NAMES:
            return False
        unlocked=set(getattr(self,"unlocked_secret_themes",set()))
        if name in unlocked:
            return False
        unlocked.add(name); self.unlocked_secret_themes=unlocked
        self.salvar_config_app()
        try:
            refresh=getattr(self,"_refresh_secret_theme_gallery",None)
            if callable(refresh): self.after(0,refresh)
        except Exception: pass
        if announce:
            if not self._play_secret_theme_sound(name,"unlock",0): self._play_ui_sound("secret_unlock",0)
            self.show_toast("TEMA SECRETO DESBLOQUEADO", f"{name}" + (f" • {reason}" if reason else "") + "  •  Personalizar > Temas Secretos", kind="success", duration=6200)
        return True

    def _secret_music_tick(self):
        try:
            app_music=bool(getattr(self,"sounds_enabled",False) and getattr(self,"music_enabled",False) and float(getattr(self,"music_volume",0.0))>0.01)
            snap=dict(getattr(self,"_spotify_current",{}) or {})
            spotify_music=bool(snap.get("title") and "PLAYING" in str(snap.get("status") or "").upper())
            active=bool(app_music or spotify_music)
            if active and "Frequency" not in set(getattr(self,"unlocked_secret_themes",set())):
                self.secret_music_seconds=int(getattr(self,"secret_music_seconds",0) or 0)+1
                if self.secret_music_seconds>=60:
                    self.secret_music_seconds=60
                    self._unlock_secret_theme("Frequency","1 minuto ouvindo a música do ZKStrap")
                elif self.secret_music_seconds%10==0:
                    self.salvar_config_app()
        except Exception:
            pass
        try:self._secret_music_job=self.after(1000,self._secret_music_tick)
        except Exception:self._secret_music_job=None

    def _check_app_secret_unlocks(self):
        try:
            if int(getattr(self,"creator_total_completed",0) or 0)>=5:
                self._unlock_secret_theme("Party","5 desafios concluídos no total",announce=False)
            if len(getattr(self,"combo_entries",[]))>=5:
                self._unlock_secret_theme("Architect","5 builds salvas no Combo Planner")
            if int(getattr(self,"roulette_roll_count",0) or 0)>=20:
                self._unlock_secret_theme("Jackpot","20 builds sorteadas")
        except Exception:pass

    def _fast_retheme_widget_tree(self, root, old_t, new_t):
        """Troca a paleta dos widgets existentes sem destruir/recriar todas as páginas.
        Isso evita os 10–30 s de tela branca causados pelo rebuild completo.
        """
        keys=("bg","panel","sidebar","card","card_active","icon_bg","accent","hover","text","muted","border")
        cmap={}
        for k in keys:
            ov=old_t.get(k); nv=new_t.get(k)
            if isinstance(ov,str) and isinstance(nv,str): cmap[ov.upper()]=nv
        attrs=("fg_color","hover_color","text_color","border_color","button_color","button_hover_color","progress_color","scrollbar_button_color","scrollbar_button_hover_color","placeholder_text_color")
        stack=[root]; seen=set()
        while stack:
            w=stack.pop()
            if id(w) in seen: continue
            seen.add(id(w))
            try: stack.extend(w.winfo_children())
            except Exception: pass
            for attr in attrs:
                try: val=w.cget(attr)
                except Exception: continue
                new_val=None
                if isinstance(val,str): new_val=cmap.get(val.upper())
                elif isinstance(val,(tuple,list)) and len(val)==2:
                    mapped=[]; changed=False
                    for x in val:
                        y=cmap.get(str(x).upper(),x);mapped.append(y);changed|=(y!=x)
                    if changed:new_val=tuple(mapped)
                if new_val is not None and new_val!=val:
                    try:w.configure(**{attr:new_val})
                    except Exception:pass
            # Canvas nativo
            if isinstance(w,tk.Canvas):
                try:
                    bg=w.cget("bg"); nb=cmap.get(str(bg).upper())
                    if nb:w.configure(bg=nb)
                except Exception:pass

    def _fast_apply_theme(self, old_t, novo_tema):
        new_t=TEMAS[novo_tema]
        started=time.perf_counter()
        try:self.configure(fg_color=new_t["bg"])
        except Exception:pass
        self._fast_retheme_widget_tree(getattr(self,"main_container",self),old_t,new_t)
        panel=getattr(self,"_owner_panel",None)
        try:
            if panel is not None and panel.winfo_exists(): self._fast_retheme_widget_tree(panel,old_t,new_t)
        except Exception:pass
        # Ícones e arte vetorial dependem do tema e são baratos de redesenhar.
        try:
            for key,b in getattr(self,"nav_buttons",{}).items():
                img=self._make_nav_icon(key,theme_name=novo_tema,size=20); self.nav_icon_images[key]=img; b.configure(image=img)
        except Exception:pass
        for cv in [getattr(self,"canvas",None),getattr(self,"header_theme_canvas",None),getattr(self,"sidebar_theme_canvas",None),getattr(self,"dock_theme_canvas",None)]:
            try:
                if cv is not None and cv.winfo_exists(): self._draw_theme_art(cv,novo_tema,new_t)
            except Exception:pass
        try:
            cv=getattr(self,"page_theme_canvases",{}).get(getattr(self,"current_page_key",""))
            if cv is not None and cv.winfo_exists(): self._draw_theme_art(cv,novo_tema,new_t)
        except Exception:pass
        try:self._refresh_sound_button()
        except Exception:pass
        try:self.update_idletasks()
        except Exception:pass
        _startup_log(f"THEME FAST APPLY {novo_tema!r}: {(time.perf_counter()-started)*1000:.0f} ms")

    def mudar_tema_interface(self, novo_tema, manter_cor=False):
        if novo_tema not in TEMAS:
            return
        if novo_tema in UNLOCKABLE_THEME_NAMES and not self._owner_secret_theme_unlocked(novo_tema):
            rule=SECRET_THEME_RULES.get(novo_tema,{})
            self.show_toast("TEMA BLOQUEADO", "Dica: "+rule.get("hint","Há algo escondido no ZKStrap."), kind="info", duration=3800)
            self._play_ui_sound("warning",0)
            return
        old_name=getattr(self,"tema_atual","ZKStrap Core")
        old_t=dict(TEMAS.get(old_name,TEMAS["ZKStrap Core"]))
        self.tema_atual = novo_tema
        self._play_ui_sound("theme",.0)
        TEMAS[novo_tema] = TEMAS_PADRAO[novo_tema].copy()
        ov = self.theme_overrides.get(novo_tema, {}) if isinstance(self.theme_overrides.get(novo_tema, {}), dict) else {}
        for k, v in ov.items():
            if k in TEMAS[novo_tema] and self._cor_hex_valida(v):
                TEMAS[novo_tema][k] = v.upper()
        self.salvar_config_app()
        # Devolve o controle ao Tk antes da recoloração; o clique não congela a janela.
        def apply_now():
            try:
                self._fast_apply_theme(old_t,novo_tema)
                self.show_toast("TEMA APLICADO", novo_tema, kind="success", duration=1900)
            except Exception as exc:
                _startup_log("FAST THEME failed "+repr(exc))
                # Fallback raro: mantém o app funcional, mas não bloqueia o callback do botão.
                try:self.after(30,self.reconstruir_interface)
                except Exception:pass
        self.after(1,apply_now)


    def log_output(self, mensagem):
        timestamp = datetime.now().strftime("%H:%M:%S")
        linha = f"[{timestamp}] {mensagem}"
        if not hasattr(self, "_log_history"):
            self._log_history = []
        self._log_history.append(linha)
        self._log_history = self._log_history[-120:]
        try:
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", linha + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        except:
            print(linha)

    def watchdog_processo_jogo_thread(self):
        while self.loop_verificar_jogo:
            jogo_aberto = any(proc.info['name'] == "RobloxPlayerBeta.exe" for proc in psutil.process_iter(['name']) if proc.info['name'])
            cor = "#00FF66" if jogo_aberto else "#FF3333"
            texto = "Roblox Status: 🟢 CORE ATIVO" if jogo_aberto else "Roblox Status: 🔴 FORA DE EXECUÇÃO"
            self.after(0, lambda t=texto, c=cor: self.lbl_status_jogo.configure(text=t, text_color=c))
            time.sleep(2.5)

    def tentar_achar_roblox_automatico(self):
        if self.pasta_roblox_salva and os.path.exists(os.path.join(self.pasta_roblox_salva, "RobloxPlayerBeta.exe")):
            texto = f"Diretório: .../{os.path.basename(self.pasta_roblox_salva)}"
            try:
                self.after(0, lambda txt=texto: self.lbl_pasta_atual.configure(text=txt, text_color="#00FF66"))
            except Exception:
                pass
            self.log_output(f"[*] Diretório Roblox restaurado: {self.pasta_roblox_salva}")
            return
        caminhos = [os.path.expandvars(r'%LOCALAPPDATA%\Roblox\Versions'), r"C:\Program Files (x86)\Roblox\Versions", r"C:\Program Files\Roblox\Versions"]
        encontrado = False
        for rota in caminhos:
            try:
                if os.path.exists(rota):
                    subpastas = sorted(glob.glob(os.path.join(rota, 'version-*')), key=os.path.getmtime, reverse=True)
                    if subpastas and os.path.exists(os.path.join(subpastas[0], 'RobloxPlayerBeta.exe')):
                        self.pasta_roblox_salva = subpastas[0]
                        texto = f"{self.tr[self.idioma]['diretorio_buscando'][:-3]} .../{os.path.basename(self.pasta_roblox_salva)}"
                        try:
                            self.after(0, lambda txt=texto: self.lbl_pasta_atual.configure(text=txt, text_color="#00FF66"))
                        except:
                            pass
                        encontrado = True
                        self.salvar_config_app()
                        self.log_output(f"[*] Diretório Roblox encontrado: {self.pasta_roblox_salva}")
                        break
            except Exception:
                continue
        if not encontrado:
            try:
                self.after(0, lambda: self.lbl_pasta_atual.configure(text=self.tr[self.idioma]['diretorio_nao_encontrado'], text_color="#FF3333"))
            except:
                pass
            self.log_output("[!] Diretório do Roblox não foi encontrado automaticamente.")
            try:
                self.after(100, lambda: self._legacy_info(self.tr[self.idioma]['about_notice_title'], self.tr[self.idioma]['about_location_instructions']))
            except:
                pass

    def atualizar_pasta_roblox_atual(self):
        """Atualiza para a version-* mais recente para não escrever flags em uma build antiga após update do Roblox."""
        caminhos = [
            os.path.expandvars(r'%LOCALAPPDATA%\Roblox\Versions'),
            r"C:\Program Files (x86)\Roblox\Versions",
            r"C:\Program Files\Roblox\Versions",
        ]
        candidatos = []
        for rota in caminhos:
            try:
                if os.path.isdir(rota):
                    for pasta in glob.glob(os.path.join(rota, 'version-*')):
                        if os.path.exists(os.path.join(pasta, 'RobloxPlayerBeta.exe')):
                            candidatos.append(pasta)
            except Exception:
                pass
        if candidatos:
            mais_nova = max(candidatos, key=os.path.getmtime)
            if mais_nova != self.pasta_roblox_salva:
                self.pasta_roblox_salva = mais_nova
                self.salvar_config_app()
                try:
                    self.lbl_pasta_atual.configure(text=f"Diretório: .../{os.path.basename(mais_nova)}", text_color="#00FF66")
                except Exception:
                    pass
                self.log_output(f"[*] Roblox atualizado/detectado: {mais_nova}")
        return self.pasta_roblox_salva

    def selecionar_pasta_roblox(self):
        pasta = filedialog.askdirectory()
        if pasta:
            exe = os.path.join(pasta, "RobloxPlayerBeta.exe")
            if not os.path.exists(exe):
                messagebox.showwarning(self.tr[self.idioma]['msg_warning'], "Selecione a pasta version-* que contém RobloxPlayerBeta.exe.")
                return
            self.pasta_roblox_salva = pasta
            try:
                self.lbl_pasta_atual.configure(text=f"Diretório: .../{os.path.basename(pasta)}", text_color="#00FF66")
            except Exception:
                pass
            self.salvar_config_app()
            self.log_output(f"[*] Diretório selecionado: {pasta}")

    def _corrigir_tipos_flags(self, dados):
        if isinstance(dados, dict):
            return {k: self._corrigir_tipos_flags(v) for k, v in dados.items()}
        if isinstance(dados, str):
            if dados.lower() == "true": return True
            if dados.lower() == "false": return False
            try: return float(dados) if '.' in dados else int(dados)
            except ValueError: return dados
        return dados

    def _roblox_esta_aberto(self):
        try:
            return any((p.info.get('name') or '').lower() == 'robloxplayerbeta.exe' for p in psutil.process_iter(['name']))
        except Exception:
            return False

    def _salvar_flags_compiladas(self, mostrar_popup=True, usar_editor=True, criar_backup=True):
        self.atualizar_pasta_roblox_atual()
        if not self.pasta_roblox_salva or not os.path.exists(self.pasta_roblox_salva):
            if mostrar_popup:
                messagebox.showwarning(self.tr[self.idioma]['msg_warning'], self.tr[self.idioma]['no_dir_warning'])
            return False

        flags_brutas = {}
        # Módulos rápidos: cada switch corresponde a um conjunto específico de flags.
        for key, data in FLAG_MODULES.items():
            ativo = bool(getattr(self, "module_switches", {}).get(key).get()) if key in getattr(self, "module_switches", {}) else bool(self.module_states.get(key, False))
            self.module_states[key] = ativo
            if ativo:
                flags_brutas.update(self._flags_do_modulo(key, data))

        # Ajustes finos têm prioridade sobre os módulos rápidos.
        flags_brutas.update(self.obter_flags_avancadas())

        # v2.7: sem editor livre. Somente opções expostas pelo executor entram no arquivo.
        editor_flags = {}
        self.custom_flags = {}
        flags_finais = self._corrigir_tipos_flags(flags_brutas)

        client_settings_path = os.path.join(self.pasta_roblox_salva, 'ClientSettings')
        os.makedirs(client_settings_path, exist_ok=True)
        arquivo_final = os.path.join(client_settings_path, 'ClientAppSettings.json')

        existentes = {}
        if os.path.exists(arquivo_final):
            try:
                with open(arquivo_final, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    existentes = loaded
            except Exception as e:
                self.log_output(f"[!] ClientAppSettings existente não pôde ser lido: {e}")

        # Remove apenas o que este app gerencia, preservando outras chaves existentes.
        managed_keys = set(ADVANCED_MANAGED_KEYS) | set(self.last_custom_keys)
        for key, data in FLAG_MODULES.items():
            managed_keys.update(self._flags_do_modulo(key, data).keys())
        resultado = {k: v for k, v in existentes.items() if k not in managed_keys}
        resultado.update(flags_finais)

        try:
            if criar_backup and os.path.exists(arquivo_final):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup = arquivo_final + f'.bak.{ts}'
                try:
                    shutil.copy2(arquivo_final, backup)
                    self.log_output(f"[*] Backup criado: {os.path.basename(backup)}")
                except Exception as e:
                    self.log_output(f"[!] Falha ao criar backup: {e}")

            tmp = arquivo_final + ".tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=4, ensure_ascii=False)
            os.replace(tmp, arquivo_final)

            # Verificação real: lê de volta do disco para distinguir 'não gravou' de 'Roblox ignorou'.
            with open(arquivo_final, 'r', encoding='utf-8') as f:
                confirmado = json.load(f)
            faltando = [k for k, v in flags_finais.items() if confirmado.get(k) != v]
            if faltando:
                raise IOError("Falha na verificação das flags: " + ", ".join(faltando[:8]))

            self.last_custom_keys = set(editor_flags.keys())
            self.salvar_config_app()
            fora_allowlist = sorted(k for k in flags_finais if k not in ROBLOX_LOCAL_FFLAG_ALLOWLIST)
            self.log_output(f"[+] ClientAppSettings confirmado no disco: {arquivo_final}")
            self.log_output(f"[+] {len(flags_finais)} flag(s) gravada(s).")
            if self.module_states.get("micro_opt", False):
                self.log_output(f"[i] Micro-opt: {self.get_logical_processors()} threads lógicas | alvo {self.micro_fps_target} FPS.")
            if fora_allowlist:
                self.log_output(f"[i] {len(fora_allowlist)} flag(s) fora da allowlist conhecida foram gravadas; o Roblox pode ignorá-las.")
            jogo_aberto = self._roblox_esta_aberto()
            if jogo_aberto:
                self.log_output("[!] Roblox está aberto. Reinicie o jogo para ele reler ClientAppSettings.json.")

            if mostrar_popup:
                msg = f"{len(flags_finais)} flag(s) gravada(s) e verificadas no arquivo."
                if fora_allowlist:
                    msg += f"\n\n{len(fora_allowlist)} flag(s) estão fora da allowlist conhecida e podem ser ignoradas pelo Roblox."
                if jogo_aberto:
                    msg += "\n\nReinicie o Roblox para carregar as alterações."
                self._legacy_info(self.tr[self.idioma]['msg_ok'], msg)
            return True
        except Exception as e:
            self.log_output(f"[-] Falha: {str(e)}")
            if mostrar_popup:
                messagebox.showerror(self.tr[self.idioma]['msg_error'], str(e))
            return False

    def compilar_e_salvar_flags(self):
        # Compatibilidade com atalhos antigos: o nome novo da ação é Aplicar Configurações.
        return self.aplicar_configuracoes()

    def animate_title_pulse(self):
        t = TEMAS[self.tema_atual]
        accent = t.get("accent", "#00FF66")
        hover = t.get("hover", accent)
        self.pulse_phase += 0.03
        if self.pulse_phase > 2.0:
            self.pulse_phase = 0.0
        phase = self.pulse_phase if self.pulse_phase <= 1.0 else 2.0 - self.pulse_phase
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        def rgb_to_hex(rgb):
            return '#%02x%02x%02x' % rgb
        ra = hex_to_rgb(accent); rb = hex_to_rgb(hover)
        blended = tuple(int(ra[i] + (rb[i]-ra[i]) * phase) for i in range(3))
        color = rgb_to_hex(blended)
        try:
            self.lbl_titulo.configure(text_color=color)
        except:
            pass
        if getattr(self, "loop_animacao", True):
            self.after(60, self.animate_title_pulse)

    def _shutdown_app(self):
        """Fecha a aplicação por completo e evita janela raiz/overlay órfão após o X."""
        if getattr(self,"_closing",False): return
        self._closing=True
        try: self.withdraw()
        except Exception: pass
        self.loop_verificar_jogo=False
        self.loop_animacao=False
        for attr in ("_page_anim_job","_layout_job"):
            job=getattr(self,attr,None)
            if job is not None:
                try: self.after_cancel(job)
                except Exception: pass
                try: setattr(self,attr,None)
                except Exception: pass
        try: self._fechar_busca_universal()
        except Exception: pass
        try: self._tutorial_close(mark_complete=False,voltar_home=False)
        except Exception: pass
        try:
            for toast in list(getattr(self,"_toast_items",[])):
                try: toast.destroy()
                except Exception: pass
            self._toast_items=[]
        except Exception: pass
        if not getattr(self,"_owner_skip_shutdown_save",False):
            try: self.salvar_config_app()
            except Exception: pass
        try:
            mgr=getattr(self,"_sound_manager",None)
            if mgr is not None: mgr.shutdown()
        except Exception: pass
        # v3.10: não há processo/modelo externo para encerrar.
        # Fecha explicitamente qualquer Toplevel/tooltip que ainda exista.
        try:
            for child in list(self.winfo_children()):
                try:
                    if isinstance(child,(Toplevel,ctk.CTkToplevel)) and child.winfo_exists(): child.destroy()
                except Exception: pass
        except Exception: pass
        try: self.quit()
        except Exception: pass
        try:
            ctk.CTk.destroy(self)
        except Exception:
            try: self.tk.call("destroy", ".")
            except Exception: pass

    def destroy(self):
        self._shutdown_app()

if __name__ == "__main__":
    if "--zk-audio-helper" in sys.argv:
        _run_audio_helper()
        raise SystemExit(0)
    if "--zk-splash" in sys.argv:
        _run_splash_process()
        raise SystemExit(0)

    _splash_handle = _launch_detached_splash()
    app = None
    try:
        _startup_log("BOOT: creating main app")
        app = ModernConfigApp()
        _startup_log("BOOT: main app constructed")
        _raise_if_splash_cancelled()

        # Confirma 100% para a splash, mas não espera o processo-filho decidir
        # sozinho quando encerrar. A versão anterior podia ficar presa exatamente
        # nessa passagem e a janela principal nunca era mapeada.
        _detached_splash_report(1.0, "Tudo pronto.", "Abrindo ZKStrap", "[OK] ZKSTRAP ready")
        _startup_log("SPLASH: 100% reported")

        # Mantém o 100% visível por um instante e continua aceitando cancelamento.
        hold_until = time.time() + 0.90
        while time.time() < hold_until:
            if _splash_cancel_requested():
                raise StartupCancelled("Cancelado na splash")
            time.sleep(.03)

        if _splash_cancel_requested():
            raise StartupCancelled("Cancelado na splash")

        # O processo principal encerra a splash de forma determinística. Isso evita
        # deadlock/espera no handoff e mantém o comportamento da 3.13.2.4 que abriu
        # corretamente no Windows.
        _close_detached_splash(_splash_handle, cleanup=False)
        _startup_log("SPLASH: child closed by parent")
        if _splash_cancel_requested():
            raise StartupCancelled("Cancelado na splash")
        _cleanup_splash_ipc(_splash_handle)
        _splash_handle = None

        def _show_main_window():
            if app is None or getattr(app, "_closing", False):
                return
            try:
                app.state("normal")
            except Exception:
                pass
            try:
                app.deiconify()
            except Exception:
                pass
            try:
                app.attributes("-alpha", 1.0)
            except Exception:
                pass
            try:
                app.update_idletasks()
                app.lift()
                # Topmost só por alguns ms para tirar a janela de trás de outras
                # janelas; depois volta ao comportamento normal.
                app.attributes("-topmost", True)
                app.after(180, lambda: app.attributes("-topmost", False) if app.winfo_exists() else None)
                app.focus_force()
            except Exception:
                pass
            _startup_log("MAIN: reveal callback executed")

        # O ponto principal do fix: deiconify acontece COM o mainloop rodando.
        # Antes ele acontecia antes do loop de eventos e em algumas instalações do
        # Windows a janela permanecia withdrawn mesmo depois da splash fechar.
        app.after(0, _show_main_window)
        # Watchdog visual único: se o primeiro mapeamento for ignorado pelo WM,
        # tenta revelar de novo sem criar loop recorrente.
        app.after(900, _show_main_window)
        _startup_log("MAIN: entering mainloop")
        app.mainloop()
        _startup_log("MAIN: mainloop returned")
        try:
            if app.winfo_exists():
                app._shutdown_app()
        except Exception:
            pass
    except StartupCancelled:
        _startup_log("BOOT: cancelled from splash")
        try:
            if app is not None:
                app._shutdown_app()
        except Exception:
            pass
        _close_detached_splash(_splash_handle)
        raise SystemExit(0)
    except Exception as e:
        _startup_log("BOOT ERROR: " + repr(e))
        _close_detached_splash(_splash_handle)
        show_startup_error(e)
