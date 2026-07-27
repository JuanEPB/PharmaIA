from __future__ import annotations

from typing import Iterable, Sequence


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


def _pdf_text(
    x: int,
    y: int,
    text: object,
    *,
    size: int = 10,
    font: str = "F1",
) -> str:
    return (
        "BT\n"
        f"/{font} {size} Tf\n"
        f"{x} {y} Td\n"
        f"({_escape_pdf_text(text)}) Tj\n"
        "ET"
    )


def _pdf_line(x1: int, y1: int, x2: int, y2: int) -> str:
    return f"{x1} {y1} m {x2} {y2} l S"


def _pdf_rect(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    fill: str | None = None,
    stroke: str | None = None,
) -> list[str]:
    commands: list[str] = []

    if fill:
        commands.append(fill)

    if stroke:
        commands.append(stroke)

    commands.append(f"{x} {y} {width} {height} re")
    commands.append("B" if fill and stroke else "f" if fill else "S")

    return commands


def _truncate(value: object, max_length: int) -> str:
    text = str(value or "")

    if len(text) <= max_length:
        return text

    return text[: max(0, max_length - 3)] + "..."


def build_ticket_pdf(
    *,
    title: str,
    subtitle: str,
    folio: object,
    date_text: object,
    business_name: object,
    customer_name: object,
    items: Sequence[dict[str, object]],
    total: object,
    footer: str = "Gracias por su compra.",
) -> bytes:
    content: list[str] = [
        "0.96 0.98 1 rg",
        "0 0 612 792 re f",
        *_pdf_rect(42, 56, 528, 680, fill="1 1 1 rg", stroke="0.84 0.88 0.94 RG"),
        *_pdf_rect(42, 676, 528, 60, fill="0.15 0.39 0.92 rg"),
        _pdf_text(66, 714, title, size=20, font="F2"),
        _pdf_text(66, 694, subtitle, size=10, font="F1"),
        _pdf_text(445, 714, "TICKET", size=16, font="F2"),
        _pdf_text(445, 696, f"Folio {folio}", size=9, font="F1"),
        *_pdf_rect(62, 596, 488, 56, fill="0.98 0.99 1 rg", stroke="0.88 0.91 0.96 RG"),
        _pdf_text(78, 632, "Farmacia", size=8, font="F2"),
        _pdf_text(78, 616, _truncate(business_name, 30), size=11, font="F1"),
        _pdf_text(272, 632, "Cliente / usuario", size=8, font="F2"),
        _pdf_text(272, 616, _truncate(customer_name, 26), size=11, font="F1"),
        _pdf_text(444, 632, "Fecha", size=8, font="F2"),
        _pdf_text(444, 616, _truncate(date_text, 16), size=10, font="F1"),
        *_pdf_rect(62, 546, 488, 26, fill="0.94 0.97 1 rg"),
        _pdf_text(78, 555, "Producto", size=9, font="F2"),
        _pdf_text(344, 555, "Cant.", size=9, font="F2"),
        _pdf_text(408, 555, "P. unitario", size=9, font="F2"),
        _pdf_text(502, 555, "Importe", size=9, font="F2"),
    ]

    y = 522
    if not items:
        content.append(_pdf_text(78, y, "Sin productos registrados.", size=10))
        y -= 22

    for item in items[:14]:
        content.append(_pdf_text(78, y, _truncate(item.get("name"), 34), size=9))
        content.append(_pdf_text(354, y, item.get("quantity"), size=9))
        content.append(_pdf_text(408, y, item.get("unit_price"), size=9))
        content.append(_pdf_text(502, y, item.get("subtotal"), size=9, font="F2"))
        y -= 22
        content.append("0.90 0.93 0.97 RG")
        content.append(_pdf_line(62, y + 10, 550, y + 10))

    if len(items) > 14:
        content.append(
            _pdf_text(
                78,
                y,
                f"+ {len(items) - 14} productos adicionales",
                size=9,
            )
        )

    content.extend(
        [
            *_pdf_rect(360, 114, 190, 54, fill="0.94 0.97 1 rg", stroke="0.78 0.86 0.98 RG"),
            _pdf_text(382, 146, "TOTAL", size=10, font="F2"),
            _pdf_text(445, 128, total, size=18, font="F2"),
            _pdf_text(62, 132, footer, size=10, font="F2"),
            _pdf_text(62, 114, "Control inteligente para farmacia", size=9),
        ]
    )

    stream = "\n".join(content).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 792] "
            b"/Resources << /Font << "
            b"/F1 4 0 R /F2 5 0 R "
            b">> >> "
            b"/Contents 6 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
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
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(payload)
        pdf.extend(b"\nendobj\n")

    xref_position = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

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
