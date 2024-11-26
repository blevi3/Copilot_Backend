# chat.py

from fastapi import APIRouter, HTTPException
from openai import OpenAIError, OpenAI
from pydantic import BaseModel
from typing import List, Optional
import os

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

@router.post("/ask/")
async def ask_question(request: ChatRequest):
    try:
        # Retrieve or initialize session history
        session_history = chat_sessions.get(request.session_id, [])

        # Prepare question and files context
        question = request.question
        selected_files = request.selected_files
        files_context = "\n".join(
            [f"File: {file.name}\n{read_file(file.path, request.directory_path)}" for file in selected_files]
        )
        context = f"Question: {question}\n\nFiles:\n{files_context}"

        # Combine session history with new context
        full_context = "\n".join(session_history) + "\n" + context

        # Request to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_context},
            ],
        )

        # Check if response is empty or malformed
        if not response.choices:
            raise HTTPException(status_code=500, detail="No choices in OpenAI API response")
        
        answer = response.choices[0].message.content
        print(f"Answer: {answer}")

        # Update session history
        session_history.append(f"Q: {question}\nA: {answer}")
        chat_sessions[request.session_id] = session_history

        return {"answer": answer}
    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
