from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import sys
import webbrowser
import uvicorn
import multiprocessing
import time
import threading

app = FastAPI()

last_heartbeat = time.time()

@app.post("/api/heartbeat")
def heartbeat():
    global last_heartbeat
    last_heartbeat = time.time()
    return {"status": "ok"}

def monitor_heartbeat():
    global last_heartbeat
    while True:
        time.sleep(5)
        # If no heartbeat for 15 seconds, exit
        if time.time() - last_heartbeat > 15:
            os._exit(0)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base path for the application
if getattr(sys, 'frozen', False):
    # If the app is frozen (packaged by PyInstaller)
    BASE_DIR = os.path.dirname(sys.executable)
    # Resources (like the frontend dist) are in sys._MEIPASS
    RESOURCES_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    # If the app is running in a normal Python environment
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RESOURCES_DIR = BASE_DIR

# Paths for data
if getattr(sys, 'frozen', False):
    # In production, keep progress and data next to the EXE
    DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, "question_bank", "题库_整合.json"))
    PROGRESS_PATH = os.path.abspath(os.path.join(BASE_DIR, "user_progress.json"))
else:
    # In development, keep them in the project root or dist folder
    DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, "question_bank", "题库_整合.json"))
    PROGRESS_PATH = os.path.abspath(os.path.join(BASE_DIR, "dist", "user_progress.json"))

if not os.path.exists(os.path.dirname(PROGRESS_PATH)):
    os.makedirs(os.path.dirname(PROGRESS_PATH), exist_ok=True)
# If it doesn't exist in dist, but exists in root, move it or just use root
if not os.path.exists(PROGRESS_PATH):
    root_progress = os.path.abspath(os.path.join(BASE_DIR, "user_progress.json"))
    if os.path.exists(root_progress):
        PROGRESS_PATH = root_progress

# Path for static files (frontend dist)
STATIC_DIR = os.path.join(RESOURCES_DIR, "frontend", "dist")

def load_questions():
    if not os.path.exists(DATA_PATH):
        # Fallback to internal path if not found in BASE_DIR (e.g. first run)
        internal_data = os.path.join(RESOURCES_DIR, "question_bank", "题库_整合.json")
        if os.path.exists(internal_data):
            return json.load(open(internal_data, "r", encoding="utf-8"))
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_progress():
    if not os.path.exists(PROGRESS_PATH):
        return {
            "wrong_questions": [],
            "history": [],
            "total_answered": 0,
            "correct_answered": 0,
            "cat_stats": {}
        }
    with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_progress(progress):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def save_questions(questions):
    # Ensure directory exists
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

questions_db = load_questions()

# ... (Keep existing models and API routes)

class Question(BaseModel):
    id: Optional[int] = None
    type: str
    category: str
    question: str
    options: List[str] = []
    answer: str
    explanation: str

class ImportRequest(BaseModel):
    questions: List[Question]

class ReportRequest(BaseModel):
    question_id: int
    is_correct: bool

@app.get("/api/filters")
def get_filters():
    # Filter out empty categories
    categories = sorted(list(set(q["category"] for q in questions_db if q.get("category"))))
    types = sorted(list(set(q["type"] for q in questions_db)))
    
    # Map type codes to Chinese names
    type_map = {
        "choice": "选择题",
        "fill": "填空题",
        "true_false": "判断题",
        "short_answer": "简答题",
        "单选题": "单选题",
        "多选题": "多选题",
        "填空题": "填空题",
        "判断题": "判断题"
    }
    
    type_filters = [{"id": t, "name": type_map.get(t, t)} for t in types]
    category_filters = [{"id": c, "name": c} for c in categories]
    
    return {
        "categories": category_filters,
        "types": type_filters
    }

@app.get("/api/questions", response_model=List[Question])
def get_questions(category: Optional[str] = None, type: Optional[str] = None, mode: str = "all"):
    # Reload to get latest
    all_qs = load_questions()
    progress = load_progress()
    # Ensure IDs are compared correctly as integers
    history = set(int(hid) for hid in progress.get("history", []))
    wrong_questions = set(int(wid) for wid in progress.get("wrong_questions", []))
    
    # Start with all
    filtered = all_qs
    
    # Filter by mode first
    if mode == "done":
        filtered = [q for q in all_qs if int(q["id"]) in history]
    elif mode == "undone":
        filtered = [q for q in all_qs if int(q["id"]) not in history]
    elif mode == "recommend":
        # Smart recommendation
        wrong = [q for q in all_qs if int(q["id"]) in wrong_questions]
        undone = [q for q in all_qs if int(q["id"]) not in history and int(q["id"]) not in wrong_questions]
        done = [q for q in all_qs if int(q["id"]) in history and int(q["id"]) not in wrong_questions]
        
        import random
        random.shuffle(wrong)
        random.shuffle(undone)
        random.shuffle(done)
        filtered = wrong + undone + done
    # If mode is "all", we keep all_qs

    # Then filter by category and type
    if category:
        filtered = [q for q in filtered if q["category"] == category]
    if type:
        filtered = [q for q in filtered if q["type"] == type]
        
    return filtered

