"""
Automatic GitHub Push & Sync Script
Author: Antigravity AI
Repository: https://github.com/choi75077633-web/win-cli-remote
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

# Fix Windows encoding output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_URL = "https://github.com/choi75077633-web/win-cli-remote.git"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_git_cmd():
    """Finds git.exe path."""
    if shutil.which("git"):
        return "git"
    common_paths = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Git\cmd\git.exe")
    ]
    for path in common_paths:
        if os.path.exists(path):
            return f'"{path}"'
    return "git"

GIT = get_git_cmd()

def run_git(args, allow_error=False):
    cmd = f"{GIT} {args}"
    print(f"[*] Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=BASE_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.stdout.strip():
        print(res.stdout)
    if res.returncode != 0 and not allow_error:
        print(f"[!] Git Warning/Error: {res.stderr.strip()}")
    return res.returncode, res.stdout, res.stderr

def sync_to_github(commit_msg=None):
    print("=" * 70)
    print(" 🚀 AUTOMATIC GITHUB SYNC & PUSH SERVICE")
    print(f" 📍 Repository: {REPO_URL}")
    print("=" * 70)

    # 1. Check if git repo is initialized
    git_dir = os.path.join(BASE_DIR, ".git")
    if not os.path.exists(git_dir):
        print("[*] Initializing local Git repository...")
        run_git("init")

    # Ensure user identity is set for commits
    run_git('config user.name "choi75077633-web"', allow_error=True)
    run_git('config user.email "choi75077633-web@users.noreply.github.com"', allow_error=True)

    # 2. Add or update remote origin
    code, out, err = run_git("remote get-url origin", allow_error=True)
    if code != 0:
        print("[*] Adding GitHub remote origin...")
        run_git(f"remote add origin {REPO_URL}")
    else:
        print("[*] Updating GitHub remote origin URL...")
        run_git(f"remote set-url origin {REPO_URL}")

    # 3. Git add all files
    print("[*] Staging files for commit...")
    run_git("add .")

    # 4. Commit changes
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = commit_msg or f"Auto sync update: {now_str}"
    print(f"[*] Committing changes ('{msg}')...")
    code, out, err = run_git(f'commit -m "{msg}"', allow_error=True)

    # 5. Set default branch to main
    run_git("branch -M main", allow_error=True)

    # 6. Push to remote origin
    print("[*] Pushing to GitHub (origin main)...")
    code, out, err = run_git("push -u origin main")

    if code == 0:
        print(f"\n✅ SUCCESS! All files have been synced to GitHub!")
        print(f"🌐 Repository Link: https://github.com/choi75077633-web/win-cli-remote")
    else:
        print(f"\n⚠️ Push requires GitHub credentials or browser login.")
        print(f"   Please run: py git_push.py in your terminal to complete GitHub login.")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    sync_to_github(msg)
