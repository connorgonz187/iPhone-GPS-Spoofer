import customtkinter
import tkintermapview
import asyncio
import threading
from pathlib import Path
from location_sim import _run

class LocationGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Location Picker")
        self.geometry("800x600")
        
        # State variable to track the active simulation thread
        self.sim_thread = None
        self.selected_coords = None

        # --- UI Layout ---
        # 1. The Map Widget
        cache_db = str(Path(__file__).parent / "map_cache.db")
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

        self.teleport_btn = customtkinter.CTkButton(self, text="Teleport to Target", command=self.start_spoofing)
        self.teleport_btn.pack(pady=10)

    def target_selected(self, coords):
        """Called when you right-click the map"""
        self.selected_coords = coords # tuple: (lat, lon)
        self.map_widget.delete_all_marker()
        self.map_widget.set_marker(coords[0], coords[1], text="Spoof Target")
        self.status_label.configure(text=f"Target: {coords[0]:.5f}, {coords[1]:.5f}")

    def start_spoofing(self):
        """Spins up the async connection in a background thread"""
        if not self.selected_coords:
            self.status_label.configure(text="Error: Right-click the map to set a target first!")
            return

        lat, lon = self.selected_coords
        self.status_label.configure(text="Status: Injecting Location...")
        
        # Run the asyncio loop in a separate thread so the GUI doesn't freeze
        self.sim_thread = threading.Thread(target=self.run_async_spoof, args=(lat, lon), daemon=True)
        self.sim_thread.start()
        
        self.status_label.configure(text="Status: Location Locked! (Rubber-banding prevented)")

    def run_async_spoof(self, lat, lon):
        """Wrapper to run your existing async function"""
        # Note: Ensure the _run function in location_sim.py has the `while True` loop we added earlier!
        asyncio.run(_run(lat, lon, clear=False))

if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    app = LocationGUI()
    app.mainloop()