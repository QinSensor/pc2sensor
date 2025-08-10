# bluvib_scanner.py
import asyncio
import threading
import uuid
import tkinter as tk
from tkinter import ttk
from bleak import BleakScanner

# ---- configure target UUID (the BluVib service UUID you expect) ----
TARGET_UUID_STR = "1c930001-d459-11e7-9296-b8e856369374"
TARGET_UUID = uuid.UUID(TARGET_UUID_STR)
TARGET_UUID_LE = TARGET_UUID.bytes_le  # 16 bytes little-endian (what appears in raw AD)

class BluVibScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BluVib Scanner (advertised UUID / name match)")

        cols = ("address", "name", "rssi", "uuids", "matched_by")
        self.tree = ttk.Treeview(root, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=140 if c != "rssi" else 70)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=8, pady=(0,8))
        tk.Button(btn_frame, text="Scan (5s)", command=self.start_scan).pack(side="left")
        tk.Button(btn_frame, text="Scan (continuous 5s)", command=self.start_continuous_scan).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Stop continuous", command=self.stop_continuous_scan).pack(side="left")

        self.scanning = False
        self._continuous = False
        self._scan_thread = None

        # Double click to print details (or later open editor)
        self.tree.bind("<Double-1>", self.on_double_click)

    def start_scan(self):
        if self.scanning:
            return
        threading.Thread(target=self.scan_devices_once, daemon=True).start()

    def start_continuous_scan(self):
        if self._continuous:
            return
        self._continuous = True
        threading.Thread(target=self._continuous_scan_loop, daemon=True).start()

    def stop_continuous_scan(self):
        self._continuous = False

    def _continuous_scan_loop(self):
        while self._continuous:
            self.scan_devices_once()
            # small pause so GUI remains responsive and to avoid continuous CPU
            threading.Event().wait(1.0)

    def scan_devices_once(self):
        # run the async scan in this thread
        try:
            self.scanning = True
            results = asyncio.run(BleakScanner.discover(timeout=5, return_adv=True))
        except Exception as e:
            print("Scan error:", e)
            results = {}
        finally:
            self.scanning = False

        found = []
        for addr, dev_adv in results.items():
            try:
                # bleak returns either (device, adv_data) depending on platform/version
                if isinstance(dev_adv, tuple) or isinstance(dev_adv, list):
                    device, adv = dev_adv
                else:
                    # some versions return a BLEDevice object as value
                    device = dev_adv
                    adv = None
            except Exception:
                device = dev_adv
                adv = None

            name = ""
            rssi = "N/A"
            uuids_list = []
            matched_by = []

            # Try to get name and RSSI in a tolerant way
            try:
                if adv:
                    name = getattr(adv, "local_name", None) or getattr(device, "name", None) or ""
                    rssi = getattr(adv, "rssi", None) or getattr(device, "rssi", None) or "N/A"
                    uuids_list = getattr(adv, "service_uuids", None) or []
                else:
                    name = getattr(device, "name", None) or ""
                    rssi = getattr(device, "rssi", None) or "N/A"
                    uuids_list = []
            except Exception:
                name = getattr(device, "name", None) or ""
                rssi = getattr(device, "rssi", None) or "N/A"
                uuids_list = []

            # 1) Name prefix match
            if isinstance(name, str) and name.startswith("BluVib"):
                matched_by.append("name")

            # 2) service_uuids textual match
            try:
                for u in uuids_list:
                    if not u:
                        continue
                    if u.lower() == TARGET_UUID_STR.lower():
                        matched_by.append("service_uuid")
                        break
            except Exception:
                pass

            # 3) check service_data and manufacturer_data raw bytes for little-endian UUID sequence
            # adv.service_data -> dict or None; adv.manufacturer_data -> dict
            if adv:
                # service_data: keys might be str->bytes or uuid->bytes; values are bytes
                svc_data = getattr(adv, "service_data", {}) or {}
                try:
                    for k, v in svc_data.items():
                        # k could be a uuid string
                        if isinstance(k, str) and k.lower() == TARGET_UUID_STR.lower():
                            matched_by.append("service_data_key")
                            break
                        if isinstance(v, (bytes, bytearray)) and TARGET_UUID_LE in v:
                            matched_by.append("service_data_raw")
                            break
                except Exception:
                    pass

                man_data = getattr(adv, "manufacturer_data", {}) or {}
                try:
                    for k, v in man_data.items():
                        if isinstance(v, (bytes, bytearray)) and TARGET_UUID_LE in v:
                            matched_by.append("manufacturer_raw")
                            break
                except Exception:
                    pass

            # final decision: if matched_by not empty -> it's a BluVib (advertised)
            if matched_by:
                found.append((device.address, name, rssi, ", ".join(uuids_list), ", ".join(sorted(set(matched_by)))))

        # update GUI on main thread
        self.root.after(0, lambda: self.update_table(found))

    def update_table(self, rows):
        # clear
        for item in self.tree.get_children():
            self.tree.delete(item)
        # insert
        for addr, name, rssi, uuids, matched in rows:
            self.tree.insert("", tk.END, values=(addr, name, rssi, uuids, matched))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        address, name = values[0], values[1]
        print(f"Double-clicked: address={address}, name={name}")
        # Here you could open your MultiParamEditor(address), etc.

if __name__ == "__main__":
    root = tk.Tk()
    app = BluVibScannerApp(root)
    root.mainloop()
