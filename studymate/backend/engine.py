import random, uuid, time
import store, learner
from llm import chat, chat_json

import os
MIN_CONF = float(os.getenv("MIN_CONF", "0.55"))

def answer_question(question, reveal=False):
    hits = store.hybrid(question, 6)
    dists = [h["dist"] for h in hits if h["dist"] is not None]
    conf = round(max(0.0, 1 - min(dists)), 2) if dists else 0.0
    if not hits or conf < MIN_CONF:
        return {"answer": "I can't find this in your uploaded materials, so I won't guess. Try rephrasing, or upload the relevant lecture, chapter or slides.",
                "sources": [], "confidence": conf, "mode": "unsupported", "topic": None}
    topic = max({h["topic"] for h in hits}, key=lambda t: sum(1 for h in hits if h["topic"] == t))
    m = learner.get(topic)
    ctx = "\n\n".join(f"[S{i + 1}] ({store.label(h)}) {h['text']}" for i, h in enumerate(hits))
    socratic = (not reveal) and m["score"] < 0.6
    system = ("You are StudyMate, a personal tutor. Use ONLY the numbered sources. Cite every claim inline like [S1] or [S2][S3]. "
              "If the sources don't cover something, say so. ")
    system += ("The learner's mastery of this topic is low and they have not asked for the full answer: do NOT give it. Give one short hint with a citation, "
               "then ask ONE guiding question that leads them toward the answer. End with: 'Tap Show full answer if you want it.'" if socratic else
               f"Give a clear, complete answer. Learner mastery of this topic is {m['score']:.2f} (0-1); match the depth to it.")
    text = chat(system, f"Sources:\n{ctx}\n\nQuestion: {question}", 900)
    learner.nudge(topic, -0.02 if reveal else 0.01)
    return {"answer": text, "sources": [store.public(h) for h in hits], "confidence": conf,
            "mode": "socratic" if socratic else "full", "topic": topic}

def gen_question(topic):
    m = learner.get(topic)
    chunks = store.all_chunks(topic); random.shuffle(chunks); ch = chunks[:3]
    diff = min(0.95, max(0.1, m["score"] + 0.1))
    qtype = "mcq" if diff < 0.4 else "short" if diff < 0.7 else "application"
    ctx = "\n\n".join(f"[{i}] ({store.label(c)}) {c['text']}" for i, c in enumerate(ch))
    q = chat_json("You write exam questions grounded ONLY in the given sources.",
        f"Topic: {topic}\nType: {qtype} (mcq = 4 options; short = recall/explain in 1-3 sentences; application = apply the concept to a new scenario)\n"
        f"Difficulty (0-1): {diff:.2f}\nSources:\n{ctx}\n\n"
        'JSON: {"question": str, "options": [4 strings starting "A) ".."D) " - mcq only, else []], "answer": "A-D letter for mcq, else model answer", '
        '"explanation": str, "rubric": "key points a correct answer must contain", "source": index of the source used}')
    src = ch[min(int(q.get("source", 0)), len(ch) - 1)]
    qid = uuid.uuid4().hex[:10]
    data = {"id": qid, "topic": topic, "type": qtype, "difficulty": diff, "question": q["question"], "options": q.get("options") or [],
            "answer": q["answer"], "explanation": q.get("explanation", ""), "rubric": q.get("rubric", ""), "citation": store.public(src)}
    learner.save_question(qid, data)
    return {k: data[k] for k in ("id", "topic", "type", "difficulty", "question", "options")}

def next_question():
    t = learner.pick(store.topics())
    if not t: return None
    return gen_question(t)

def grade(qid, user_answer):
    q = learner.load_question(qid)
    if not q: raise ValueError("Unknown question")
    lab = q["citation"]["label"]
    if q["type"] == "mcq":
        score = 1.0 if user_answer.strip().upper()[:1] == q["answer"].strip().upper()[:1] else 0.0
        fb = f'{q["explanation"]} [{lab}]'
    else:
        g = chat_json("You are a strict but encouraging grader.",
            f"Question: {q['question']}\nModel answer: {q['answer']}\nRubric: {q['rubric']}\nSource ({lab}): {q['citation']['text']}\n"
            f"Student answer: {user_answer}\n\nJSON: " '{"score": 0.0-1.0, "feedback": "explain what was right/missing, and end by citing the source label in square brackets"}')
        score, fb = max(0.0, min(1.0, float(g["score"]))), g["feedback"]
    m = learner.update(q["topic"], score, q["difficulty"])
    return {"score": score, "correct": score >= 0.7, "feedback": fb, "answer": q["answer"], "citation": q["citation"],
            "mastery": round(m["score"], 2), "next_review_days": m["interval"]}

def dashboard():
    ms = learner.all_mastery(); now = time.time()
    weak = [m for m in ms if m["score"] < 0.5]
    plan = []
    for m in (weak or ms)[:3]:
        ch = store.all_chunks(m["topic"])[:1]
        plan.append({"topic": m["topic"], "mastery": round(m["score"], 2), "action": "Review, then take 3 practice questions",
                     "source": store.public(ch[0]) if ch else None})
    unseen = [t for t in store.topics() if t not in {m["topic"] for m in ms}]
    return {"mastery": [{"topic": m["topic"], "score": round(m["score"], 2), "due": m["next_review"] <= now, "attempts": m["attempts"]} for m in ms],
            "unseen": unseen, "weak": [m["topic"] for m in weak], "history": learner.history(), "plan": plan}
