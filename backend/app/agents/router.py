from app.models.schemas import Team
import os
import json
import asyncio
from app.config import settings


def _route_rule_based(category: str, ticket_text: str = "") -> dict:
    # Enhanced routing with content analysis
    lower_text = ticket_text.lower() if ticket_text else ""
    
    # Base mapping
    base_mapping = {
        "billing": "billing_team",
        "refund": "billing_team",
        "login": "account_team",
        "bug": "tech_team",
        "general": "support_team",
    }
    
    assigned_team = base_mapping.get(category, "support_team")
    
    # Content-based routing adjustments
    if "urgent" in lower_text or "asap" in lower_text:
        # For urgent issues, escalate to senior teams
        if category == "billing":
            assigned_team = "billing_team"  # Keep billing urgent in billing
        elif category == "bug":
            assigned_team = "tech_team"  # Keep tech issues in tech
        else:
            assigned_team = "support_team"  # General urgent goes to support
    
    # Complex issues might need senior attention
    if len(ticket_text.split()) > 50:  # Long messages might be complex
        if category == "bug":
            assigned_team = "tech_team"  # Complex bugs stay with tech
    
    # Financial amounts might need special handling
    import re
    if re.search(r'\$\d+', ticket_text) or re.search(r'\d+\s*dollars?', lower_text):
        if category in ["billing", "refund"]:
            assigned_team = "billing_team"
    
    return {"assigned_team": assigned_team}


def _route_agents_sdk(ticket_text: str, category: str) -> dict | None:
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
            name="SupportRouterAgent",
            model=settings.openai_model,
            instructions=(
                "You are a customer support ticket router. "
                "Based on the ticket content and category, assign it to the most appropriate team. "
                "Return ONLY valid JSON with key: assigned_team. "
                "assigned_team must be one of: billing_team, account_team, tech_team, support_team."
            ),
        )

        prompt = (
            "Route this customer support ticket to the appropriate team:\n"
            f"Ticket: {ticket_text}\n"
            f"Category: {category}\n\n"
            "Output strict JSON only."
        )

        # Add timeout to prevent hanging on API issues
        try:
            result = asyncio.run(asyncio.wait_for(
                asyncio.to_thread(Runner.run_sync, agent, input=prompt),
                timeout=8.0  # 8 second timeout
            ))
        except asyncio.TimeoutError:
            raise Exception("AI routing timed out")

        final_output = getattr(result, "final_output", None)
        output_text = final_output if isinstance(final_output, str) else str(final_output or "")
        parsed = json.loads(output_text)

        assigned_team = parsed.get("assigned_team")
        if assigned_team not in {"billing_team", "account_team", "tech_team", "support_team"}:
            return None

        return {"assigned_team": assigned_team}
    except Exception as e:
        # Log the error but don't fail - fall back to rule-based
        print(f"AI routing failed, falling back to rules: {e}")
        return None


def route_ticket(category: str, ticket_text: str = "") -> dict:
    ai_result = _route_agents_sdk(ticket_text, category)
    if ai_result:
        return ai_result

    return _route_rule_based(category, ticket_text)
