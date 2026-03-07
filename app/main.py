from .config import settings
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File
from .ingestor import ingest_pdf
from .retriever import retrieve
from .llm import generate_answer
import shutil

app = FastAPI()

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: list[str]

@app.post("/ingest")
def upload_file(file: UploadFile = File(...)):

    with open(f"data/uploads/{file.filename}", "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_path = f"data/uploads/{file.filename}"
    ingest_pdf(file_path)

    return {"message": f"File {file.filename} uploaded successfully"}

@app.post("/ask")
def ask(request: AskRequest) -> AskResponse:
    answer = generate_answer(request.question, retrieve(request.question))
    return AskResponse(answer= answer["answer"], sources = answer["sources"])
