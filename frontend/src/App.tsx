import { ChangeEvent, useEffect, useMemo, useState } from "react";

type TicketInput = {
  ticket_id: string;
  text: string;
};

type TraceStep = {
  agent: string;
  output: Record<string, unknown>;
};

type TicketResult = {
  ticket_id: string;
  category: string;
  urgency: string;
  sentiment: string;
  status: "new" | "in_review" | "resolved";
  assigned_team: string;
  draft_reply: string;
  qa_status: string;
  trace: TraceStep[];
};

type AnalyzeResponse = {
  results: TicketResult[];
  metrics: Record<string, number>;
};

type HistoryRunSummary = {
  run_id: number;
  created_at: string;
  total_tickets: number;
  high_priority: number;
  approved: number;
  needs_review: number;
};

type HistoryTicketRecord = {
  ticket_id: string;
  original_text: string;
  category: string;
  urgency: string;
  sentiment: string;
  status: string;
  assigned_team: string;
  draft_reply: string;
  qa_status: string;
};

type HistoryRunDetail = {
  run_id: number;
  created_at: string;
  metrics: Record<string, number>;
  tickets: HistoryTicketRecord[];
};

type CsvRowError = {
  rowNumber: number;
  message: string;
  rowContent: string;
};

type CsvParseResult = {
  tickets: TicketInput[];
  errors: CsvRowError[];
};

const API_URL = "http://127.0.0.1:8000";
const DEFAULT_TEXT = `T1|I was charged twice for my subscription. This is urgent.
T2|I cannot login after resetting my password.
T3|The dashboard crashes when I export reports.
T4|Please cancel my plan and process a refund.`;

function parseTicketLines(raw: string): TicketInput[] {
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, idx) => {
      const [id, ...rest] = line.split("|");
      const text = rest.join("|").trim();
      return {
        ticket_id: (id || `T${idx + 1}`).trim(),
        text,
      };
    })
    .filter((t) => t.text.length > 0);
}

function parseCsvRow(row: string): string[] {
  const cols: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < row.length; i += 1) {
    const char = row[i];
    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }
    if (char === "," && !inQuotes) {
      cols.push(current.trim());
      current = "";
      continue;
    }
    current += char;
  }

  cols.push(current.trim());
  return cols;
}

function parseCsvTickets(csvText: string): CsvParseResult {
  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim());

  const nonEmptyLines = lines.filter(Boolean);
  if (!nonEmptyLines.length) {
    return { tickets: [], errors: [] };
  }

  const startAt = nonEmptyLines[0].toLowerCase().startsWith("ticket_id,") ? 1 : 0;

  const tickets: TicketInput[] = [];
  const errors: CsvRowError[] = [];
  const seenIds = new Set<string>();

  for (let i = startAt; i < nonEmptyLines.length; i += 1) {
    const line = nonEmptyLines[i];
    const rowNumber = i + 1;
    const cols = parseCsvRow(line);

    if (cols.length < 2) {
      errors.push({
        rowNumber,
        message: "Expected at least 2 columns: ticket_id,text",
        rowContent: line,
      });
      continue;
    }

    const ticketId = cols[0].trim();
    const text = cols.slice(1).join(",").trim();

    if (!ticketId) {
      errors.push({
        rowNumber,
        message: "Missing ticket_id",
        rowContent: line,
      });
      continue;
    }

    if (!text) {
      errors.push({
        rowNumber,
        message: "Missing ticket text",
        rowContent: line,
      });
      continue;
    }

    if (text.length < 5) {
      errors.push({
        rowNumber,
        message: "Ticket text is too short (min 5 chars)",
        rowContent: line,
      });
      continue;
    }

    if (seenIds.has(ticketId)) {
      errors.push({
        rowNumber,
        message: "Duplicate ticket_id",
        rowContent: line,
      });
      continue;
    }

    seenIds.add(ticketId);
    tickets.push({ ticket_id: ticketId, text });
  }

  return { tickets, errors };
}

function uniqueValues(values: string[]): string[] {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
}

