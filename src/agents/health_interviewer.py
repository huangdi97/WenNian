"""Health interviewer agent — active questioning (max 3 rounds).

Converts vague health perceptions into structured biomarker-relevant
data through targeted follow-up questions. Never provides diagnoses.

Reference: Google AI Clinical Study (2026) — Active questioning improves diagnosis by 27%
"""

from typing import Any, Dict, List, Optional

from . import BaseAgent, AgentOutput, CapabilityToken

DEFAULT_AGENT_ID = "health_interviewer.v2"


class HealthInterviewer(BaseAgent):
    """Conducts structured health interviews with active follow-up.

    Performs up to 3 rounds of questioning to refine vague health
    perceptions into structured observations.

    Args:
        max_rounds: Maximum interview rounds (default 3).
        agent_id: Unique identifier.
        capability: Capability token.
    """

    QUESTION_BANK = [
        {
            "trigger_keywords": ["疲劳", "累", "没精神", "tired", "fatigue"],
            "follow_up": "您的疲劳感主要在什么时间出现？是否伴随睡眠质量下降或情绪波动？",
            "dimension": "metabolic",
        },
        {
            "trigger_keywords": ["关节", "膝盖", "腰", "疼痛", "pain", "ache"],
            "follow_up": "疼痛是持续性的还是活动后加重？是否影响日常活动（如上下楼梯、弯腰）？",
            "dimension": "musculoskeletal",
        },
        {
            "trigger_keywords": ["记忆力", "记性", "忘记", "memory", "forget"],
            "follow_up": "是近期记忆减退（如忘记刚发生的事）还是远期记忆问题？是否影响工作或社交？",
            "dimension": "neural",
        },
        {
            "trigger_keywords": ["皮肤", "皱纹", "斑", "skin", "wrinkle"],
            "follow_up": "皮肤变化主要集中在面部还是全身？是否伴随干燥、瘙痒或色素沉着？",
            "dimension": "skin",
        },
        {
            "trigger_keywords": ["睡眠", "失眠", "sleep", "insomnia"],
            "follow_up": "是入睡困难、易醒还是早醒？平均每晚睡眠几小时？这种情况持续多久了？",
            "dimension": "social",
        },
        {
            "trigger_keywords": ["压力", "焦虑", "心情", "stress", "anxiety", "mood"],
            "follow_up": "这种感受是否与特定事件相关？是否影响了您的社交活动或工作表现？",
            "dimension": "social",
        },
        {
            "trigger_keywords": ["消化", "肠胃", "腹胀", "便秘", "digestion", "gut"],
            "follow_up": "症状是否与特定食物相关？大便频率和性状是否有变化？",
            "dimension": "microbiome",
        },
        {
            "trigger_keywords": ["视力", "听力", "vision", "hearing"],
            "follow_up": "是逐渐下降还是突然变化？是否已影响驾驶、阅读或日常沟通？",
            "dimension": "sensory",
        },
    ]

    def __init__(
        self,
        max_rounds: int = 3,
        agent_id: str = DEFAULT_AGENT_ID,
        capability: Optional[CapabilityToken] = None,
    ) -> None:
        super().__init__(agent_id=agent_id, capability=capability)
        self.max_rounds = max_rounds

    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        """Conduct health interview with up to 3 rounds of active questioning.

        Args:
            context: Should include 'initial_complaint' (user's free text).

        Returns:
            AgentOutput with structured interview summary.
        """
        initial = context.get("initial_complaint", "")
        history = context.get("history", [])
        round_num = len(history) + 1

        if round_num > self.max_rounds:
            return self._summarize(initial, history)

        # Find relevant follow-up questions
        follow_ups = self._select_questions(initial)
        questions = [q["follow_up"] for q in follow_ups[:2]]

        if not questions:
            return self._summarize(initial, history)

        return AgentOutput(
            success=True,
            data={
                "round": round_num,
                "questions": questions,
                "identified_dimensions": [q["dimension"] for q in follow_ups],
                "interview_ongoing": round_num < self.max_rounds,
            },
        )

    def _select_questions(self, text: str) -> List[Dict]:
        text_lower = text.lower()
        return [q for q in self.QUESTION_BANK
                if any(kw in text_lower for kw in q["trigger_keywords"])]

    def _summarize(self, initial: str, history: List[Dict]) -> AgentOutput:
        dimensions_found = set()
        for q in self.QUESTION_BANK:
            if any(kw in initial.lower() for kw in q["trigger_keywords"]):
                dimensions_found.add(q["dimension"])

        return AgentOutput(
            success=True,
            data={
                "interview_complete": True,
                "initial_complaint": initial,
                "rounds_conducted": len(history),
                "identified_dimensions": sorted(dimensions_found),
                "structured_summary": (
                    f"经过{len(history)}轮追问，您的健康关注主要集中在: "
                    f"{', '.join(sorted(dimensions_found)) if dimensions_found else '一般健康关注'}。"
                    "建议进行相应维度的详细评估。"
                ),
                "disclaimer": "本访谈不构成医疗诊断，仅供健康数据采集参考。",
            },
        )
