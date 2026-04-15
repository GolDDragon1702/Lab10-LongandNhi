# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Trương Công Nhị  
**Vai trò:** Team Lead & Monitoring Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `etl_pipeline.py`: Quản lý luồng chạy chính, điều phối và gắn kết các module.
- `monitoring/freshness_check.py`: Triển khai logic kiểm tra SLA freshness dựa trên manifest.
- `docs/*.md`: Hoàn thiện Runbook, Pipeline Architecture và Data Contract.
- `reports/group_report.md`: Tổng hợp kết quả và điều phối báo cáo nhóm.

**Kết nối với thành viên khác:**

Với tư cách là Team Lead, tôi làm việc chặt chẽ với Long (phụ trách Cleaning và Embed) để đảm bảo các rule clean được phản ánh đúng trong manifest và log. Tôi chịu trách nhiệm cuối cùng về việc đảm bảo tính quan sát (observability) của toàn bộ pipeline, từ lúc bắt đầu chạy đến khi dữ liệu được publish an toàn vào ChromaDB.

**Bằng chứng (commit / comment trong code):**

- `etl_pipeline.py`: "run_id=args.run_id or datetime.now(timezone.utc).strftime..."
- `monitoring/freshness_check.py`: "status, detail = check_manifest_freshness(p, sla_hours=sla)"

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi đã quyết định thiết lập SLA Freshness ở mức **24 giờ** và sử dụng `latest_exported_at` làm gốc đo. 

**Lý do:** Trong hệ thống RAG phục vụ Policy, dữ liệu không thay đổi từng giây nhưng tính "tươi" vẫn cực kỳ quan trọng. Việc tách biệt Freshness check thành một bước riêng sau khi tạo Manifest giúp chúng tôi có thể trigger alert độc lập mà không nhất thiết phải dừng pipeline embedding (trừ khi data quá cũ). Quyết định này giúp hệ thống có tính linh hoạt: chúng ta vẫn có thể serve data cũ trong lúc chờ data mới, nhưng đồng thời có cảnh báo đỏ (FAIL) trên dashboard để đội vận hành biết cần can thiệp.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Trong quá trình chạy thử, tôi phát hiện pipeline luôn báo `freshness_check=FAIL` dù code logic có vẻ đúng.

- **Triệu chứng:** Kết quả trả về `{"reason": "freshness_sla_exceeded"}` mặc dù pipeline vừa mới chạy xong.
- **Nguyên nhân:** Qua việc kiểm tra lineage thông qua manifest, tôi nhận ra `latest_exported_at` lấy từ file raw là ngày **2026-04-10**, trong khi thời điểm hiện tại là **2026-04-15**.
- **Xử lý:** Tôi đã ghi nhận đây là một "Incident giả" (do data tĩnh) và cập nhật vào Runbook hướng dẫn cách phân biệt giữa lỗi code parser và lỗi dữ liệu nguồn quá hạn. Tôi cũng đề xuất giải pháp cập nhật timestamp export trong môi trường production thực tế.

---

## 4. Bằng chứng trước / sau (80–120 từ)

**Run ID:** `2026-04-15T09-21Z`

**Kết quả kiểm tra Freshness:**
```bash
freshness_check=FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 121.355, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}
```

Dòng log này chứng minh monitor của tôi đã hoạt động chính xác theo contract đã cam kết: phát hiện dữ liệu đã cũ hơn 5 ngày mặc dù pipeline vẫn báo `PIPELINE_OK`.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tích hợp thông báo qua Slack/Webhook ngay trong module `freshness_check`. Hiện tại lỗi mới chỉ hiện ở log, việc đẩy nó ra một kênh alarm chủ động sẽ giúp đội on-call phản ứng nhanh hơn thay vì phải đợi đọc log định kỳ.
