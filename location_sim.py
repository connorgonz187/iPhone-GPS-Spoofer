"""
location_sim.py — iOS geofence simulator for home automation testing

Usage:
    python location_sim.py enter      # Simulate arriving home
    python location_sim.py leave      # Simulate leaving home
    python location_sim.py restore    # Return to real GPS

Prerequisites:
    1. iPhone connected via USB, Developer Mode ON
    2. Run start_tunneld.bat as Administrator (keep open)
    3. pip install -r requirements.txt
    4. pymobiledevice3 usbmux pair   (one-time pairing)
"""

import sys
import asyncio
import tomllib
import logging
from pathlib import Path

from pymobiledevice3.tunneld.api import get_tunneld_devices, TUNNELD_DEFAULT_ADDRESS
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys.executable).parent
else:
    _BASE_DIR = Path(__file__).parent

CONFIG_PATH = _BASE_DIR / "config.toml"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(
            "config.toml not found.\n"
            "Copy config.toml.example to config.toml and fill in your home coordinates."
        )
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


async def get_device(udid: str | None = None):
    try:
        devices = await get_tunneld_devices(TUNNELD_DEFAULT_ADDRESS)
    except Exception:
        sys.exit(
            "Cannot reach tunneld.\n"
            "Open start_tunneld.bat as Administrator and keep it running."
        )

    if not devices:
        sys.exit(
            "tunneld is running but no devices found.\n"
            "Ensure the iPhone is plugged in via USB and you tapped 'Trust'."
        )

    if udid:
        match = next((d for d in devices if d.udid == udid), None)
        if match is None:
            for d in devices:
                await d.close()
            sys.exit(f"Device '{udid}' not found. Available: {[d.udid for d in devices]}")
        for d in devices:
            if d is not match:
                await d.close()
        return match

    selected = devices[0]
    for d in devices[1:]:
        await d.close()
    return selected


async def _run(lat: float, lon: float | None, clear: bool = False, on_success=None):
    rsd = await get_device()
    log.info("Connected: %s", rsd.udid)

    # Retry once on DTServiceHub "No such service" (known iOS 26 intermittent issue)
    for attempt in range(2):
        try:
            async with DvtProvider(rsd) as dvt, LocationSimulation(dvt) as loc:
                if clear:
                    await loc.clear()
                    log.info("Simulation cleared — device is back on real GPS")
                else:
                    await loc.set(lat, lon)
                    log.info("Location set to %.6f, %.6f", lat, lon)
                    if on_success:
                        on_success()
                    log.info("Holding location...")
                    while True:
                        await asyncio.sleep(1)
            return
        except Exception as e:
            if attempt == 0 and "No such service" in str(e):
                log.warning("DTServiceHub not ready, retrying in 2s...")
                await asyncio.sleep(2)
                continue
            sys.exit(f"Failed: {e}\nEnsure Developer Mode is ON and tunneld is running as Administrator.")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("enter", "leave", "restore"):
        print("Usage: python location_sim.py [enter|leave|restore]")
        sys.exit(1)

    cfg = load_config()
    cmd = sys.argv[1]

    if cmd == "enter":
        lat = cfg["home"]["latitude"]
        lon = cfg["home"]["longitude"]
        log.info("Simulating ENTER HOME (%.6f, %.6f)", lat, lon)
        asyncio.run(_run(lat, lon))

    elif cmd == "leave":
        lat = cfg["away"]["latitude"]
        lon = cfg["away"]["longitude"]
        log.info("Simulating LEAVE HOME (%.6f, %.6f)", lat, lon)
        asyncio.run(_run(lat, lon))

    elif cmd == "restore":
        log.info("Restoring real GPS location")
        asyncio.run(_run(0, 0, clear=True))


if __name__ == "__main__":
    main()