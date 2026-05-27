"""
VoiceForge — Document Generation Service
==========================================
Generates PDFs, DOCX files, and structured text documents
from templates + extracted field values.
"""

import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger


OUTPUT_DIR = Path("generated_docs")


class DocumentService:
    """Generate structured documents from templates and field data."""

    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async def generate_pdf(self, template: Dict, field_values: Dict,
                            ai_content: str, user_prefs: Dict = None) -> Optional[str]:
        """
        Generate a PDF document.
        Returns the filename (relative to OUTPUT_DIR), or None on failure.
        """
        prefs = user_prefs or {}
        font_size = self._prefs_font_size(prefs.get("font_size", "medium"))
        template_name = template.get("name", "document")
        title = template.get("title", "Document")

        filename = f"{template_name}_{uuid.uuid4().hex[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        filepath = OUTPUT_DIR / filename

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.enums import TA_CENTER, TA_LEFT

            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=letter,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch,
            )

            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                "VFTitle",
                parent=styles["Heading1"],
                fontSize=font_size + 6,
                textColor=colors.HexColor("#1a1a2e"),
                spaceAfter=12,
                alignment=TA_CENTER,
            )
            story.append(Paragraph(title, title_style))
            story.append(Paragraph(
                f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}",
                ParagraphStyle("date", fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
            ))
            story.append(Spacer(1, 0.3 * inch))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#6c63ff")))
            story.append(Spacer(1, 0.2 * inch))

            # Fields section
            field_style = ParagraphStyle(
                "VFField",
                parent=styles["Normal"],
                fontSize=font_size,
                spaceAfter=4,
            )
            label_style = ParagraphStyle(
                "VFLabel",
                parent=styles["Normal"],
                fontSize=font_size - 1,
                textColor=colors.HexColor("#555"),
                spaceBefore=8,
            )

            fields = template.get("fields", [])
            if fields and field_values:
                story.append(Paragraph("Form Details", styles["Heading2"]))
                story.append(Spacer(1, 0.1 * inch))

                table_data = []
                for field in fields:
                    value = field_values.get(field)
                    if value and value != "null":
                        label = field.replace("_", " ").title()
                        table_data.append([
                            Paragraph(f"<b>{label}</b>", field_style),
                            Paragraph(str(value), field_style),
                        ])

                if table_data:
                    table = Table(table_data, colWidths=[2.5 * inch, 4 * inch])
                    table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f8")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd")),
                        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 0.3 * inch))

            # AI-generated narrative content
            if ai_content:
                story.append(Paragraph("Document Content", styles["Heading2"]))
                story.append(Spacer(1, 0.1 * inch))
                for para in ai_content.split("\n\n"):
                    if para.strip():
                        story.append(Paragraph(para.strip(), field_style))
                        story.append(Spacer(1, 0.1 * inch))

            # Footer note
            story.append(Spacer(1, 0.3 * inch))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#ddd")))
            story.append(Paragraph(
                "Generated by VoiceForge Accessibility Assistant",
                ParagraphStyle("footer", fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
            ))

            doc.build(story)
            logger.info(f"PDF generated: {filename}")
            return filename

        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            # Fallback: plain text file
            return await self._generate_text_fallback(filename.replace(".pdf", ".txt"),
                                                       title, field_values, ai_content)

    async def _generate_text_fallback(self, filename: str, title: str,
                                       field_values: Dict, content: str) -> str:
        """Plain text fallback when PDF generation fails."""
        filepath = OUTPUT_DIR / filename
        lines = [
            f"{'=' * 60}",
            f"  {title.upper()}",
            f"  Generated: {datetime.utcnow().strftime('%B %d, %Y')}",
            f"{'=' * 60}\n",
        ]
        for key, value in field_values.items():
            if value and value != "null":
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        if content:
            lines.append(f"\n{'-' * 40}\n{content}")
        lines.append(f"\n{'=' * 60}")
        lines.append("Generated by VoiceForge Accessibility Assistant")

        with open(filepath, "w") as f:
            f.write("\n".join(lines))

        return filename

    def _prefs_font_size(self, pref: str) -> int:
        return {"small": 9, "medium": 11, "large": 13, "x-large": 16}.get(pref, 11)
