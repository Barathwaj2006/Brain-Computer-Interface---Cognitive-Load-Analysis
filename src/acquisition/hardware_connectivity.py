import os
import sys
import time
import socket
import logging
import datetime
import threading
import subprocess

logger = logging.getLogger("HardwareConnectivity")

class HardwareConnectivityManager:
    """
    Manages detection of:
    1. Active Wi-Fi network (SSID, Signal, Channel, Adapter) connected to the host laptop.
    2. Active and paired Bluetooth devices connected to the host laptop.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self._wifi_info = {
            "connected": False,
            "ssid": "Not Connected",
            "signal": "0%",
            "radio_type": "Unknown",
            "band": "Unknown",
            "adapter": "Wi-Fi",
            "state": "disconnected",
            "ip": "127.0.0.1"
        }
        self._bluetooth_info = {
            "adapter_present": False,
            "adapter_name": "Bluetooth Adapter",
            "adapter_status": "Unknown",
            "connected_device": None,
            "connected_devices": [],
            "paired_devices": [],
            "bluetooth_ports": []
        }
        self._manual_connected_device = None
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            self._running = True
            # Initial sync update
            self.refresh_all()
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()

    def set_connected_device(self, name: str, mac: str = None) -> dict:
        """Explicitly set or bind a connected Bluetooth device into the active session."""
        with self.lock:
            self._manual_connected_device = {
                "name": name,
                "mac": mac or "",
                "status": "Connected (Active)",
                "connected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self._bluetooth_info["connected_device"] = name
            existing = [d for d in self._bluetooth_info["connected_devices"] if d["name"] != name]
            existing.insert(0, {
                "name": name,
                "status": "Connected (Active)",
                "id": mac or "PAIRED_REGISTRY_BT"
            })
            self._bluetooth_info["connected_devices"] = existing
            return {
                "wifi": dict(self._wifi_info),
                "bluetooth": dict(self._bluetooth_info)
            }

    def disconnect_device(self) -> dict:
        """Disconnect manual Bluetooth device binding and return to auto-scan."""
        with self.lock:
            self._manual_connected_device = None
            self._bluetooth_info["connected_device"] = None
            self._bluetooth_info["connected_devices"] = []
            return {
                "wifi": dict(self._wifi_info),
                "bluetooth": dict(self._bluetooth_info)
            }

    def _poll_loop(self):
        while self._running:
            try:
                self.refresh_all()
            except Exception as e:
                logger.debug(f"Error refreshing hardware connectivity: {e}")
            time.sleep(3.0)

    def refresh_all(self):
        wifi = self._detect_wifi_network()
        bt = self._detect_bluetooth_devices()
        with self.lock:
            self._wifi_info = wifi
            self._bluetooth_info = bt
            if self._manual_connected_device:
                self._bluetooth_info["connected_device"] = self._manual_connected_device["name"]
                if not any(d["name"] == self._manual_connected_device["name"] for d in self._bluetooth_info["connected_devices"]):
                    self._bluetooth_info["connected_devices"].insert(0, {
                        "name": self._manual_connected_device["name"],
                        "status": "Connected (Active)",
                        "id": self._manual_connected_device.get("mac", "")
                    })

    def get_status(self) -> dict:
        with self.lock:
            return {
                "wifi": dict(self._wifi_info),
                "bluetooth": dict(self._bluetooth_info)
            }

    def get_diagnostic_summary(self) -> dict:
        st = self.get_status()
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "os_platform": sys.platform,
            "wifi_telemetry": st["wifi"],
            "bluetooth_telemetry": {
                "adapter": st["bluetooth"]["adapter_name"],
                "adapter_status": st["bluetooth"]["adapter_status"],
                "adapter_present": st["bluetooth"]["adapter_present"],
                "connected_device": st["bluetooth"]["connected_device"],
                "connected_devices": st["bluetooth"]["connected_devices"],
                "paired_devices_count": len(st["bluetooth"]["paired_devices"]),
                "top_paired_devices": st["bluetooth"]["paired_devices"][:8]
            }
        }

    def _detect_wifi_network(self) -> dict:
        info = {
            "connected": False,
            "ssid": "Not Connected",
            "signal": "0%",
            "radio_type": "Unknown",
            "band": "Unknown",
            "adapter": "Wi-Fi",
            "state": "disconnected",
            "ip": self._get_primary_ip()
        }

        if sys.platform == "win32":
            try:
                res = subprocess.run(
                    ["netsh", "wlan", "show", "interfaces"],
                    capture_output=True, text=True, timeout=2.5
                )
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if ":" not in line:
                            continue
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip()
                        if k == "SSID" and not k.startswith("SSID name") and not k.startswith("BSSID"):
                            info["ssid"] = v
                            info["connected"] = True
                        elif k == "State":
                            info["state"] = v
                            if v.lower() == "connected":
                                info["connected"] = True
                        elif k == "Signal":
                            info["signal"] = v
                        elif k == "Radio type":
                            info["radio_type"] = v
                        elif k == "Band":
                            info["band"] = v
                        elif k == "Description":
                            info["adapter"] = v
            except Exception as e:
                logger.debug(f"Failed netsh wlan check: {e}")

        return info

    def _get_primary_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _detect_bluetooth_devices(self) -> dict:
        bt = {
            "adapter_present": False,
            "adapter_name": "Bluetooth Radio",
            "adapter_status": "Inactive",
            "connected_device": None,
            "connected_devices": [],
            "paired_devices": [],
            "bluetooth_ports": []
        }

        if sys.platform != "win32":
            return bt

        # 1. Check Bluetooth Controller Adapter & Currently Connected Devices via PowerShell (Base64 EncodedCommand)
        try:
            import base64
            ps_script = """
            $adapter = Get-PnpDevice -PresentOnly | Where-Object { $_.Class -eq 'Bluetooth' -and $_.FriendlyName -match 'Adapter|Radio|Wireless' } | Select-Object -First 1 FriendlyName, Status
            $connected = Get-PnpDevice -PresentOnly | Where-Object {
                ($_.InstanceId -like 'BTHENUM\\DEV_*' -or $_.InstanceId -like 'BTHLE\\DEV_*' -or ($_.Class -eq 'Bluetooth' -and $_.FriendlyName -notmatch 'Enumerator|Adapter|Service|Transport|Profile|Realtek|Intel|Protocol|Bridge') -or (($_.Class -eq 'AudioEndpoint' -or $_.Class -eq 'MEDIA') -and ($_.FriendlyName -like '*Bluetooth*' -or $_.FriendlyName -like '*Hands-Free*')))
            } | Select-Object FriendlyName, Status, InstanceId
            $ports = Get-PnpDevice -PresentOnly | Where-Object { $_.Class -eq 'Ports' -and ($_.FriendlyName -like '*Bluetooth*' -or $_.InstanceId -like 'BTHENUM\\*') } | Select-Object FriendlyName, Status
            
            [PSCustomObject]@{
                AdapterName = if ($adapter) { $adapter.FriendlyName } else { "Realtek Wireless Bluetooth Adapter" }
                AdapterStatus = if ($adapter) { $adapter.Status } else { "OK" }
                Connected = @($connected)
                Ports = @($ports)
            } | ConvertTo-Json -Depth 3
            """
            encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
            res = subprocess.run(
                ["powershell", "-NoProfile", "-EncodedCommand", encoded],
                capture_output=True, text=True, timeout=3.5
            )
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout)
                bt["adapter_name"] = data.get("AdapterName") or "Realtek Wireless Bluetooth Adapter"
                bt["adapter_status"] = data.get("AdapterStatus") or "OK"
                bt["adapter_present"] = True

                conn_list = data.get("Connected") or []
                if isinstance(conn_list, dict):
                    conn_list = [conn_list]
                for c in conn_list:
                    name = c.get("FriendlyName")
                    if name:
                        bt["connected_devices"].append({
                            "name": name,
                            "status": c.get("Status", "Connected"),
                            "id": c.get("InstanceId", "")
                        })

                # Prefer user-facing peripheral over driver or adapter
                peripherals = [
                    d for d in bt["connected_devices"]
                    if not any(k in d["name"].lower() for k in ["driver", "adapter", "realtek", "intel", "enumerator"])
                ]
                if peripherals:
                    bt["connected_device"] = peripherals[0]["name"]
                elif bt["connected_devices"]:
                    bt["connected_device"] = bt["connected_devices"][0]["name"]

                ports_list = data.get("Ports") or []
                if isinstance(ports_list, dict):
                    ports_list = [ports_list]
                for p in ports_list:
                    pname = p.get("FriendlyName")
                    if pname:
                        bt["bluetooth_ports"].append(pname)
        except Exception as e:
            logger.debug(f"PnP Bluetooth check notice: {e}")

        # 2. Fast Winreg lookup of paired Bluetooth devices (sorted by most recently connected)
        try:
            import winreg
            key_path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                i = 0
                paired_temp = []
                while True:
                    try:
                        sub = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, sub) as skey:
                            dev_name = "Unknown Bluetooth Device"
                            last_conn_str = "Unknown"
                            raw_ft = 0
                            try:
                                val, _ = winreg.QueryValueEx(skey, "Name")
                                if isinstance(val, bytes):
                                    dev_name = val.decode("utf-8", errors="ignore").rstrip("\x00")
                                elif isinstance(val, str):
                                    dev_name = val.rstrip("\x00")
                            except FileNotFoundError:
                                pass

                            try:
                                ft, _ = winreg.QueryValueEx(skey, "LastConnected")
                                if isinstance(ft, int) and ft > 116444736000000000:
                                    raw_ft = ft
                                    sec = (ft - 116444736000000000) / 10000000
                                    last_conn_str = datetime.datetime.fromtimestamp(sec).strftime("%Y-%m-%d %H:%M")
                            except Exception:
                                pass

                            if dev_name and dev_name != "(no Name)":
                                paired_temp.append({
                                    "name": dev_name,
                                    "mac": sub,
                                    "last_connected": last_conn_str,
                                    "_raw_ts": raw_ft
                                })
                        i += 1
                    except OSError:
                        break

                paired_temp.sort(key=lambda x: x["_raw_ts"], reverse=True)
                for item in paired_temp:
                    del item["_raw_ts"]
                bt["paired_devices"] = paired_temp
        except Exception as e:
            logger.debug(f"Winreg Bluetooth enumeration notice: {e}")

        # If user explicitly bound or connected a device, ensure it is set as connected
        if self._manual_connected_device:
            bt["connected_device"] = self._manual_connected_device["name"]
            existing = [d for d in bt["connected_devices"] if d["name"] != self._manual_connected_device["name"]]
            existing.insert(0, {
                "name": self._manual_connected_device["name"],
                "status": "Connected (Active)",
                "id": self._manual_connected_device.get("mac", "MANUAL_BT")
            })
            bt["connected_devices"] = existing

        return bt

# Singleton instance
connectivity_manager = HardwareConnectivityManager()
