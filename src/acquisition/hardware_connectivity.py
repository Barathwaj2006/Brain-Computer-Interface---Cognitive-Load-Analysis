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
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            self._running = True
            # Initial sync update
            self.refresh_all()
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()

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

    def get_status(self) -> dict:
        with self.lock:
            return {
                "wifi": dict(self._wifi_info),
                "bluetooth": dict(self._bluetooth_info)
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

        # 1. Check Bluetooth Controller Adapter & Currently Connected Devices via PowerShell (PnpDevice)
        try:
            ps_script = r"""
            $adapter = Get-PnpDevice -PresentOnly | Where-Object { $_.Class -eq 'Bluetooth' -and $_.FriendlyName -match 'Adapter|Radio|Wireless' } | Select-Object -First 1 FriendlyName, Status
            $connected = Get-PnpDevice -PresentOnly | Where-Object {
                ($_.InstanceId -like 'BTHENUM\DEV_*' -or $_.InstanceId -like 'BTHLE\DEV_*' -or ($_.Class -eq 'Bluetooth' -and $_.FriendlyName -notmatch 'Enumerator|Adapter|Service|Transport|Profile|Realtek|Intel|Protocol|Bridge'))
            } | Select-Object FriendlyName, Status, InstanceId
            $ports = Get-PnpDevice -PresentOnly | Where-Object { $_.Class -eq 'Ports' -and ($_.FriendlyName -like '*Bluetooth*' -or $_.InstanceId -like 'BTHENUM\*') } | Select-Object FriendlyName, Status
            
            [PSCustomObject]@{
                AdapterName = if ($adapter) { $adapter.FriendlyName } else { "Realtek Wireless Bluetooth Adapter" }
                AdapterStatus = if ($adapter) { $adapter.Status } else { "OK" }
                Connected = @($connected)
                Ports = @($ports)
            } | ConvertTo-Json -Depth 3
            """
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
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

                if bt["connected_devices"]:
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

        # 2. Fast Winreg lookup of paired Bluetooth devices
        try:
            import winreg
            key_path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, sub) as skey:
                            dev_name = "Unknown Bluetooth Device"
                            last_conn_str = "Unknown"
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
                                    sec = (ft - 116444736000000000) / 10000000
                                    last_conn_str = datetime.datetime.fromtimestamp(sec).strftime("%Y-%m-%d %H:%M")
                            except Exception:
                                pass

                            if dev_name and dev_name != "(no Name)":
                                bt["paired_devices"].append({
                                    "name": dev_name,
                                    "mac": sub,
                                    "last_connected": last_conn_str
                                })
                        i += 1
                    except OSError:
                        break
        except Exception as e:
            logger.debug(f"Winreg Bluetooth enumeration notice: {e}")

        return bt

# Singleton instance
connectivity_manager = HardwareConnectivityManager()
