"""
app.py — Unified launcher for Location Simulator

Launches Apple Devices, tunneld, and the GUI in one process.
Close the GUI window to stop everything.
"""

import subprocess
import threading
import time
import urllib.request


def launch_apple_devices():
    try:
        subprocess.Popen(
            ["explorer.exe", r"shell:AppsFolder\AppleInc.AppleDevices_nzyj5cx40ttqa!App"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


tunneld_error = None

def start_tunneld():
    global tunneld_error
    try:
        import uvicorn
        _original_run = uvicorn.run
        def _patched_run(*args, **kwargs):
            kwargs["log_config"] = None
            return _original_run(*args, **kwargs)
        uvicorn.run = _patched_run

        from pymobiledevice3.tunneld.server import TunneldRunner
        TunneldRunner.create("127.0.0.1", 49151)
    except Exception as e:
        tunneld_error = str(e)


def wait_for_tunneld(gui):
    """Poll until tunneld is accepting connections, then enable the GUI."""
    for _ in range(30):
        if tunneld_error:
            gui._set_status(f"Error: tunneld failed — {tunneld_error}")
            return
        try:
            urllib.request.urlopen("http://127.0.0.1:49151/hello", timeout=1)
            gui._set_status("Status: Ready — right-click the map to set a target")
            gui._re_enable_button()
            return
        except Exception:
            time.sleep(1)
    gui._set_status("Error: tunneld did not start. Try running as Administrator.")


def kill_apple_devices():
    try:
        subprocess.run(
            ["taskkill", "/IM", "AppleDevices.exe", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def main():
    # Launch Apple Devices (required for USB detection)
    launch_apple_devices()
    time.sleep(3)

    # Start tunneld in a daemon thread
    tunneld_thread = threading.Thread(target=start_tunneld, daemon=True)
    tunneld_thread.start()

    # Launch the GUI
    import customtkinter
    from gui_sim import LocationGUI

    customtkinter.set_appearance_mode("dark")
    app = LocationGUI()

    # Disable teleport until tunneld is ready
    app.status_label.configure(text="Status: Starting tunneld...")
    app.teleport_btn.configure(state="disabled")

    # Poll for tunneld readiness in background
    ready_thread = threading.Thread(target=wait_for_tunneld, args=(app,), daemon=True)
    ready_thread.start()

    app.mainloop()

    # Cleanup when GUI is closed
    kill_apple_devices()


if __name__ == "__main__":
    main()
