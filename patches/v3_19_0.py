from pathlib import Path
import os, re

root = Path(os.environ.get('ZK_SOURCE_DIR', '.'))
path = root / 'ZKStrap_v3_18_0.py'
s = path.read_text(encoding='utf-8')


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit(f'v3.19.0 patch: pattern not found: {label}')
    s = s.replace(old, new, count)


def regex_rep(pattern, replacement, label, flags=re.S):
    global s
    ns, n = re.subn(pattern, replacement, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'v3.19.0 patch: regex pattern not found/ambiguous: {label} ({n})')
    s = ns


rep('APP_VERSION = "3.18.9"', 'APP_VERSION = "3.19.0"', 'version')
# Be tolerant of the exact v3.18.9 build label.
s, n = re.subn(r'BUILD_TIMESTAMP = "[^"]*"', 'BUILD_TIMESTAMP = "Native Smooth Scroll Container"', s, count=1)
if n != 1:
    raise SystemExit('v3.19.0 patch: BUILD_TIMESTAMP missing')

native_scroll_class = r'''
class ZKSmoothScrollFrame(ctk.CTkFrame):
    """Scrollable content frame backed by a plain Tk canvas.

    CTkScrollableFrame installs global wheel handlers and redraws through its
    own internal canvas. ZKStrap uses this smaller adapter instead: callers can
    keep creating child widgets with this object as the parent, while geometry
    management is forwarded to a host containing a native Canvas + scrollbar.
    """
    def __init__(self, master, width=200, height=200, fg_color="transparent",
                 corner_radius=0, scrollbar_button_color=None,
                 scrollbar_button_hover_color=None, **kwargs):
        self._zk_outer_master = master
        self._zk_requested_fg = fg_color
        self._zk_host = ctk.CTkFrame(master, fg_color=fg_color, corner_radius=corner_radius)
        bg = self._zk_find_canvas_bg(master)
        self._parent_canvas = tk.Canvas(
            self._zk_host, bg=bg, highlightthickness=0, bd=0,
            relief="flat", takefocus=0
        )
        sb_color = scrollbar_button_color or "#5A5A5A"
        sb_hover = scrollbar_button_hover_color or sb_color
        self._scrollbar = ctk.CTkScrollbar(
            self._zk_host, orientation="vertical",
            command=self._parent_canvas.yview,
            fg_color="transparent", button_color=sb_color,
            button_hover_color=sb_hover, width=11
        )
        self._parent_canvas.configure(yscrollcommand=self._scrollbar.set)
        self._parent_canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y", padx=(4,0))

        # The public object itself is the content frame. Widgets created with
        # parent=body therefore keep working without touching page builders.
        super().__init__(
            self._parent_canvas,
            width=width, height=height,
            fg_color=fg_color, corner_radius=0,
            **kwargs
        )
        self._zk_window = self._parent_canvas.create_window(
            0, 0, window=self, anchor="nw"
        )
        self._zk_scroll_state = {"target": 0.0, "job": None, "last_input": 0.0}
        self.bind("<Configure>", self._zk_sync_region, add="+")
        self._parent_canvas.bind("<Configure>", self._zk_canvas_resized, add="+")
        try:self.after_idle(self._zk_sync_region)
        except Exception:pass

    @staticmethod
    def _zk_find_canvas_bg(widget):
        cur = widget
        for _ in range(14):
            if cur is None: break
            try:
                val = cur.cget("fg_color")
                if isinstance(val, (tuple, list)) and len(val) >= 2:
                    val = val[1] if str(ctk.get_appearance_mode()).lower() == "dark" else val[0]
                if val and str(val).lower() != "transparent":
                    return str(val)
            except Exception:
                pass
            try:
                val = cur.cget("bg")
                if val: return str(val)
            except Exception:
                pass
            cur = getattr(cur, "master", None)
        return "#0B0B0D"

    def _zk_canvas_resized(self, event=None):
        try:
            width = max(1, int(getattr(event, "width", self._parent_canvas.winfo_width())))
            self._parent_canvas.itemconfigure(self._zk_window, width=width)
            self._zk_sync_region()
        except Exception:
            pass

    def _zk_sync_region(self, event=None):
        try:
            self.update_idletasks()
            req_h = max(1, int(self.winfo_reqheight()))
            canvas_w = max(1, int(self._parent_canvas.winfo_width()))
            self._parent_canvas.itemconfigure(self._zk_window, width=canvas_w)
            self._parent_canvas.configure(scrollregion=(0, 0, canvas_w, req_h))
            need = req_h > int(self._parent_canvas.winfo_height()) + 2
            if need and not self._scrollbar.winfo_ismapped():
                self._scrollbar.pack(side="right", fill="y", padx=(4,0))
            elif not need and self._scrollbar.winfo_ismapped():
                self._scrollbar.pack_forget()
        except Exception:
            pass

    # Geometry management belongs to the host; the content frame is managed by
    # Canvas.create_window(). This keeps old body.pack(...) calls compatible.
    def pack(self, *args, **kwargs):
        return self._zk_host.pack(*args, **kwargs)

    def pack_forget(self):
        return self._zk_host.pack_forget()

    def grid(self, *args, **kwargs):
        return self._zk_host.grid(*args, **kwargs)

    def grid_forget(self):
        return self._zk_host.grid_forget()

    def place(self, *args, **kwargs):
        return self._zk_host.place(*args, **kwargs)

    def place_forget(self):
        return self._zk_host.place_forget()

    def winfo_ismapped(self):
        try:return bool(self._zk_host.winfo_ismapped())
        except Exception:return False

    def destroy(self):
        try:
            if self._zk_host.winfo_exists():
                self._zk_host.destroy()
                return
        except Exception:
            pass
        try:super().destroy()
        except Exception:pass

'''
anchor = 'class ModernConfigApp(ctk.CTk):\n'
if anchor not in s:
    raise SystemExit('v3.19.0 patch: ModernConfigApp anchor missing')
