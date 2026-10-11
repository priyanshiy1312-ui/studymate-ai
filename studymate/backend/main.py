import shutil, tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import ingest, store, engine

app = FastAPI(title="StudyMate")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/files", StaticFiles(directory=str(ingest.UP)), name="files")

class Ask(BaseModel): question: str; reveal: bool = False
class Yt(BaseModel): url: str
class Ans(BaseModel): qid: str; answer: str

@app.post("/api/ingest")
async def up(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / file.filename
        with open(p, "wb") as f: shutil.copyfileobj(file.file, f)
        try: chunks = ingest.ingest_path(p, file.filename)
        except ValueError as e: raise HTTPException(400, str(e))
    store.add(chunks)
    return {"chunks": len(chunks), "topics": sorted({c["topic"] for c in chunks})}

@app.post("/api/ingest/youtube")
def yt(b: Yt):
    chunks = ingest.ingest_youtube(b.url); store.add(chunks)
    return {"chunks": len(chunks), "topics": sorted({c["topic"] for c in chunks})}

@app.get("/api/sources")
def sources(): return store.sources()

@app.post("/api/ask")
def ask(b: Ask): return engine.answer_question(b.question, b.reveal)

@app.post("/api/quiz/next")
def qnext():
    q = engine.next_question()
    if not q: raise HTTPException(400, "Upload study material first.")
    return q

@app.post("/api/quiz/answer")
def qans(b: Ans):
    try: return engine.grade(b.qid, b.answer)
    except ValueError as e: raise HTTPException(404, str(e))

@app.get("/api/dashboard")
def dash(): return engine.dashboard()
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def any_error(request: Request, exc: Exception):
    return JSONResponse({"detail": f"{type(exc).__name__}: {exc}"}, status_code=500,
                        headers={"Access-Control-Allow-Origin": "*"})
