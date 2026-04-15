# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Nhị và Long
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Nguyễn Trương Công Nhị | Team Lead & Monitoring | congnhi2004@gmail.com |
| Phạm Hoàng Long | Ingestion / Cleaning / Quality / Embed | long@example.com |

**Ngày nộp:** 2026-04-15
**Repo:** VinUni-AI20k/Lecture-Day-08-09-10
**Độ dài:** ~800 từ

---

## 1. Pipeline tổng quan (150–200 từ)

Hệ thống pipeline được thiết kế để tự động hóa luồng dữ liệu từ Ingestion đến Vector Store, đảm bảo tính quan sát (observability) và chất lượng dữ liệu cho Agent. Nguồn dữ liệu thô (raw) là file CSV (`policy_export_dirty.csv`) mô phỏng các lỗi thực tế trong hệ thống doanh nghiệp như duplicate, stale versions và format không chuẩn.

Chuỗi lệnh chạy end-to-end:
```bash
/home/shine/Downloads/app/anaconda/anaconda3/envs/vin/bin/python etl_pipeline.py run
```
`run_id` được sinh tự động theo timestamp UTC (ví dụ: `2026-04-15T09-21Z`) và được lưu trong `artifacts/logs/` cùng `artifacts/manifests/`.

---

## 2. Cleaning & expectation (150–200 từ)

Nhóm đã kế thừa các rule baseline và bổ sung thêm 3 rule cleaning mới cùng 2 expectation mới để thắt chặt chất lượng dữ liệu.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| `chunk_too_short` (Rule) | N/A | quarantine_records += 1 | `quarantine_inject-bad.csv` |
| `contains_contact_info` (Rule) | N/A | quarantine_records += 1 | Log check matched_pattern |
| `sla_p1_no_stale_6h_resolution` (Expectation) | Pass | Halt (nếu inject data bẩn) | `expectations.py` line 115 |
| `unique_chunk_ids_integrity` (Expectation) | Pass | Pass | `expectations.py` line 130 |

**Rule chính (baseline + mở rộng):**
- **Baseline:** Parse ngày ISO, Quarantine HR version cũ (<2026), Deduplication, Fix stale refund window (14 -> 7 days).
- **Mở rộng:** Loại bỏ các chunk chứa thông tin liên hệ (Email/Ext/URL) để bảo mật, loại bỏ các chunk version history không có giá trị kiến thức, và kiểm soát độ dài tối thiểu của chunk (>50 chars).

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**
Khi chạy với flag `--no-refund-fix`, expectation `refund_no_stale_14d_window` đã báo FAIL (halt). Cách xử lý là quay lại kiểm tra module `cleaning_rules.py` để đảm bảo hàm `apply_refund_window_fix` được gọi chính xác.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

**Kịch bản inject:**
Chúng tôi đã cố ý chạy pipeline với flag `--no-refund-fix` và `--skip-validate` (Run ID: `inject-bad`). Điều này cho phép dữ liệu stale ("14 ngày") chui vào Vector store bất chấp cảnh báo từ Quality suite.

**Kết quả định lượng (từ CSV / bảng):**
- **Good Run (`2026-04-15T09-21Z`):** Câu hỏi `q_refund_window` trả về `hits_forbidden=no`. Retrieval thành công.
- **Bad Run (`inject-bad`):** Câu hỏi `q_refund_window` trả về `hits_forbidden=yes`.
Điều này chứng minh rằng Quality suite đã phát hiện đúng lỗi logic mà nếu không có nó, Agent sẽ tư vấn sai cho khách hàng (gây thiệt hại về tài chính do kéo dài thời gian hoàn tiền).

---

## 4. Freshness & monitoring (100–150 từ)

SLA được chọn là **24 giờ**.
- **PASS:** Dữ liệu được export trong vòng 24h qua.
- **FAIL:** Dữ liệu cũ hơn 24h (như bản mẫu export ngày 10/04/2026 hiện tại đang báo FAIL).
Ý nghĩa: Đảm bảo Agent luôn đọc được các chính sách mới nhất, đặc biệt quan trọng với các thay đổi về HR và SLA hỗ trợ.

---

## 5. Liên hệ Day 09 (50–100 từ)

Dữ liệu sau khi embed bởi pipeline này được lưu vào collection `day10_kb`. Các Agent từ Day 09 có thể tham chiếu trực tiếp đến collection này thay vì parse file text thủ công. Việc tách collection giúp chúng tôi blue-green deployment: kiểm tra data mới trong collection nháp trước khi đổi collection ID cho Agent production.

---

## 6. Rủi ro còn lại & việc chưa làm

- Chưa tự động hóa việc crawl lại data khi SLA freshness fail.
- Cần thêm module so sánh ngữ nghĩa (semantic similarity) để phát hiện các chính sách mâu thuẫn ẩn (ví dụ: một chỗ ghi 7 ngày, một chỗ ghi 1 tuần nhưng không bắt được bằng keyword).
- Phân quyền access cho vector store chưa được triển khai.

