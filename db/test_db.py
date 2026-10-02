from db.crud import (
    create_job, list_jobs, get_job,
    create_candidate, get_candidate, save_graph, load_graph,
    create_task, get_task, create_submission, get_submission,
    create_session, get_session, add_turn, update_turn_with_answer,
    update_session_state, set_session_status, save_profile,
    get_profile, list_finished_profiles_for_job,
    cache_get, cache_set, get_setting, set_setting
)
from db.seed import reset_and_seed

def run_tests():
    print("Resetting and seeding...")
    reset_and_seed()

    # Jobs
    job = create_job({
        "title": "Test Job",
        "company": "Test Co",
        "description": "test",
        "required_skills": ["test"],
        "seniority": "mid"
    })
    jobs = list_jobs()
    assert len(jobs) >= 1
    job_id = job["job_id"]
    fetched_job = get_job(job_id)
    assert fetched_job["title"] == "Test Job"

    # Candidate
    cand = create_candidate({
        "name": "Test Cand",
        "email": "test@test.com",
        "projects": [
            {
                "name": "Test Proj",
                "files": [{"path": "test.py", "content": "print('hi')"}]
            }
        ]
    })
    cand_id = cand["candidate_id"]
    fetched_cand = get_candidate(cand_id)
    assert fetched_cand["name"] == "Test Cand"
    assert len(fetched_cand["projects"]) == 1

    save_graph(cand_id, {"nodes": [], "edges": []})
    g = load_graph(cand_id)
    assert g is not None

    # Tasks & submissions
    task = create_task({
        "job_id": job_id,
        "title": "Test Task",
        "brief": "brief",
        "requirements": [],
        "language": "py",
        "starter_code": "",
        "time_limit_min": 10,
        "rubric": []
    })
    task_id = task["task_id"]
    fetched_task = get_task(task_id)
    assert fetched_task is not None

    sub = create_submission({
        "candidate_id": cand_id,
        "task_id": task_id,
        "notes": "test",
        "files": [{"path": "ans.py", "content": "test"}]
    })
    sub_id = sub["submission_id"]
    fetched_sub = get_submission(sub_id)
    assert fetched_sub is not None

    # Sessions and Depth Check
    sess = create_session(sub_id, 3)
    sess_id = sess["session_id"]
    
    turn = add_turn(sess_id, {
        "turn_number": 1,
        "type": "question",
        "level": 1,
        "node_ref": "n",
        "question_text": "q?",
        "expects": "text"
    })
    
    update_turn_with_answer(
        sess_id, 1, "a", None, {"score": 5}, {"meta": "data"}
    )
    
    update_session_state(sess_id, {"state": "active"})
    set_session_status(sess_id, "done")
    
    fetched_sess = get_session(sess_id)
    assert fetched_sess["status"] == "done"
    assert len(fetched_sess["turns"]) == 1
    assert fetched_sess["turns"][0]["answer_text"] == "a"

    # Profile
    save_profile(sess_id, cand_id, job_id, {
        "overall_score": 100,
        "confidence": 0.9,
        "recommendation": "yes",
        "skill_profile": {},
        "strengths": [],
        "concerns": [],
        "evidence": [],
        "summary": "Great"
    })
    
    p = get_profile(sess_id)
    assert p["overall_score"] == 100
    
    profiles = list_finished_profiles_for_job(job_id)
    assert len(profiles) == 1
    assert profiles[0]["name"] == "Test Cand"

    # Cache & config
    cache_set("k1", "alias1", {"res": 1})
    c = cache_get("k1")
    assert c["res"] == 1

    set_setting("demo", "true")
    s = get_setting("demo")
    assert s == "true"

    print("OK")

if __name__ == "__main__":
    run_tests()
