import json, math, re, sqlite3
from pathlib import Path
from llm import embed

DB = Path(__file__).parent / "data" / "kb.db"
DB.parent.mkdir(parents=True, exist_ok=True)
tok = lambda s: re.findall(r"\w+", s.lower())

def _db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

with _db() as _c:
    _c.execute("CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY, source_id TEXT, source_name TEXT, type TEXT, loc TEXT, topic TEXT, text TEXT, emb TEXT)")

def _norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]

def add(chunks):
    if not chunks: return
    vecs = embed([c["text"] for c in chunks])
    with _db() as c:
        c.executemany("INSERT OR REPLACE INTO chunks VALUES(?,?,?,?,?,?,?,?)",
                      [(k["id"], k["source_id"], k["source_name"], k["type"], json.dumps(k["loc"]), k["topic"], k["text"],
                        json.dumps([round(x, 5) for x in _norm(v)])) for k, v in zip(chunks, vecs)])

def _row(r, emb=False):
    d = {"id": r["id"], "text": r["text"], "source_id": r["source_id"], "source_name": r["source_name"], "type": r["type"],
         "loc": json.loads(r["loc"]), "topic": r["topic"], "dist": None}
    if emb: d["emb"] = json.loads(r["emb"])
    return d

def all_chunks(topic=None, emb=False):
    with _db() as c:
        rows = c.execute("SELECT * FROM chunks WHERE topic=?", (topic,)).fetchall() if topic else c.execute("SELECT * FROM chunks").fetchall()
    return [_row(r, emb) for r in rows]

def topics(): return sorted({c["topic"] for c in all_chunks()})

def sources():
    seen = {}
    for c in all_chunks():
        s = seen.setdefault(c["source_id"], {"source_id": c["source_id"], "name": c["source_name"], "type": c["type"], "chunks": 0})
        s["chunks"] += 1
    return list(seen.values())

def mmss(s): return f"{s // 60}:{s % 60:02d}"

def label(c):
    l = c["loc"]
    if c["type"] == "video": return f'{c["source_name"]}, {mmss(l["t"])}'
    if c["type"] == "pdf": return f'{c["source_name"]} p.{l["page"]}'
    return f'{c["source_name"]} Slide {l["slide"]}'

def public(c):
    return {"id": c["id"], "label": label(c), "type": c["type"], "loc": c["loc"], "text": c["text"], "topic": c["topic"]}

def _bm25(q, docs, k1=1.5, b=0.75):
    toks = [tok(d) for d in docs]; N = len(toks); avg = (sum(map(len, toks)) / N) or 1
    df = {}
    for t in toks:
        for w in set(t): df[w] = df.get(w, 0) + 1
    qs, out = set(tok(q)), []
    for t in toks:
        tf = {}
        for w in t: tf[w] = tf.get(w, 0) + 1
        s = 0.0
        for w in qs:
            if w in tf:
                s += math.log(1 + (N - df[w] + .5) / (df[w] + .5)) * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * len(t) / avg))
        out.append(s)
    return out

def hybrid(q, k=6):
    rows = all_chunks(emb=True)
    if not rows: return []
    qv = _norm(embed([q], "RETRIEVAL_QUERY")[0])
    for r in rows:
        r["dist"] = 1 - sum(a * b for a, b in zip(qv, r.pop("emb")))  # cosine distance
    sem = sorted(rows, key=lambda r: r["dist"])[:12]
    sc = _bm25(q, [r["text"] for r in rows])
    kw = [rows[i] for i in sorted(range(len(rows)), key=lambda i: -sc[i])[:12] if sc[i] > 0]
    fused = {}
    for lst in (sem, kw):  # reciprocal rank fusion of semantic + BM25
        for rank, r in enumerate(lst):
            f = fused.setdefault(r["id"], dict(r, score=0.0)); f["score"] += 1 / (60 + rank)
    for f in fused.values():  # rerank: boost by semantic similarity
        f["score"] += (1 - f["dist"]) * 0.05
    return sorted(fused.values(), key=lambda r: -r["score"])[:k]
