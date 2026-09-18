#!/usr/bin/env python3
"""
NeuroSim Local Web Application & Wi-Fi Telemetry Launcher
Proxies directly to server.py to provide the full web server,
laptop Wi-Fi UDP stream receiver, and real-time WebSocket bridge.
"""

from server import main

if __name__ == '__main__':
    main()
