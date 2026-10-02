import os
import json
from ai.fake_crud import reset, create_candidate, create_job, create_submission, get_profile
from ai.api import build_graph, start_depth, submit_answer, finish_depth
from pprint import pprint

def run_test(candidate_name, answers_file):
    print(f"\n--- Testing Candidate: {candidate_name} ---")
    reset()
    
    # Setup data
    job = create_job({
        "title": "Backend Intern",
        "description": "Build an API",
        "required_skills": ["python", "fastapi"]
    })
    
    cand = create_candidate({
        "name": candidate_name,
        "linkedin_text": "I am a great dev with fastapi experience.",
        "projects": [
            {
                "name": "Proj1",
                "files": [
                    {"path": "main.py", "content": "import fastapi\ndef hello():\n    return 'world'"}
                ]
            }
        ]
    })
    
    build_graph(cand["candidate_id"])
    
    sub = create_submission({
        "candidate_id": cand["candidate_id"],
        "task_id": "task_1",
        "files": [{"path": "limiter.py", "content": "def limit(): pass"}]
    })
    
    res = start_depth(sub["submission_id"])
    session_id = res["session_id"]
    next_turn = res.get("turn")
    
    # Try to load answers, or fallback to dummy
    answers = []
    if os.path.exists(answers_file):
        with open(answers_file, 'r') as f:
            answers = json.load(f)
    else:
        # Dummy fallback if files not found
        if "strong" in answers_file:
            answers = [{"answer_text": "I used FastAPI because it is asynchronous and fast. Here is how it handles requests."}] * 6
        else:
            answers = [{"answer_text": "I don't know, I just copied it."}] * 6
            
    turn_idx = 0
    while next_turn and turn_idx < len(answers):
        print(f"\nTurn {next_turn['turn_number']} (Level {next_turn['level']})")
        print(f"Q: {next_turn['question_text']}")
        
        ans = answers[turn_idx]
        print(f"A: {ans.get('answer_text')}")
        
        out = submit_answer(session_id, ans.get("answer_text", ""), ans.get("answer_code"))
        if not out:
            break
            
        if out.get("status") == "done":
            break
            
        eval_dict = out.get("evaluation", {})
        print(f"Score: {eval_dict.get('score')} | Flags: {eval_dict.get('flags')}")
        
        next_turn = out.get("next")
        turn_idx += 1

    # End
    finish_depth(session_id)
    profile = get_profile(session_id)
    
    print("\n--- Final Profile ---")
    print(f"Score: {profile.get('overall_score')} / 100")
    print(f"Confidence: {profile.get('confidence')}")
    print(f"Recommendation: {profile.get('recommendation')}")
    print("Summary:")
    print(profile.get("summary"))

if __name__ == "__main__":
    run_test("Strong Candidate", "data/seed/answers_strong.json")
    run_test("Weak Candidate", "data/seed/answers_weak.json")