@app.post("/api/questions", response_model=Question)
def add_question(question: Question):
    global questions_db
    questions_db = load_questions()
    
    # Generate new ID if not provided
    if question.id is None:
        new_id = max([q["id"] for q in questions_db], default=0) + 1
        question.id = new_id
    
    # Check if ID already exists
    for i, q in enumerate(questions_db):
        if q["id"] == question.id:
            questions_db[i] = question.dict()
            save_questions(questions_db)
            return question

    questions_db.append(question.dict())
    save_questions(questions_db)
    return question

@app.put("/api/questions/{question_id}", response_model=Question)
def update_question(question_id: int, question: Question):
    global questions_db
    questions_db = load_questions()
    
    for i, q in enumerate(questions_db):
        if q["id"] == question_id:
            updated_question = question.dict()
            updated_question["id"] = question_id # Ensure ID doesn't change
            questions_db[i] = updated_question
            save_questions(questions_db)
            return updated_question
            
    raise HTTPException(status_code=404, detail="Question not found")

@app.delete("/api/questions/{question_id}")
def delete_question(question_id: int):
    global questions_db
    questions_db = load_questions()
    
    initial_len = len(questions_db)
    questions_db = [q for q in questions_db if q["id"] != question_id]
    
    if len(questions_db) == initial_len:
        raise HTTPException(status_code=404, detail="Question not found")
        
    save_questions(questions_db)
    return {"status": "success"}

@app.post("/api/questions/import")
def import_questions(data: ImportRequest):
    global questions_db
    questions_db = load_questions()
    
    max_id = max([q["id"] for q in questions_db], default=0)
    
    new_questions = []
    for q in data.questions:
        max_id += 1
        q_dict = q.dict()
        q_dict["id"] = max_id
        new_questions.append(q_dict)
        
    questions_db.extend(new_questions)
    save_questions(questions_db)
    return {"status": "success", "count": len(new_questions)}

@app.get("/api/questions/{question_id}", response_model=Question)
def get_question(question_id: int):
    for q in questions_db:
        if q["id"] == question_id:
            return q
    raise HTTPException(status_code=404, detail="Question not found")

@app.post("/api/report")
def report_question(report: ReportRequest):
    progress = load_progress()
    
    # Update total stats
    progress["total_answered"] = progress.get("total_answered", 0) + 1
    
    # Track history (all answered questions)
    if "history" not in progress:
        progress["history"] = []
    if report.question_id not in progress["history"]:
        progress["history"].append(report.question_id)

    if report.is_correct:
        progress["correct_answered"] = progress.get("correct_answered", 0) + 1
        # Remove from wrong questions if it was there and now correct
        if report.question_id in progress.get("wrong_questions", []):
            progress["wrong_questions"].remove(report.question_id)
    else:
        # Add to wrong questions if not already there
        if report.question_id not in progress.get("wrong_questions", []):
            if "wrong_questions" not in progress:
                progress["wrong_questions"] = []
            progress["wrong_questions"].append(report.question_id)
            
    # Update category stats
    question = next((q for q in questions_db if q["id"] == report.question_id), None)
    if question:
        cat = question.get("category", "未分类")
        if "cat_stats" not in progress:
            progress["cat_stats"] = {}
        if cat not in progress["cat_stats"]:
            progress["cat_stats"][cat] = {"total": 0, "correct": 0}
        progress["cat_stats"][cat]["total"] += 1
        if report.is_correct:
            progress["cat_stats"][cat]["correct"] += 1
            
    save_progress(progress)
    return {"status": "success"}

@app.get("/api/stats")
def get_stats():
    progress = load_progress()
    return {
        "total_answered": progress.get("total_answered", 0),
        "correct_answered": progress.get("correct_answered", 0),
        "wrong_count": len(progress.get("wrong_questions", [])),
        "cat_stats": progress.get("cat_stats", {})
    }

@app.get("/api/wrong-questions", response_model=List[Question])
def get_wrong_questions():
    progress = load_progress()
    wrong_ids = progress.get("wrong_questions", [])
    return [q for q in questions_db if q["id"] in wrong_ids]

@app.delete("/api/wrong-questions/{question_id}")
def remove_wrong_question(question_id: int):
    progress = load_progress()
    if "wrong_questions" in progress and question_id in progress["wrong_questions"]:
        progress["wrong_questions"].remove(question_id)
        save_progress(progress)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Question not found in wrong questions")

# Serve static files from the frontend build
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not found. Please build the frontend first."}

def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    # Essential for PyInstaller + multiprocessing
    multiprocessing.freeze_support()

    # Fix for PyInstaller windowed mode: sys.stdout/stderr are None
    if sys.platform == 'win32' and getattr(sys, 'frozen', False):
        import os
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')

    # Ensure logs are visible
    print(f"Starting server... DATA_PATH: {DATA_PATH}, PROGRESS_PATH: {PROGRESS_PATH}")
    
    # Start heartbeat monitor
    threading.Thread(target=monitor_heartbeat, daemon=True).start()

    # Open browser in a separate thread after a short delay
    import threading
    import time
    def delayed_open():
        time.sleep(1.5)
        open_browser()
    threading.Thread(target=delayed_open, daemon=True).start()

    # Disable default uvicorn logging config to avoid 'isatty' error in windowed mode
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
