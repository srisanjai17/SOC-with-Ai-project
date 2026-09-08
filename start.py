#!/usr/bin/env python3
"""SOC with AI — Real-Time Startup Script

Auto-detects network interfaces, installs dependencies, and launches
the full AI-powered SOC monitoring system on the admin PC.

Usage:
    python start.py                  # Auto-detect interface, start on port 8002
    python start.py --port 9000      # Custom port
    python start.py --interface eth0 # Specific interface
    python start.py --demo           # Demo mode (synthetic traffic)
    python start.py --setup          # First-time setup only (install deps)
"""

import argparse
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

#  Constants 

PROJECT_ROOT = Path(__file__).parent
REQUIRED_PYTHON = (3, 10)
DEFAULT_PORT = 8002
DEFAULT_HOST = "0.0.0.0"

#  Helpers 

def banner():
    print()
    print("=" * 70)
    print("  SOC with AI — Real-Time Network Defense System")
    print("  AI-Powered Packet Capture + Threat Detection + Auto-Response")
    print("=" * 70)
    print()

def check_python():
    v = sys.version_info
    if v < REQUIRED_PYTHON:
        print(f"[ERROR] Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required, found {v.major}.{v.minor}")
        sys.exit(1)
    print(f"[OK] Python {v.major}.{v.minor}.{v.micro}")

