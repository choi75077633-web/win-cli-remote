"""
Windows CLI Remote Management Controller (Client)
Author: Antigravity AI
Version: 1.0.0
Description: Interactive menu-driven terminal client for controlling remote Windows server agent.
"""

import sys
import os

# Fix Windows console unicode encoding issues
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import socket
import json
import time
import base64
import ctypes

# Enable VT100 ANSI Escape Sequences in Windows Console
if sys.platform == "win32":
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        os.system("color")

# ANSI Style Definitions
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    WHITE = "\033[97m"

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    default_cfg = {"host": "127.0.0.1", "port": 9999, "auth_token": "WinRemoteSecret2026", "timeout": 30}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default_cfg.update(cfg)
        except Exception:
            pass
    return default_cfg

class RemoteClient:
    def __init__(self, host, port, token):
        self.host = host
        self.port = port
        self.token = token
        self.sock = None
        self.connected = False

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect((self.host, self.port))
            self.connected = True
            # Test ping
            res = self.send_request("ping")
            if res.get("status") == "success":
                return True, f"Successfully connected to {res.get('hostname', self.host)} ({self.host}:{self.port})"
            else:
                self.disconnect()
                return False, res.get("message", "Authentication or handshake failed.")
        except Exception as e:
            self.disconnect()
            return False, f"Connection error: {e}"

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None
        self.connected = False

    def send_request(self, action, params=None):
        if not self.connected or not self.sock:
            return {"status": "error", "message": "Not connected to server."}
        payload = {
            "token": self.token,
            "action": action,
            "params": params or {}
        }
        try:
            req_str = json.dumps(payload) + "\n"
            self.sock.sendall(req_str.encode("utf-8"))
            
            # Read response line
            buffer = ""
            while "\n" not in buffer:
                chunk = self.sock.recv(65536)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")
            
            if "\n" in buffer:
                line, _ = buffer.split("\n", 1)
                return json.loads(line)
            return {"status": "error", "message": "Empty response received from server."}
        except Exception as e:
            self.connected = False
            return {"status": "error", "message": f"Network error during request: {e}"}

# --- UI DRAWING HELPERS ---

def print_header(title, host, connected):
    os.system("cls" if os.name == "nt" else "clear")
    status_str = f"{Style.GREEN}● ONLINE{Style.RESET}" if connected else f"{Style.RED}○ OFFLINE{Style.RESET}"
    print(f"{Style.CYAN}{Style.BOLD}╔═════════════════════════════════════════════════════════════════════════════╗{Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}║     WINDOWS CLI REMOTE SERVER MANAGEMENT CONSOLE v1.0                        ║{Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}╠═════════════════════════════════════════════════════════════════════════════╣{Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}║  Host: {Style.WHITE}{host:<22}{Style.CYAN}{Style.BOLD} Status: {status_str:<18}{Style.CYAN}{Style.BOLD} Mode: TCP Client ║{Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}╚═════════════════════════════════════════════════════════════════════════════╝{Style.RESET}")
    print(f"{Style.YELLOW}{Style.BOLD} {title}{Style.RESET}\n")

def print_table(headers, rows):
    if not rows:
        print(f"{Style.DIM}  (데이터 없음 / No items found){Style.RESET}\n")
        return

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            val_str = str(val) if val is not None else ""
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(val_str))

    header_str = " │ ".join([f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers))])
    sep_str = "─┼─".join(["─" * col_widths[i] for i in range(len(headers))])
    
    print(f"{Style.CYAN}{Style.BOLD}┌─" + "─┬─".join(["─" * col_widths[i] for i in range(len(headers))]) + "─┐{Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}│ {header_str} │{Style.RESET}")
    print(f"{Style.CYAN}├─" + sep_str + "─┤{Style.RESET}")

    for row in rows:
        row_str = " │ ".join([f"{str(row[i]):<{col_widths[i]}}" for i in range(len(row))])
        print(f"│ {row_str} │")

    print(f"{Style.CYAN}└─" + "─┴─".join(["─" * col_widths[i] for i in range(len(headers))]) + "─┘{Style.RESET}\n")

