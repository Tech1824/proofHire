import ast
import re
import networkx as nx

SKILLS_MAP = {
    "fastapi": "rest api",
    "sqlite3": "sql",
    "flask": "rest api",
    "django": "rest api",
    "sqlalchemy": "sql",
    "react": "frontend",
    "vue": "frontend",
}

def estimate_tokens(text: str) -> int:
    return len(text) // 4 if text else 0

def _parse_python_file(g: nx.DiGraph, file_node_id: str, content: str, filename: str):
    try:
        tree = ast.parse(content, filename=filename)
    except SyntaxError:
        return

    # Add functions and classes
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_id = f"func:{filename}::{node.name}"
            code_lines = content.split('\n')[node.lineno - 1 : node.end_lineno]
            g.add_node(func_id, type="function", label=node.name, code="\n".join(code_lines), size=len("\n".join(code_lines)))
            g.add_edge(file_node_id, func_id, type="contains")
            
            # Find calls inside the function
            for sub_node in ast.walk(node):
                if isinstance(sub_node, ast.Call):
                    if isinstance(sub_node.func, ast.Name):
                        called_func = f"func:{filename}::{sub_node.func.id}"
                        g.add_node(called_func, type="function", label=sub_node.func.id, size=10) # dummy size
                        g.add_edge(func_id, called_func, type="calls")
                        
        elif isinstance(node, ast.ClassDef):
            class_id = f"class:{filename}::{node.name}"
            code_lines = content.split('\n')[node.lineno - 1 : node.end_lineno]
            g.add_node(class_id, type="class", label=node.name, code="\n".join(code_lines), size=len("\n".join(code_lines)))
            g.add_edge(file_node_id, class_id, type="contains")

    # Find imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                skill = SKILLS_MAP.get(alias.name.split('.')[0])
                if skill:
                    skill_id = f"skill:{skill}"
                    g.add_node(skill_id, type="skill", label=skill, size=10)
                    g.add_edge(file_node_id, skill_id, type="uses")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                skill = SKILLS_MAP.get(node.module.split('.')[0])
                if skill:
                    skill_id = f"skill:{skill}"
                    g.add_node(skill_id, type="skill", label=skill, size=10)
                    g.add_edge(file_node_id, skill_id, type="uses")

def _parse_generic_file(g: nx.DiGraph, file_node_id: str, content: str, filename: str):
    # 1. Extract Classes / Structs / Interfaces
    class_pattern = re.compile(r'(?:class|struct|interface|enum)\s+([a-zA-Z0-9_]+)')
    for match in class_pattern.finditer(content):
        name = match.group(1)
        if name:
            class_id = f"class:{filename}::{name}"
            g.add_node(class_id, type="class", label=name, code=f"// {name} definition", size=50)
            g.add_edge(file_node_id, class_id, type="contains")

    # 2. Extract Functions / Methods (Heuristic)
    # Looks for: optional modifiers, optional return type, name, parens, followed by block/arrow
    func_pattern = re.compile(r'(?:(?:public|private|protected|static|inline|async|fun|function|def)\s+)*(?:[a-zA-Z0-9_<>\[\]]+\s+)?([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(?:{|throws|:|->|=>)')
    for match in func_pattern.finditer(content):
        name = match.group(1)
        if name and name not in ['if', 'while', 'for', 'switch', 'catch', 'return', 'new', 'elif', 'else']:
            func_id = f"func:{filename}::{name}"
            g.add_node(func_id, type="function", label=name, code=f"// {name} function", size=100)
            g.add_edge(file_node_id, func_id, type="contains")

    # 3. Extract Imports / Dependencies
    import_pattern = re.compile(r'(?:import|#include|require|using)\s+[\'\"<]?([a-zA-Z0-9_./@-]+)[\'\">]?')
    for match in import_pattern.finditer(content):
        lib = match.group(1)
        if lib and len(lib) > 1:
            skill = lib.split('/')[-1].split('.')[0]
            if skill:
                skill_id = f"skill:{skill}"
                g.add_node(skill_id, type="skill", label=skill, size=10)
                g.add_edge(file_node_id, skill_id, type="uses")

