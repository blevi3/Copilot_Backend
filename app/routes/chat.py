from fastapi import APIRouter, HTTPException
from openai import OpenAIError, OpenAI
from pydantic import BaseModel
from typing import List, Optional
import os
from sqlalchemy.orm import Session
from fastapi import Depends
from dotenv import load_dotenv
from .chat_history import ChatHistory, SessionLocal

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("API key for OpenAI is not set. Please define it in the .env file.")

client = OpenAI(
    api_key=API_KEY
)

class FileDetail(BaseModel):
    name: str
    path: str

class ChatRequest(BaseModel):
    question: str
    selected_files: List[FileDetail]
    directory_path: Optional[str] = None
    session_id: str

def read_file(file_path: str, directory_path) -> str:
    full_path = os.path.join(directory_path, file_path.replace("/", os.sep))
    full_path = os.path.normpath(full_path)
    try:
        with open(full_path, "r") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {full_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading file {full_path}: {str(e)}")

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/ask/")
async def ask_question(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        chat_history = db.query(ChatHistory).filter(ChatHistory.session_id == request.session_id).all()

        history_context = ""
        for entry in chat_history:
            history_context += f"Q: {entry.question}\nA: {entry.answer}\n\n"

        context = history_context

        if "CODE" in request.question:
            print("Code detected in question")
            files_context = "\n".join(
                [f"File: {file.name}\n{read_file(file.path, request.directory_path)}" for file in request.selected_files]
            )
            context += f"Files:\n{files_context}\n"

        context += f"Q: {request.question}\n"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": context}
            ],
        )

        if not response.choices:
            raise HTTPException(status_code=500, detail="No choices in OpenAI API response")

        answer = response.choices[0].message.content

        chat_entry = ChatHistory(session_id=request.session_id, question=request.question, answer=answer)
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)

        return {"answer": answer}

    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/history/")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    chat_history = db.query(ChatHistory).filter(ChatHistory.session_id == session_id).all()
    return {"history": chat_history}
