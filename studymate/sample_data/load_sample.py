"""Ingest the sample course into the StudyMate knowledge base. Run: python load_sample.py"""
import sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / "backend"))
import ingest, store
for f in sorted(here.iterdir()):
    if f.suffix.lower() in (".pdf", ".pptx", ".txt"):
        chunks = ingest.ingest_path(f, f.name); store.add(chunks)
        print(f"{f.name}: {len(chunks)} chunks, topics: {sorted({c['topic'] for c in chunks})}")
