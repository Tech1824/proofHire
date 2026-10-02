def merge_profile(db_candidate: dict, github_data: dict, linkedin_data: dict) -> dict:
    """
    Takes the raw candidate dict from the DB, GitHub data from ingest,
    and LinkedIn parsed claims from ingest.
    Returns a new candidate dict ready for ai/graph.py.
    """
    # Create a copy so we don't mutate the original
    merged = dict(db_candidate)
    
    # Merge projects
    db_projects = merged.get("projects") or []
    gh_projects = github_data.get("projects") or []
    
    merged_projects = []
    seen_names = set()
    
    # Add DB projects first (they take priority if names conflict)
    for p in db_projects:
        name = p.get("name", "").lower().strip()
        if not name:
            name = "untitled"
        merged_projects.append(p)
        seen_names.add(name)
        
    # Add GitHub projects if not already seen
    for p in gh_projects:
        name = p.get("name", "").lower().strip()
        if not name:
            name = "untitled"
        if name not in seen_names:
            merged_projects.append(p)
            seen_names.add(name)
            
    merged["projects"] = merged_projects
    
    # Merge claims
    # Deduplicate claims based on exact text match just in case
    raw_claims = linkedin_data.get("claims") or []
    seen_claims = set()
    deduped_claims = []
    
    for c in raw_claims:
        text = c.get("text", "").strip()
        if text and text not in seen_claims:
            seen_claims.add(text)
            deduped_claims.append(c)
            
    merged["parsed_claims"] = deduped_claims
    
    return merged
