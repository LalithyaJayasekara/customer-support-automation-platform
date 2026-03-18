import os

from app.config import settings


def _generate_rule_reply(category: str, urgency: str, team: str) -> str:
    opening = "Sorry for the inconvenience."
    if urgency == "high":
        opening = "Sorry for the urgent inconvenience caused."

    next_step = {
        "billing": "Our billing team is reviewing your payment details now.",
        "refund": "Our billing team is validating your refund request now.",
        "login": "Our account team is verifying your access issue now.",
        "bug": "Our technical team is investigating the issue now.",
        "general": "Our support team is reviewing your request now.",
    }.get(category, "Our support team is reviewing your request now.")

    reply = (
        f"{opening} "
        f"We understand your concern. "
        f"{next_step} "
        f"Assigned owner: {team}. "
        "We will share an update as soon as possible."
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

        result = Runner.run_sync(agent, input=prompt)
        final_output = getattr(result, "final_output", None)
        if isinstance(final_output, str) and final_output.strip():
            return final_output.strip()

        text_output = str(final_output or "").strip()
        return text_output or None
    except Exception:
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
