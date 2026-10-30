import random

def should_stop(state: dict) -> bool:
    turns_done = state.get("turn_number", 0) - 1 # assuming turn_number is the *next* turn to be asked
    max_turns = state.get("max_turns", 6)
    
    # Actually if turn_number is the current turn index (1-based)
    turns = len(state.get("scores", []))
    
    if turns >= max_turns:
        return True
        
    confidences = state.get("confidences", [])
    if turns >= 4 and (sum(confidences) / len(confidences) >= 0.8 if confidences else False):
        return True
        
    flags = state.get("last_flags", [])
    if turns >= 2 and flags == ["empty", "empty"]: # Simplification for "two empty answers in a row"
        # We would need to track history of flags properly. For MVP, if last two turns scored 0, we can stop.
        scores = state.get("scores", [])
        if len(scores) >= 2 and scores[-1] == 0 and scores[-2] == 0:
            return True
            
    return False

def pick_next(state: dict, g, job: dict) -> dict:
    asked_nodes = state.get("asked_nodes", [])
    
    # Calculate priorities
    best_node = None
    best_priority = -1.0
    
    for node, data in g.nodes(data=True):
        if node in asked_nodes and asked_nodes.count(node) >= 2:
            continue
            
        weight = data.get("weight", 0.1)
        
        uncertainty = 1.0
        if node in asked_nodes:
            # Did they give a strong answer or a vague answer?
            # We would need to map node to its score, but for simplicity:
            last_score = state.get("scores", [0])[-1] if state.get("scores") else 0
            if last_score >= 4:
                uncertainty = 0.2
            else:
                uncertainty = 0.6
                
        priority = weight * uncertainty
        if priority > best_priority:
            best_priority = priority
            best_node = node
            
    if not best_node:
        # Fallback to random node
        nodes = list(g.nodes())
        best_node = random.choice(nodes) if nodes else "unknown"

    level = state.get("level", 1)
    
    # Apply level rules based on last score
    scores = state.get("scores", [])
    if scores:
        last_score = scores[-1]
        flags = state.get("last_flags", [])
        
        if last_score in [4, 5]:
            level = min(5, level + 1)
            q_type = "question"
        elif last_score == 3:
            q_type = "question"
        elif last_score in [1, 2] or "vague" in flags:
            best_node = asked_nodes[-1] if asked_nodes else best_node
            q_type = "question"
        elif last_score == 0 or "empty" in flags:
            level = max(1, level - 1)
            q_type = "question"
    else:
        q_type = "question"
        
    # Special turns
    turns = len(scores)
    if turns >= 2:
        # turn 3 or later (since turns starts at 0 for the check, 2 means 3rd turn)
        claims = [n for n, d in g.nodes(data=True) if d.get("type") == "claim"]
        unasked_claims = [c for c in claims if c not in asked_nodes]
        if unasked_claims:
            best_node = unasked_claims[0]
            
    if level in [4, 5]:
        q_type = "modify" if level == 4 else "debug"

    return {
        "node_ref": best_node,
        "level": level,
        "type": q_type,
        "reason": f"Priority {best_priority:.2f}, level {level}"
    }
