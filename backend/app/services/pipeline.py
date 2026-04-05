from app.agents.classifier import classify_ticket
from app.agents.qa import qa_check
from app.agents.replier import generate_reply
from app.agents.router import route_ticket
from app.models.schemas import TicketInput, TicketResult, TraceStep


def determine_status(urgency: str, qa_status: str, sentiment: str) -> str:
    if qa_status == "needs_review":
        return "in_review"
    if urgency == "high":
        return "in_review"
    if urgency == "low" and sentiment == "positive":
        return "resolved"
    return "new"


def run_ticket_pipeline(ticket: TicketInput) -> TicketResult:
    trace: list[TraceStep] = []

    classification = classify_ticket(ticket.text)
    trace.append(TraceStep(agent="ClassifierAgent", output=classification))

    routing = route_ticket(classification["category"], ticket.text)
    trace.append(TraceStep(agent="RouterAgent", output=routing))

    reply = generate_reply(
        ticket_text=ticket.text,
        category=classification["category"],
        urgency=classification["urgency"],
        team=routing["assigned_team"],
    )
    trace.append(TraceStep(agent="ReplyAgent", output=reply))

    qa = qa_check(reply["draft_reply"])
    trace.append(TraceStep(agent="QAAgent", output=qa))

    # Simple one-retry loop if QA fails.
    if qa["qa_status"] == "needs_review":
        repaired_reply = generate_reply(
            ticket_text=ticket.text + " Please provide next step.",
            category=classification["category"],
            urgency=classification["urgency"],
            team=routing["assigned_team"],
        )
        qa = qa_check(repaired_reply["draft_reply"])
        reply = repaired_reply
        trace.append(TraceStep(agent="ReplyAgentRetry", output=reply))
        trace.append(TraceStep(agent="QAAgentRetry", output=qa))

    status = determine_status(
        urgency=classification["urgency"],
        qa_status=qa["qa_status"],
        sentiment=classification["sentiment"],
    )
    trace.append(TraceStep(agent="StatusAgent", output={"status": status}))

    return TicketResult(
        ticket_id=ticket.ticket_id,
        category=classification["category"],
        urgency=classification["urgency"],
        sentiment=classification["sentiment"],
        status=status,
        assigned_team=routing["assigned_team"],
        draft_reply=reply["draft_reply"],
        qa_status=qa["qa_status"],
        trace=trace,
    )


def build_metrics(results: list[TicketResult]) -> dict:
    return {
        "total_tickets": len(results),
        "high_priority": sum(1 for r in results if r.urgency == "high"),
        "needs_review": sum(1 for r in results if r.qa_status == "needs_review"),
        "approved": sum(1 for r in results if r.qa_status == "approved"),
        "new": sum(1 for r in results if r.status == "new"),
        "in_review": sum(1 for r in results if r.status == "in_review"),
        "resolved": sum(1 for r in results if r.status == "resolved"),
    }
