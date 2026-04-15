# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

- Agent trả lời sai về chính sách hoàn tiền: Vẫn khẳng định là "14 ngày làm việc" thay vì "7 ngày".
- Agent trả lời sai về ngày phép: Trả lời "10 ngày" cho nhân viên dưới 3 năm thay vì "12 ngày".
- Retrieval Evaluation (`eval_retrieval.py`) báo `hits_forbidden=yes` cho câu hỏi refund.

---

## Detection

- **Freshness Alarm:** `python etl_pipeline.py freshness` trả về `FAIL`.
- **Expectation Halt:** Log pipeline có dòng `PIPELINE_HALT: expectation suite failed (halt).`
- **Quality Alert:** Cột `hits_forbidden` trong `before_after_eval.csv` có giá trị `yes`.

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` | Xem `latest_exported_at` có bị quá hạn so với SLA không. |
| 2 | Mở `artifacts/quarantine/*.csv` | Xem các record bị loại bỏ có chứa lý do `invalid_effective_date_format` hay `stale_hr_policy` không. |
| 3 | Chạy `python eval_retrieval.py` | Kiểm tra xem VectorDB hiện tại có đang truy xuất dữ liệu từ đúng version không (cột `top1_doc_id`). |

---

## Mitigation

1. **Fix Ingestion:** Nếu lỗi do data source cung cấp sai version, yêu cầu nguồn export lại.
2. **Rerun Pipeline:** Chạy `python etl_pipeline.py run` để fix dữ liệu (pipeline có rule tự động fix 14 -> 7 ngày).
3. **Emergency Override:** Nếu cần publish gấp, có thể dùng `--skip-validate` (không khuyến nghị trừ khi đã review kĩ).
4. **Rollback:** Nếu bản mới tệ hơn, xóa `chroma_db` và restore từ snapshot manifest cũ.

---

## Prevention

1. **Add Expectation:** Thêm rule chặn hoàn toàn các chunk chứa từ khóa phiên bản cũ.
2. **Alert Monitoring:** Tích hợp `freshness_check` vào Slack/PagerDuty kênh `#data-alerts-p1`.
3. **Data Contract Compliance:** Thắt chặt contract với đội HR/IT để đảm bảo format `effective_date` luôn là ISO.

