from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import re
from pathlib import Path

router = APIRouter()

class DirectoryPath(BaseModel):
    path: str

def build_hierarchy(directory_path: Path):
    """
    Recursively build the directory structure hierarchy.
    """
    if not directory_path.is_dir():
        return None

    children = []
    for item in directory_path.iterdir():
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


async def update_file_content(file_path: str, content: str):
    full_path = os.path.normpath(file_path)
    print(f"Updating file: {full_path}")
    try:
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


async def process_files(answer, request):
    print("Processing files...")
    # Regex to capture the keyword (New or Modified), file name, and content
    file_regex = r"(New|Modified)\s+(\w+\.\w+):\s*```python\n(.*?)```"

    # Find all matches for both New and Modified files
    matches = re.findall(file_regex, answer, re.DOTALL)
    print(f"Found {len(matches)} files to process.")
    for match in matches:
        action, file_name, content = match  # Unpack the three captured groups
        print(f"Action: {action} | File: {file_name} | Content: {content[:30]}...")  # Print first 30 chars

        # Determine the full file path
        full_file_path = os.path.join(request.directory_path, file_name)

        # Call the appropriate function based on the action (New or Modified)
        try:
            if action == "Modified":
                print(f"Updating file {file_name}")
                await update_file_content(full_file_path, content.strip())
            elif action == "New":
                print(f"Creating new file {file_name}")
                await create_new_file_content(full_file_path, content.strip())
        except Exception as e:
            print(f"Error with file {file_name}: {str(e)}")