function toDisplayLabel(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function csvEscape(value: string): string {
  const escaped = value.replace(/"/g, '""');
  return `"${escaped}"`;
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function buildDecisionSteps(result: TicketResult): string[] {
  return [
    `The message was understood as ${toDisplayLabel(result.category)}.`,
    `Priority was set to ${toDisplayLabel(result.urgency)} based on the message tone and words.`,
    `It was sent to ${toDisplayLabel(result.assigned_team)}.`,
    `Reply quality check result is ${toDisplayLabel(result.qa_status)}.`,
    `Current progress is ${toDisplayLabel(result.status)}.`,
  ];
}

export default function App() {
  const [rawTickets, setRawTickets] = useState(DEFAULT_TEXT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [csvErrors, setCsvErrors] = useState<CsvRowError[]>([]);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [urgencyFilter, setUrgencyFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [qaFilter, setQaFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyRuns, setHistoryRuns] = useState<HistoryRunSummary[]>([]);
  const [selectedHistory, setSelectedHistory] = useState<HistoryRunDetail | null>(null);
  const [aiModeActive, setAiModeActive] = useState(false);
  const [modeLoaded, setModeLoaded] = useState(false);

  const parsedCount = useMemo(() => parseTicketLines(rawTickets).length, [rawTickets]);

  useEffect(() => {
    async function loadSystemMode() {
      try {
        const response = await fetch(`${API_URL}/system-mode`);
        if (!response.ok) {
          throw new Error("Could not load mode");
        }
        const json = (await response.json()) as { ai_mode_active?: boolean };
        setAiModeActive(Boolean(json.ai_mode_active));
      } catch {
        setAiModeActive(false);
      } finally {
        setModeLoaded(true);
      }
    }

    loadSystemMode();
  }, []);

  async function handleCsvUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      const csvText = await file.text();
      const parsed = parseCsvTickets(csvText);
      setCsvErrors(parsed.errors);

      const tickets = parsed.tickets;
      if (!tickets.length) {
        setError("No valid CSV rows found. Please fix the CSV validation errors below.");
        setData(null);
        return;
      }

      const textAreaData = tickets.map((t) => `${t.ticket_id}|${t.text}`).join("\n");
      setRawTickets(textAreaData);
      if (parsed.errors.length) {
        setError(`Loaded ${tickets.length} valid row(s) with ${parsed.errors.length} row error(s).`);
      } else {
        setError("");
      }
      setData(null);
    } catch {
      setError("Could not read CSV file.");
      setCsvErrors([]);
    } finally {
      e.target.value = "";
    }
  }

  async function handleAnalyze() {
    setLoading(true);
    setError("");
    setCsvErrors([]);
    setData(null);
    try {
      const tickets = parseTicketLines(rawTickets);
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tickets }),
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const json = (await response.json()) as AnalyzeResponse;
      setData(json);
      setUrgencyFilter("all");
      setCategoryFilter("all");
      setQaFilter("all");
      setStatusFilter("all");
      loadHistoryRuns();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  async function loadHistoryRuns() {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const response = await fetch(`${API_URL}/history?limit=20`);
      if (!response.ok) {
        throw new Error(`Could not load history (${response.status})`);
      }
      const json = (await response.json()) as HistoryRunSummary[];
      setHistoryRuns(json);
    } catch (e) {
      setHistoryError(e instanceof Error ? e.message : "Could not load history");
    } finally {
      setHistoryLoading(false);
    }
  }

  async function openHistoryRun(runId: number) {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const response = await fetch(`${API_URL}/history/${runId}`);
      if (!response.ok) {
        throw new Error(`Could not load run details (${response.status})`);
      }
      const json = (await response.json()) as HistoryRunDetail;
      setSelectedHistory(json);
    } catch (e) {
      setHistoryError(e instanceof Error ? e.message : "Could not load run details");
      setSelectedHistory(null);
    } finally {
      setHistoryLoading(false);
    }
  }

  async function deleteHistoryRun(runId: number) {
    const confirmed = window.confirm(`Delete run #${runId}? This cannot be undone.`);
    if (!confirmed) {
      return;
    }

    setHistoryLoading(true);
    setHistoryError("");
    try {
      const response = await fetch(`${API_URL}/history/${runId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`Could not delete run (${response.status})`);
      }

      if (selectedHistory?.run_id === runId) {
        setSelectedHistory(null);
      }

      await loadHistoryRuns();
    } catch (e) {
      setHistoryError(e instanceof Error ? e.message : "Could not delete run");
    } finally {
      setHistoryLoading(false);
    }
  }

  const urgencyOptions = useMemo(
    () => uniqueValues(data?.results.map((r) => r.urgency) ?? []),
    [data]
  );
  const categoryOptions = useMemo(
    () => uniqueValues(data?.results.map((r) => r.category) ?? []),
    [data]
  );
  const qaOptions = useMemo(() => uniqueValues(data?.results.map((r) => r.qa_status) ?? []), [data]);
  const statusOptions = useMemo(() => uniqueValues(data?.results.map((r) => r.status) ?? []), [data]);

  const filteredResults = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.results.filter((r) => {
      const byUrgency = urgencyFilter === "all" || r.urgency === urgencyFilter;
      const byCategory = categoryFilter === "all" || r.category === categoryFilter;
      const byQa = qaFilter === "all" || r.qa_status === qaFilter;
      const byStatus = statusFilter === "all" || r.status === statusFilter;
      return byUrgency && byCategory && byQa && byStatus;
    });
  }, [data, urgencyFilter, categoryFilter, qaFilter, statusFilter]);

  function downloadCsvErrorReport() {
    if (!csvErrors.length) {
      return;
    }

    const header = "row_number,error_message,row_content";
    const rows = csvErrors.map(
      (item) => `${item.rowNumber},${csvEscape(item.message)},${csvEscape(item.rowContent)}`
    );
    const csvContent = [header, ...rows].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `csv_validation_report_${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  return (
    <div className="container">
      <header>
        <div className="title-row">
          <h1>Smart Customer Support Helper</h1>
          {modeLoaded && (
            <span className={aiModeActive ? "mode-badge active" : "mode-badge inactive"}>
              {aiModeActive ? "AI mode active" : "Rule-based mode"}
            </span>
          )}
        </div>
        <p>
          Add customer messages in <strong>ID|TEXT</strong> format and get issue type, priority,
          team assignment, and a suggested reply.
        </p>
      </header>

      <section className="panel">
        <label htmlFor="tickets">Customer Messages</label>
        <input id="csvUpload" type="file" accept=".csv" onChange={handleCsvUpload} />
        <textarea
          id="tickets"
          value={rawTickets}
          onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
            setRawTickets(e.target.value);
            if (csvErrors.length) {
              setCsvErrors([]);
            }
          }}
          rows={9}
        />
        <div className="row">
          <span>{parsedCount} message(s) ready</span>
          <button onClick={handleAnalyze} disabled={loading || parsedCount === 0}>
            {loading ? "Processing..." : "Process Messages"}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        {csvErrors.length > 0 && (
          <div className="csv-errors" role="status" aria-live="polite">
            <h3>File Check Report</h3>
            <p>
              Found {csvErrors.length} issue(s). Valid rows are loaded when possible.
            </p>
            <div className="report-actions">
              <button type="button" onClick={downloadCsvErrorReport}>
                Download Issue Report (.csv)
              </button>
            </div>
            <ul>
              {csvErrors.map((item, idx) => (
                <li key={`${item.rowNumber}-${idx}`}>
                  Row {item.rowNumber}: {item.message}
                  <div className="csv-row-content">{item.rowContent}</div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {data && (
        <>
          <section className="metrics-grid">
            <div className="metric">
              <h3>Total</h3>
              <p>{data.metrics.total_tickets ?? 0}</p>
            </div>
            <div className="metric">
              <h3>High Priority</h3>
              <p>{data.metrics.high_priority ?? 0}</p>
            </div>
            <div className="metric">
              <h3>Reply Ready</h3>
              <p>{data.metrics.approved ?? 0}</p>
            </div>
            <div className="metric">
              <h3>Needs Review</h3>
              <p>{data.metrics.needs_review ?? 0}</p>
            </div>
            <div className="metric">
              <h3>New</h3>
              <p>{data.metrics.new ?? 0}</p>
            </div>
            <div className="metric">
              <h3>In Review</h3>
              <p>{data.metrics.in_review ?? 0}</p>
            </div>
            <div className="metric">
              <h3>Resolved</h3>
              <p>{data.metrics.resolved ?? 0}</p>
            </div>
          </section>

          <section className="panel">
            <h2>Filters</h2>
            <div className="filters-grid">
              <label>
                Priority
                <select
                  value={urgencyFilter}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setUrgencyFilter(e.target.value)}
                >
                  <option value="all">All</option>
                  {urgencyOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {toDisplayLabel(opt)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Issue Type
                <select
                  value={categoryFilter}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setCategoryFilter(e.target.value)}
                >
                  <option value="all">All</option>
                  {categoryOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {toDisplayLabel(opt)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Reply Check
                <select
                  value={qaFilter}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setQaFilter(e.target.value)}
                >
                  <option value="all">All</option>
                  {qaOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {toDisplayLabel(opt)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Progress
                <select
                  value={statusFilter}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All</option>
                  {statusOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {toDisplayLabel(opt)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="row">
              <span>
                Showing {filteredResults.length} of {data.results.length} message(s)
              </span>
              <button
                type="button"
                onClick={() => {
                  setUrgencyFilter("all");
                  setCategoryFilter("all");
                  setQaFilter("all");
                  setStatusFilter("all");
                }}
              >
                Clear Filters
              </button>
            </div>
          </section>

          <section className="panel">
            <h2>Results</h2>
            {filteredResults.map((r) => (
              <article key={r.ticket_id} className="ticket-card">
                <h3>{r.ticket_id}</h3>
                <p>
                  <strong>Issue Type:</strong> {toDisplayLabel(r.category)} | <strong>Priority:</strong>{" "}
                  {toDisplayLabel(r.urgency)} | <strong>Progress:</strong> {toDisplayLabel(r.status)} |{" "}
                  <strong>Assigned Team:</strong> {toDisplayLabel(r.assigned_team)} | <strong>Reply Check:</strong>{" "}
                  {toDisplayLabel(r.qa_status)}
                </p>
                <p>
                  <strong>Suggested Reply:</strong> {r.draft_reply}
                </p>
                <details>
                  <summary>How This Decision Was Made</summary>
                  <ul className="decision-list">
                    {buildDecisionSteps(r).map((step, index) => (
                      <li key={`${r.ticket_id}-step-${index + 1}`}>{step}</li>
                    ))}
                  </ul>
                </details>
              </article>
            ))}
          </section>
        </>
      )}

      <section className="panel">
        <div className="history-header">
          <h2>History</h2>
          <button type="button" onClick={loadHistoryRuns} disabled={historyLoading}>
            {historyLoading ? "Loading..." : "Load History"}
          </button>
        </div>
        <p>View earlier message processing runs and open any run to see details.</p>
        {historyError && <p className="error">{historyError}</p>}

        {historyRuns.length === 0 ? (
          <p>No history loaded yet. Click Load History.</p>
        ) : (
          <div className="history-runs">
            {historyRuns.map((run) => (
              <div key={run.run_id} className="history-run-row">
                <button
                  type="button"
                  className="history-run-btn"
                  onClick={() => openHistoryRun(run.run_id)}
                >
                  Run #{run.run_id} | {formatDateTime(run.created_at)} | {run.total_tickets} message(s)
                </button>
                <button
                  type="button"
                  className="delete-btn"
                  onClick={() => deleteHistoryRun(run.run_id)}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}

        {selectedHistory && (
          <div className="history-detail">
            <h3>
              Run #{selectedHistory.run_id} - {formatDateTime(selectedHistory.created_at)}
            </h3>
            <div className="metrics-grid">
              <div className="metric">
                <h3>Total</h3>
                <p>{selectedHistory.metrics.total_tickets ?? 0}</p>
              </div>
              <div className="metric">
                <h3>High Priority</h3>
                <p>{selectedHistory.metrics.high_priority ?? 0}</p>
              </div>
              <div className="metric">
                <h3>Reply Ready</h3>
                <p>{selectedHistory.metrics.approved ?? 0}</p>
              </div>
              <div className="metric">
                <h3>Needs Review</h3>
                <p>{selectedHistory.metrics.needs_review ?? 0}</p>
              </div>
            </div>

            {selectedHistory.tickets.map((ticket) => (
              <article key={`${selectedHistory.run_id}-${ticket.ticket_id}`} className="ticket-card">
                <h3>{ticket.ticket_id}</h3>
                <p>
                  <strong>Customer Message:</strong> {ticket.original_text}
                </p>
                <p>
                  <strong>Issue Type:</strong> {toDisplayLabel(ticket.category)} | <strong>Priority:</strong>{" "}
                  {toDisplayLabel(ticket.urgency)} | <strong>Progress:</strong> {toDisplayLabel(ticket.status)}
                </p>
                <p>
                  <strong>Assigned Team:</strong> {toDisplayLabel(ticket.assigned_team)} | <strong>Reply Check:</strong>{" "}
                  {toDisplayLabel(ticket.qa_status)}
                </p>
                <p>
                  <strong>Suggested Reply:</strong> {ticket.draft_reply}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
