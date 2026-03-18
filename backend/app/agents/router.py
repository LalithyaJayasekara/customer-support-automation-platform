from app.models.schemas import Team


def route_ticket(category: str) -> dict:
    mapping: dict[str, Team] = {
        "billing": "billing_team",
        "refund": "billing_team",
        "login": "account_team",
        "bug": "tech_team",
        "general": "support_team",
    }
    assigned_team = mapping.get(category, "support_team")
    return {"assigned_team": assigned_team}
