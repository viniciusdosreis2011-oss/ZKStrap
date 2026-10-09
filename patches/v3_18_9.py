from pathlib import Path
import os, re

root = Path(os.environ.get('ZK_SOURCE_DIR', '.'))
path = root / 'ZKStrap_v3_18_0.py'
s = path.read_text(encoding='utf-8')


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit(f'v3.18.9 patch: pattern not found: {label}')
    s = s.replace(old, new, count)


def regex_rep(pattern, replacement, label, flags=re.S):
    global s
    ns, n = re.subn(pattern, replacement, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'v3.18.9 patch: regex pattern not found/ambiguous: {label} ({n})')
    s = ns


rep('APP_VERSION = "3.18.8"', 'APP_VERSION = "3.18.9"', 'version')
rep('BUILD_TIMESTAMP = "Startup Hotfix + Callback Validation"', 'BUILD_TIMESTAMP = "Burst Safe Scroll + Windows Repaint"', 'timestamp')

new_scroll_core = r'''    def _scroll_canvas_metrics(self, canvas):
        try:
            first,last=canvas.yview()
        except Exception:
            first,last=0.0,1.0
        visible=max(0.0,min(1.0,float(last)-float(first)))
        total=1.0
        try:
            raw=canvas.cget("scrollregion")
            vals=[float(v) for v in canvas.tk.splitlist(raw)]
            if len(vals)>=4:total=max(1.0,vals[3]-vals[1])
        except Exception:
            try:
                box=canvas.bbox("all")
                if box:total=max(1.0,float(box[3]-box[1]))
            except Exception:pass
        return float(first),visible,total

    def _force_windows_repaint(self):
        """Invalidate the whole Tk toplevel on Windows to clear stale GDI/CTk pixels."""
        try:self.update_idletasks()
        except Exception:pass
        if os.name!="nt":return
        try:
            import ctypes
            hwnd=int(self.winfo_id())
            RDW_INVALIDATE=0x0001
            RDW_ERASE=0x0004
            RDW_ALLCHILDREN=0x0080
            RDW_UPDATENOW=0x0100
            ctypes.windll.user32.RedrawWindow(hwnd,0,0,RDW_INVALIDATE|RDW_ERASE|RDW_ALLCHILDREN|RDW_UPDATENOW)
        except Exception:
            try:self.update()
            except Exception:pass

    def _queue_scroll_step(self, scrollable, step):
        """Adaptive scroll: normal wheel is immediate; rapid bursts render only the final target."""
        try:
            if scrollable is None or not step:return "break"
            canvas=getattr(scrollable,"_parent_canvas",None)
            if canvas is None or not canvas.winfo_exists():return "break"

            now=time.monotonic()
            first,visible,total=self._scroll_canvas_metrics(canvas)
            max_first=max(0.0,1.0-visible)
            state=getattr(scrollable,"_zk_scroll_state",None)
            if not isinstance(state,dict):
                state={
                    "target":first,"last_input":0.0,"burst":0,
                    "settle":None,"paint_job":None,"last_paint":0.0
                }
                setattr(scrollable,"_zk_scroll_state",state)

            gap=now-float(state.get("last_input",0.0) or 0.0)
            if gap>.16:
                state["target"]=first
                state["burst"]=0
            elif gap<.045:
                state["burst"]=min(20,int(state.get("burst",0))+1)
            else:
                state["burst"]=max(0,int(state.get("burst",0))-1)

            pixel_delta=float(step)*78.0
            target=float(state.get("target",first) or first)+(pixel_delta/max(1.0,total))
            state["target"]=max(0.0,min(max_first,target))
            state["last_input"]=now
            self._mark_fast_scroll()

            def paint(final=False):
                state["paint_job"]=None
                try:
                    if not canvas.winfo_exists():return
                    _,vis,_=self._scroll_canvas_metrics(canvas)
                    pos=max(0.0,min(max(0.0,1.0-vis),float(state.get("target",0.0))))
                    canvas.yview_moveto(pos)
                    state["last_paint"]=time.monotonic()
                    canvas.update_idletasks()
                    if final:
                        self._force_windows_repaint()
                except Exception:
                    pass

            def settle():
                state["settle"]=None
                paint(True)
                state["burst"]=0

            # Any new wheel input replaces the previous settle timer.
            try:
                old=state.get("settle")
                if old is not None:self.after_cancel(old)
            except Exception:pass
            try:state["settle"]=self.after(72,settle)
            except Exception:state["settle"]=None

            rapid=int(state.get("burst",0))>=3
            if rapid:
                # Critical behavior: while the wheel is being spammed we DO NOT
                # move the canvas every event. Only the newest target survives.
                return "break"

            # Normal scrolling stays responsive but is capped to one live paint
            # roughly every 28 ms. A final Windows repaint still runs on settle.
            since=now-float(state.get("last_paint",0.0) or 0.0)
            if since>=.028:
                paint(False)
            elif state.get("paint_job") is None:
                delay=max(1,int((.028-since)*1000))
                try:state["paint_job"]=self.after(delay,lambda:paint(False))
                except Exception:state["paint_job"]=None
            return "break"
        except Exception:
            return "break"

'''

regex_rep(
    r'    def _scroll_canvas_metrics\(self, canvas\):\n.*?(?=    def _install_global_scroll_router\(self\):\n)',
    new_scroll_core,
    'burst-safe scroll core'
)

# Keep support callbacks protected after the visual-patch regression.
required_text = (
    'def _open_support_page(self)',
    'def _copy_support_link(self)',
    'def _install_global_scroll_router(self)',
    'def _force_windows_repaint(self)',
)
for marker in required_text:
    if marker not in s:
        raise SystemExit('v3.18.9 patch: required method missing after patch: '+marker)

path.write_text(s, encoding='utf-8')
print('Applied ZKStrap v3.18.9 burst-safe scroll patch')
