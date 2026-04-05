import os
import asyncio
import random

from app.config import settings


def _generate_rule_reply(category: str, urgency: str, team: str) -> str:
    # Add randomness for more probabilistic responses
    openings = [
        "Sorry for the inconvenience.",
        "We apologize for any inconvenience caused.",
        "We're sorry to hear about this issue.",
        "Thank you for bringing this to our attention."
    ]
    
    if urgency == "high":
        openings = [
            "Sorry for the urgent inconvenience caused.",
            "We understand this is urgent and apologize for the delay.",
            "We're prioritizing this urgent matter."
        ]

    next_steps = {
        "billing": [
            "Our billing team is reviewing your payment details now.",
            "Our billing specialists are examining your account immediately.",
            "We're investigating your billing concern right away."
        ],
        "refund": [
            "Our billing team is validating your refund request now.",
            "We're processing your refund request with priority.",
            "Our team is reviewing your refund eligibility."
        ],
        "login": [
            "Our account team is verifying your access issue now.",
            "We're checking your account security and access.",
            "Our account specialists are resolving your login issue."
        ],
        "bug": [
            "Our technical team is investigating the issue now.",
            "We're debugging this technical problem immediately.",
            "Our engineers are working on fixing this bug."
        ],
        "general": [
            "Our support team is reviewing your request now.",
            "We're addressing your concern with our support team.",
            "Our team is looking into this matter for you."
        ]
    }

    closings = [
        "We will share an update as soon as possible.",
        "We'll follow up with you shortly.",
        "You can expect to hear from us soon.",
        "We'll keep you updated on our progress."
    ]

    opening = random.choice(openings)
    next_step = random.choice(next_steps.get(category, next_steps["general"]))
    closing = random.choice(closings)

    reply = (
        f"{opening} "
        f"We understand your concern. "
        f"{next_step} "
        f"Assigned owner: {team}. "
        f"{closing}"
    )

    return reply


def _generate_agents_sdk_reply(ticket_text: str, category: str, urgency: str, team: str) -> str | None:
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
            name="SupportReplyAgent",
            model=settings.openai_model,
            instructions=(
                "You write short, polite customer-support replies. "
                "Always include: apology, clear next step, and realistic expectation. "
                "Do not make promises you cannot guarantee."
            ),
        )

        prompt = (
            "Create a support reply using these details:\n"
            f"- Ticket text: {ticket_text}\n"
            f"- Category: {category}\n"
            f"- Urgency: {urgency}\n"
            f"- Assigned team: {team}\n"
            "Keep it concise and professional."
        )

        try:
            result = asyncio.run(asyncio.wait_for(
                asyncio.to_thread(Runner.run_sync, agent, input=prompt),
                timeout=8.0  # 8 second timeout
            ))
        except asyncio.TimeoutError:
            raise Exception("AI reply generation timed out")

        final_output = getattr(result, "final_output", None)
        if isinstance(final_output, str) and final_output.strip():
            return final_output.strip()

        text_output = str(final_output or "").strip()
        return text_output or None
    except Exception as e:
        # Log the error but don't fail - fall back to rule-based
        print(f"AI reply generation failed, falling back to rules: {e}")
        return None


def generate_reply(ticket_text: str, category: str, urgency: str, team: str) -> dict:
    ai_reply = _generate_agents_sdk_reply(
        ticket_text=ticket_text,
        category=category,
        urgency=urgency,
        team=team,
    )

    if ai_reply:
        return {"draft_reply": ai_reply}

    return {"draft_reply": _generate_rule_reply(category=category, urgency=urgency, team=team)}