# --- MENU ACTIONS ---

def menu_sysinfo(client):
    res = client.send_request("sysinfo")
    if res.get("status") != "success":
        print(f"{Style.RED}[!] 오류: {res.get('message')}{Style.RESET}")
        return

    data = res.get("data", {})
    print(f"{Style.GREEN}{Style.BOLD}[1] System Information Overview{Style.RESET}")
    print(f" 🔹 Hostname:       {Style.WHITE}{Style.BOLD}{data.get('Hostname')}{Style.RESET}")
    print(f" 🔹 Active User:     {data.get('Username')}")
    print(f" 🔹 OS Version:      {data.get('OS')} (Build: {data.get('Build')})")
    print(f" 🔹 System Uptime:   {Style.YELLOW}{data.get('Uptime')}{Style.RESET}")
    print(f" 🔹 CPU Model:       {data.get('CPU_Name')} ({data.get('CPU_Cores')} Cores / {data.get('CPU_Logical')} Threads)")
    
    ram_pct = data.get('RAM_Percent', 0)
    ram_color = Style.GREEN if ram_pct < 70 else (Style.YELLOW if ram_pct < 85 else Style.RED)
    print(f" 🔹 Memory (RAM):    {ram_color}{data.get('RAM_UsedMB')} MB / {data.get('RAM_TotalMB')} MB ({ram_pct}% Used){Style.RESET}")

    print(f"\n{Style.CYAN}{Style.BOLD}Storage Drives:{Style.RESET}")
    headers = ["Drive", "Volume Label", "Total Space", "Used Space", "Free Space", "Usage %"]
    rows = []
    for d in data.get("Disks", []):
        pct = d.get("PercentUsed", 0)
        p_str = f"{Style.RED}{pct}%{Style.RESET}" if pct > 85 else f"{pct}%"
        rows.append([d.get("Drive"), d.get("Volume") or "-", f"{d.get('TotalGB')} GB", f"{d.get('UsedGB')} GB", f"{d.get('FreeGB')} GB", p_str])
    print_table(headers, rows)

    print(f"{Style.CYAN}{Style.BOLD}IP Addresses:{Style.RESET}")
    ips = data.get("IP_Addresses", [])
    if isinstance(ips, list):
        print("   " + ", ".join(ips))
    else:
        print("   " + str(ips))
    print()

def menu_processes(client):
    search = input(f"{Style.YELLOW}검색할 프로세스 이름/PID (전체 보기 엔터): {Style.RESET}").strip()
    res = client.send_request("processes", {"search": search})
    if res.get("status") != "success":
        print(f"{Style.RED}[!] 오류: {res.get('message')}{Style.RESET}")
        return

    procs = res.get("data", [])
    print(f"{Style.GREEN}{Style.BOLD}[2] Active Processes ({len(procs)} listed){Style.RESET}")
    headers = ["PID", "Process Name", "Memory (MB)", "CPU (sec)", "Window Title"]
    rows = []
    for p in procs:
        rows.append([p.get("PID"), p.get("Name"), p.get("MemoryMB"), p.get("CPU_Sec") or "0", p.get("Title") or ""])
    print_table(headers, rows)

    sub = input(f"{Style.CYAN}프로세스 종료 원함? (종료할 PID 입력 / 취소 엔터): {Style.RESET}").strip()
    if sub:
        kres = client.send_request("kill_process", {"pid_or_name": sub})
        if kres.get("status") == "success":
            print(f"{Style.GREEN}[+] {kres.get('message')}{Style.RESET}")
        else:
            print(f"{Style.RED}[!] {kres.get('message')}{Style.RESET}")

