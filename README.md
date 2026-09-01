# Docker-G

Docker Compose로 **DB · API · Back · Front** 4개 서비스를 한 번에 띄우는 실습 프로젝트입니다.

## 구성

```
브라우저
   │  localhost:3000
   ▼
front   React + Vite          :3000
   │  localhost:8080  (브라우저에서 호출 → localhost)
   ▼
back    Spring Boot           :8080
   │  http://api:8000  (컨테이너끼리 → 서비스 이름)
   ▼
api     FastAPI               :8000
   │  db:5432
   ▼
db      PostgreSQL 16         :5432
```

**핵심 포인트**: 컨테이너끼리는 `localhost`가 아니라 **서비스 이름**(`db`, `api`)으로 통신합니다. 반면 브라우저는 컨테이너 밖에서 돌기 때문에 `localhost:8080`이 맞습니다.

## 폴더 구조

```
Docker-G/
├── compose.yml         4개 서비스 정의
├── .env.example        환경변수 예시 (복사해서 .env로 사용)
├── db/init.sql         테이블 생성 + 샘플 데이터
├── api/                FastAPI — DB에 직접 붙는 유일한 서비스
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── back/               Spring Boot — 프론트와 API 사이 중간 계층
│   ├── Dockerfile      멀티 스테이지 빌드
│   ├── build.gradle
│   └── src/main/...
└── front/              React + Vite
    ├── Dockerfile
    └── src/
```

## 실행

```bash
# 1. 환경변수 파일 준비
cp .env.example .env

# 2. 빌드 + 실행 (처음엔 Gradle/npm 다운로드로 5~10분 걸립니다)
docker compose up --build

# 백그라운드로 돌리려면
docker compose up --build -d
```

접속 주소:

| 서비스 | 주소 |
|---|---|
| 프론트엔드 | http://localhost:3000 |
| Spring API | http://localhost:8080/api/memos |
| FastAPI 문서 | http://localhost:8000/docs |
| PostgreSQL | `localhost:5432` (appuser / apppassword) |

## 자주 쓰는 명령어

```bash
# 상태 확인
docker compose ps

# 로그 보기 (에러 잡을 때 제일 많이 씁니다)
docker compose logs -f          # 전체
docker compose logs -f api      # 특정 서비스만

# 컨테이너 안으로 들어가기
docker compose exec api bash
docker compose exec db psql -U appuser -d appdb

# 특정 서비스만 다시 빌드/재시작
docker compose build back
docker compose restart back
docker compose up -d --build back

# 중지
docker compose stop             # 멈추기만 (데이터 유지)
docker compose down             # 컨테이너 삭제 (DB 볼륨은 남음)
docker compose down -v          # 볼륨까지 삭제 (DB 데이터 초기화)

# 정리
docker system prune -a          # 안 쓰는 이미지 전부 삭제
```

## 동작 확인

```bash
# api 단독 확인
curl http://localhost:8000/memos

# back을 거쳐서 확인 (back → api → db 경로가 살아있는지)
curl http://localhost:8080/api/memos

# 메모 추가
curl -X POST http://localhost:8080/api/memos \
  -H "Content-Type: application/json" \
  -d '{"title":"테스트","content":"컨테이너에서 저장됨"}'

# DB에서 직접 확인
docker compose exec db psql -U appuser -d appdb -c "SELECT * FROM memos;"
```

## 실습해볼 것

1. **볼륨 확인** — 메모를 추가하고 `docker compose down` 후 다시 `up`. 데이터가 남아 있습니다. `down -v` 로 내리면 사라집니다.
2. **코드 핫 리로드** — `api/main.py`나 `front/src/App.jsx`를 수정하면 재빌드 없이 바로 반영됩니다. 볼륨 마운트 덕분입니다.
3. **의존성 순서** — `docker compose up db` 만 실행해보고, 그다음 `docker compose up api` 를 하면 api가 db를 기다렸다 뜨는 걸 볼 수 있습니다.
4. **Spring은 왜 재빌드가 필요한가** — `back`은 볼륨 마운트가 없어서 코드를 고치면 `docker compose up -d --build back` 이 필요합니다.

## 문제 해결

| 증상 | 확인할 것 |
|---|---|
| `port is already allocated` | 이미 그 포트를 쓰는 중. `compose.yml`의 왼쪽 포트 번호를 바꾸세요 |
| 프론트에서 "백엔드에 연결하지 못했습니다" | `docker compose logs back` 확인. CORS는 `WebConfig.java`에 설정돼 있습니다 |
| api가 계속 재시작 | `docker compose logs api`. DB 접속 주소가 `db`인지 확인 |
| `init.sql`을 고쳤는데 반영이 안 됨 | 최초 1회만 실행됩니다. `docker compose down -v` 후 다시 up |
| back 빌드가 너무 오래 걸림 | 첫 빌드는 Gradle 의존성 다운로드로 원래 오래 걸립니다 |
| 파일을 고쳐도 반영 안 됨 | 볼륨 마운트가 있는지 (`api`, `front`만 있음) 확인 |


34skn 3nd 1team