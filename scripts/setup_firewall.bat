@echo off
:: ==============================================================================
:: NEUROSIM : AUTOMATED WINDOWS DEFENDER FIREWALL RULES CONFIGURATION
:: Configures inbound rules for UDP port 5005, HTTP port 8000, and WS port 8765.
:: Right-click and select "Run as administrator" to apply.
:: ==============================================================================

echo ============================================================================
echo   NEUROSIM BCI WORKSTATION - FIREWALL CONFIGURATION UTILITY
echo ============================================================================
echo.

:: Check for administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Administrative permissions required!
    echo Please right-click this batch file and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

echo [1/3] Adding Inbound Rule for UDP Telemetry (Port 5005, All Profiles)...
netsh advfirewall firewall add rule name="NeuroSim-UDP-5005" dir=in action=allow protocol=UDP localport=5005 profile=any >nul

echo [2/3] Adding Inbound Rule for HTTP Web Dashboard (Port 8000, All Profiles)...
netsh advfirewall firewall add rule name="NeuroSim-HTTP-8000" dir=in action=allow protocol=TCP localport=8000 profile=any >nul

echo [3/3] Adding Inbound Rule for WebSocket Real-Time Relay (Port 8765, All Profiles)...
netsh advfirewall firewall add rule name="NeuroSim-WS-8765" dir=in action=allow protocol=TCP localport=8765 profile=any >nul

echo.
echo ============================================================================
echo   SUCCESS: Windows Firewall rules configured for NeuroSim!
echo   Ports 5005 (UDP), 8000 (TCP), and 8765 (TCP) are now open.
echo ============================================================================
echo.
pause
