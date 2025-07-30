from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from parser import extract_text_from_pdf
from scorer import build_faiss_index, search_top_k
from llm import explain_match
from cache import init_db, get_embedding_with_cache
import re
from collections import OrderedDict
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/api/rank")
async def rank_resumes(
    files: list[UploadFile] = File(...),
    job_description: str = Form(...)
):
    unique_resumes = OrderedDict()

    # Step 1: Deduplicate and extract text
    for file in files:
        if file.filename not in unique_resumes:
            content = await file.read()
            unique_resumes[file.filename] = extract_text_from_pdf(content)

    filenames = list(unique_resumes.keys())
    texts = list(unique_resumes.values())

    # Step 2: Get embeddings (from cache or compute)
    embeddings = await asyncio.gather(*[get_embedding_with_cache(text) for text in texts])
    resumes = list(zip(filenames, texts))

    # Step 3: Build index for matching
    job_vec = await get_embedding_with_cache(job_description)
    index = build_faiss_index(embeddings)
    idxs, scores = search_top_k(index, job_vec, k=10)

    # Step 4: LLM scoring + filtering
    results = []
    seen_names = set()
    CONFIDENCE_THRESHOLD = 0.6

    for i, sim_score in zip(idxs, scores):
        if sim_score < CONFIDENCE_THRESHOLD:
            continue
        name, text = resumes[i]
        if name in seen_names:
            continue
        seen_names.add(name)

        score_exp = explain_match(job_description, text)
        score_match = re.search(r"(?i)(score|match score)[^\d]*?(\d{1,3})", score_exp)
        score = int(score_match.group(2)) if score_match else 0
        explanation = score_exp.replace(score_match.group(0), "").strip() if score_match else score_exp

        results.append({
            "name": name,
            "score": score,
            "explanation": explanation
        })

        if len(results) >= 10:
            break

    # Step 5: Sort and return
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results}
