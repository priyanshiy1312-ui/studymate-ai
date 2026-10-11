"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API || "http://localhost:8000";
const post = (p, body) => fetch(API + p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) }).then(async r => { const j = await r.json(); if (!r.ok) throw new Error(j.detail || "Request failed"); return j; });
const get = p => fetch(API + p).then(r => r.json());
const btn = "rounded-lg px-4 py-2 text-sm font-medium bg-ink text-paper hover:bg-moss transition-colors disabled:opacity-40 disabled:cursor-not-allowed";
const ghost = "rounded-lg px-3 py-1.5 text-sm border border-line bg-white hover:border-moss transition-colors disabled:opacity-40";
const TYPE = { video: { n: "Lecture", c: "#B4452F" }, pdf: { n: "Textbook", c: "#2F6F5E" }, slide: { n: "Slides", c: "#3A5BA0" } };
const SUGGEST = ["Why does a large learning rate hurt training?", "What is the difference between overfitting and underfitting?", "How does L2 regularization work?"];

const Pill = ({ t }) => { const x = TYPE[t] || TYPE.pdf; return <span className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-full" style={{ background: x.c + "1A", color: x.c }}><i className="w-1.5 h-1.5 rounded-full" style={{ background: x.c }} />{x.n}</span>; };
const Dots = () => <span className="inline-flex gap-1 items-center"><i className="dot" /><i className="dot" /><i className="dot" /></span>;
const Bar = ({ v, c = "#2F6F5E" }) => <div className="h-1.5 w-24 rounded-full bg-line overflow-hidden"><div className="h-full rounded-full" style={{ width: `${Math.round(v * 100)}%`, background: c }} /></div>;

function Cited({ text, sources, open }) {
  return text.split(/(\[S\d+\])/g).map((p, i) => {
    const m = p.match(/^\[S(\d+)\]$/); const s = m && sources[+m[1] - 1];
    if (!m) return <span key={i}>{p}</span>;
    return s ? <button key={i} className="cite" onClick={() => open(s)} title="Open source"><i className="w-1.5 h-1.5 rounded-full" style={{ background: (TYPE[s.type] || TYPE.pdf).c }} />{s.label}</button> : null;
  });
}

function Viewer({ s, close }) {
  if (!s) return null; const l = s.loc; let media = null;
  if (s.type === "video") {
    const id = l.url && (l.url.match(/(?:v=|youtu\.be\/)([\w-]{11})/) || [])[1];
    if (id) media = <iframe className="w-full aspect-video rounded-lg" src={`https://www.youtube.com/embed/${id}?start=${l.t}`} allowFullScreen />;
    else if (l.file) media = <video key={s.id} className="w-full rounded-lg" controls src={`${API}${l.file}#t=${l.t}`} />;
  }
  if (s.type === "pdf" && l.file) media = <iframe className="w-full h-80 rounded-lg border border-line" src={`${API}${l.file}#page=${l.page}`} />;
  return (
    <aside className="fixed right-0 top-0 h-full w-full max-w-md bg-white border-l border-line p-5 overflow-y-auto shadow-2xl z-20" aria-label="Source viewer">
      <div className="flex justify-between items-start mb-4 gap-3">
        <div><Pill t={s.type} /><h3 className="font-serif text-xl mt-2">{s.label}</h3><p className="text-xs text-ink/60 mt-0.5">Topic: {s.topic}</p></div>
        <button className={ghost} onClick={close}>Close</button>
      </div>
      {media}
      <p className="text-xs uppercase tracking-wide text-ink/50 mt-4 mb-1">Cited passage</p>
      <p className="text-sm leading-relaxed whitespace-pre-wrap bg-paper rounded-lg p-3 border-l-4 border-mark">{s.text}</p>
    </aside>
  );
}

function Upload({ onDone }) {
  const [busy, setBusy] = useState(false), [msg, setMsg] = useState(""), [url, setUrl] = useState(""), [list, setList] = useState([]);
  const load = () => get("/api/sources").then(setList).catch(() => {});
  useEffect(() => { load(); }, []);
  const run = async fn => { setBusy(true); setMsg("Processing. Videos can take a few minutes."); try { const r = await fn(); setMsg(`Added ${r.chunks} passages across ${r.topics.length} topics.`); load(); onDone(); } catch (e) { setMsg(e.message); } setBusy(false); };
  const file = e => { const f = e.target.files[0]; if (!f) return; const fd = new FormData(); fd.append("file", f); run(() => fetch(API + "/api/ingest", { method: "POST", body: fd }).then(async r => { const j = await r.json(); if (!r.ok) throw new Error(j.detail); return j; })); e.target.value = ""; };
  return (
    <section className="card p-5 space-y-3">
      <h2 className="font-serif text-xl">Your materials</h2>
      <label className="block rounded-lg border-2 border-dashed border-line hover:border-moss p-4 text-center cursor-pointer transition-colors">
        <span className="block text-sm font-medium">{busy ? "Working..." : "Drop in a lecture, textbook or slides"}</span>
        <span className="block text-xs text-ink/60 mt-1">PDF, PPTX, MP4/MP3, or a timestamped transcript</span>
        <input type="file" className="hidden" disabled={busy} onChange={file} accept=".pdf,.pptx,.txt,.vtt,.mp4,.mp3,.wav,.m4a,.mkv,.webm" /></label>
      <div className="flex gap-2"><input value={url} onChange={e => setUrl(e.target.value)} placeholder="Or paste a YouTube lecture link" className="flex-1 min-w-0 border border-line rounded-lg px-3 py-1.5 text-sm bg-white" />
        <button className={btn} disabled={busy || !url} onClick={() => run(() => post("/api/ingest/youtube", { url }))}>Add</button></div>
      {msg && <p className="text-sm text-moss" role="status">{msg}</p>}
      {list.length === 0 ? <p className="text-sm text-ink/60">Nothing here yet. Add a source to begin.</p> :
        <ul className="space-y-2">{list.map(s => <li key={s.source_id} className="flex items-center justify-between gap-2 text-sm"><span className="truncate">{s.name}</span><span className="flex items-center gap-2 shrink-0"><Pill t={s.type} /><span className="text-xs text-ink/50">{s.chunks}</span></span></li>)}</ul>}
    </section>
  );
}

function Chat({ open }) {
  const [msgs, setMsgs] = useState([]), [q, setQ] = useState(""), [busy, setBusy] = useState(false);
  const ask = async (question, reveal = false) => {
    setBusy(true); if (!reveal) setMsgs(m => [...m, { role: "user", text: question }]);
    try { const r = await post("/api/ask", { question, reveal }); setMsgs(m => [...m, { role: "ai", ...r, question }]); }
    catch (e) { setMsgs(m => [...m, { role: "ai", text: e.message, sources: [], mode: "error" }]); }
    setBusy(false);
  };
  const send = t => { if (t && !busy) { ask(t); setQ(""); } };
  const badge = { socratic: ["Guided hint", "#B4452F"], full: ["Full answer", "#2F6F5E"], unsupported: ["Not in your sources", "#6B7280"] };
  return (
    <section className="space-y-5">
      {msgs.length === 0 && <div className="card p-6">
        <h3 className="font-serif text-2xl">Ask your materials anything</h3>
        <p className="text-ink/60 mt-1 mb-4">Answers combine your lectures, textbook and slides, and every claim links back to the exact timestamp, page or slide.</p>
        <div className="grid gap-2 sm:grid-cols-3">{SUGGEST.map(s => <button key={s} className="chip" onClick={() => send(s)}>{s}</button>)}</div></div>}
      {msgs.map((m, i) => m.role === "user" ? <p key={i} className="font-serif text-xl pt-2">{m.text}</p> :
        <div key={i} className="card p-5 leading-relaxed">
          {badge[m.mode] && <span className="inline-block text-[11px] font-semibold uppercase tracking-wide mb-2" style={{ color: badge[m.mode][1] }}>{badge[m.mode][0]}</span>}
          <p><Cited text={m.answer || m.text} sources={m.sources} open={open} /></p>
          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-ink/60 border-t border-line pt-3">
            {m.mode !== "error" && <span className="flex items-center gap-2">Confidence <Bar v={m.confidence || 0} c={m.confidence > 0.5 ? "#2F6F5E" : "#E0A030"} /> {Math.round((m.confidence || 0) * 100)}%</span>}
            {m.topic && <span>Topic: {m.topic}</span>}
            {m.mode === "socratic" && <button className={ghost} disabled={busy} onClick={() => ask(m.question, true)}>Show full answer</button>}
          </div>
        </div>)}
      {busy && <p className="text-sm text-ink/60 flex items-center gap-2"><Dots /> Searching your sources</p>}
      <div className="flex gap-2 sticky bottom-4">
        <input value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === "Enter" && send(q)} placeholder="Ask a question about your materials" className="flex-1 border border-line rounded-lg px-4 py-3 bg-white shadow-sm" />
        <button className={btn} disabled={busy || !q} onClick={() => send(q)}>Ask</button>
      </div>
    </section>
  );
}

