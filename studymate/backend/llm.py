
import os, json, re, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
from google import genai
from google.genai import types

MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
_c = None

def client():
    global _c
    if _c is None:
        _c = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _c

def _retry(fn, tries=3):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            limited = getattr(e, "code", None) == 429 or "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if not limited or i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))  # 2s, 4s backoff on rate limits

def _config(system=None, max_tokens=1200):
    kw = dict(max_output_tokens=max_tokens)
    if system:
        kw["system_instruction"] = system
    if "flash" in MODEL:  # keep hidden "thinking" tokens from eating the output budget
        kw["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    return types.GenerateContentConfig(**kw)

def _generate(contents, config):
    return _retry(lambda: client().models.generate_content(model=MODEL, contents=contents, config=config).text or "")

def chat(system, user, max_tokens=1200):
    return _generate(user, _config(system, max_tokens))

def chat_json(system, user, max_tokens=1500):
    t = chat(system + "\nReturn ONLY valid JSON, no prose, no code fences.", user, max_tokens)
    t = re.sub(r"```(?:json)?", "", t)
    return json.loads(re.search(r"[\[{].*[\]}]", t, re.S).group(0))

def describe_image(data: bytes, media="image/png"):
    prompt = "Describe this figure, diagram or table for a student in 2-3 sentences, including key labels and values."
    return _generate([types.Part.from_bytes(data=data, mime_type=media), prompt], _config(None, 300))

def embed(texts, task="RETRIEVAL_DOCUMENT"):
    """Gemini embeddings (768 dims), so no local model or native DLLs are needed."""
    out = []
    for i in range(0, len(texts), 100):
        batch = texts[i:i + 100]
        r = _retry(lambda: client().models.embed_content(model=EMBED_MODEL, contents=batch,
                   config=types.EmbedContentConfig(task_type=task, output_dimensionality=768)))
        out += [e.values for e in r.embeddings]
    return out

