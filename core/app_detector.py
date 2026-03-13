"""
Foreground application detector — polls the active window and fires
a callback when the foreground app changes.
Windows: GetForegroundWindow + QueryFullProcessImageNameW (with UWP resolution).
macOS:   NSWorkspace.sharedWorkspace().frontmostApplication().
"""

import os
import sys
import threading
import time


# ==================================================================
# Platform-specific get_foreground_exe()
# ==================================================================

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as wt

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    MAX_PATH = 260

    user32.GetForegroundWindow.restype = wt.HWND
    user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
    user32.GetWindowThreadProcessId.restype = wt.DWORD

    kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    kernel32.OpenProcess.restype = wt.HANDLE
    kernel32.CloseHandle.argtypes = [wt.HANDLE]
    kernel32.CloseHandle.restype = wt.BOOL

    kernel32.QueryFullProcessImageNameW.argtypes = [
        wt.HANDLE, wt.DWORD,
        ctypes.c_wchar_p, ctypes.POINTER(wt.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wt.BOOL

    user32.FindWindowExW.argtypes = [wt.HWND, wt.HWND, wt.LPCWSTR, wt.LPCWSTR]
    user32.FindWindowExW.restype = wt.HWND

    user32.GetClassNameW.argtypes = [wt.HWND, ctypes.c_wchar_p, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int

    WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    user32.EnumChildWindows.argtypes = [wt.HWND, WNDENUMPROC, wt.LPARAM]
    user32.EnumChildWindows.restype = wt.BOOL

    def _exe_from_pid(pid: int) -> str | None:
        hproc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not hproc:
            return None
        try:
            buf = ctypes.create_unicode_buffer(MAX_PATH)
            size = wt.DWORD(MAX_PATH)
            if kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value)
        finally:
            kernel32.CloseHandle(hproc)
        return None

    def _resolve_uwp_child(hwnd) -> str | None:
        host_pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(host_pid))
        result = [None]

        def _enum_cb(child_hwnd, _lparam):
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(child_hwnd, cls, 256)
            if cls.value == "Windows.UI.Core.CoreWindow":
                child_pid = wt.DWORD()
                user32.GetWindowThreadProcessId(child_hwnd, ctypes.byref(child_pid))
                if child_pid.value != host_pid.value:
                    exe = _exe_from_pid(child_pid.value)
                    if exe:
                        result[0] = exe
                        return False
            return True

        user32.EnumChildWindows(hwnd, WNDENUMPROC(_enum_cb), 0)
        return result[0]

    def get_foreground_exe() -> str | None:
        """Return the .exe filename of the current foreground window, or None."""
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return None
        exe = _exe_from_pid(pid.value)
        if not exe:
            return None
        if exe.lower() == "applicationframehost.exe":
            real = _resolve_uwp_child(hwnd)
            if real:
                return real
        return exe

elif sys.platform == "darwin":
    def get_foreground_exe() -> str | None:
        """Return the bundle-exe name of the frontmost app on macOS."""
        try:
            from AppKit import NSWorkspace
            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if app is None:
                return None
            url = app.executableURL()
            if url:
                return os.path.basename(url.path())
            ident = app.bundleIdentifier()
            return ident or app.localizedName()
        except Exception:
            return None

elif sys.platform.startswith("linux"):
    def get_foreground_exe() -> str | None:
        """Return the executable name of the focused window on Linux."""
        try:
            # First try X11 approach
            display = os.environ.get("DISPLAY")
            if display:
                try:
                    from Xlib import X, display as xdisplay
                    d = xdisplay.Display()
                    # Get the currently focused window
                    focus = d.get_input_focus().focus
                    if focus and hasattr(focus, 'get_wm_class'):
                        wm_class = focus.get_wm_class()
                        if wm_class:
                            # wm_class returns (instance, class)
                            # Return the instance name (usually the application name)
                            return wm_class[0] if wm_class[0] else wm_class[1]
                    
                    # Try to get the _NET_ACTIVE_WINDOW property
                    root = d.screen().root
                    net_active_window = d.intern_atom('_NET_ACTIVE_WINDOW')
                    active_window_id = root.get_full_property(net_active_window, X.AnyPropertyType)
                    
                    if active_window_id and active_window_id.value:
                        window_id = active_window_id.value[0]
                        active_window = d.create_resource_object('window', window_id)
                        
                        # Try _NET_WM_PID first
                        net_wm_pid = d.intern_atom('_NET_WM_PID')
                        pid_prop = active_window.get_full_property(net_wm_pid, X.AnyPropertyType)
                        
                        if pid_prop and pid_prop.value:
                            pid = pid_prop.value[0]
                            # Read process name from /proc
                            try:
                                with open(f"/proc/{pid}/comm", 'r') as f:
                                    return f.read().strip()
                            except (IOError, FileNotFoundError):
                                pass
                        
                        # Fallback to WM_CLASS
                        wm_class = active_window.get_wm_class()
                        if wm_class:
                            return wm_class[0] if wm_class[0] else wm_class[1]
                        
                except Exception:
                    pass
            
            # Wayland fallback - try to get info from /proc
            # This is less reliable but might work in some cases
            wayland_display = os.environ.get("WAYLAND_DISPLAY")
            if wayland_display:
                # On Wayland, we can't easily get the focused window
                # Try using D-Bus to query window managers that support it
                try:
                    import subprocess
                    # Try GNOME Shell's D-Bus interface (GNOME on Wayland)
                    result = subprocess.run([
                        'gdbus', 'call', '--session',
                        '--dest', 'org.gnome.Shell',
                        '--object-path', '/org/gnome/Shell',
                        '--method', 'org.gnome.Shell.Eval',
                        'global.display.focus_window.get_wm_class()'
                    ], capture_output=True, text=True, timeout=0.5)
                    
                    if result.returncode == 0:
                        # Parse the result - it's in format: (true, '"AppName"')
                        output = result.stdout.strip()
                        if '"' in output:
                            # Extract the app name between quotes
                            start = output.find('"') + 1
                            end = output.rfind('"')
                            if start > 0 and end > start:
                                return output[start:end]
                except Exception:
                    pass
                
                # Another fallback: try KDE/KWin D-Bus interface
                try:
                    import subprocess
                    result = subprocess.run([
                        'qdbus', 'org.kde.KWin', '/KWin',
                        'org.kde.KWin.queryWindowInfo'
                    ], capture_output=True, text=True, timeout=0.5)
                    
                    if result.returncode == 0:
                        # Parse KWin output for application name
                        for line in result.stdout.split('\n'):
                            if 'resourceClass' in line or 'resourceName' in line:
                                parts = line.split(':')
                                if len(parts) > 1:
                                    return parts[1].strip()
                except Exception:
                    pass
                    
        except Exception:
            pass
        return None

else:
    def get_foreground_exe() -> str | None:
        return None


class AppDetector:
    """
    Polls the foreground window every *interval* seconds.
    Calls ``on_change(exe_name: str)`` when the foreground app changes.
    """

    def __init__(self, on_change, interval: float = 0.3):
        self._on_change = on_change
        self._interval = interval
        self._last_exe: str | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._poll, daemon=True, name="AppDetector")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    # ------------------------------------------------------------------
    def _poll(self):
        while not self._stop.is_set():
            try:
                exe = get_foreground_exe()
                if exe and exe != self._last_exe:
                    self._last_exe = exe
                    self._on_change(exe)
            except Exception:
                pass
            self._stop.wait(self._interval)
