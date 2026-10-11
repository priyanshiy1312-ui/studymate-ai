"""Evaluates StudyMate on 20 chunks: citation accuracy + question quality. Run after load_sample.py. Output: results.json"""
import sys, json, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
import store, engine
from llm import chat_json

random.seed(7)
chunks = [c for c in store.all_chunks() if len(c["text"].split()) > 25]
sample = random.sample(chunks, min(20, len(chunks)))
rows, cite_hit, supported, qual = [], 0, 0, []
for c in sample:
    q = chat_json("Write one factual question that this passage answers.", f"Passage: {c['text']}\nJSON: " '{"question": str}')["question"]
    r = engine.answer_question(q, reveal=True)
    cited = {int(n) - 1 for n in __import__("re").findall(r"\[S(\d+)\]", r["answer"])}
    cited_ids = {r["sources"][i]["id"] for i in cited if i < len(r["sources"])}
    hit = c["id"] in cited_ids; cite_hit += hit
    cited_text = "\n".join(r["sources"][i]["text"] for i in cited if i < len(r["sources"]))
    sup = 0
    if cited_text:
        sup = int(chat_json("Judge strictly.", f"Answer: {r['answer']}\nCited text: {cited_text}\nIs every claim in the answer supported by the cited text? " 'JSON: {"supported": 0 or 1}')["supported"])
    supported += sup
    gq = engine.gen_question(c["topic"])
    full = engine.learner.load_question(gq["id"])
    s = chat_json("Rate an exam question.", f"Source: {full['citation']['text']}\nQuestion: {full['question']}\nAnswer: {full['answer']}\n" 'Rate 1-5 for groundedness in the source and clarity. JSON: {"score": int}')["score"]
    qual.append(s)
    rows.append({"question": q, "source_retrieved_and_cited": hit, "answer_supported": bool(sup), "quiz_question_quality": s})
res = {"n": len(sample), "citation_recall": cite_hit / len(sample), "citation_support_rate": supported / len(sample),
       "avg_question_quality_1to5": sum(qual) / len(qual), "items": rows}
Path(__file__).with_name("results.json").write_text(json.dumps(res, indent=2))
print({k: v for k, v in res.items() if k != "items"})
