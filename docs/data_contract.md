# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn                  | Phương thức ingest                           | Failure mode chính                                                 | Metric / alert                                            |
| ---------------------- | -------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------- |
| policy_refund_v4       | Export từ hệ thống policy nội bộ (CSV batch) | Duplicate content, conflict version (7 ngày vs 14 ngày), null text | % duplicate chunks, % conflict semantic, null rate        |
| sla_p1_2026            | Sync từ hệ thống ticketing (API → CSV)       | Sai hoặc outdated SLA gây hallucination                            | SLA inconsistency rate, freshness (effective_date vs now) |
| it_helpdesk_faq        | Export từ knowledge base                     | Sai format ngày (01/02/2026), thiếu chuẩn hóa schema               | % invalid date format, parsing error rate                 |
| hr_leave_policy        | Sync từ HR system                            | Conflict version (10 ngày vs 12 ngày phép)                         | Version conflict rate, temporal inconsistency             |
| legacy_catalog_xyz_zzz | Data legacy import                           | Outlier content (không liên quan domain chính)                     | Embedding distance outlier, low retrieval relevance score |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | Hash ổn định từ nội dung và doc_id |
| doc_id | string | Có | Phải thuộc allowlist trong contract |
| chunk_text | string | Có | Nội dung text đã được clean (strip, fix stale) |
| effective_date | date | Có | Định dạng ISO YYYY-MM-DD |
| exported_at | datetime | Có | ISO format thời điểm export từ nguồn |

---

## 3. Quy tắc quarantine vs drop

> Record bị flag đi đâu? Ai approve merge lại?

- **Quarantine:** Các record sai format ngày, sai `doc_id`, hoặc text quá ngắn sẽ được đẩy vào `artifacts/quarantine/`.
- **Merge Back:** Data Owner (Data Platform team) sẽ review các file này hàng tuần. Nếu do lỗi parser, sẽ fix code và rerun. Nếu do lỗi hệ nguồn, sẽ yêu cầu nguồn gửi lại bản fix.

---

## 4. Phiên bản & canonical

> Source of truth cho policy refund: file nào / version nào?

- **Canonical Source:** `data/docs/policy_refund_v4.txt` là nguồn chuẩn.
- **Rule:** Bất kỳ record nào từ hệ thống export (CSV) mà vẫn còn nội dung "14 ngày làm việc" sẽ bị coi là bẩn và được pipeline tự động chuyển sang "7 ngày làm việc" kèm theo tag `[cleaned: stale_refund_window]`.

