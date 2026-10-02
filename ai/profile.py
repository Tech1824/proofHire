import json
from pydantic import BaseModel
from ai.llm import complete_json

class SummarySchema(BaseModel):
    summary: str

SUMMARY_SYSTEM_PROMPT = """You are a senior hiring manager writing a plain-English summary (3-4 sentences). Use ONLY the evidence provided below. Quote nothing that is not listed. Be objective and concise."""

def compute_profile(session: dict) -> dict:
    turns = session.get("turns", [])
    num_turns = len(turns)
    if num_turns == 0:
        return {
            "overall_score": 0, "confidence": 0.0, "recommendation": "needs_more_evidence",
            "skill_profile": {}, "strengths": [], "concerns": [], "evidence": [], "summary": ""
        }

    # Aggregate dimensions and confidences
    dim_scores = {"understanding": [], "reasoning": [], "debugging": [], "modification": [], "communication": []}
    confidences = []
    ownership_score = 5.0
    
    evidence_list = []

    for t in turns:
        eval_dict = t.get("evaluation") or {}
        confidences.append(eval_dict.get("confidence", 0.0))
        
        flags = eval_dict.get("flags", [])
        if "contradicts_claim" in flags:
            ownership_score = max(0.0, ownership_score - 2.0)
            
        for d, s in eval_dict.get("dimensions", {}).items():
            if d in dim_scores:
                dim_scores[d].append(s)
                
        if eval_dict.get("evidence_quote"):
            evidence_list.append({
                "claim": f"Performance on turn {t.get('turn_number', '?')}",
                "quote": eval_dict.get("evidence_quote"),
                "turn_number": t.get("turn_number"),
                "score": eval_dict.get("score", 0)
            })

    # Averages
    skill_profile = {"ownership": ownership_score}
    for d, scores in dim_scores.items():
        if scores:
            skill_profile[d] = sum(scores) / len(scores)

    # Weights
    raw_weights = {
        "understanding": 0.30,
        "reasoning": 0.20,
        "debugging": 0.10,
        "modification": 0.10,
        "ownership": 0.15,
        "communication": 0.15
    }
    
    active_weights = {k: v for k, v in raw_weights.items() if k in skill_profile}
    total_weight = sum(active_weights.values())
    
    if total_weight > 0:
        normalized_weights = {k: v / total_weight for k, v in active_weights.items()}
        weighted_mean = sum(skill_profile[k] * normalized_weights[k] for k in active_weights)
    else:
        weighted_mean = 0.0

    overall_score = round(100 * weighted_mean / 5)
    
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    confidence = avg_conf * min(1.0, num_turns / 5.0)
    
    if confidence < 0.5:
        recommendation = "needs_more_evidence"
    elif overall_score >= 80:
        recommendation = "strong_yes"
    elif overall_score >= 65:
        recommendation = "yes"
    elif overall_score >= 50:
        recommendation = "maybe"
    else:
        recommendation = "no"

    # Best 3, worst 1
    evidence_list.sort(key=lambda x: x["score"], reverse=True)
    best_3 = evidence_list[:3]
    worst_1 = [evidence_list[-1]] if evidence_list and evidence_list[-1]["score"] <= 2 else []
    
    final_evidence = best_3 + worst_1
    strengths = [e["quote"] for e in best_3]
    concerns = [e["quote"] for e in worst_1]

    profile = {
        "overall_score": overall_score,
        "confidence": round(confidence, 2),
        "recommendation": recommendation,
        "skill_profile": skill_profile,
        "strengths": strengths,
        "concerns": concerns,
        "evidence": final_evidence
    }
    
    return profile

def write_summary(profile: dict, evidence: list) -> str:
    if not evidence:
        return "Not enough evidence to generate a summary."
        
    user_prompt = f"Evidence:\n{json.dumps(evidence)}\n\nProfile Scores:\n{json.dumps(profile['skill_profile'])}"
    res = complete_json("smart", SUMMARY_SYSTEM_PROMPT, user_prompt, SummarySchema)
    return res.get("summary", "")
