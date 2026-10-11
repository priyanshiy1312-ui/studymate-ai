import math, re, zlib
import numpy as np

STOP = set("""a an the and or but if then else of to in on at by for with from as is are was were be been being it its this that these those
you your we our they their he she his her i me my not no yes do does did done can could should would will may might must so than too very
about into over under between during after before above below up down out off again further once here there when where why how all any both each
few more most other some such only own same just also what which who whom whose have has had having let us""".split())


def tokens(text: str):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower())]


def stem(t: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(t) > len(suf) + 3 and t.endswith(suf):
            return t[: -len(suf)]
    return t


def content_terms(text: str):
    return [stem(t) for t in tokens(text) if t not in STOP and len(t) > 2]


def key_terms(text: str, n: int = 6):
    """Most informative terms (frequency x length) for rubric/cloze fallbacks."""
    counts = {}
    for t in tokens(text):
        if t in STOP or len(t) < 4:
            continue
        counts[t] = counts.get(t, 0) + 1
    ranked = sorted(counts, key=lambda t: (counts[t] * math.log(1 + len(t)), len(t)), reverse=True)
    return ranked[:n]


def sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text)) if len(s.strip()) > 20]


def fmt_time(sec: float) -> str:
    sec = int(sec)
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class HashEmbedder:
    """Offline feature-hashing embedder (no downloads). Used when sentence-transformers is unavailable."""
    dim = 768

    def encode(self, texts):
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            toks = [stem(x) for x in tokens(t) if x not in STOP]
            feats = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
            for f in feats:
                h = zlib.crc32(f.encode())
                out[i, h % self.dim] += (1.0 if h & 1 << 20 else -1.0) * (1.0 if "_" not in f else 0.7)
            out[i] = np.sign(out[i]) * np.sqrt(np.abs(out[i]))
            n = np.linalg.norm(out[i])
            if n:
                out[i] /= n
        return out.tolist()


class STEmbedder:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def encode(self, texts):
        return self.m.encode(list(texts), normalize_embeddings=True, show_progress_bar=False).tolist()


def make_embedder():
    import config
    if config.EMBEDDING_BACKEND in ("auto", "sentence-transformers"):
        try:
            return STEmbedder(), "sentence-transformers/all-MiniLM-L6-v2"
        except Exception as e:
            if config.EMBEDDING_BACKEND == "sentence-transformers":
                raise
    return HashEmbedder(), "hash (offline)"
