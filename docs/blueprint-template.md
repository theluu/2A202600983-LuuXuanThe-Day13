# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Cá nhân — Lưu Xuân Thế (MSSV 2A202600983)
- [REPO_URL]: <!-- TODO: dán URL repo GitHub của bạn -->
- [MEMBERS]:
  - Member A: Lưu Xuân Thế | Role: Logging & PII
  - Member B: Lưu Xuân Thế | Role: Tracing & Enrichment
  - Member C: Lưu Xuân Thế | Role: SLO & Alerts
  - Member D: Lưu Xuân Thế | Role: Load Test & Dashboard
  - Member E: Lưu Xuân Thế | Role: Demo & Report

> Đây là bài làm **cá nhân**: toàn bộ vai trò do Lưu Xuân Thế (2A202600983) thực hiện.

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 27
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/evidence/EVIDENCE.md#2-json-log-có-correlation_id (mẫu log; correlation_id=req-fb4a3d84 nối request_received + response_sent)
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/evidence/EVIDENCE.md#3-log-line-có-pii-redaction ([REDACTED_EMAIL]/[REDACTED_CREDIT_CARD]/[REDACTED_PASSPORT])
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/evidence/langfuse-traces.json (27 traces, đã xác minh qua API; chụp UI Langfuse khi đăng nhập) <!-- TODO: docs/evidence/02-langfuse-trace-waterfall.png -->
- [TRACE_WATERFALL_EXPLANATION]: Trace tên `run` (LabAgent.run, @observe) mang tags ["lab","qa","claude-sonnet-4-5"] + session_id + user_id (đã hash). Bên trong gồm retrieve (RAG) rồi llm.generate; khi bật rag_slow, span RAG phình to chiếm gần hết thời gian — đó là dấu hiệu khoanh vùng root cause (xem mục 4).

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/05-dashboard-6-panels.png (đủ 6 panel + đơn vị + đường SLO + auto-refresh 15s)
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 155ms |
| Error Rate | < 2% | 28d | 0% |
| Cost Budget | < $2.5/day | 1d | ~$0.002 / req |
| Quality | > 0.75 | 28d | 0.88 |

> Số liệu lấy từ snapshot `/metrics` sau load test (P50/P95/P99 = 153/155/155ms, quality_avg = 0.88). Dashboard: `dashboard.html` (mở qua `python scripts/serve_dashboard.py` → http://127.0.0.1:8014/dashboard.html).

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: config/alert_rules.yaml (3 rule: high_latency_p95 P2, high_error_rate P1, cost_budget_spike P2)
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#1-high-latency-p95

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Latency P95 vượt ngưỡng SLO (3000ms). Đo thật: cùng query, latency tăng từ ~150ms lên ~2655ms (≈17×) ngay sau khi bật toggle. Alert `high_latency_p95` (P2) kích hoạt.
- [ROOT_CAUSE_PROVED_BY]: Flow Metrics→Traces→Logs — Metrics báo P95 vọt → Trace cho thấy span RAG chiếm gần hết thời gian (không phải LLM) → Log lọc theo correlation_id xác nhận incident toggle `rag_slow` đang bật. <!-- TODO: dán Trace ID / log line cụ thể sau khi bật Langfuse -->
- [FIX_ACTION]: Tắt sự cố qua `POST /incidents/rag_slow/disable` (mô phỏng rollback nguồn retrieval chậm); runbook: truncate query dài, fallback retrieval source, giảm prompt size.
- [PREVENTIVE_MEASURE]: Đặt alert P95 + timeout cho RAG span, theo dõi tách riêng latency RAG vs LLM trên dashboard để phát hiện sớm.

---

## 5. Individual Contributions & Evidence

> Bài cá nhân — tất cả vai trò do Lưu Xuân Thế (2A202600983) thực hiện. Liệt kê theo từng vai trò.

### Lưu Xuân Thế — Role A: Logging & PII
- [TASKS_COMPLETED]: Cài PII scrubber vào pipeline structlog (`app/logging_config.py`: thêm `scrub_event` trước `JsonlFileProcessor`); bổ sung regex hộ chiếu + địa chỉ VN (`app/pii.py`). Kết quả: email/thẻ/hộ chiếu bị che, validate PII PASS.
- [EVIDENCE_LINK]: <!-- TODO: link commit --> · docs/evidence/EVIDENCE.md#3-log-line-có-pii-redaction

### Lưu Xuân Thế — Role B: Tracing & Enrichment
- [TASKS_COMPLETED]: Enrich log với context request (`app/main.py`: bind user_id_hash, session_id, feature, model, env); xác nhận `@observe()` của agent gửi tags + usage. Kết quả: validate Log enrichment PASS, 0 record thiếu context.
- [EVIDENCE_LINK]: <!-- TODO: link commit --> · docs/evidence/EVIDENCE.md#2-json-log-có-correlation_id

### Lưu Xuân Thế — Role C: SLO & Alerts
- [TASKS_COMPLETED]: Rà soát/áp dụng SLO (`config/slo.yaml`: P95<3000ms, error<2%, cost<$2.5/ngày, quality>0.75) và 3 alert rule + runbook (`config/alert_rules.yaml`, `docs/alerts.md`).
- [EVIDENCE_LINK]: config/slo.yaml · config/alert_rules.yaml · docs/alerts.md

### Lưu Xuân Thế — Role D: Load Test & Dashboard
- [TASKS_COMPLETED]: Correlation ID middleware (`app/middleware.py`); chạy load test sinh ≥80 request; dựng dashboard 6 panel (`dashboard.html` + `scripts/serve_dashboard.py`) với đơn vị + đường SLO; demo incident rag_slow (155→2656ms).
- [EVIDENCE_LINK]: docs/evidence/05-dashboard-6-panels.png · docs/evidence/06-dashboard-incident-rag-slow.png

### Lưu Xuân Thế — Role E: Demo & Report
- [TASKS_COMPLETED]: Tổng hợp evidence (`docs/evidence/EVIDENCE.md`), viết báo cáo này, infographic tổng quan (`infographic-day13.html`); chạy `validate_logs.py` đạt 100/100, `pytest` 2 passed.
- [EVIDENCE_LINK]: docs/evidence/EVIDENCE.md · infographic-day13.html

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
