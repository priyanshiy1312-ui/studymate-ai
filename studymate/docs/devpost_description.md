# StudyMate

## Inspiration
Students learn from a lecture video, a textbook and a slide deck, but each lives in its own place. When you are stuck, you search three tools and still do not know which source to trust.

## What it does
StudyMate merges lecture videos, textbooks and slides into one knowledge base. Every answer cites its source, down to the lecture timestamp, page or slide, and one click opens it. If your materials do not cover the question, it says so instead of guessing.
It tutors, not just answers: when your mastery of a topic is low it gives a hint and a guiding question first. It generates quiz questions from your own materials, adapts difficulty to what you know, brings weak topics back with spaced repetition, and shows your progress on a mastery heatmap with a next-session plan.

## How we built it
FastAPI backend, Next.js frontend. Whisper transcribes video with timestamps; PDFs and slides are parsed by page and slide, and a vision model describes figures and diagrams. Chunks go into Chroma with BM25 for hybrid search, fused with reciprocal rank fusion. Gemini writes cited answers, questions and grading feedback. An Elo-style learner model in SQLite tracks mastery per topic.

## Challenges
Keeping citations honest: we only let the model cite numbered retrieved passages, refuse below a confidence threshold, and measure citation support with an evaluation script.

## Accomplishments
Clickable timestamp and page citations; a tutor that scaffolds before answering; adaptive questions that cite their source; measured citation accuracy (see eval/results.json).

## What we learned
Grounding and pedagogy work together: the same citations that build trust also let learners go back to the source.

## What's next
Cross-encoder reranking, slide image rendering, multi-learner accounts, and exam-date-aware study plans.

## Built with
Python, FastAPI, Next.js, Tailwind CSS, Gemini, Whisper (faster-whisper), ChromaDB, BM25, SQLite
