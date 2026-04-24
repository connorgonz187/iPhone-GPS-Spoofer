import sys
import customtkinter
import tkintermapview
import asyncio
import threading
from pathlib import Path
from location_sim import _run

if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys.executable).parent
else:
    _BASE_DIR = Path(__file__).parent

class LocationGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Location Picker")
        self.geometry("800x600")
        
        self.sim_thread = None
        self.selected_coords = None
        self._spoof_loop = None

        # --- UI Layout ---
        # 1. The Map Widget
        cache_db = str(_BASE_DIR / "map_cache.db")
        self.map_widget = tkintermapview.TkinterMapView(self, corner_radius=10, database_path=cache_db)
        self.map_widget.pack(fill="both", expand=True, padx=20, pady=20)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga")
        self.map_widget.set_position(39.6895, -84.1688)  # Kettering, OH
        self.map_widget.set_zoom(13)

        # Allow user to right click to set a marker
        self.map_widget.add_right_click_menu_command(label="Set Spoof Target",
                                                     command=self.target_selected,
                                                     pass_coords=True)

        # 2. Control Panel
        self.status_label = customtkinter.CTkLabel(self, text="Status: Waiting for target...", font=("Arial", 14))
        self.status_label.pack(pady=5)

        btn_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.teleport_btn = customtkinter.CTkButton(btn_frame, text="Teleport to Target", command=self.start_spoofing)
        self.teleport_btn.pack(side="left", padx=5)

        self.reset_btn = customtkinter.CTkButton(btn_frame, text="Reset Location", command=self.reset_location, fg_color="gray")
        self.reset_btn.pack(side="left", padx=5)

    def target_selected(self, coords):
        """Called when you right-click the map"""
        self.selected_coords = coords # tuple: (lat, lon)
        self.map_widget.delete_all_marker()
        self.map_widget.set_marker(coords[0], coords[1], text="Spoof Target")
        self.status_label.configure(text=f"Target: {coords[0]:.5f}, {coords[1]:.5f}")

    def _stop_current_spoof(self):
        """Stop any running spoof thread."""
        if self._spoof_loop and self._spoof_loop.is_running():
            self._spoof_loop.call_soon_threadsafe(self._spoof_loop.stop)
            if self.sim_thread:
                self.sim_thread.join(timeout=3)
        self._spoof_loop = None

    def start_spoofing(self):
        if not self.selected_coords:
            self.status_label.configure(text="Error: Right-click the map to set a target first!")
            return

        self._stop_current_spoof()

        lat, lon = self.selected_coords
        self.status_label.configure(text="Status: Connecting to device...")
        self.teleport_btn.configure(state="disabled")

        self.sim_thread = threading.Thread(target=self.run_async_spoof, args=(lat, lon), daemon=True)
        self.sim_thread.start()

    def reset_location(self):
        self._stop_current_spoof()
        self.status_label.configure(text="Status: Resetting location...")
        self.reset_btn.configure(state="disabled")

        self.sim_thread = threading.Thread(target=self.run_async_reset, daemon=True)
        self.sim_thread.start()

    def _set_status(self, text):
        self.after(0, lambda: self.status_label.configure(text=text))

    def _re_enable_button(self):
        self.after(0, lambda: self.teleport_btn.configure(state="normal"))

    def _re_enable_reset(self):
        self.after(0, lambda: self.reset_btn.configure(state="normal"))

    def run_async_spoof(self, lat, lon):
        def on_success():
            self._set_status("Status: Location Locked! (Rubber-banding prevented)")
            self._re_enable_button()

        try:
            loop = asyncio.new_event_loop()
            self._spoof_loop = loop
            loop.run_until_complete(_run(lat, lon, clear=False, on_success=on_success))
        except SystemExit as e:
            self._set_status(f"Error: {e}")
            self._re_enable_button()
        except Exception as e:
            if "Event loop stopped" not in str(e) and "Event loop is closed" not in str(e):
                self._set_status(f"Error: {e}")
            self._re_enable_button()

    def run_async_reset(self):
        try:
            asyncio.run(_run(0, 0, clear=True))
            self._set_status("Status: Location reset to real GPS")
        except SystemExit as e:
            self._set_status(f"Error: {e}")
        except Exception as e:
            self._set_status(f"Error: {e}")
        self._re_enable_reset()

if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    app = LocationGUI()
    app.mainloop()