function Quiz({ open }) {
  const [q, setQ] = useState(null), [res, setRes] = useState(null), [a, setA] = useState(""), [busy, setBusy] = useState(false), [err, setErr] = useState(""), [n, setN] = useState(0), [right, setRight] = useState(0);
  const next = async () => { setBusy(true); setRes(null); setA(""); setErr(""); try { setQ(await post("/api/quiz/next")); setN(x => x + 1); } catch (e) { setErr(e.message); } setBusy(false); };
  const submit = async ans => { setBusy(true); try { const r = await post("/api/quiz/answer", { qid: q.id, answer: ans }); setRes(r); if (r.correct) setRight(x => x + 1); } catch (e) { setErr(e.message); } setBusy(false); };
  const kind = { mcq: "Multiple choice", short: "Short answer", application: "Application" };
  return (
    <section className="space-y-4">
      {!q && <div className="card p-6"><h3 className="font-serif text-2xl">Adaptive practice</h3>
        <p className="text-ink/60 mt-1 mb-4">Questions come from your own sources, aim just above your current level, and bring weak or due topics back first.</p>
        <button className={btn} onClick={next} disabled={busy}>{busy ? "Preparing..." : "Start practice"}</button></div>}
      {err && <p className="text-red-700 text-sm" role="alert">{err}</p>}
      {q && <div className="card p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink/60">
          <span className="font-medium text-ink">{q.topic}</span>
          <span className="flex items-center gap-3">{kind[q.type]} <span className="flex items-center gap-1.5">Difficulty <Bar v={q.difficulty} c="#B4452F" /></span> <span>Question {n}, {right} correct</span></span></div>
        <p className="font-serif text-2xl leading-snug">{q.question}</p>
        {!res && (q.type === "mcq" ? <div className="grid gap-2">{q.options.map((o, i) => <button key={i} disabled={busy} className="chip" onClick={() => submit("ABCD"[i])}>{o}</button>)}</div> :
          <><textarea value={a} onChange={e => setA(e.target.value)} rows={4} className="w-full border border-line rounded-lg p-3" placeholder="Write your answer in your own words" /><button className={btn} disabled={busy || !a} onClick={() => submit(a)}>{busy ? "Grading..." : "Check answer"}</button></>)}
        {res && <div className={`rounded-lg p-4 space-y-3 ${res.correct ? "bg-moss/10" : "bg-mark/20"}`}>
          <p className="font-medium">{res.correct ? "Correct" : res.score > 0 ? "Partly right" : "Not quite"}</p>
          <p className="text-sm leading-relaxed">{res.feedback}</p>
          <p className="flex items-center gap-2 text-xs text-ink/60">Topic mastery <Bar v={res.mastery} /> {Math.round(res.mastery * 100)}%</p>
          <div className="flex gap-2"><button className={ghost} onClick={() => open(res.citation)}>Open source: {res.citation.label}</button><button className={btn} onClick={next} disabled={busy}>Next question</button></div></div>}
      </div>}
    </section>
  );
}

