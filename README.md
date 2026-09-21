# 🖥️ Windows CLI Remote Management & Control App

Windows 서버 관리자 스타일의 번호 기반 대화형 CLI 원격 조작 및 모니터링 애플리케이션입니다.

---

## 🚀 빠른 실행 방법 (Quick Start)

### 1. 통합 런처 실행 (추천)
```cmd
py run.py , py C:\Users\A\.gemini\antigravity\scratch\win_cli_remote\run.py
```
- 실행 후 메뉴에서 선택:
  - `1`: 원격 서버 (Agent Server) 실행
  - `2`: 조작 클라이언트 (Client Controller) 실행
  - `3`: 로컬 데모 모드 (서버 + 클라이언트 통합 테스트)

### 2. 개별 실행
- **원격 타겟 컴퓨터 (서버 Agent)**:
  ```cmd
  py server.py
  ```
- **조작 컴퓨터 (클라이언트 Client)**:
  ```cmd
  py client.py
  ```

---

## 📋 CLI 메뉴 항목 및 기능 안내 (Menu Items)

클라이언트 실행 시 1번부터 8번까지의 번호 메뉴가 표시되며, 번호를 입력하여 원격 컴퓨터를 조작합니다:

| 번호 | 기능명 | 주요 특징 및 기능 상세 |
| :---: | :--- | :--- |
| `[1]` | 📊 **System Info & Metrics** | CPU 모델/코어, RAM 사용량%, 디스크 용량, OS 버전, 업타임, IP 주소 실시간 확인 |
| `[2]` | ⚙️ **Process Manager** | 실행 중인 프로세스 목록/메모리/CPU 조회, 이름 검색, 특정 PID/이름 프로세스 강제 종료 |
| `[3]` | 💻 **Interactive Remote Shell** | 원격 컴퓨터의 PowerShell / CMD 명령어를 실시간 입력하고 결과를 출력받는 셸 |
| `[4]` | 🛠️ **Windows Service Manager** | 윈도우 서비스(Running/Stopped) 조회, 특정 서비스 시작(`start`), 중지(`stop`), 재시작(`restart`) |
| `[5]` | 📁 **Remote File Manager** | 원격 디렉터리 탐색(`cd`), 파일 내용 읽기(`read`), 원격 파일 다운로드(`download`) |
| `[6]` | 🌐 **Network & Port Monitor** | Open된 TCP 포트, Listening 상태, 연결된 IP 및 해당 PID/프로세스 정보 모니터링 |
| `[7]` | 📜 **Windows Event Logs** | Windows 이벤트 로그(System/Application/Security)의 최신 오류 및 경고 조회 |
| `[8]` | ⚡ **Power Management** | 원격 컴퓨터 화면 잠금(Lock), 사용자 로그오프(Logoff), 재부팅(Reboot), 시스템 종료(Shutdown) |
| `[0]` | 🚪 **Disconnect** | 원격 연결 안전하게 해제 및 클라이언트 종료 |

---

## ⚙️ 설정 파일 (`config.json`)

`config.json` 파일에서 포트 번호 및 보안 인증 토큰을 자유롭게 변경할 수 있습니다:

```json
{
  "host": "0.0.0.0",
  "port": 9999,
  "auth_token": "WinRemoteSecret2026",
  "timeout": 30
}
```

> ⚠️ **보안 주의사항**: 외부 네트워크/인터넷 연결 시 `auth_token`을 강력한 비밀번호로 변경하세요.

---

## 🛠️ 요구 사항 (Requirements)
- **OS**: Windows 10 / 11 / Server 2016+
- **Runtime**: Python 3.7+ (`py`)
- **의존성**: Python 표준 라이브러리 기반으로 제작되어 별도의 `pip install` 없이 바로 작동합니다.
