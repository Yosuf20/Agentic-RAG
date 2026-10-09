"""
api.py — FastAPI backend for the Multi-Agent RAG chat frontend.

Wraps the existing initialize_system logic (refactored to accept
a file path + filename instead of a Streamlit upload object) and
exposes three endpoints:

  POST /upload   — upload & process a PDF, returns session info
  POST /chat     — send a message, get an agent reply
  POST /reset    — clear a session

Run with:
  uvicorn api:app --reload --port 8000
"""

import re
import uuid
import os
import shutil
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.pdfAgent import build_pdf_agent
from agents.webAgent import build_web_agent
from graph.workflow import build_workflow
from rag.pdf_processing import process_pdf


# ─────────────────────────────────────────────
# In-memory session store
# { session_id: {"graph": ..., "pdf_info": ...} }
# ─────────────────────────────────────────────
SESSIONS: dict = {}

TEMP_DIR = Path(tempfile.gettempdir()) / "agentrag_uploads"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def strip_think(text: str) -> str:
    """Remove <think>...</think> blocks left by reasoning models."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Also handle the case where the model only closes </think>
    cleaned = cleaned.split("</think>")[-1]
    return cleaned.strip()


def initialize_system(pdf_path: str, filename: str):
    """
    Build the full RAG pipeline from a file path + filename.
    Mirrors the original Streamlit initialize_system() but accepts
    a plain path instead of a Streamlit UploadedFile object.
    """
    pdf_info, retriever, bm25_retriever = process_pdf(pdf_path, filename)

    pdf_agent = build_pdf_agent(retriever, bm25_retriever)
    web_agent  = build_web_agent()
    graph      = build_workflow(pdf_agent, web_agent)

    return graph, pdf_info


# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────

app = FastAPI(
    title="AgentRAG API",
    description="Multi-Agent RAG — PDF + Web agent pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Allow file:// origin for direct HTML open (browsers send null origin)
        "null",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ResetRequest(BaseModel):
    session_id: str


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "sessions": len(SESSIONS)}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Accept a PDF, process it, store the graph in session, return session id.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    session_id = str(uuid.uuid4())
    pdf_path   = str(TEMP_DIR / f"{session_id}.pdf")

    # Persist the upload to disk so process_pdf can read it
    try:
        with open(pdf_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Build the pipeline (CPU-bound but acceptable for now)
    try:
        graph, pdf_info = initialize_system(pdf_path, file.filename)
    except Exception as e:
        os.remove(pdf_path)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    SESSIONS[session_id] = {
        "graph":    graph,
        "pdf_info": pdf_info,
        "filename": file.filename,
    }

    return {
        "session_id": session_id,
        "filename":   file.filename,
        "pdf_info":   pdf_info,
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Invoke the graph for a given session and return the assistant reply.
    """
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload a PDF first.",
        )

    graph    = session["graph"]
    pdf_info = session["pdf_info"]

    try:
        result = graph.invoke(
            {
                "messages": [{"role": "user", "content": req.message}],
                "pdf_info": pdf_info,
            }
        )
        raw_reply = result["messages"][-1].content
        reply     = strip_think(raw_reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    return {"reply": reply}


@app.post("/reset")
async def reset(req: ResetRequest):
    """
    Clear a session from memory and remove the temp PDF.
    """
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")

    del SESSIONS[req.session_id]

    pdf_path = TEMP_DIR / f"{req.session_id}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()

    return {"status": "reset", "session_id": req.session_id}