function Dash({ open, tick }) {
  const [d, setD] = useState(null);
  useEffect(() => { get("/api/dashboard").then(setD).catch(() => {}); }, [tick]);
  if (!d) return <p className="text-ink/60">Loading...</p>;
  const h = d.history.map(x => x.avg), W = 300, H = 80, ms = d.mastery;
  const avg = ms.length ? ms.reduce((s, m) => s + m.score, 0) / ms.length : 0;
  const pts = h.map((v, i) => `${h.length < 2 ? 0 : (i / (h.length - 1)) * W},${H - v * H}`).join(" ");
  const col = s => `rgba(47,111,94,${0.1 + s * 0.9})`;
  const stats = [["Average mastery", `${Math.round(avg * 100)}%`], ["Topics mastered", `${ms.filter(m => m.score >= 0.7).length} of ${ms.length + d.unseen.length}`], ["Due for review", ms.filter(m => m.due && m.attempts).length]];
  return (
    <section className="space-y-6">
      <div className="grid grid-cols-3 gap-3">{stats.map(([k, v]) => <div key={k} className="card p-4"><p className="text-xs text-ink/60">{k}</p><p className="font-serif text-2xl mt-1">{v}</p></div>)}</div>
      <div className="card p-5"><h3 className="font-serif text-lg mb-3">Mastery by topic</h3>
        {ms.length + d.unseen.length === 0 ? <p className="text-ink/60 text-sm">No topics yet. Upload material, then take a quiz.</p> :
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {ms.map(m => { const dark = m.score > 0.5; return <div key={m.topic} className="rounded-lg p-3" style={{ background: col(m.score) }}><p className="text-sm font-medium" style={{ color: dark ? "#fff" : "#1B2A41" }}>{m.topic}</p><p className="text-xs" style={{ color: dark ? "#fff" : "#1B2A41" }}>{Math.round(m.score * 100)}%{m.due && m.attempts ? ", due" : ""}</p></div>; })}
            {d.unseen.map(t => <div key={t} className="rounded-lg p-3 border border-dashed border-line"><p className="text-sm">{t}</p><p className="text-xs text-ink/50">Not attempted</p></div>)}
          </div>}</div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-5"><h3 className="font-serif text-lg mb-3">Progress over time</h3>
          {h.length < 2 ? <p className="text-ink/60 text-sm">Answer a few questions to see your trend.</p> :
            <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-24"><polyline points={pts} fill="none" stroke="#2F6F5E" strokeWidth="2" strokeLinejoin="round" /></svg>}</div>
        <div className="card p-5"><h3 className="font-serif text-lg mb-3">Weak topics</h3>
          <p className="text-sm">{d.weak.length ? d.weak.join(", ") : "None below 50%."}</p></div>
      </div>
      <div className="card p-5"><h3 className="font-serif text-lg mb-3">Next study session</h3>
        {d.plan.length === 0 ? <p className="text-ink/60 text-sm">Your plan appears after your first quiz.</p> :
          <ol className="space-y-3 list-decimal pl-5 text-sm">{d.plan.map(p => <li key={p.topic}><span className="font-medium">{p.topic}</span> ({Math.round(p.mastery * 100)}%): {p.action}. {p.source && <button className="cite" onClick={() => open(p.source)}>{p.source.label}</button>}</li>)}</ol>}</div>
    </section>
  );
}

export default function Page() {
  const [tab, setTab] = useState("Tutor"), [view, setView] = useState(null), [tick, setTick] = useState(0);
  const steps = [["1", "Upload", "Lectures, books and slides in one place"], ["2", "Ask", "Cited answers, Socratic hints"], ["3", "Practice", "Adaptive quizzes, tracked mastery"]];
  return (
    <>
      <header className="border-b border-line bg-white/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-5 py-3 flex items-center justify-between gap-3">
          <div className="flex items-baseline gap-3"><h1 className="font-serif text-2xl">StudyMate</h1><span className="hidden sm:inline text-sm text-ink/60">Study from your own sources, with proof.</span></div>
          <span className="text-xs font-medium px-3 py-1 rounded-full bg-ink text-paper">Multimodal AI Hackathon 2026 · Track D</span>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-5 py-8 grid md:grid-cols-[340px_1fr] gap-8">
        <div className="space-y-5">
          <ol className="card p-5 space-y-3">{steps.map(([n, t, s]) => <li key={n} className="flex gap-3 items-start"><span className="w-6 h-6 shrink-0 rounded-full bg-moss text-white text-xs grid place-items-center">{n}</span><span className="text-sm"><b>{t}</b><span className="block text-ink/60">{s}</span></span></li>)}</ol>
          <Upload onDone={() => setTick(t => t + 1)} />
        </div>
        <div className="min-w-0">
          <nav className="flex gap-1 border-b border-line mb-6" role="tablist">{["Tutor", "Practice", "Progress"].map(t => <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)} className={`px-5 py-2.5 text-sm -mb-px border-b-2 transition-colors ${tab === t ? "border-moss font-semibold" : "border-transparent text-ink/60 hover:text-ink"}`}>{t}</button>)}</nav>
          {tab === "Tutor" && <Chat open={setView} />}
          {tab === "Practice" && <Quiz open={setView} />}
          {tab === "Progress" && <Dash open={setView} tick={tick} />}
        </div>
        <Viewer s={view} close={() => setView(null)} />
      </main>
    </>
  );
}
