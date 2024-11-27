from fastapi import APIRouter, HTTPException
from openai import OpenAIError, OpenAI
from pydantic import BaseModel
from typing import List, Optional
import os
from sqlalchemy.orm import Session
from fastapi import Depends
from dotenv import load_dotenv
from .chat_history import ChatHistory, SessionLocal
import re
from .file_manager import update_file_content, create_new_file_content, process_files

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
        system_prompt = (
            """
            "You are a precise and systematic assistant. When responding to the user, your response must adhere to the following rules strictly:\n\n"
            "1. Modify Code: If the user asks for modifications to an existing file, make the changes in the code and label it as 'Modified' followed by the full path to the filename and the updated content.\n\n"
            "2. Create New File: If the user requests a new file to be created, provide the code and label it as 'New' followed by the full path to the filename and the content of the newly created file.\n\n"
            "3. Explain Code: If the user asks for an explanation of the code, provide detailed explanations of each part of the code. The explanation should cover all aspects of the code the user inquires about, including but not limited to function definitions, variables, loops, classes, imports, and any specific lines the user references.\n\n"
            "Formatting Rules:\n"
            "- Label Every File: Begin the response for each file with one of the labels:\n"
            "  - 'New' if it is a newly created file.\n"
            "  - 'Modified' if it is an updated version of an existing file.\n"
            "- Format: Use this format exactly:\n"
            "  - '<Label> <full_path_to_filename>:'\n"
            "  - '<code content>'\n\n"
            "For example:\n"
            "- New /path/to/your/views_test.py:\n"
            "  ```python\n"
            "  # Code content here\n"
            "  ```\n\n"
            "- Modified /path/to/your/views_test.py:\n"
            "  ```python\n"
            "  # Updated code content here\n"
            "  ```\n\n"
            "Response Example 1 (Modify Code):\n"
            "- User Request: Modify the existing 'views.py' file to include a new view function that returns a list of items.\n"
            "- Response: \n"
            "  ```yaml\n"
            "  Modified /path/to/your/views.py:\n"
            "  def item_list(request):\n"
            "      items = [\"item1\", \"item2\", \"item3\"]\n"
            "      return JsonResponse({\"items\": items})\n"
            "  ```\n\n"
            "Response Example 2 (Create New File):\n"
            "- User Request: Create a new file named 'views_test.py' with a simple 'Hello World' program in it.\n"
            "- Response:\n"
            "  ```yaml\n"
            "  New /path/to/your/views_test.py:\n"
            "  print(\"Hello, World!\")\n"
            "  ```\n\n"
            "Response Example 3 (Explain Code):\n"
            "- User Request: Explain the code in the following function: 'def add(a, b): return a + b'.\n"
            "- Response:\n"
            "  ```yaml\n"
            "  Explanation:\n"
            "  - 'def add(a, b):': This is a function definition. The 'def' keyword defines a function named 'add', which takes two arguments 'a' and 'b'.\n"
            "  - 'return a + b': This line returns the sum of the two arguments 'a' and 'b'.\n"
            "  - 'The function add performs an addition operation on the two provided values and returns the result to the caller.'\n"
            "  ```\n\n"
            "Additional Guidelines:\n"
            "- Include all content of the file, even unchanged portions, when responding with the 'Modified' label.\n"
            "- Do not include any additional text, commentary, or explanation outside the code block or response format.\n\n"
            "Always ensure that the response is in one of the following formats:\n"
            "- Either 'New' or 'Modified' is always present, followed by the full path to the file and its content.\n"
            "- For explanations, provide a clear and comprehensive breakdown of the code the user asks about."
            """
        )
        if "CODE" in request.question:
            print("Code detected in question")
            files_context = "\n".join(
                [f"File: /{file.path}\n{read_file(file.path, request.directory_path)}" for file in request.selected_files]
            )
            context += f"Files:\n{files_context}\n"

        context += f"Q: {request.question}\n"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
        )


        if not response.choices:
            raise HTTPException(status_code=500, detail="No choices in OpenAI API response")
        print("directory_path", request.directory_path)
        answer = response.choices[0].message.content

        await process_files(answer, request)

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
