import json
from pydantic import BaseModel, model_validator
from typing import Any
from ai.llm import complete_json

class SummarySchema(BaseModel):
    summary: str

    @model_validator(mode='before')
    @classmethod
    def sanitize_summary(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"summary": data}
        if isinstance(data, list):
            return {"summary": " ".join(str(x) for x in data)}
        return data

SUMMARY_SYSTEM_PROMPT = """You are a senior hiring manager writing an objective, plain-English summary (3-4 sentences).
STRICT EVIDENCE CONSTRAINTS:
1. Synthesize ONLY the verified evidence quotes and concrete skill profile scores provided below.
2. Quote NOTHING that is not explicitly in the Evidence list.
3. NEVER assume or invent past employers, university degrees, years of experience, or external technologies not mentioned.
4. If reasoning or communication was rated low, note it plainly as an open question."""

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
        eval_dict = t.get("evaluation")
        if not eval_dict:
            continue
            
        confidences.append(eval_dict.get("confidence", 0.0))
        
        flags = eval_dict.get("flags", [])
        turn_score = eval_dict.get("score", 0)
        
        if "contradicts_claim" in flags:
            ownership_score = max(0.0, ownership_score - 2.0)
        elif turn_score <= 1:
            # If they can't answer basic questions about their own code, they lose ownership credit
            ownership_score = max(0.0, ownership_score - 1.0)
            
        for d, s in eval_dict.get("dimensions", {}).items():
            if d in dim_scores:
                dim_scores[d].append(s)
                
        if eval_dict.get("evidence_quote"):
            evidence_list.append({
                "claim": f"Performance on turn {t.get('turn_number', '?')}",
                "quote": eval_dict.get("evidence_quote"),
                "turn_number": t.get("turn_number"),
                "score": eval_dict.get("score", 0),
                "source_file_path": eval_dict.get("source_file_path"),
                "source_lines": eval_dict.get("source_lines")
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
    
    turn_scores = [t.get("evaluation", {}).get("score", 0) for t in turns if t.get("evaluation")]
    base_avg = sum(turn_scores) / len(turn_scores) if turn_scores else 0.0
    
    if total_weight > 0 and len(skill_profile) > 1: # more than just ownership
        normalized_weights = {k: v / total_weight for k, v in active_weights.items()}
        weighted_mean = sum(skill_profile[k] * normalized_weights[k] for k in active_weights)
        final_mean = (weighted_mean + base_avg) / 2
    else:
        final_mean = base_avg

    overall_score = round(100 * final_mean / 5)
    
    answered_turns = len(confidences)
    avg_conf = sum(confidences) / answered_turns if answered_turns > 0 else 0.0
    confidence = avg_conf * min(1.0, answered_turns / 5.0)
    
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
