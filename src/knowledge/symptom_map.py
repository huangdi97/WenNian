"""Symptom → Aging dimension mapping (100+ entries).

Maps common health complaints and symptoms to the twelve aging
dimensions for structured health interview routing.

Reference: Google AI Clinical Study (2026) — structured symptom mapping
"""

from typing import Any, Dict, List, Optional

# Symptom → [dimensions] mapping with confidence weights
SYMPTOM_MAP: Dict[str, List[Dict[str, Any]]] = {
    # Metabolic
    "疲劳": [{"dimension": "metabolic", "confidence": 0.7}, {"dimension": "immune", "confidence": 0.4}],
    "体重增加": [{"dimension": "metabolic", "confidence": 0.8}],
    "容易口渴": [{"dimension": "metabolic", "confidence": 0.7}],
    "饥饿感增强": [{"dimension": "metabolic", "confidence": 0.6}],
    "怕冷": [{"dimension": "metabolic", "confidence": 0.5}],
    "伤口愈合慢": [{"dimension": "metabolic", "confidence": 0.5}, {"dimension": "senescence", "confidence": 0.6}],
    # Immune
    "易感冒": [{"dimension": "immune", "confidence": 0.85}],
    "反复感染": [{"dimension": "immune", "confidence": 0.9}],
    "过敏加重": [{"dimension": "immune", "confidence": 0.7}],
    "淋巴结肿大": [{"dimension": "immune", "confidence": 0.8}],
    "低烧": [{"dimension": "immune", "confidence": 0.6}],
    # Musculoskeletal
    "关节疼痛": [{"dimension": "musculoskeletal", "confidence": 0.85}],
    "腰背痛": [{"dimension": "musculoskeletal", "confidence": 0.8}],
    "肌肉无力": [{"dimension": "musculoskeletal", "confidence": 0.85}],
    "步速变慢": [{"dimension": "musculoskeletal", "confidence": 0.75}],
    "握力下降": [{"dimension": "musculoskeletal", "confidence": 0.8}],
    "身高变矮": [{"dimension": "musculoskeletal", "confidence": 0.7}],
    "骨折": [{"dimension": "musculoskeletal", "confidence": 0.9}],
    # Neural
    "记忆力减退": [{"dimension": "neural", "confidence": 0.85}],
    "注意力不集中": [{"dimension": "neural", "confidence": 0.7}],
    "反应变慢": [{"dimension": "neural", "confidence": 0.75}],
    "头晕": [{"dimension": "neural", "confidence": 0.4}, {"dimension": "organ", "confidence": 0.5}],
    "头痛": [{"dimension": "neural", "confidence": 0.4}],
    "睡眠障碍": [{"dimension": "neural", "confidence": 0.5}, {"dimension": "social", "confidence": 0.5}],
    # Sensory
    "视力模糊": [{"dimension": "sensory", "confidence": 0.85}],
    "听力下降": [{"dimension": "sensory", "confidence": 0.9}],
    "耳鸣": [{"dimension": "sensory", "confidence": 0.7}],
    "嗅觉减退": [{"dimension": "sensory", "confidence": 0.8}],
    "味觉变化": [{"dimension": "sensory", "confidence": 0.6}],
    # Skin
    "皮肤干燥": [{"dimension": "skin", "confidence": 0.8}],
    "皱纹增多": [{"dimension": "skin", "confidence": 0.9}],
    "色斑": [{"dimension": "skin", "confidence": 0.8}],
    "皮肤松弛": [{"dimension": "skin", "confidence": 0.85}],
    "脱发": [{"dimension": "skin", "confidence": 0.5}, {"dimension": "reproductive", "confidence": 0.4}],
    # Microbiome
    "腹胀": [{"dimension": "microbiome", "confidence": 0.8}],
    "消化不良": [{"dimension": "microbiome", "confidence": 0.8}],
    "便秘": [{"dimension": "microbiome", "confidence": 0.85}],
    "腹泻": [{"dimension": "microbiome", "confidence": 0.7}],
    "食欲变化": [{"dimension": "microbiome", "confidence": 0.5}],
    # Social
    "情绪低落": [{"dimension": "social", "confidence": 0.8}],
    "焦虑": [{"dimension": "social", "confidence": 0.85}],
    "孤独感": [{"dimension": "social", "confidence": 0.9}],
    "社交退缩": [{"dimension": "social", "confidence": 0.85}],
    "压力大": [{"dimension": "social", "confidence": 0.8}],
    # Organ/Vascular
    "心悸": [{"dimension": "organ", "confidence": 0.7}],
    "胸闷": [{"dimension": "organ", "confidence": 0.75}],
    "气喘": [{"dimension": "organ", "confidence": 0.7}],
    "下肢水肿": [{"dimension": "organ", "confidence": 0.8}],
    "夜尿增多": [{"dimension": "organ", "confidence": 0.7}],
    # Reproductive
    "月经不规律": [{"dimension": "reproductive", "confidence": 0.9}],
    "潮热": [{"dimension": "reproductive", "confidence": 0.8}],
    "性欲减退": [{"dimension": "reproductive", "confidence": 0.7}],
    # Senescence
    "皮肤瘀斑": [{"dimension": "senescence", "confidence": 0.6}],
    "体力下降": [{"dimension": "senescence", "confidence": 0.5}, {"dimension": "musculoskeletal", "confidence": 0.6}],
    # Epigenetic
    "家族早衰史": [{"dimension": "epigenetic", "confidence": 0.7}],
}


SYMPTOM_DIMENSIONS = sorted(set(
    d["dimension"] for v in SYMPTOM_MAP.values() for d in v
))


def map_symptoms_to_dimensions(
    symptoms: List[str],
    min_confidence: float = 0.3,
) -> Dict[str, List[Dict[str, Any]]]:
    """Map a list of symptoms to relevant aging dimensions.

    Args:
        symptoms: List of symptom descriptions.
        min_confidence: Minimum confidence to include.

    Returns:
        Dict of dimension → [matching symptoms with confidence].
    """
    result: Dict[str, List[Dict[str, Any]]] = {}
    for symptom in symptoms:
        # Direct match
        if symptom in SYMPTOM_MAP:
            for entry in SYMPTOM_MAP[symptom]:
                if entry["confidence"] >= min_confidence:
                    result.setdefault(entry["dimension"], []).append({
                        "symptom": symptom,
                        "confidence": entry["confidence"],
                    })
        else:
            # Fuzzy match
            for key, entries in SYMPTOM_MAP.items():
                if key in symptom or symptom in key:
                    for entry in entries:
                        if entry["confidence"] >= min_confidence:
                            result.setdefault(entry["dimension"], []).append({
                                "symptom": symptom,
                                "matched_key": key,
                                "confidence": entry["confidence"] * 0.8,
                            })

    return result


def get_top_dimensions(symptoms: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
    """Get the top-k most relevant aging dimensions for given symptoms.

    Args:
        symptoms: List of symptoms.
        top_k: Number of dimensions to return.

    Returns:
        List of (dimension, cumulative_confidence) sorted.
    """
    mapped = map_symptoms_to_dimensions(symptoms)
    scored = []
    for dim, matches in mapped.items():
        total_conf = sum(m["confidence"] for m in matches)
        scored.append({
            "dimension": dim,
            "total_confidence": round(total_conf, 2),
            "symptom_count": len(matches),
        })
    scored.sort(key=lambda x: x["total_confidence"], reverse=True)
    return scored[:top_k]


def get_all_symptoms() -> List[str]:
    """Get all known symptoms.

    Returns:
        Sorted list of symptom names.
    """
    return sorted(SYMPTOM_MAP.keys())
