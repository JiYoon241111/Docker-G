"""데이터 계층 API. DB와 직접 통신하는 유일한 서비스입니다."""
#
import os
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://appuser:apppassword@db:5432/appdb"
)

app = FastAPI(title="Docker-G API", version="1.0.0")


def make_engine(retries: int = 10, delay: int = 3):
    """DB가 아직 준비되지 않았을 수 있으므로 잠시 재시도합니다."""
    for attempt in range(1, retries + 1):
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"DB 연결 성공 (시도 {attempt}회)")
            return engine
        except OperationalError as exc:
            print(f"DB 연결 대기 중... ({attempt}/{retries}) {exc.__class__.__name__}")
            time.sleep(delay)
    raise RuntimeError("DB에 연결하지 못했습니다.")


engine = make_engine()


class MemoIn(BaseModel):
    title: str
    content: str = ""


@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "service": "api"}


@app.get("/memos")
def list_memos():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, title, content, created_at FROM memos ORDER BY id DESC")
        ).mappings()
        return [dict(row) for row in rows]


@app.post("/memos", status_code=201)
def create_memo(memo: MemoIn):
    if not memo.title.strip():
        raise HTTPException(status_code=400, detail="제목을 입력하세요.")
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "INSERT INTO memos (title, content) VALUES (:t, :c) "
                "RETURNING id, title, content, created_at"
            ),
            {"t": memo.title.strip(), "c": memo.content},
        ).mappings().one()
        return dict(row)


@app.delete("/memos/{memo_id}", status_code=204)
def delete_memo(memo_id: int):
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM memos WHERE id = :id"), {"id": memo_id}
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="해당 메모가 없습니다.")
