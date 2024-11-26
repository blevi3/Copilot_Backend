from fastapi import APIRouter
from pydantic import BaseModel
import os
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
