"""
Windows CLI Remote Management Agent (Server)
Author: Antigravity AI
Version: 1.0.0
Description: Lightweight, multi-threaded TCP agent that exposes system administration APIs over JSON-RPC.
"""

import sys
import os

# Fix Windows console unicode encoding issues (CP949 vs UTF-8)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import socket
import threading
import json
import subprocess
import platform
import time
import base64
import shutil
from datetime import datetime

# Default Configuration
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    default_cfg = {"host": "0.0.0.0", "port": 9999, "auth_token": "WinRemoteSecret2026", "timeout": 30}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default_cfg.update(cfg)
        except Exception as e:
            print(f"[!] Warning: Failed to load config.json: {e}")
    return default_cfg

CONFIG = load_config()

def run_powershell(cmd):
    """Executes a PowerShell command and returns (stdout, stderr, returncode)."""
    try:
        ps_cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd]
        res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=25, encoding="cp949", errors="replace")
        return res.stdout, res.stderr, res.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out after 25 seconds.", 1
    except Exception as e:
        return "", str(e), 1

def run_cmd(cmd):
    """Executes a standard CMD / system command."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=25, encoding="cp949", errors="replace")
        return res.stdout, res.stderr, res.returncode
    except Exception as e:
        return "", str(e), 1

# --- API HANDLERS ---

def handle_sysinfo():
    """Returns detailed Windows system info and current performance metrics."""
    script = """
    $os = Get-CimInstance Win32_OperatingSystem
    $cs = Get-CimInstance Win32_ComputerSystem
    $cpu = Get-CimInstance Win32_Processor
    $disks = Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 }
    $net = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" }
    
    $uptime = (Get-Date) - $os.LastBootUpTime
    $totalRamMB = [math]::Round($os.TotalVisibleMemorySize / 1024, 0)
    $freeRamMB = [math]::Round($os.FreePhysicalMemory / 1024, 0)
    $usedRamMB = $totalRamMB - $freeRamMB
    $ramPercent = [math]::Round(($usedRamMB / $totalRamMB) * 100, 1)

    $diskInfo = @()
    foreach ($d in $disks) {
        $sizeGB = [math]::Round($d.Size / 1GB, 1)
        $freeGB = [math]::Round($d.FreeSpace / 1GB, 1)
        $usedGB = [math]::Round($sizeGB - $freeGB, 1)
        $pct = if ($sizeGB -gt 0) { [math]::Round(($usedGB / $sizeGB) * 100, 1) } else { 0 }
        $diskInfo += @{
            Drive = $d.DeviceID
            Volume = $d.VolumeName
            TotalGB = $sizeGB
            FreeGB = $freeGB
            UsedGB = $usedGB
            PercentUsed = $pct
        }
    }

    $ipList = $net | Select-Object -ExpandProperty IPAddress

    [PSCustomObject]@{
        Hostname = $env:COMPUTERNAME
        Username = $env:USERNAME
        OS = "$($os.Caption) ($($os.OSArchitecture))"
        Build = $os.BuildNumber
        Uptime = "$($uptime.Days)d $($uptime.Hours)h $($uptime.Minutes)m"
        CPU_Name = $cpu.Name
        CPU_Cores = $cpu.NumberOfCores
        CPU_Logical = $cpu.NumberOfLogicalProcessors
        RAM_TotalMB = $totalRamMB
        RAM_UsedMB = $usedRamMB
        RAM_FreeMB = $freeRamMB
        RAM_Percent = $ramPercent
        Disks = $diskInfo
        IP_Addresses = $ipList
    } | ConvertTo-Json -Depth 3
    """
    stdout, stderr, code = run_powershell(script)
    if code == 0 and stdout.strip():
        try:
            return {"status": "success", "data": json.loads(stdout)}
        except Exception as e:
            return {"status": "error", "message": f"JSON parse error: {e}", "raw": stdout}
    return {"status": "error", "message": stderr or "Failed to retrieve system info."}

def handle_processes(search=""):
    """Returns top running processes or filtered by search string."""
    script = """
    $procs = Get-Process | Sort-Object -Property WorkingSet64 -Descending
    if ('SEARCH_TERM') {
        $procs = $procs | Where-Object { $_.Name -like "*SEARCH_TERM*" -or $_.Id -like "*SEARCH_TERM*" }
    }
    $result = $procs | Select-Object -First 40 | ForEach-Object {
        $memMB = [math]::Round($_.WorkingSet64 / 1MB, 1)
        [PSCustomObject]@{
            PID = $_.Id
            Name = $_.ProcessName
            MemoryMB = $memMB
            CPU_Sec = [math]::Round($_.CPU, 1)
            Title = $_.MainWindowTitle
        }
    }
    $result | ConvertTo-Json
    """.replace("SEARCH_TERM", search)
    stdout, stderr, code = run_powershell(script)
    if code == 0:
        try:
            data = json.loads(stdout) if stdout.strip() else []
            if isinstance(data, dict):
                data = [data]
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": f"Parse error: {e}", "raw": stdout}
    return {"status": "error", "message": stderr or "Failed to list processes."}

def handle_kill_process(pid_or_name):
    """Kills a process by PID or process name."""
    is_pid = pid_or_name.isdigit()
    if is_pid:
        script = f"Stop-Process -Id {pid_or_name} -Force -ErrorAction Stop"
    else:
        script = f"Stop-Process -Name '{pid_or_name}' -Force -ErrorAction Stop"
    stdout, stderr, code = run_powershell(script)
    if code == 0:
        return {"status": "success", "message": f"Successfully terminated process: {pid_or_name}"}
    return {"status": "error", "message": stderr.strip() or f"Failed to terminate {pid_or_name}."}

def handle_services(filter_str=""):
    """Lists Windows services."""
    script = """
    $svcs = Get-Service
    if ('FILTER_TERM') {
        $svcs = $svcs | Where-Object { $_.Name -like "*FILTER_TERM*" -or $_.DisplayName -like "*FILTER_TERM*" }
    }
    $svcs | Select-Object -First 50 Name, DisplayName, Status, StartType | ConvertTo-Json
    """.replace("FILTER_TERM", filter_str)
    stdout, stderr, code = run_powershell(script)
    if code == 0:
        try:
            data = json.loads(stdout) if stdout.strip() else []
            if isinstance(data, dict):
                data = [data]
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": f"Parse error: {e}"}
    return {"status": "error", "message": stderr or "Failed to list services."}

def handle_service_control(service_name, action):
    """Actions: start, stop, restart."""
    action_map = {"start": "Start-Service", "stop": "Stop-Service", "restart": "Restart-Service"}
    cmd_name = action_map.get(action.lower())
    if not cmd_name:
        return {"status": "error", "message": "Invalid action. Use start, stop, or restart."}
    script = f"{cmd_name} -Name '{service_name}' -ErrorAction Stop"
    stdout, stderr, code = run_powershell(script)
    if code == 0:
        return {"status": "success", "message": f"Service '{service_name}' {action} command sent successfully."}
    return {"status": "error", "message": stderr.strip() or f"Failed to {action} service '{service_name}'."}

def handle_remote_shell(command):
    """Executes a arbitrary PowerShell command."""
    stdout, stderr, code = run_powershell(command)
    return {
        "status": "success" if code == 0 else "error",
        "output": stdout,
        "error": stderr,
        "returncode": code
    }

def handle_file_manager(action, path=".", extra_data=None):
    """File operations: list, read, write, info."""
    path = os.path.abspath(path)
    if action == "list":
        if not os.path.exists(path):
            return {"status": "error", "message": f"Path standard not found: {path}"}
        items = []
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        stat = entry.stat()
                        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        items.append({
                            "name": entry.name,
                            "is_dir": entry.is_dir(),
                            "size": stat.st_size if not entry.is_dir() else 0,
                            "modified": mtime
                        })
                    except Exception:
                        continue
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            return {"status": "success", "current_path": path, "items": items}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif action == "read":
        if not os.path.isfile(path):
            return {"status": "error", "message": "File not found or is a directory."}
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(50000) # limit to 50KB for display
            return {"status": "success", "path": path, "content": content}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif action == "download":
        if not os.path.isfile(path):
            return {"status": "error", "message": "File not found."}
        try:
            with open(path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("ascii")
            return {"status": "success", "filename": os.path.basename(path), "data_b64": b64_data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": f"Unknown file action: {action}"}

def handle_network_info():
    """Lists listening ports & active netstat connections."""
    script = """
    $conns = Get-NetTCPConnection | Select-Object -First 35 LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess
    $result = @()
    foreach ($c in $conns) {
        $procName = (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue).ProcessName
        $result += [PSCustomObject]@{
            Local = "$($c.LocalAddress):$($c.LocalPort)"
            Remote = "$($c.RemoteAddress):$($c.RemotePort)"
            State = $c.State
            PID = $c.OwningProcess
            Process = $procName
        }
    }
    $result | ConvertTo-Json
    """
    stdout, stderr, code = run_powershell(script)
    if code == 0:
        try:
            data = json.loads(stdout) if stdout.strip() else []
            if isinstance(data, dict):
                data = [data]
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": f"Parse error: {e}"}
    return {"status": "error", "message": stderr or "Failed to list network connections."}

def handle_event_logs(log_type="System", count=15):
    """Lists recent Event Log warnings and errors."""
    script = """
    Get-EventLog -LogName 'LOG_TYPE' -EntryType Error, Warning -Newest LOG_COUNT -ErrorAction SilentlyContinue | ForEach-Object {
        [PSCustomObject]@{
            Time = $_.TimeGenerated.ToString("yyyy-MM-dd HH:mm:ss")
            EntryType = $_.EntryType.ToString()
            Source = $_.Source
            EventID = $_.InstanceId
            Message = if ($_.Message.Length -gt 120) { $_.Message.Substring(0,120) + "..." } else { $_.Message }
        }
    } | ConvertTo-Json
    """.replace("LOG_TYPE", log_type).replace("LOG_COUNT", str(count))
    stdout, stderr, code = run_powershell(script)
    if code == 0:
        try:
            data = json.loads(stdout) if stdout.strip() else []
            if isinstance(data, dict):
                data = [data]
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": f"Parse error: {e}"}
    return {"status": "error", "message": stderr or f"Failed to read {log_type} event logs."}

def handle_power(action):
    """System power management."""
    if action == "lock":
        run_cmd("rundll32.exe user32.dll,LockWorkStation")
        return {"status": "success", "message": "Workstation locked successfully."}
    elif action == "logoff":
        run_cmd("shutdown /l")
        return {"status": "success", "message": "Logoff command issued."}
    elif action == "reboot":
        run_cmd("shutdown /r /t 15 /c \"Remote reboot initiated via CLI Remote Agent\"")
        return {"status": "success", "message": "System reboot scheduled in 15 seconds. Use 'shutdown /a' to cancel."}
    elif action == "shutdown":
        run_cmd("shutdown /s /t 15 /c \"Remote shutdown initiated via CLI Remote Agent\"")
        return {"status": "success", "message": "System shutdown scheduled in 15 seconds. Use 'shutdown /a' to cancel."}
    elif action == "cancel":
        stdout, stderr, code = run_cmd("shutdown /a")
        if code == 0:
            return {"status": "success", "message": "Scheduled shutdown/reboot cancelled."}
        return {"status": "error", "message": stderr.strip() or "No scheduled shutdown to cancel."}
    return {"status": "error", "message": "Unknown power command."}

# --- SOCKET DISPATCHER ---

def process_client_request(req):
    auth_token = req.get("token")
    if auth_token != CONFIG.get("auth_token"):
        return {"status": "error", "message": "Authentication failed: Invalid security token."}

    action = req.get("action")
    params = req.get("params", {})

    if action == "ping":
        return {"status": "success", "message": "PONG", "hostname": platform.node(), "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    elif action == "sysinfo":
        return handle_sysinfo()
    elif action == "processes":
        return handle_processes(params.get("search", ""))
    elif action == "kill_process":
        return handle_kill_process(str(params.get("pid_or_name", "")))
    elif action == "services":
        return handle_services(params.get("filter", ""))
    elif action == "service_control":
        return handle_service_control(params.get("service", ""), params.get("cmd", ""))
    elif action == "shell":
        return handle_remote_shell(params.get("command", ""))
    elif action == "file_mgr":
        return handle_file_manager(params.get("file_action", "list"), params.get("path", "."), params)
    elif action == "network":
        return handle_network_info()
    elif action == "event_logs":
        return handle_event_logs(params.get("log_type", "System"), params.get("count", 15))
    elif action == "power":
        return handle_power(params.get("power_action", ""))
    else:
        return {"status": "error", "message": f"Unknown action requested: {action}"}

def client_handler_thread(conn, addr):
    print(f"[+] Client connected from {addr[0]}:{addr[1]}")
    try:
        conn.settimeout(CONFIG.get("timeout", 60))
        buffer = ""
        while True:
            data = conn.recv(65536)
            if not data:
                break
            buffer += data.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                    response = process_client_request(req)
                except json.JSONDecodeError as e:
                    response = {"status": "error", "message": f"Invalid JSON payload: {e}"}
                except Exception as e:
                    response = {"status": "error", "message": f"Server exception: {e}"}

                resp_bytes = (json.dumps(response) + "\n").encode("utf-8")
                conn.sendall(resp_bytes)
    except socket.timeout:
        print(f"[-] Client {addr[0]} timed out.")
    except Exception as e:
        print(f"[-] Connection error with {addr[0]}: {e}")
    finally:
        conn.close()
        print(f"[-] Client disconnected from {addr[0]}:{addr[1]}")

def start_server(host=None, port=None):
    bind_host = host or CONFIG.get("host", "0.0.0.0")
    bind_port = port or CONFIG.get("port", 9999)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((bind_host, bind_port))
        server.listen(10)
        print("=" * 75)
        print(" WINDOWS CLI REMOTE AGENT SERVER RUNNING")
        print(f" Listening on: {bind_host}:{bind_port}")
        print(f" Security Token: {CONFIG.get('auth_token')}")
        print(f" Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 75)
        print("[*] Waiting for incoming client connections... (Press Ctrl+C to stop)")

        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=client_handler_thread, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down Agent Server...")
    except Exception as e:
        print(f"[!] Server fatal error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
