from app.schemas.intent import IntentClassification
from app.services.ai_client import complete_json
import re

SYSTEM_PROMPT = """You are the intent classifier for an AI Support & Operations Agent.

Classify the user's request into exactly one of these intents:

knowledge:
Questions that should be answered from the company's
knowledge base or documents.

data:
Requests to retrieve or inspect structured business data,
such as customers or support tickets.

action:
Requests that would require changing business data or
performing an operational write.

Rules:
- Do not perform the requested action.
- Only classify the request.
- Choose the most appropriate intent.
- Return a confidence score between 0 and 1.
- Give a short reason.
- Return ONLY a JSON object with the keys: intent, confidence, reason."""

def classify_intent(
    user_message: str,
) -> IntentClassification:
    if not user_message.strip():
        raise ValueError("User message cannot be empty.")

    # Resume/CV questions are document lookups. Route these deterministically
    # so a vague phrase such as "skills of that person in the resume" does not
    # get sent to customer-data or action handling by the classifier model.
    mentions_resume = re.search(
        r"\b(resume|resumes|cv|cvs|curriculum vitae)\b",
        user_message,
        flags=re.IGNORECASE,
    )
    asks_for_information = re.search(
        r"\b(what|which|list|show|find|tell|summari[sz]e|describe|skills?|experience|education|qualifications?)\b",
        user_message,
        flags=re.IGNORECASE,
    )
    if mentions_resume and asks_for_information:
        return IntentClassification(
            intent="knowledge",
            confidence=1.0,
            reason="The user is asking for information from a resume or CV.",
        )

    result = complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        response_model=IntentClassification,
    )
    assert isinstance(result, IntentClassification)
    return result
