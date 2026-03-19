from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    AnalyticsOverview,
    AnalyticsRunRecord,
    AnalyticsTicketRecord,
    AnalyzeRequest,
    AnalyzeResponse,
    HistoryRunDetail,
    HistoryRunSummary,
    TicketInput,
)
from app.config import settings
from app.services.pipeline import build_metrics, run_ticket_pipeline
from app.services.storage import (
    delete_history_run,
    get_analytics_overview,
    get_history_run_detail,
    init_db,
    list_analytics_runs,
    list_analytics_tickets,
    list_history_runs,
    save_analysis_run,
)


app = FastAPI(title="AI Support Ticket Triage Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/system-mode")
def system_mode() -> dict:
    ai_mode_active = bool(settings.use_agents_sdk)
    return {
        "ai_mode_active": ai_mode_active,
        "mode": "ai" if ai_mode_active else "rule_based",
        "ai_ready": bool(settings.use_llm and settings.use_agents_sdk and settings.openai_api_key),
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_tickets(payload: AnalyzeRequest) -> AnalyzeResponse:
    results = [run_ticket_pipeline(ticket) for ticket in payload.tickets]
    metrics = build_metrics(results)
    save_analysis_run(payload.tickets, results, metrics)
    return AnalyzeResponse(results=results, metrics=metrics)


@app.get("/history", response_model=list[HistoryRunSummary])
def history(limit: int = 20) -> list[HistoryRunSummary]:
    safe_limit = max(1, min(limit, 100))
    return list_history_runs(safe_limit)


@app.get("/history/{run_id}", response_model=HistoryRunDetail)
def history_detail(run_id: int) -> HistoryRunDetail:
    run = get_history_run_detail(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.delete("/history/{run_id}")
def history_delete(run_id: int) -> dict:
    deleted = delete_history_run(run_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"status": "deleted", "run_id": run_id}


@app.get("/analytics/overview", response_model=AnalyticsOverview)
def analytics_overview(limit_runs: int = 200) -> AnalyticsOverview:
    safe_limit = max(1, min(limit_runs, 5000))
    return AnalyticsOverview(**get_analytics_overview(safe_limit))


@app.get("/analytics/runs", response_model=list[AnalyticsRunRecord])
def analytics_runs(limit: int = 200) -> list[AnalyticsRunRecord]:
    safe_limit = max(1, min(limit, 5000))
    return [AnalyticsRunRecord(**row) for row in list_analytics_runs(safe_limit)]


@app.get("/analytics/tickets", response_model=list[AnalyticsTicketRecord])
def analytics_tickets(limit: int = 5000, run_id: int | None = None) -> list[AnalyticsTicketRecord]:
    safe_limit = max(1, min(limit, 20000))
    return [AnalyticsTicketRecord(**row) for row in list_analytics_tickets(safe_limit, run_id)]


@app.get("/sample-tickets", response_model=list[TicketInput])
def sample_tickets() -> list[TicketInput]:
    return [
        TicketInput(ticket_id="T1", text="I was charged twice for my subscription. This is urgent."),
        TicketInput(ticket_id="T2", text="I cannot login after resetting my password."),
        TicketInput(ticket_id="T3", text="The dashboard crashes when I export reports."),
        TicketInput(ticket_id="T4", text="Please cancel my plan and process a refund."),
    ]