def menu_interactive_shell(client):
    print(f"{Style.MAGENTA}{Style.BOLD}[3] Interactive Remote PowerShell Session{Style.RESET}")
    print(f"{Style.DIM}   Type any PowerShell / Windows CLI command to run on remote server.{Style.RESET}")
    print(f"{Style.DIM}   Type 'exit' to return to main menu.{Style.RESET}\n")

    while True:
        try:
            cmd = input(f"{Style.GREEN}{Style.BOLD}PS Remote>{Style.RESET} ").strip()
            if not cmd:
                continue
            if cmd.lower() in ["exit", "quit", "back"]:
                break
            
            res = client.send_request("shell", {"command": cmd})
            out = res.get("output", "")
            err = res.get("error", "")
            code = res.get("returncode", 0)

            if out:
                print(out.rstrip())
            if err:
                print(f"{Style.RED}{err.rstrip()}{Style.RESET}")
            if code != 0 and not err and not out:
                print(f"{Style.RED}Command exited with code {code}{Style.RESET}")
            print()
        except KeyboardInterrupt:
            print("\n[*] Shell session paused.")
            break

def menu_services(client):
    filter_str = input(f"{Style.YELLOW}검색할 서비스 이름 (전체 보기 엔터): {Style.RESET}").strip()
    res = client.send_request("services", {"filter": filter_str})
    if res.get("status") != "success":
        print(f"{Style.RED}[!] 오류: {res.get('message')}{Style.RESET}")
        return

    svcs = res.get("data", [])
    print(f"{Style.GREEN}{Style.BOLD}[4] Windows Services ({len(svcs)} listed){Style.RESET}")
    headers = ["Service Name", "Display Name", "Status", "Start Type"]
    rows = []
    for s in svcs:
        st = s.get("Status")
        st_color = f"{Style.GREEN}Running{Style.RESET}" if str(st) == "4" or str(st) == "Running" else f"{Style.DIM}Stopped{Style.RESET}"
        rows.append([s.get("Name"), (s.get("DisplayName") or "")[:35], st_color, s.get("StartType") or "-"])
    print_table(headers, rows)

    sub = input(f"{Style.CYAN}서비스 제어 (명령 형식: [service_name] [start/stop/restart] / 취소 엔터): {Style.RESET}").strip()
    if sub and " " in sub:
        svc_name, action = sub.split(" ", 1)
        cres = client.send_request("service_control", {"service": svc_name, "cmd": action})
        if cres.get("status") == "success":
            print(f"{Style.GREEN}[+] {cres.get('message')}{Style.RESET}")
        else:
            print(f"{Style.RED}[!] {cres.get('message')}{Style.RESET}")

def menu_file_manager(client):
    current_path = "."
    while True:
        res = client.send_request("file_mgr", {"file_action": "list", "path": current_path})
        if res.get("status") != "success":
            print(f"{Style.RED}[!] 오류: {res.get('message')}{Style.RESET}")
            break

        path = res.get("current_path", current_path)
        items = res.get("items", [])

        print(f"{Style.GREEN}{Style.BOLD}[5] File Manager Directory: {path}{Style.RESET}")
        headers = ["Type", "Name", "Size (Bytes)", "Last Modified"]
        rows = []
        for it in items:
            t_str = f"{Style.CYAN}[DIR]{Style.RESET}" if it["is_dir"] else "[FILE]"
            sz_str = f"{it['size']:,}" if not it["is_dir"] else "-"
            rows.append([t_str, it["name"], sz_str, it["modified"]])
        print_table(headers, rows)

        print(f"{Style.YELLOW}옵션: [cd 디렉토리] / [read 파일명] / [download 파일명] / [.. 상위로] / [back 메뉴로]{Style.RESET}")
        cmd_in = input(f"{Style.CYAN}FileMgr>{Style.RESET} ").strip()
        if not cmd_in or cmd_in.lower() == "back":
            break
        elif cmd_in == "..":
            current_path = os.path.dirname(path)
        elif cmd_in.startswith("cd "):
            target = cmd_in[3:].strip()
            current_path = os.path.join(path, target)
        elif cmd_in.startswith("read "):
            fname = cmd_in[5:].strip()
            fpath = os.path.join(path, fname)
            rres = client.send_request("file_mgr", {"file_action": "read", "path": fpath})
            if rres.get("status") == "success":
                print(f"\n{Style.WHITE}{Style.BOLD}--- Content of {fname} ---{Style.RESET}")
                print(rres.get("content"))
                print(f"{Style.WHITE}{Style.BOLD}--- End of File ---{Style.RESET}\n")
            else:
                print(f"{Style.RED}[!] {rres.get('message')}{Style.RESET}")
        elif cmd_in.startswith("download "):
            fname = cmd_in[9:].strip()
            fpath = os.path.join(path, fname)
            dres = client.send_request("file_mgr", {"file_action": "download", "path": fpath})
            if dres.get("status") == "success":
                b64 = dres.get("data_b64")
                dest_path = os.path.join(os.getcwd(), fname)
                with open(dest_path, "wb") as f:
                    f.write(base64.b64decode(b64))
                print(f"{Style.GREEN}[+] Saved file to local path: {dest_path}{Style.RESET}")
            else:
                print(f"{Style.RED}[!] {dres.get('message')}{Style.RESET}")

