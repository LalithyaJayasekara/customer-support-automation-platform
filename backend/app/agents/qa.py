import json
import os

from app.config import settings


def _qa_rule_check(draft_reply: str) -> dict:
    checks = {
        "has_apology": "sorry" in draft_reply.lower(),
        "has_next_step": "reviewing" in draft_reply.lower() or "investigating" in draft_reply.lower(),
        "has_no_false_promise": "guarantee" not in draft_reply.lower(),
    }

    passed = all(checks.values())
    return {
        "qa_status": "approved" if passed else "needs_review",
        "checks": checks,
    }


def _qa_agents_sdk_check(draft_reply: str) -> dict | None:
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
            name="SupportQAAgent",
            model=settings.openai_model,
            instructions=(
                "You are a quality checker for support replies. "
                "Return ONLY valid JSON with keys: qa_status, checks, reasoning. "
                "qa_status must be 'approved' or 'needs_review'. "
                "checks must include booleans: has_apology, has_next_step, has_no_false_promise."
            ),
        )

        prompt = (
            "Review this support reply for quality and safety:\n"
            f"{draft_reply}\n\n"
            "Output strict JSON only."
        )

        result = Runner.run_sync(agent, input=prompt)
        final_output = getattr(result, "final_output", None)
        output_text = final_output if isinstance(final_output, str) else str(final_output or "")
        parsed = json.loads(output_text)

        qa_status = parsed.get("qa_status")
        checks = parsed.get("checks")

        if qa_status not in {"approved", "needs_review"}:
            return None
        if not isinstance(checks, dict):
            return None

        normalized_checks = {
            "has_apology": bool(checks.get("has_apology", False)),
            "has_next_step": bool(checks.get("has_next_step", False)),
            "has_no_false_promise": bool(checks.get("has_no_false_promise", False)),
        }

        return {
            "qa_status": qa_status,
            "checks": normalized_checks,
            "reasoning": str(parsed.get("reasoning", "")).strip(),
        }
    except Exception:
        return None


def qa_check(draft_reply: str) -> dict:
    ai_result = _qa_agents_sdk_check(draft_reply)
    if ai_result:
        return ai_result

    return _qa_rule_check(draft_reply)
