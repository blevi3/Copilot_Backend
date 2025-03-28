# Copilot Code Assistant
## Frontend: https://github.com/blevi3/Copilot_Frontend
## Overview

This project is a desktop application designed to act as an AI-powered copilot for developers. It integrates with the local file system, allowing users to select code files and directories, and then interact with an AI assistant (powered by OpenAI) to understand, modify, or generate code. The application features a React-based frontend built with Electron and a Python FastAPI backend.


## Key Features

* **Directory & File Management:** Users can select a project directory, and the application displays the file structure. Specific files can be selected for interaction with the AI.
* **AI-Powered Chat Interface:** Engage in a conversation with an AI to ask questions about selected code, request modifications, or generate new code snippets/files.
* **Contextual Code Understanding:** The AI receives the content of selected files, enabling context-aware responses and modifications.
* **Automated Code Modification/Creation:** Based on the chat interaction, the AI can suggest and apply modifications to existing files or create new files with specified content.
* **File Modification Tracking & Revert:** The application tracks files modified by the AI and allows users to revert changes back to the previous state.
* **Conversation History:** Past chat sessions are saved and can be revisited, preserving the context and history of interactions for different projects or tasks.
* **Desktop Application:** Built using Electron, providing a native desktop experience.


## Tech Stack

* **Frontend:**
    * React
    * Electron
    * Material UI (@mui/material, @mui/icons-material)
    * Axios (for API communication)
    * Markdown-it, React-Syntax-Highlighter (for displaying code/markdown)
* **Backend:**
    * FastAPI (Python web framework)
    * SQLAlchemy (ORM for database interaction - chat & file history)
    * DeepSeek API (AI Model Interaction)
    * Uvicorn (ASGI server)
* **Database:**
    * SQLite (used for storing chat and file modification history)


## Setup & Installation


**Prerequisites:**
* Node.js and npm
* Python 3.x and pip
* An API key for the OpenAI API

**Backend:**
1.  Navigate to the `backend` directory.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate the virtual environment (e.g., `source venv/bin/activate` on Linux/macOS, `venv\Scripts\activate` on Windows).
4.  Install dependencies: `pip install -r req.txt`
5.  Create a `.env` file and add your `OPENAI_API_KEY=YOUR_API_KEY`.
6.  Run the backend server: `uvicorn app.main:app --reload --port 8000`

**Frontend:**
1.  Navigate to the `frontend` directory.
2.  Install dependencies: `npm install`
3.  Start the development server: `npm start`