def menu_network(client):
    res = client.send_request("network")
    if res.get("status") != "success":
        print(f"{Style.RED}[!] 오류: {res.get('message')}{Style.RESET}")
        return

    conns = res.get("data", [])
    print(f"{Style.GREEN}{Style.BOLD}[6] Active Network Connections & Ports{Style.RESET}")
    headers = ["Local Address", "Remote Address", "State", "PID", "Process"]
    rows = []
    for c in conns:
        st = c.get("State")
        st_color = f"{Style.GREEN}{st}{Style.RESET}" if st == "Listen" or st == "Established" else str(st)
        rows.append([c.get("Local"), c.get("Remote"), st_color, c.get("PID"), c.get("Process") or "-"])
    print_table(headers, rows)

def menu_event_logs(client):
    ltype = input(f"{Style.YELLOW}이벤트 로그 종류 (System / Application / Security) [기본 System]: {Style.RESET}").strip() or "System"
    res = client.send_request("event_logs", {"log_type": ltype, "count": 15})
    if res.get("status") != "success":
        print(f"{Style.RED}[!] 오류: {res.get('message')}{Style.RESET}")
        return

    logs = res.get("data", [])
    print(f"{Style.GREEN}{Style.BOLD}[7] Recent Windows Event Logs ({ltype}){Style.RESET}")
    headers = ["Time", "Type", "Source", "Event ID", "Message Snippet"]
    rows = []
    for l in logs:
        etype = l.get("EntryType")
        t_color = f"{Style.RED}{etype}{Style.RESET}" if etype == "Error" else f"{Style.YELLOW}{etype}{Style.RESET}"
        rows.append([l.get("Time"), t_color, l.get("Source"), l.get("EventID"), l.get("Message")])
    print_table(headers, rows)

def menu_power(client):
    print(f"{Style.RED}{Style.BOLD}[8] System Power & Session Management{Style.RESET}")
    print(" 1. Lock Workstation (원격 화면 잠금)")
    print(" 2. User Logoff (사용자 로그오프)")
    print(" 3. System Reboot (15초 후 시스템 재부팅)")
    print(" 4. System Shutdown (15초 후 시스템 종료)")
    print(" 5. Cancel Scheduled Reboot/Shutdown (예약 취소)")
    print(" 0. Back to Main Menu")

    sel = input(f"\n{Style.YELLOW}선택 (0-5): {Style.RESET}").strip()
    cmd_map = {"1": "lock", "2": "logoff", "3": "reboot", "4": "shutdown", "5": "cancel"}
    p_action = cmd_map.get(sel)

    if p_action:
        if p_action in ["reboot", "shutdown"]:
            confirm = input(f"{Style.RED}{Style.BOLD}경고: 진짜 원격 컴퓨터를 {p_action.upper()} 하시겠습니까? (yes 입력시 실행): {Style.RESET}").strip()
            if confirm.lower() != "yes":
                print("[*] Action cancelled.")
                return

        res = client.send_request("power", {"power_action": p_action})
        if res.get("status") == "success":
            print(f"{Style.GREEN}[+] {res.get('message')}{Style.RESET}")
        else:
            print(f"{Style.RED}[!] {res.get('message')}{Style.RESET}")

