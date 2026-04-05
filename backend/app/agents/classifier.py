from app.models.schemas import Category, Urgency
import os
import json
import asyncio
import random
import re
from app.config import settings


BILLING_KEYWORDS = {"charged", "charge", "billing", "payment", "invoice", "card", "fee", "cost", "price", "subscription", "plan"}
LOGIN_KEYWORDS = {"login", "log in", "password", "otp", "account locked", "cannot sign in", "access", "signin", "authentication", "credentials"}
BUG_KEYWORDS = {"error", "bug", "crash", "broken", "issue", "not working", "glitch", "problem", "failure", "malfunction"}
REFUND_KEYWORDS = {"refund", "money back", "cancel", "cancellation", "return", "reimbursement"}
HIGH_URGENCY = {"urgent", "asap", "immediately", "production", "blocked", "cannot", "stuck", "critical", "emergency", "priority"}
ANGRY_WORDS = {"angry", "frustrated", "worst", "terrible", "unacceptable", "ridiculous", "outrageous", "disappointed", "furious"}
POSITIVE_WORDS = {"thanks", "appreciate", "thank you", "great", "good", "excellent", "wonderful", "helpful"}


def _classify_rule_based(text: str) -> dict:
    lower = text.lower()
    
    # Enhanced keyword sets with weights
    keyword_scores = {
        "billing": {
            "primary": ["charged", "charge", "billing", "payment", "invoice", "card", "fee", "cost", "price", "subscription", "plan", "bill"],
            "secondary": ["money", "pay", "amount", "transaction", "purchase"]
        },
        "login": {
            "primary": ["login", "log in", "password", "otp", "account locked", "cannot sign in", "access", "signin", "authentication", "credentials"],
            "secondary": ["account", "sign", "locked", "forgot", "reset"]
        },
        "bug": {
            "primary": ["error", "bug", "crash", "broken", "issue", "not working", "glitch", "problem", "failure", "malfunction"],
            "secondary": ["app", "application", "system", "website", "page", "loading", "stuck"]
        },
        "refund": {
            "primary": ["refund", "money back", "cancel", "cancellation", "return", "reimbursement"],
            "secondary": ["stop", "end", "terminate", "reverse", "back"]
        }
    }
    
    # Calculate scores for each category
    category_scores = {}
    for category, keywords in keyword_scores.items():
        score = 0
        for word in keywords["primary"]:
            if word in lower:
                score += 2  # Primary keywords worth more
        for word in keywords["secondary"]:
            if word in lower:
                score += 1  # Secondary keywords worth less
        category_scores[category] = score
    
    # Determine category with some randomness for ties
    max_score = max(category_scores.values())
    top_categories = [cat for cat, score in category_scores.items() if score == max_score]
    
    if max_score > 0:
        category = random.choice(top_categories) if len(top_categories) > 1 else top_categories[0]
    else:
        category = "general"
    
    # Enhanced urgency detection
    urgency_indicators = {
        "high": ["urgent", "asap", "immediately", "production", "blocked", "cannot", "stuck", "critical", "emergency", "priority", "help", "broken"],
        "medium": ["issue", "problem", "question", "need", "would like"],
        "low": ["whenever", "no hurry", "eventually", "sometime", "later"]
    }
    
    urgency_score = {"high": 0, "medium": 0, "low": 0}
    for level, words in urgency_indicators.items():
        for word in words:
            if word in lower:
                urgency_score[level] += 1
    
    # Add context-based urgency (exclamation marks, caps, question marks)
    if text.count('!') > 1:
        urgency_score["high"] += 1
    if text.isupper() and len(text) > 10:
        urgency_score["high"] += 1
    if text.count('?') > 2:
        urgency_score["medium"] += 1
    
    max_urgency = max(urgency_score.values())
    urgency_candidates = [u for u, s in urgency_score.items() if s == max_urgency]
    urgency = random.choice(urgency_candidates) if len(urgency_candidates) > 1 else urgency_candidates[0]
    
    # Enhanced sentiment analysis
    sentiment_indicators = {
        "angry": ["angry", "frustrated", "worst", "terrible", "unacceptable", "ridiculous", "outrageous", "disappointed", "furious", "mad", "upset"],
        "positive": ["thanks", "appreciate", "thank you", "great", "good", "excellent", "wonderful", "helpful", "pleased", "happy"],
        "neutral": ["please", "could you", "would you", "can you", "need", "help", "issue", "problem"]
    }
    
    sentiment_score = {"angry": 0, "positive": 0, "neutral": 0}
    for sent, words in sentiment_indicators.items():
        for word in words:
            if word in lower:
                sentiment_score[sent] += 1
    
    # Add emoji and punctuation-based sentiment
    if any(emoji in text for emoji in ['😊', '🙂', '😀', '👍', '❤️']):
        sentiment_score["positive"] += 1
    if any(emoji in text for emoji in ['😠', '😡', '😤', '👎']):
        sentiment_score["angry"] += 1
    if text.count('!') > 2:
        sentiment_score["angry"] += 0.5  # Multiple exclamation marks can indicate frustration
    
    max_sentiment = max(sentiment_score.values())
    sentiment_candidates = [s for s, score in sentiment_score.items() if score == max_sentiment]
    sentiment = random.choice(sentiment_candidates) if len(sentiment_candidates) > 1 else sentiment_candidates[0]
    
    return {
        "category": category,
        "urgency": urgency,
        "sentiment": sentiment,
    }


def _classify_agents_sdk(text: str) -> dict | None:
    if not (settings.use_llm and settings.use_agents_sdk and settings.openai_api_key):
        return None

    try:
        # Lazy import keeps local/dev mode working without Agents SDK installed.
        from agents import Agent, Runner  # type: ignore
    except Exception:
        return None

    try:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

        agent = Agent(
            name="SupportClassifierAgent",
            model=settings.openai_model,
            instructions=(
                "You are a customer support ticket classifier. "
                "Analyze the ticket text and return ONLY valid JSON with keys: category, urgency, sentiment. "
                "category must be one of: billing, login, bug, refund, general. "
                "urgency must be one of: low, medium, high. "
                "sentiment must be one of: positive, neutral, angry."
            ),
        )

        prompt = (
            "Classify this customer support ticket:\n"
            f"{text}\n\n"
            "Output strict JSON only."
        )

        # Add timeout to prevent hanging on API issues
        try:
            result = asyncio.run(asyncio.wait_for(
                asyncio.to_thread(Runner.run_sync, agent, input=prompt),
                timeout=8.0  # 8 second timeout
            ))
        except asyncio.TimeoutError:
            raise Exception("AI classification timed out")

        final_output = getattr(result, "final_output", None)
        output_text = final_output if isinstance(final_output, str) else str(final_output or "")
        parsed = json.loads(output_text)

        category = parsed.get("category")
        urgency = parsed.get("urgency")
        sentiment = parsed.get("sentiment")

        if category not in {"billing", "login", "bug", "refund", "general"}:
            return None
        if urgency not in {"low", "medium", "high"}:
            return None
        if sentiment not in {"positive", "neutral", "angry"}:
            return None

        return {
            "category": category,
            "urgency": urgency,
            "sentiment": sentiment,
        }
    except Exception as e:
        # Log the error but don't fail - fall back to rule-based
        print(f"AI classification failed, falling back to rules: {e}")
        return None


def classify_ticket(text: str) -> dict:
    ai_result = _classify_agents_sdk(text)
    if ai_result:
        return ai_result

    return _classify_rule_based(text)
