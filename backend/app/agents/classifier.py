from app.models.schemas import Category, Urgency


BILLING_KEYWORDS = {"charged", "charge", "billing", "payment", "invoice", "card"}
LOGIN_KEYWORDS = {"login", "log in", "password", "otp", "account locked", "cannot sign in"}
BUG_KEYWORDS = {"error", "bug", "crash", "broken", "issue", "not working"}
REFUND_KEYWORDS = {"refund", "money back", "cancel", "cancellation"}
HIGH_URGENCY = {"urgent", "asap", "immediately", "production", "blocked", "cannot"}
ANGRY_WORDS = {"angry", "frustrated", "worst", "terrible", "unacceptable"}


def classify_ticket(text: str) -> dict:
    lower = text.lower()

    category: Category = "general"
    if any(k in lower for k in BILLING_KEYWORDS):
        category = "billing"
    elif any(k in lower for k in LOGIN_KEYWORDS):
        category = "login"
    elif any(k in lower for k in REFUND_KEYWORDS):
        category = "refund"
    elif any(k in lower for k in BUG_KEYWORDS):
        category = "bug"

    urgency: Urgency = "medium"
    if any(k in lower for k in HIGH_URGENCY):
        urgency = "high"
    elif "whenever" in lower or "no hurry" in lower:
        urgency = "low"

    sentiment = "neutral"
    if any(k in lower for k in ANGRY_WORDS):
        sentiment = "angry"
    elif "thanks" in lower or "appreciate" in lower:
        sentiment = "positive"

    return {
        "category": category,
        "urgency": urgency,
        "sentiment": sentiment,
    }
