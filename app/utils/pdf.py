from __future__ import annotations

from typing import Iterable


def _escape_pdf_text(value: object) -> str:
    text = str(value or "")
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def build_simple_pdf(
    *,
    title: str,
    lines: Iterable[object],
) -> bytes:
    content_lines = [
        "BT",
        "/F1 18 Tf",
        "50 790 Td",
        f"({_escape_pdf_text(title)}) Tj",
        "/F1 10 Tf",
        "0 -28 Td",
    ]

    for line in lines:
        content_lines.append(
            f"({_escape_pdf_text(line)}) Tj"
        )
        content_lines.append("0 -15 Td")

    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        ),
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]

    for index, payload in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(
            f"{index} 0 obj\n".encode("ascii")
        )
        pdf.extend(payload)
        pdf.extend(b"\nendobj\n")

    xref_position = len(pdf)
    pdf.extend(
        f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    )
    pdf.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        pdf.extend(
            f"{offset:010d} 00000 n \n".encode("ascii")
        )

    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_position}\n"
            "%%EOF\n"
        ).encode("ascii")
    )

    return bytes(pdf)
