from __future__ import annotations

import csv
import io
from typing import Any

from PIL import Image, ImageDraw, ImageFont


class TaxExportService:
    @staticmethod
    def _t(is_en: bool, ar: str, en: str) -> str:
        return en if is_en else ar

    @classmethod
    def _status_label(cls, status: str, is_en: bool) -> str:
        labels = {
            "draft": ("مسودة", "Draft"),
            "sent": ("مرسلة", "Sent"),
            "paid": ("مدفوعة", "Paid"),
            "cancelled": ("ملغاة", "Cancelled"),
        }
        ar, en = labels.get(str(status or "draft").strip().lower(), labels["draft"])
        return en if is_en else ar

    @classmethod
    def _basis_label(cls, basis: str, is_en: bool) -> str:
        key = str(basis or "cash").strip().lower()
        if key == "accrual":
            return cls._t(is_en, "استحقاق", "Accrual")
        return cls._t(is_en, "نقدي", "Cash")

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def report_to_csv_bytes(cls, report: dict, currency_view: str, is_en: bool = False) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(
            [
                cls._t(is_en, "القسم", "Section"),
                cls._t(is_en, "الحقل", "Field"),
                cls._t(is_en, "القيمة", "Value"),
            ]
        )

        summary_rows = [
            (cls._t(is_en, "الفترة", "Period"), str(report.get("period_key", ""))),
            (cls._t(is_en, "أساس التقرير", "Reporting Basis"), cls._basis_label(report.get("basis", "cash"), is_en)),
            (cls._t(is_en, "العملة", "Currency"), currency_view),
            (cls._t(is_en, "عدد الفواتير", "Invoice Count"), int(report.get("counts", {}).get("total_invoices", 0))),
            (cls._t(is_en, "الإجمالي قبل الضريبة", "Subtotal"), f"{cls._safe_float(report.get('totals', {}).get('subtotal', 0.0)):.3f}"),
            (cls._t(is_en, "الضريبة", "Tax"), f"{cls._safe_float(report.get('totals', {}).get('tax', 0.0)):.3f}"),
            (cls._t(is_en, "الإجمالي النهائي", "Total"), f"{cls._safe_float(report.get('totals', {}).get('total', 0.0)):.3f}"),
            (cls._t(is_en, "المفتوح غير المسدد", "Outstanding Open"), f"{cls._safe_float(report.get('totals', {}).get('outstanding_open_total', 0.0)):.3f}"),
        ]
        for field_name, value in summary_rows:
            writer.writerow([cls._t(is_en, "الملخص", "Summary"), field_name, value])

        writer.writerow([])
        writer.writerow(
            [
                cls._t(is_en, "الحالات", "Statuses"),
                cls._t(is_en, "الحالة", "Status"),
                cls._t(is_en, "الإجمالي", "Total"),
            ]
        )
        for key, value in (report.get("status_totals") or {}).items():
            writer.writerow(["", cls._status_label(key, is_en), f"{cls._safe_float(value):.3f}"])

        writer.writerow([])
        writer.writerow(
            [
                cls._t(is_en, "تفصيل النسب", "Tax Rates"),
                cls._t(is_en, "النسبة", "Rate"),
                cls._t(is_en, "عدد الفواتير", "Count"),
                cls._t(is_en, "قبل الضريبة", "Subtotal"),
                cls._t(is_en, "الضريبة", "Tax"),
                cls._t(is_en, "الإجمالي", "Total"),
            ]
        )
        for row in report.get("rates", []):
            writer.writerow(
                [
                    "",
                    f"{cls._safe_float(row.get('tax_rate', 0.0)):.3f}%",
                    int(row.get("count", 0) or 0),
                    f"{cls._safe_float(row.get('subtotal', 0.0)):.3f}",
                    f"{cls._safe_float(row.get('tax', 0.0)):.3f}",
                    f"{cls._safe_float(row.get('total', 0.0)):.3f}",
                ]
            )

        writer.writerow([])
        writer.writerow(
            [
                cls._t(is_en, "الفواتير", "Invoices"),
                cls._t(is_en, "الرقم", "Number"),
                cls._t(is_en, "العميل", "Customer"),
                cls._t(is_en, "المشروع", "Project"),
                cls._t(is_en, "الحالة", "Status"),
                cls._t(is_en, "الإصدار", "Issue Date"),
                cls._t(is_en, "الاستحقاق", "Due Date"),
                cls._t(is_en, "نسبة الضريبة", "Tax Rate"),
                cls._t(is_en, "الضريبة", "Tax"),
                cls._t(is_en, "الإجمالي", "Total"),
            ]
        )
        for inv in report.get("invoices", []):
            writer.writerow(
                [
                    "",
                    str(inv.get("invoice_number", "") or ""),
                    str(inv.get("customer_name", "") or ""),
                    str(inv.get("linked_project", "") or ""),
                    cls._status_label(inv.get("status", "draft"), is_en),
                    str(inv.get("issue_date", "") or ""),
                    str(inv.get("due_date", "") or ""),
                    f"{cls._safe_float(inv.get('tax_rate', 0.0)):.3f}%",
                    f"{cls._safe_float(inv.get('tax_amount', 0.0)):.3f}",
                    f"{cls._safe_float(inv.get('total_amount', 0.0)):.3f}",
                ]
            )

        return buffer.getvalue().encode("utf-8-sig")

    @staticmethod
    def _load_font(size: int):
        font_candidates = [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Tahoma.ttf",
            "DejaVuSans.ttf",
        ]
        for path in font_candidates:
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
        return ImageFont.load_default()

    @staticmethod
    def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
        words = str(text or "").split()
        if not words:
            return [""]

        lines = []
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            bbox = draw.textbbox((0, 0), trial, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    @classmethod
    def _report_lines(cls, report: dict, currency_view: str, is_en: bool) -> list[str]:
        counts = report.get("counts", {})
        totals = report.get("totals", {})

        lines = [
            cls._t(is_en, "تقرير الضرائب والفواتير", "Invoices and Tax Report"),
            f"{cls._t(is_en, 'الفترة', 'Period')}: {report.get('period_key', '')}",
            f"{cls._t(is_en, 'أساس التقرير', 'Reporting Basis')}: {cls._basis_label(report.get('basis', 'cash'), is_en)}",
            f"{cls._t(is_en, 'العملة', 'Currency')}: {currency_view}",
            "",
            cls._t(is_en, "الملخص", "Summary"),
            f"{cls._t(is_en, 'عدد الفواتير', 'Invoice Count')}: {int(counts.get('total_invoices', 0) or 0)}",
            f"{cls._t(is_en, 'الإجمالي قبل الضريبة', 'Subtotal')}: {cls._safe_float(totals.get('subtotal', 0.0)):.3f} {currency_view}",
            f"{cls._t(is_en, 'الضريبة', 'Tax')}: {cls._safe_float(totals.get('tax', 0.0)):.3f} {currency_view}",
            f"{cls._t(is_en, 'الإجمالي النهائي', 'Total')}: {cls._safe_float(totals.get('total', 0.0)):.3f} {currency_view}",
            f"{cls._t(is_en, 'المفتوح غير المسدد', 'Outstanding Open')}: {cls._safe_float(totals.get('outstanding_open_total', 0.0)):.3f} {currency_view}",
            "",
            cls._t(is_en, "الإجماليات حسب الحالة", "Totals By Status"),
        ]

        for key, value in (report.get("status_totals") or {}).items():
            lines.append(f"- {cls._status_label(key, is_en)}: {cls._safe_float(value):.3f} {currency_view}")

        lines.extend(["", cls._t(is_en, "تفصيل نسب الضريبة", "Tax Rate Breakdown")])
        for row in report.get("rates", []):
            lines.append(
                f"- {cls._safe_float(row.get('tax_rate', 0.0)):.3f}% | "
                f"{cls._t(is_en, 'عدد', 'Count')}: {int(row.get('count', 0) or 0)} | "
                f"{cls._t(is_en, 'الضريبة', 'Tax')}: {cls._safe_float(row.get('tax', 0.0)):.3f} {currency_view}"
            )

        lines.extend(["", cls._t(is_en, "قائمة الفواتير", "Invoice List")])
        invoices = report.get("invoices", [])
        if not invoices:
            lines.append(cls._t(is_en, "لا توجد فواتير في هذه الفترة.", "No invoices for this period."))
        else:
            for inv in invoices:
                lines.append(
                    f"- {inv.get('invoice_number', '')} | "
                    f"{str(inv.get('customer_name', '') or '-') } | "
                    f"{cls._status_label(inv.get('status', 'draft'), is_en)} | "
                    f"{cls._safe_float(inv.get('total_amount', 0.0)):.3f} {currency_view}"
                )
        return lines

    @classmethod
    def report_to_pdf_bytes(cls, report: dict, currency_view: str, is_en: bool = False) -> bytes:
        page_width, page_height = 1240, 1754
        margin = 80
        title_font = cls._load_font(34)
        body_font = cls._load_font(20)
        line_gap = 10

        pages: list[Image.Image] = []
        image = Image.new("RGB", (page_width, page_height), "white")
        draw = ImageDraw.Draw(image)
        y = margin

        def new_page():
            nonlocal image, draw, y
            pages.append(image)
            image = Image.new("RGB", (page_width, page_height), "white")
            draw = ImageDraw.Draw(image)
            y = margin

        lines = cls._report_lines(report, currency_view, is_en=is_en)
        max_width = page_width - (margin * 2)

        for idx, raw_line in enumerate(lines):
            font = title_font if idx == 0 else body_font
            wrapped_lines = cls._wrap_text(draw, raw_line, font, max_width) if raw_line else [""]
            for line in wrapped_lines:
                bbox = draw.textbbox((0, 0), line or " ", font=font)
                line_height = (bbox[3] - bbox[1]) + line_gap
                if y + line_height > (page_height - margin):
                    new_page()
                draw.text((margin, y), line, fill="black", font=font)
                y += line_height

        pages.append(image)
        output = io.BytesIO()
        first, rest = pages[0], pages[1:]
        first.save(output, format="PDF", resolution=150.0, save_all=True, append_images=rest)
        return output.getvalue()
