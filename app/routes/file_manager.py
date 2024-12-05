# file_manager.py in routes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import re
from pathlib import Path
from models.file_history import FileHistory
from sqlalchemy.orm import Session
from fastapi import Depends
from models.chat_history import SessionLocal

router = APIRouter()

class DirectoryPath(BaseModel):
    path: str

def build_hierarchy(directory_path: Path):
    """
    Recursively build the directory structure hierarchy, excluding specific folders.
    """
    if not directory_path.is_dir():
        return None

    excluded_folders = {"node_modules", "venv"}

    children = []
    for item in directory_path.iterdir():
        if item.name in excluded_folders:
            continue
        if item.is_dir():
            children.append({
                "name": item.name,
                "type": "folder",
                "children": build_hierarchy(item) or []
            })
        else:
            children.append({
                "name": item.name,
                "type": "file",
                "children": []
            })

    return children


@router.post("/select-directory/")
async def select_directory(data: DirectoryPath):
    path = Path(data.path)

    # Check if the directory exists
    if not path.exists() or not path.is_dir():
        return {"error": "Directory does not exist."}

    # Build hierarchical structure
    directory_structure = build_hierarchy(path)

    return {"files": directory_structure}


async def update_file_content(file_path: str, content: str, db: Session):
    full_path = os.path.normpath(file_path)
    print(f"Updating file: {full_path}")
    try:

        if os.path.exists(full_path):
            with open(full_path, "r") as file:
                current_content = file.read()
                history_entry = FileHistory(
                    file_path=full_path,
                    content=current_content,
                )
                db.add(history_entry)
                db.commit()


        with open(full_path, "w") as file:
            print("Writing content...")
            if content.endswith("```"):
                content = content[:-3]
            if content.startswith("```python"):
                content = content[:-9]
            file.write(content)
            print("File content written successfully.")

        return {"detail": "File updated successfully"}
    except Exception as e:
        print(f"Error updating file {full_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating file {full_path}: {str(e)}")
    
async def create_new_file_content(file_path: str, content: str):
    full_path = os.path.normpath(file_path)
    print(f"Creating new file: {full_path}")
    try:
        with open(full_path, "w") as file:
            print("Writing content...")
            if content.endswith("```"):
                content = content[:-3]
            if content.startswith("```python"):
                content = content[:-9]
            file.write(content)
            print("File content written successfully.")

        return {"detail": "File created successfully"}
    except Exception as e:
        print(f"Error creating file {full_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating file {full_path}: {str(e)}")


async def process_files(answer, request, db):
    print("Processing files...")

    # Updated regex to capture the full file path (with slashes or backslashes), keyword, and content
    file_regex = r"(New|Modified)\s+([A-Za-z0-9/\\_.: -]+(?:[\\/][A-Za-z0-9/\\_.: -]+)*):\s*([\s\S]+?)(?=\n(?:New|Modified)|$)"

    # Find all matches for both New and Modified files
    matches = re.findall(file_regex, answer, re.DOTALL)
    print(f"Found {len(matches)} files to process.")

    for match in matches:
        action, file_name, content = match  # Unpack the three captured groups
        print(f"Action: {action} | File: {file_name} | Content: {content[:30]}...")  # Print first 30 chars

        print(f"Path: {file_name}")
        full_path = request.directory_path + file_name
        try:
            if action == "Modified":
                print(f"Updating file {full_path}")
                await update_file_content(full_path, content.strip(), db)
            elif action == "New":
                print(f"Creating new file {full_path}")
                await create_new_file_content(full_path, content.strip())
        except Exception as e:
            print(f"Error with file {full_path}: {str(e)}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/revert-file/")
async def revert_file(file_path: str, db: Session = Depends(get_db)):
    print(f"Reverting file: {file_path}")
    history_entry = (
        db.query(FileHistory)
        .filter(FileHistory.file_path == file_path)
        .order_by(FileHistory.timestamp.desc())
        .first()
    )

    if not history_entry:
        raise HTTPException(status_code=404, detail="No previous version found for this file")

    try:
        # Revert file content
        with open(file_path, "w") as file:
            file.write(history_entry.content)

        # Remove this history entry
        db.delete(history_entry)
        db.commit()

        return {"detail": "File reverted successfully"}
    except Exception as e:
        print(f"Error reverting file {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reverting file {file_path}: {str(e)}")
    
@router.get("/modified-files/")
async def get_modified_files(db: Session = Depends(get_db)):
    files = db.query(FileHistory).distinct(FileHistory.file_path).all()
    return [{"file_path": file.file_path, "last_modified": file.timestamp} for file in files]

