from ai.profile_merger import merge_profile

def test_merge():
    db_candidate = {
        "candidate_id": "cand_1",
        "name": "Test User",
        "projects": [
            {"name": "Local-API", "files": [{"path": "main.py", "content": "print('local')"}]}
        ]
    }
    
    github_data = {
        "projects": [
            {"name": "Local-API", "files": [{"path": "main.py", "content": "print('github')"}]},
            {"name": "Other-Repo", "files": [{"path": "app.js", "content": "console.log('js')"}]}
        ]
    }
    
    linkedin_data = {
        "claims": [
            {"text": "Built stuff", "skills": ["python"]},
            {"text": "Built stuff", "skills": ["python"]}
        ]
    }
    
    merged = merge_profile(db_candidate, github_data, linkedin_data)
    
    print("Merged projects:", [p["name"] for p in merged["projects"]])
    assert len(merged["projects"]) == 2
    
    local_api_proj = next(p for p in merged["projects"] if p["name"] == "Local-API")
    assert local_api_proj["files"][0]["content"] == "print('local')"
    
    print("Merged claims:", len(merged["parsed_claims"]))
    assert len(merged["parsed_claims"]) == 1
    
    print("Tests passed.")

if __name__ == "__main__":
    test_merge()
