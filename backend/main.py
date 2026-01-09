from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "question_bank", "题库_整合.json")
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), "..", "user_progress.json")

def load_questions():
    if not os.path.exists(DATA_PATH):
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
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

questions_db = load_questions()

class Question(BaseModel):
    id: Optional[int] = None
    type: str
    category: str
    question: str
    options: List[str]
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
def get_questions(category: Optional[str] = None, type: Optional[str] = None):
    global questions_db
    questions_db = load_questions() # Reload to get latest
    filtered = questions_db
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
