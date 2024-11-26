from fastapi import APIRouter, HTTPException
from openai import OpenAIError
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional
import os


def read_file(file_path: str, directory_path) -> str:
    full_path = os.path.join(directory_path, file_path.replace("/", os.sep))
    full_path = os.path.normpath(full_path)
    try:
        with open(full_path, "r") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {full_path}: {str(e)}")  # Log the specific error
        raise HTTPException(status_code=500, detail=f"Error reading file {full_path}: {str(e)}")


# Store chat history
chat_history = []

# Create FastAPI router
router = APIRouter()

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

@router.post("/ask/")
async def ask_question(request: ChatRequest):
    try:
        # Log incoming request data for debugging
        print(f"Received question: {request.question}")
        print(f"Received selected files: {request.selected_files}")
        print(f"Received directory path: {request.directory_path}")
        
        question = request.question
        selected_files = request.selected_files
        files_context = "\n".join(
            [f"File: {file.name}\n{read_file(file.path, request.directory_path)}" for file in selected_files]
        )
        context = f"Question: {question}\n\nFiles:\n{files_context}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": context},
            ],
        )

        # Check if response is empty or malformed
        if not response.choices:
            raise HTTPException(status_code=500, detail="No choices in OpenAI API response")
        
        answer = response.choices[0].message.content
        print(f"Answer: {answer}")
        chat_history.append(f"Q: {question}\nA: {answer}")
        return {"answer": answer}
    except OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")  # Log the error details
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Log any other exceptions
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
