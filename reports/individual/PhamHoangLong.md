# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Phạm Hoàng Long  
**Vai trò:** Ingestion / Cleaning / Quality / Embed Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `transform/cleaning_rules.py`: Triển khai 3 quy tắc clean mới (contact info, version history, min length).
- `quality/expectations.py`: Xây dựng các bộ kiểm tra chất lượng (SLA P1 check, Unique ID integrity).
- `etl_pipeline.py`: Phụ trách logic Embedding an toàn (`cmd_embed_internal`).

**Kết nối với thành viên khác:**

Tôi là người cung cấp "Dữ liệu sạch" cho toàn bộ hệ thống. Tôi làm việc với Nhị (Team Lead) để thống nhất về các mức độ nghiêm trọng (halt vs warn) cho từng quy tắc chất lượng. Nếu dữ liệu của tôi không vượt qua được gate, pipeline của Nhị sẽ dừng lại, đảm bảo không có rác nào lọt vào Vector store.

**Bằng chứng (commit / comment trong code):**

- `cleaning_rules.py`: "if _CONTACT_PATTERNS.search(text): ... reason: contains_contact_info"
- `expectations.py`: "E8 [NEW]: Data Integrity - Đảm bảo không có chunk_id nào bị trùng lặp"

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Quyết định quan trọng nhất của tôi là áp dụng chiến lược **Snapshot Pruning** kết hợp với **Upsert Idempotency** trong module embedding. 

**Lý do:** Khi làm việc với Vector DB, nếu chỉ đơn thuần thêm mới, database sẽ phình to với các bản copy cũ. Bằng cách lấy danh sách ID hiện có và so sánh với danh sách vừa được clean, tôi có thể thực hiện `col.delete(ids=drop)` để loại bỏ các chunk "ma". Điều này cực kỳ quan trọng đối với các chính sách như Refund Window (vừa đổi từ 14 sang 7 ngày). Nếu không prune, Agent có thể lấy nhầm chunk cũ có score similarity cao, dẫn đến trả lời sai nghiệp vụ.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Trong Sprint 3, khi thực hiện kịch bản "Inject Corruption" với flag `--no-refund-fix`, tôi đã phát hiện ra lỗi logic cực kỳ nguy hiểm.

- **Triệu chứng:** Pipeline chạy đến bước Quality thì báo FAIL, nhưng nếu ta dùng flag `--skip-validate` (để demo), dữ liệu bẩn sẽ chui vào database.
- **Nguyên nhân:** Do tôi chưa thắt chặt rule `must_not_contain` trong file evaluation.
- **Xử lý:** Tôi đã cập nhật lại `expectations.py` để bổ sung rule E7 và E8, đảm bảo các lỗi về SLA và tính toàn vẹn ID được phát hiện sớm nhất. Tôi cũng phối hợp với Nhị để đưa bước này thành `halt` (dừng khẩn cấp) thay vì chỉ cảnh báo đơn thuần.

---

## 4. Bằng chứng trước / sau (80–120 từ)

**Run ID:** `2026-04-15T09-21Z` (Good) vs `inject-bad` (Bad)

**Trước (Good Data):**
```csv
q_refund_window,khách hàng có... ,policy_refund_v4, ..., yes, no, , 3
```

**Sau (Inject Bad):**
```csv
q_refund_window,khách hàng có... ,policy_refund_v4, ..., yes, yes, , 3
```

Chỉ số `hits_forbidden` chuyển từ `no` sang `yes` là bằng chứng cho thấy bộ cleaning của tôi đã detect được token "14 ngày" xâm nhập vào context khi không được fix đúng cách.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ viết thêm module **Automatic Re-ingestion**. Nếu một record bị vào quarantine do lỗi format, module này sẽ tự động thử sửa các lỗi phổ biến (như encoding) và đẩy lại vào pipeline thay vì đợi con người xử lý thủ công.