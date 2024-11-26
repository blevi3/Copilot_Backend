from fastapi import APIRouter
from pydantic import BaseModel
import os
from pathlib import Path

router = APIRouter()

# Define the schema for incoming request
class DirectoryPath(BaseModel):
    path: str

def build_hierarchy(directory_path: Path):
    """
    Recursively build the directory structure hierarchy.
    """
    if not directory_path.is_dir():
        return None

    # List all items in the directory
    children = []
    for item in directory_path.iterdir():
        if item.is_dir():
            # Recursively build hierarchy for folders
            children.append({
                "name": item.name,
                "type": "folder",
                "children": build_hierarchy(item) or []  # If folder is empty, children is an empty list
            })
        else:
            # Add files directly
            children.append({
                "name": item.name,
                "type": "file",
                "children": []  # Files have no children
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
