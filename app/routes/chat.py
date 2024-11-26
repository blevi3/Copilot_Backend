# chat.py

from fastapi import APIRouter, HTTPException
from openai import OpenAIError, OpenAI
from pydantic import BaseModel
from typing import List, Optional
import os
from sqlalchemy.orm import Session
from fastapi import Depends
from .chat_history import ChatHistory, SessionLocal

# Store chat history in-memory for each session (you can use a more robust solution like a database)
chat_sessions = {}

# OpenAI API key setup
client = OpenAI(
    api_key="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"
)

class FileDetail(BaseModel):
    name: str
    path: str

class ChatRequest(BaseModel):
    question: str
    selected_files: List[FileDetail]
    directory_path: Optional[str] = None
    session_id: str  # Unique session identifier to track chat history

def read_file(file_path: str, directory_path) -> str:
    full_path = os.path.join(directory_path, file_path.replace("/", os.sep))
    full_path = os.path.normpath(full_path)
    try:
        with open(full_path, "r") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {full_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading file {full_path}: {str(e)}")

# Create FastAPI router
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
        # Fetch the chat history for the current session
        chat_history = db.query(ChatHistory).filter(ChatHistory.session_id == request.session_id).all()

        # Build the chat history context
        history_context = ""
        for entry in chat_history:
            history_context += f"Q: {entry.question}\nA: {entry.answer}\n\n"

        # Initialize the full context to send to OpenAI
        context = history_context

        if "CODE" in request.question:
            print("Code detected in question")
            files_context = "\n".join(
                [f"File: {file.name}\n{read_file(file.path, request.directory_path)}" for file in request.selected_files]
            )
            context += f"Files:\n{files_context}\n"

        context += f"Q: {request.question}\n"

        # Call OpenAI API to get the response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": context}
            ],
        )

        if not response.choices:
            raise HTTPException(status_code=500, detail="No choices in OpenAI API response")

        # Extract the answer from the response
        answer = response.choices[0].message.content

        # Store the question and answer in the database
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
