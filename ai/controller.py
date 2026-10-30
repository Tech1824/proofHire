import random

def should_stop(state: dict) -> bool:
    max_turns = state.get("max_turns", 6)
    turns = len(state.get("scores", []))
    
    if turns >= max_turns:
        return True
        
    confidences = state.get("confidences", [])
    if turns >= 5 and (sum(confidences) / len(confidences) >= 0.85 if confidences else False):
        return True
        
    scores = state.get("scores", [])
    if len(scores) >= 2 and scores[-1] == 0 and scores[-2] == 0:
        return True
            
    return False

def pick_next(state: dict, g, job: dict, task_eval: dict | None = None) -> dict:
    asked_nodes = state.get("asked_nodes", [])
    turns_done = len(state.get("scores", []))
    current_turn = turns_done + 1
    
    # ── TWO-PHASE DEPTH CHECK ────────────────────────────────────────────────
    # Phase 1 (Turns 1 - 3): Portfolio & Provenance Verification (GitHub repos, files, claims)
    # Phase 2 (Turns 4 - 6): Task Solution & Code Verification (Guided by Heavy Model)
    phase = "provenance" if current_turn <= 3 else "task_validation"
    
    submission_nodes = [
        n for n, d in g.nodes(data=True) 
        if d.get("source") == "submission" or "solution.py" in n or "limiter.py" in n or "submission" in str(d.get("type", ""))
    ]
    portfolio_nodes = [
        n for n in g.nodes() 
        if n not in submission_nodes and not n.startswith("skill:")
    ]
    
    if phase == "provenance" and portfolio_nodes:
        target_pool = portfolio_nodes
    elif submission_nodes:
        target_pool = submission_nodes
    else:
        target_pool = [n for n in g.nodes() if not n.startswith("skill:")] or list(g.nodes())
    
    # Calculate priorities within target pool
    best_node = None
    best_priority = -1.0
    
    for node in target_pool:
        if node in asked_nodes and asked_nodes.count(node) >= 2:
            continue
        data = g.nodes[node] if node in g else {}
        weight = data.get("weight", 0.1)
        uncertainty = 0.4 if node in asked_nodes else 1.0
        priority = weight * uncertainty
        if priority > best_priority:
            best_priority = priority
            best_node = node
            
    if not best_node:
        available = [n for n in target_pool if n not in asked_nodes] or target_pool or list(g.nodes())
        best_node = random.choice(available) if available else "unknown"

    level = state.get("level", 1)
    scores = state.get("scores", [])
    if scores:
        last_score = scores[-1]
        flags = state.get("last_flags", [])
        if last_score in [4, 5]:
            level = min(5, level + 1)
        elif last_score in [1, 2] or "vague" in flags:
            best_node = asked_nodes[-1] if asked_nodes else best_node
        elif last_score == 0 or "empty" in flags:
            level = max(1, level - 1)

    # Determine question type
    if current_turn == 6:
        q_type = "modify"
    elif current_turn == 5 and phase == "task_validation":
        q_type = "debug"
    else:
        q_type = "question"

    # Surgical probe hint distilled and compressed from heavy model evaluation if in phase 2
    probe_hint = None
    if phase == "task_validation" and task_eval:
        from ai.evaluator import compress_task_eval_for_turn
        compressed = compress_task_eval_for_turn(task_eval, current_turn)
        probe_hint = compressed.get("probe_hint")

    return {
        "node_ref": best_node,
        "level": level,
        "type": q_type,
        "phase": phase,
        "phase_label": "PHASE 1: PROVENANCE" if phase == "provenance" else "PHASE 2: CODE VERIFICATION",
        "probe_hint": probe_hint,
        "reason": f"Phase {phase}, priority {best_priority:.2f}, level {level}"
    }
