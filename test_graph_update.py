import networkx as nx
from ai.graph import build_from_candidate

def test_graph_update():
    candidate = {
        "candidate_id": "cand_1",
        "name": "Test User",
        "parsed_claims": [
            {"text": "Led backend refactor", "skills": ["python", "fastapi"]},
            {"text": "Built scraper", "skills": ["python", "beautifulsoup"]}
        ],
        "projects": [
            {"name": "Local-API", "files": [{"path": "main.py", "content": "import fastapi\nprint('local')"}]}
        ]
    }
    
    g = build_from_candidate(candidate, job_skills=["python", "fastapi"])
    
    print("Nodes:", len(g.nodes))
    print("Edges:", len(g.edges))
    
    claims = [d for n, d in g.nodes(data=True) if d.get("type") == "claim"]
    print(f"Claims created: {len(claims)}")
    assert len(claims) == 2
    
    skills = [d for n, d in g.nodes(data=True) if d.get("type") == "skill"]
    print(f"Skills created: {len(skills)}")
    assert len(skills) >= 2
    
    python_skill_edges = list(g.in_edges("skill:python", data=True))
    print("Edges to python skill:", len(python_skill_edges))
    assert len(python_skill_edges) >= 2  # claims + uses
    
    print("Tests passed.")

if __name__ == "__main__":
    test_graph_update()
