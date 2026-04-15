"""
Expectation suite đơn giản (không bắt buộc Great Expectations).

Sinh viên có thể thay bằng GE / pydantic / custom — miễn là có halt có kiểm soát.

NEW EXPECTATIONS (Day 10 — added by student):
  E7  — no_duplicate_chunk_id        : halt  — chunk_id trùng = pipeline ID gen lỗi
  E8  — quarantine_rate_below_50pct  : warn  — tỷ lệ quarantine > 50% báo source tệ
  E9  — effective_date_not_future    : halt  — ngày hiệu lực không được vượt hôm nay
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Tuple


@dataclass
class ExpectationResult:
    name: str
    passed: bool
    severity: str  # "warn" | "halt"
    detail: str


def run_expectations(
    cleaned_rows: List[Dict[str, Any]],
    quarantine_rows: List[Dict[str, Any]] | None = None,
) -> Tuple[List[ExpectationResult], bool]:
    """
    Trả về (results, should_halt).

    should_halt = True nếu có bất kỳ expectation severity halt nào fail.

    Args:
        cleaned_rows:    Output từ clean_rows() — danh sách row đã pass cleaning.
        quarantine_rows: Output từ clean_rows() — danh sách row bị quarantine.
                         Truyền vào để E8 tính quarantine rate; nếu None thì bỏ qua E8.
    """
    results: List[ExpectationResult] = []

    # ------------------------------------------------------------------
    # E1: có ít nhất 1 dòng sau clean
    # ------------------------------------------------------------------
    ok = len(cleaned_rows) >= 1
    results.append(
        ExpectationResult(
            "min_one_row",
            ok,
            "halt",
            f"cleaned_rows={len(cleaned_rows)}",
        )
    )

    # ------------------------------------------------------------------
    # E2: không doc_id rỗng
    # ------------------------------------------------------------------
    bad_doc = [r for r in cleaned_rows if not (r.get("doc_id") or "").strip()]
    ok2 = len(bad_doc) == 0
    results.append(
        ExpectationResult(
            "no_empty_doc_id",
            ok2,
            "halt",
            f"empty_doc_id_count={len(bad_doc)}",
        )
    )

    # ------------------------------------------------------------------
    # E3: policy refund không được chứa cửa sổ sai 14 ngày (sau khi đã fix)
    # ------------------------------------------------------------------
    bad_refund = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "policy_refund_v4"
        and "14 ngày làm việc" in (r.get("chunk_text") or "")
    ]
    ok3 = len(bad_refund) == 0
    results.append(
        ExpectationResult(
            "refund_no_stale_14d_window",
            ok3,
            "halt",
            f"violations={len(bad_refund)}",
        )
    )

    # ------------------------------------------------------------------
    # E4: chunk_text đủ dài
    # ------------------------------------------------------------------
    short = [r for r in cleaned_rows if len((r.get("chunk_text") or "")) < 8]
    ok4 = len(short) == 0
    results.append(
        ExpectationResult(
            "chunk_min_length_8",
            ok4,
            "warn",
            f"short_chunks={len(short)}",
        )
    )

    # ------------------------------------------------------------------
    # E5: effective_date đúng định dạng ISO sau clean (phát hiện parser lỏng)
    # ------------------------------------------------------------------
    iso_bad = [
        r
        for r in cleaned_rows
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", (r.get("effective_date") or "").strip())
    ]
    ok5 = len(iso_bad) == 0
    results.append(
        ExpectationResult(
            "effective_date_iso_yyyy_mm_dd",
            ok5,
            "halt",
            f"non_iso_rows={len(iso_bad)}",
        )
    )

    # ------------------------------------------------------------------
    # E6: không còn marker phép năm cũ 10 ngày trên doc HR (conflict version sau clean)
    # ------------------------------------------------------------------
    bad_hr_annual = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "hr_leave_policy"
        and "10 ngày phép năm" in (r.get("chunk_text") or "")
    ]
    ok6 = len(bad_hr_annual) == 0
    results.append(
        ExpectationResult(
            "hr_leave_no_stale_10d_annual",
            ok6,
            "halt",
            f"violations={len(bad_hr_annual)}",
        )
    )

    # ------------------------------------------------------------------
    # E7 [NEW] — no_duplicate_chunk_id                           | halt
    # ------------------------------------------------------------------
    # Tại sao halt:
    #   chunk_id được dùng làm primary key trong vector store.
    #   Nếu có trùng lặp, upsert sẽ ghi đè silently — một chunk mất dữ liệu
    #   mà không có error nào, gây retrieval thiếu hoặc sai nội dung.
    #   Nguyên nhân thường gặp: _stable_chunk_id() nhận cùng (doc_id, text, seq)
    #   do pipeline chạy lại mà không reset seq counter.
    # ------------------------------------------------------------------
    chunk_ids = [r.get("chunk_id") or "" for r in cleaned_rows]
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for cid in chunk_ids:
        if cid in seen_ids:
            duplicate_ids.add(cid)
        seen_ids.add(cid)
    ok7 = len(duplicate_ids) == 0
    results.append(
        ExpectationResult(
            "no_duplicate_chunk_id",
            ok7,
            "halt",
            f"duplicate_count={len(duplicate_ids)}"
            + (f", examples={list(duplicate_ids)[:3]}" if duplicate_ids else ""),
        )
    )

    # ------------------------------------------------------------------
    # E8 [NEW] — quarantine_rate_below_50pct                     | warn
    # ------------------------------------------------------------------
    # Tại sao warn (không halt):
    #   Quarantine rate cao là dấu hiệu source data có vấn đề nghiêm trọng,
    #   nhưng pipeline vẫn có thể chạy với phần cleaned còn lại.
    #   Halt ở đây sẽ block toàn bộ ingestion kể cả những chunk tốt.
    #   Warn để operator biết cần kiểm tra nguồn export — không dừng pipeline.
    #   Ngưỡng 50%: nếu hơn nửa số row bị loại, source cần được audit ngay.
    # ------------------------------------------------------------------
    if quarantine_rows is not None:
        total = len(cleaned_rows) + len(quarantine_rows)
        if total == 0:
            q_rate = 0.0
            ok8 = True
        else:
            q_rate = len(quarantine_rows) / total
            ok8 = q_rate <= 0.50
        results.append(
            ExpectationResult(
                "quarantine_rate_below_50pct",
                ok8,
                "warn",
                f"quarantine_rate={q_rate:.1%}"
                f" ({len(quarantine_rows)}/{total} rows)",
            )
        )

    # ------------------------------------------------------------------
    # E9 [NEW] — effective_date_not_future                        | halt
    # ------------------------------------------------------------------
    # Tại sao halt:
    #   Chunk với effective_date trong tương lai là chính sách chưa có hiệu lực.
    #   Nếu RAG retrieve và trả lời ngay hôm nay, chatbot cung cấp thông tin
    #   chưa được approve — vi phạm data contract và gây nhầm lẫn cho người dùng.
    #   Ví dụ thực tế: export nhầm draft policy effective 2027-01-01.
    #   Khác với Rule 9 ở cleaning_rules.py (version history) — rule này
    #   check giá trị effective_date của chính chunk sau khi đã chuẩn hoá.
    # ------------------------------------------------------------------
    today_iso = date.today().isoformat()  # YYYY-MM-DD
    future_rows = [
        r
        for r in cleaned_rows
        if (r.get("effective_date") or "") > today_iso
    ]
    ok9 = len(future_rows) == 0
    results.append(
        ExpectationResult(
            "effective_date_not_future",
            ok9,
            "halt",
            f"future_dated_rows={len(future_rows)}, today={today_iso}"
            + (
                f", examples={[r.get('chunk_id') for r in future_rows[:3]]}"
                if future_rows
                else ""
            ),
        )
    )

    # ------------------------------------------------------------------
    # Tổng hợp
    # ------------------------------------------------------------------
    halt = any(not r.passed and r.severity == "halt" for r in results)
    return results, halt