import sqlite3, time, math
from pathlib import Path
DB = Path(__file__).parent / "data" / "learner.db"
DB.parent.mkdir(parents=True, exist_ok=True)

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def init():
    with db() as c:
        c.executescript("""CREATE TABLE IF NOT EXISTS mastery(topic TEXT PRIMARY KEY, score REAL, interval REAL, next_review REAL, attempts INT);
        CREATE TABLE IF NOT EXISTS history(ts REAL, topic TEXT, event TEXT, result REAL, avg REAL);
        CREATE TABLE IF NOT EXISTS questions(id TEXT PRIMARY KEY, data TEXT);""")
init()

def get(topic):
    with db() as c:
        r = c.execute("SELECT * FROM mastery WHERE topic=?", (topic,)).fetchone()
    return dict(r) if r else {"topic": topic, "score": 0.3, "interval": 1.0, "next_review": 0.0, "attempts": 0}

def _save(c, m, event, result):
    c.execute("INSERT OR REPLACE INTO mastery VALUES(?,?,?,?,?)", (m["topic"], m["score"], m["interval"], m["next_review"], m["attempts"]))
    avg = c.execute("SELECT AVG(score) FROM mastery").fetchone()[0]
    c.execute("INSERT INTO history VALUES(?,?,?,?,?)", (time.time(), m["topic"], event, result, avg))

def update(topic, result, difficulty=0.5, k=0.25):
    """Elo-style update: expected = sigmoid(4*(mastery-difficulty)); spaced repetition doubles interval on success."""
    m = get(topic)
    exp = 1 / (1 + math.exp(-4 * (m["score"] - difficulty)))
    m["score"] = min(1.0, max(0.0, m["score"] + k * (result - exp)))
    m["interval"] = max(1.0, m["interval"] * 2) if result >= 0.7 else 1.0
    m["next_review"] = time.time() + m["interval"] * 86400
    m["attempts"] += 1
    with db() as c: _save(c, m, "quiz", result)
    return m

def nudge(topic, delta):
    m = get(topic); m["score"] = min(1.0, max(0.0, m["score"] + delta))
    with db() as c: _save(c, m, "tutor", delta)

def pick(topics):
    now = time.time(); ms = [get(t) for t in topics]
    ms.sort(key=lambda m: (m["next_review"] > now, m["score"]))
    return ms[0]["topic"] if ms else None

def all_mastery():
    with db() as c: return [dict(r) for r in c.execute("SELECT * FROM mastery ORDER BY score")]

def history():
    with db() as c: return [dict(r) for r in c.execute("SELECT ts, avg FROM history ORDER BY ts")]

def save_question(qid, data):
    import json
    with db() as c: c.execute("INSERT OR REPLACE INTO questions VALUES(?,?)", (qid, json.dumps(data)))

def load_question(qid):
    import json
    with db() as c: r = c.execute("SELECT data FROM questions WHERE id=?", (qid,)).fetchone()
    return json.loads(r[0]) if r else None
