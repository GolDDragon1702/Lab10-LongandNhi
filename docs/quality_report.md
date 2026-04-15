# Quality report — Lab Day 10 (nhóm)

**run_id:** `2026-04-15T09-21Z` (Good Run) / `inject-bad` (Bad Run)  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (Tốt) | Sau (Inject Bad) | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 10 | 10 | Dữ liệu đầu vào giữ nguyên |
| cleaned_records | 6 | 6 | Số lượng records được clean như nhau |
| quarantine_records | 4 | 4 | Số lượng records bị cách ly như nhau |
| Expectation halt? | OK | FAIL (`refund_no_stale_14d_window`) | Run inject có chủ đích đã tạo ra lỗi |

---

## 2. Before / after retrieval (bắt buộc)

> Đã được lưu trong: 
> Phải (Good Data): `artifacts/eval/before_after_eval.csv` 
> Trái (Bad Data): `artifacts/eval/after_inject_bad.csv`

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước (Inject Bad - Không fix 14 -> 7, Không validate):**  
```csv
q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?,policy_refund_v4,Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng.,yes,yes,,3
```
*(hits_forbidden = `yes`, nghĩa là nó bị dính lỗi chứa từ khóa cũ '14 ngày làm việc')*

**Sau (Good Run - Đã fix 14 -> 7, Đã validate):**
```csv
q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?,policy_refund_v4,Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng.,yes,no,,3
```
*(hits_forbidden = `no`)*


**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, cột `top1_doc_expected`)

**Good Run (Sau):**  
```csv
q_leave_version,"Theo chính sách nghỉ phép hiện hành (2026), nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm?",hr_leave_policy,Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026.,yes,no,yes,3
```
*(top1_doc_expected = `yes`, hits_forbidden=`no`, chứng tỏ versioning thành công)*

---

## 3. Freshness & monitor

> Kết quả `freshness_check` (FAIL) cho mẫu dữ liệu tĩnh `latest_exported_at` là `2026-04-10T08:00:00`.
> Vì SLA của tôi thiết lập là `24.0` giờ, nên đã quá hạn khoảng 121 giờ. 

---

## 4. Corruption inject (Sprint 3)

> Mô tả cố ý làm hỏng dữ liệu kiểu gì (duplicate / stale / sai format) và cách phát hiện.
**Cách thức:** Tôi đã dùng flag `--no-refund-fix` để làm hỏng dữ liệu, kèm theo `--skip-validate` để bắt pipeline nhúng thông tin cũ (14 ngày làm việc) vào chroma collection, trong khi file config policy_refund_v4 đã chuyển sang 7 ngày làm việc.
**Phát hiện:** `run_expectations` bắt được 1 validation fail trên điều kiện `refund_no_stale_14d_window`. Ngoài ra file CSV eval cũng cho thấy `hits_forbidden=yes` với câu hỏi về refund, chứng tỏ Vector database đã chứa thông tin bẩn.

---

## 5. Hạn chế & việc chưa làm

- Cần cập nhật tự động lại manifest sau các khoảng thời gian nhất định để pipeline không báo FAIL trên freshness, hoặc xử lý ingestion liên tục.
