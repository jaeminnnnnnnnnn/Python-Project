# Python Online Tetris

`pygame-ce` 클라이언트와 `FastAPI` 서버로 만드는 온라인 테트리스 프로젝트입니다.

## 실행

```powershell
python -m client.main
```

```powershell
uvicorn server.main:app --reload
```

로컬 서버에 붙여 테스트할 때는:

```powershell
.\scripts\run_client_local.ps1
```

## Fly.io 서버 배포

`fly.toml`의 `app` 값을 실제 Fly.io 앱 이름으로 바꾼 뒤 배포합니다.

```powershell
fly launch
fly deploy
```

배포 후 서버 주소를 `client/assets/config/server.json`에 반영합니다.

## exe 빌드

```powershell
pip install -r requirements.txt
.\scripts\build_client_exe.ps1
```

빌드 결과는 `dist/PythonOnlineTetris.exe`에 생성됩니다. 게임 이미지, 음악, 효과음은 `client/assets` 아래에 두면 exe에 같이 포함됩니다.

최종 사용자에게는 `dist/PythonOnlineTetris.exe`만 전달하면 됩니다. 서버 주소는 빌드 전에 `client/assets/config/server.json`에 넣어 exe에 포함합니다.

## 현재 구현 상태

- pygame 클라이언트 실행 뼈대
- Intro, Menu, Single, Online Lobby, Options 씬
- Intro 게임명 `GTRIS` 표시
- Options에서 배경음악, 효과음, 공통/게임 조작키 변경, 게임 종료 제공
- SRS 회전 킥, 고스트 피스, 홀드, 7-bag 기반 테트리스 로직
- 공통 `Hold + Board + Next` 게임 패널 UI
- 싱글/온라인 내 보드/상대 보드 동일 크기 표시
- 음악/효과음 on/off 설정과 오디오 매니저 연결
- FastAPI 방 생성/조회/입장 API 뼈대
- 온라인 로비 방 제목/비밀번호 방 생성 및 비밀번호 입장 UI
- 온라인 로비 서버 연결 상태 표시와 재시도 흐름
- WebSocket 룸 브로드캐스트 뼈대
- 온라인 매치 양쪽 보드 표시
- 온라인 매치 시작 3초 카운트다운
- 서버 match seed 기반 동일 7-bag 블록 순서
- 온라인 플레이어 P1/P2 표시
- 콤보/백투백을 반영한 공격 줄 전송
- 게임오버 기반 승패 표시
- 매치 종료 후 방으로 복귀해 재준비 가능
- heartbeat 기반 접속 끊김 감지와 stale player 자동 정리