# --- MAIN CONTROLLER LOOP ---

def main():
    cfg = load_config()
    print(f"{Style.CYAN}{Style.BOLD}========================================================================{Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}    WINDOWS CLI REMOTE CONTROL CLIENT SETUP                              {Style.RESET}")
    print(f"{Style.CYAN}{Style.BOLD}========================================================================{Style.RESET}")

    default_host = cfg.get("host", "127.0.0.1")
    default_port = cfg.get("port", 9999)
    default_token = cfg.get("auth_token", "WinRemoteSecret2026")

    in_host = input(f"Target Server IP [{default_host}]: ").strip() or default_host
    in_port_str = input(f"Target Server Port [{default_port}]: ").strip()
    in_port = int(in_port_str) if in_port_str.isdigit() else default_port
    in_token = input(f"Security Token [{default_token}]: ").strip() or default_token

    client = RemoteClient(in_host, in_port, in_token)
    print(f"\n[*] Connecting to {in_host}:{in_port}...")
    success, msg = client.connect()

    if not success:
        print(f"{Style.RED}[!] Connection failed: {msg}{Style.RESET}")
        sys.exit(1)

    print(f"{Style.GREEN}[+] {msg}{Style.RESET}")
    time.sleep(1)

    while True:
        print_header("MAIN CLI MENU", f"{in_host}:{in_port}", client.connected)
        print(" [1] System Information & Real-time Metrics (CPU, RAM, Disks, OS, Uptime)")
        print(" [2] Process Manager                (List, Search, Kill by PID/Name)")
        print(" [3] Interactive Remote Shell      (PowerShell / CMD Real-time)")
        print(" [4] Windows Service Manager       (List, Start, Stop, Restart)")
        print(" [5] Remote File Manager            (List, Read, Download Files)")
        print(" [6] Network & Port Monitor         (Active Connections, Ports)")
        print(" [7] Windows Event Log Viewer       (System/Application Error Logs)")
        print(" [8] System Power Management         (Lock, Logoff, Reboot, Shutdown)")
        print(" [0] Disconnect & Exit CLI Client")
        print(f"{Style.CYAN}═════════════════════════════════════════════════════════════════════════════{Style.RESET}")

        choice = input(f"{Style.YELLOW}{Style.BOLD}Select Menu Option (0-8): {Style.RESET}").strip()

        if choice == "1":
            menu_sysinfo(client)
        elif choice == "2":
            menu_processes(client)
        elif choice == "3":
            menu_interactive_shell(client)
        elif choice == "4":
            menu_services(client)
        elif choice == "5":
            menu_file_manager(client)
        elif choice == "6":
            menu_network(client)
        elif choice == "7":
            menu_event_logs(client)
        elif choice == "8":
            menu_power(client)
        elif choice == "0" or choice.lower() in ["exit", "q"]:
            print(f"\n{Style.CYAN}[*] Disconnecting from server... Goodbye!{Style.RESET}")
            client.disconnect()
            break
        else:
            print(f"{Style.RED}[!] 잘못된 선택입니다. 0부터 8 사이의 숫자를 입력하세요.{Style.RESET}")

        input(f"\n{Style.DIM}메뉴로 돌아가려면 [엔터] 키를 누르세요...{Style.RESET}")

if __name__ == "__main__":
    main()