s = s.replace(anchor, native_scroll_class + anchor, 1)

# Replace every CTk scrollable container currently used by the app (sidebar,
# page bodies and internal galleries). This is deliberate: leaving even one
# CTkScrollableFrame would re-install its global MouseWheel handler.
count = s.count('ctk.CTkScrollableFrame(')
if count < 4:
    raise SystemExit(f'v3.19.0 patch: expected >=4 CTkScrollableFrame uses, found {count}')
s = s.replace('ctk.CTkScrollableFrame(', 'ZKSmoothScrollFrame(')

new_queue = r'''    def _queue_scroll_step(self, scrollable, step):
        """Smooth target-following scroll with one animation loop per container."""
        try:
            if scrollable is None or not step:return "break"
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None or not canvas.winfo_exists():return "break"
            try:scrollable._zk_sync_region()
            except Exception:pass

            now=time.monotonic()
            first,visible,total=self._scroll_canvas_metrics(canvas)
            max_first=max(0.0,1.0-visible)
            state=getattr(scrollable,"_zk_scroll_state",None)
            if not isinstance(state,dict):
                state={"target":first,"job":None,"last_input":0.0}
                setattr(scrollable,"_zk_scroll_state",state)

            # If the user paused, re-anchor the target to the real current
            # position so keyboard/scrollbar changes are respected.
            if now-float(state.get("last_input",0.0) or 0.0)>.20:
                state["target"]=first

            px_per_step=72.0
            target=float(state.get("target",first) or first)+(float(step)*px_per_step/max(1.0,total))
            state["target"]=max(0.0,min(max_first,target))
            state["last_input"]=now
            self._mark_fast_scroll()

            def tick():
                state["job"]=None
                try:
                    if not canvas.winfo_exists():return
                    cur_first,cur_visible,_=self._scroll_canvas_metrics(canvas)
                    max_cur=max(0.0,1.0-cur_visible)
                    target=max(0.0,min(max_cur,float(state.get("target",cur_first))))
                    diff=target-cur_first
                    if abs(diff)<0.00035:
                        canvas.yview_moveto(target)
                        return
                    # Distance-aware interpolation: small moves feel soft;
                    # big wheel bursts catch up quickly without teleporting.
                    d=abs(diff)
                    alpha=.28 if d<.035 else (.38 if d<.12 else .50)
                    nxt=cur_first+diff*alpha
                    canvas.yview_moveto(max(0.0,min(max_cur,nxt)))
                    state["job"]=self.after(12,tick)
                except Exception:
                    state["job"]=None

            if state.get("job") is None:
                try:state["job"]=self.after(1,tick)
                except Exception:tick()
            return "break"
        except Exception:
            return "break"

'''
regex_rep(
    r'    def _queue_scroll_step\(self, scrollable, step\):\n.*?(?=    def _install_global_scroll_router\(self\):\n)',
    new_queue,
    'smooth target scroll core'
)

# The router remains useful, but now there are no CTkScrollableFrame global
# handlers underneath it. It is the only owner of wheel events in the app.
for required in (
    'class ZKSmoothScrollFrame(ctk.CTkFrame):',
    'def _open_support_page(self)',
    'def _copy_support_link(self)',
    'def _install_global_scroll_router(self)',
    'def _queue_scroll_step(self, scrollable, step)',
):
    if required not in s:
        raise SystemExit('v3.19.0 patch: required surface missing: '+required)
if 'ctk.CTkScrollableFrame(' in s:
    raise SystemExit('v3.19.0 patch: CTkScrollableFrame still present after replacement')

path.write_text(s, encoding='utf-8')
print('Applied ZKStrap v3.19.0 native smooth scroll patch')
