"""
Unified Quick Launcher for Windows CLI Remote Control
Author: Antigravity AI
Version: 1.0.0
"""

import os
import sys
import subprocess
import time
import ctypes

if sys.platform == "win32":
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        os.system("color")

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{CYAN}{BOLD}========================================================================{RESET}")
    print(f"{CYAN}{BOLD} 🖥️   WINDOWS CLI REMOTE CONTROL SYSTEM - LAUNCHER                      {RESET}")
    print(f"{CYAN}{BOLD}========================================================================{RESET}")
    print(f" {YELLOW}1.{RESET} 🚀 원격 서버(Agent) 실행     (Windows 타겟 컴퓨터에서 실행)")
    print(f" {YELLOW}2.{RESET} 💻 컨트롤러 클라이언트 실행  (원격 접속 및 메뉴 1..8 번 제어)")
    print(f" {YELLOW}3.{RESET} ⚡ 로컬 데모 모드 실행       (서버 + 클라이언트 한 번에 자동 실행)")
    print(f" {YELLOW}4.{RESET} 🌐 GitHub에 코드 자동 저장   (https://github.com/choi75077633-web/win-cli-remote)")
    print(f" {YELLOW}0.{RESET} 🚪 종료 (Exit)")
    print(f"{CYAN}========================================================================{RESET}")

def main():
    py_exec = sys.executable or "py"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(base_dir, "server.py")
    client_script = os.path.join(base_dir, "client.py")
    push_script = os.path.join(base_dir, "git_push.py")

    while True:
        print_banner()
        choice = input(f"{BOLD}메뉴 선택 (1-4, 0=종료): {RESET}").strip()

        if choice == "1":
            print(f"\n{GREEN}[*] Windows Remote Agent Server를 시작합니다...{RESET}")
            subprocess.run([py_exec, server_script])
            break
        elif choice == "2":
            print(f"\n{GREEN}[*] Remote Client Controller를 시작합니다...{RESET}")
            subprocess.run([py_exec, client_script])
            break
        elif choice == "3":
            print(f"\n{GREEN}[*] 백그라운드에 Agent Server를 띄우고 Client를 연결합니다...{RESET}")
            srv_proc = subprocess.Popen([py_exec, server_script])
            time.sleep(1.5)
            try:
                subprocess.run([py_exec, client_script])
            finally:
                print(f"\n{YELLOW}[*] 데모 종료 중... Server 프로세스를 정지합니다.{RESET}")
                srv_proc.terminate()
            break
        elif choice == "4":
            print(f"\n{GREEN}[*] GitHub로 최신 코드를 자동 동기화/푸시합니다...{RESET}")
            subprocess.run([py_exec, push_script])
            input(f"\n{YELLOW}엔터를 누르면 메뉴로 돌아갑니다...{RESET}")
        elif choice == "0" or choice.lower() in ["exit", "q"]:
            print("\nGoodbye!")
            break
        else:
            print(f"{RED}[!] 올바른 메뉴 번호를 입력하세요.{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main()