def install_deps():
    """Install required packages."""
    print("[SETUP] Installing dependencies...")
    req_file = PROJECT_ROOT / "requirements.txt"
    if req_file.exists():
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    # Core deps
    core = [
        "fastapi", "uvicorn[standard]", "pydantic", "python-dateutil",
        "jinja2", "scikit-learn", "numpy", "scipy",
    ]
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", *core, "-q"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # Optional: scapy for live capture
    try:
        import scapy
        print("[OK] scapy (live capture)")
    except ImportError:
        print("[SETUP] Installing scapy for live packet capture...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "scapy", "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    # Optional: brotli for compression
    try:
        import brotli
        print("[OK] brotli (compression)")
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "brotli-asgi", "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    print("[OK] All dependencies installed")

def detect_interfaces():
    """Detect available network interfaces on this machine."""
    interfaces = []
    system = platform.system()

    if system == "Linux":
        net_dir = Path("/sys/class/net")
        if net_dir.exists():
            for iface in net_dir.iterdir():
                name = iface.name
                if name == "lo":
                    continue
                # Get IP address
                ip = _get_linux_ip(name)
                interfaces.append({"name": name, "ip": ip, "type": "ethernet"})
    elif system == "Windows":
        try:
            result = subprocess.run(
                ["netsh", "interface", "ip", "show", "interfaces"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0] in ("enabled", "disabled"):
                    name = parts[3]
                    ip = _get_windows_ip(name)
                    interfaces.append({"name": name, "ip": ip, "type": "ethernet"})
        except Exception:
            pass
    elif system == "Darwin":
        try:
            result = subprocess.run(
                ["ifconfig"], capture_output=True, text=True, timeout=5,
            )
            current_iface = None
            for line in result.stdout.splitlines():
                if line and not line[0].isspace():
                    current_iface = line.split(":")[0]
                elif current_iface and "inet " in line:
                    ip = line.split("inet ")[1].split()[0]
                    if ip != "127.0.0.1":
                        interfaces.append({"name": current_iface, "ip": ip, "type": "ethernet"})
                    current_iface = None
        except Exception:
            pass

    return interfaces

def _get_linux_ip(iface_name):
    try:
        result = subprocess.run(
            ["ip", "-4", "addr", "show", iface_name],
            capture_output=True, text=True, timeout=3,
        )
        for line in result.stdout.splitlines():
            if "inet " in line:
                return line.split("inet ")[1].split("/")[0]
    except Exception:
        pass
    return "unknown"

def _get_windows_ip(iface_name):
    try:
        result = subprocess.run(
            ["netsh", "interface", "ip", "show", "address", iface_name],
            capture_output=True, text=True, timeout=3,
        )
        for line in result.stdout.splitlines():
            if "IP Address" in line:
                return line.split(":")[-1].strip()
    except Exception:
        pass
    return "unknown"

def get_local_ip():
    """Get the primary local IP address."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_system_info(interfaces, local_ip):
    """Print system information."""
    system = platform.system()
    print(f"[INFO] OS: {system} {platform.release()}")
    print(f"[INFO] Host: {platform.node()}")
    print(f"[INFO] Local IP: {local_ip}")
    print(f"[INFO] Python: {sys.version.split()[0]}")
    print()

    if interfaces:
        print("[INTERFACES] Available network interfaces:")
        for i, iface in enumerate(interfaces):
            marker = " <-- PRIMARY" if iface["ip"] == local_ip else ""
            print(f"  [{i+1}] {iface['name']:20s} IP: {iface['ip']}{marker}")
    else:
        print("[WARNING] No network interfaces detected (demo mode will be used)")
    print()

def start_server(host, port, interface=None):
    """Start the SOC with AI server."""
    print(f"[START] Launching SOC with AI on http://{host}:{port}")
    print(f"[START] Dashboard: http://127.0.0.1:{port}/")
    print(f"[START] Login: admin / admin123")
    print()

    if interface:
        os.environ["SOC_INTERFACE"] = interface

    os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

    # Graceful shutdown handler
    import signal

    def shutdown_handler(signum, frame):
        print("\n[SHUTDOWN] Received signal, saving state...")
        try:
            from src.api.routes import save_persistent_state
            save_persistent_state()
            print("[SHUTDOWN] State saved successfully")
        except Exception as e:
            print(f"[SHUTDOWN] Error saving state: {e}")
        print("[SHUTDOWN] Server stopped gracefully")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Start uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "src.api.routes:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to start server: {e}")
        print("[FALLBACK] Try: python -m uvicorn src.api.routes:app --host 0.0.0.0 --port 8002")

#  Main 

def main():
    parser = argparse.ArgumentParser(
        description="SOC with AI — Real-Time Network Defense System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run on (default: 8002)")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--interface", default=None, help="Network interface to capture from")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode (synthetic traffic)")
    parser.add_argument("--setup", action="store_true", help="First-time setup only (install deps)")
    parser.add_argument("--no-install", action="store_true", help="Skip dependency installation")
    parser.add_argument("--admin", action="store_true", help="Run with admin privileges (enables live packet capture)")
    args = parser.parse_args()

    banner()

    # Admin mode check
    if args.admin:
        import ctypes
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            is_admin = os.getuid() == 0
        if is_admin:
            print("[ADMIN] Running with Administrator privileges")
            print("[ADMIN] Live packet capture enabled")
            os.environ["SOC_ADMIN_MODE"] = "1"
        else:
            print("[ADMIN] WARNING: Not running as Administrator!")
            print("[ADMIN] Live capture will use demo mode")
            print("[ADMIN] Right-click run_as_admin.bat and select 'Run as administrator'")
    check_python()

    if not args.no_install:
        install_deps()

    if args.setup:
        print("[SETUP] First-time setup complete!")
        print("[SETUP] Run 'python start.py' to start the server")
        return

    # Detect interfaces
    interfaces = detect_interfaces()
    local_ip = get_local_ip()
    print_system_info(interfaces, local_ip)

    # Auto-select interface
    selected_interface = args.interface
    if not selected_interface and interfaces:
        # Pick the one with the local IP
        for iface in interfaces:
            if iface["ip"] == local_ip:
                selected_interface = iface["name"]
                break
        if not selected_interface:
            selected_interface = interfaces[0]["name"]

    if selected_interface:
        print(f"[CAPTURE] Selected interface: {selected_interface}")
    elif args.demo:
        print("[CAPTURE] Demo mode (synthetic traffic)")
    else:
        print("[CAPTURE] No interface available — using demo mode")

    # Start server
    start_server(args.host, args.port, selected_interface)

if __name__ == "__main__":
    main()