def build_from_candidate(candidate: dict, job_skills: list[str] = None) -> nx.DiGraph:
    if job_skills is None:
        job_skills = []
        
    g = nx.DiGraph()
    cand_id = candidate.get("candidate_id", "unknown_cand")
    g.add_node(cand_id, type="candidate", label=candidate.get("name", "Unknown"), size=10)
    
    parsed_claims = candidate.get("parsed_claims", [])
    if parsed_claims:
        for idx, claim in enumerate(parsed_claims):
            text = claim.get("text", "")
            skills = claim.get("skills", [])
            claim_id = f"claim:{cand_id}:{idx}"
            g.add_node(claim_id, type="claim", label=(text[:20] + "...") if len(text) > 20 else text, code=text, size=len(text))
            g.add_edge(cand_id, claim_id, type="claims")
            for skill in skills:
                skill_id = f"skill:{skill}"
                if skill_id not in g:
                    g.add_node(skill_id, type="skill", label=skill, size=10)
                g.add_edge(claim_id, skill_id, type="uses")
    elif candidate.get("linkedin_text"):
        claim_id = f"claim:{cand_id}:linkedin"
        g.add_node(claim_id, type="claim", label="LinkedIn summary", code=candidate["linkedin_text"], size=len(candidate["linkedin_text"]))
        g.add_edge(cand_id, claim_id, type="claims")
    
    projects = candidate.get("projects", [])
    for proj in projects:
        proj_id = f"project:{proj.get('name', 'Unknown')}"
        g.add_node(proj_id, type="project", label=proj.get('name'), size=50)
        g.add_edge(cand_id, proj_id, type="contains")
        
        for f in proj.get("files", []):
            path = f.get("path", "unknown")
            content = f.get("content", "")
            file_id = f"file:{path}"
            g.add_node(file_id, type="file", label=path, code=content, size=len(content))
            g.add_edge(proj_id, file_id, type="contains")
            
            if path.endswith(".py"):
                _parse_python_file(g, file_id, content, path)
            else:
                _parse_generic_file(g, file_id, content, path)
                
    # Calculate PageRank or degree-based importance without requiring numpy
    try:
        pagerank = nx.pagerank(g)
    except Exception:
        # Pure Python centrality fallback (in-degree + out-degree)
        total = float(len(g.nodes)) if len(g.nodes) > 0 else 1.0
        in_degrees = dict(g.in_degree()) if hasattr(g, 'in_degree') else {}
        out_degrees = dict(g.out_degree()) if hasattr(g, 'out_degree') else {}
        total_deg = sum(in_degrees.values()) + sum(out_degrees.values()) or 1.0
        pagerank = {
            n: (in_degrees.get(n, 0) * 2.0 + out_degrees.get(n, 0) * 1.0 + 1.0) / (total_deg + total)
            for n in g.nodes
        }

    # Weight calculation
    # weight = 0.5*pagerank + 0.3*relevance_to_job_skills + 0.2*size
    max_size = max([d.get('size', 1) for n, d in g.nodes(data=True)]) if len(g.nodes) > 0 else 1
    if max_size == 0: max_size = 1

    for node, data in g.nodes(data=True):
        pr = pagerank.get(node, 0)
        
        relevance = 0.0
        if data.get("type") == "skill" and data.get("label") in job_skills:
            relevance = 1.0
        elif data.get("type") in ["function", "class", "file"]:
            # Check if any uses/contains edges link to relevant skills
            for neighbor in g.successors(node):
                nd = g.nodes[neighbor]
                if nd.get("type") == "skill" and nd.get("label") in job_skills:
                    relevance = 1.0
                    break
        
        normalized_size = min(1.0, data.get("size", 0) / max_size)
        
        weight = 0.5 * pr + 0.3 * relevance + 0.2 * normalized_size
        g.nodes[node]["weight"] = weight

    return g

def subgraph_for_node(g: nx.DiGraph, node_id: str, depth: int = 1) -> dict:
    if node_id not in g:
        return {"nodes": [], "edges": []}
        
    sub_nodes = {node_id}
    # 1-hop neighbors (undirected for context gathering)
    for _ in range(depth):
        current_layer = list(sub_nodes)
        for n in current_layer:
            sub_nodes.update(g.predecessors(n))
            sub_nodes.update(g.successors(n))
            
    sub_g = g.subgraph(sub_nodes)
    
    # Cap to ~500 tokens (we'll just sort by weight and take top ones if too large, but for now just return all)
    return nx.node_link_data(sub_g)
