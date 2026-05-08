from __future__ import annotations


def format_mb(value: int | None) -> str:
    if value is None:
        return "-"
    if value >= 1024 * 1024 and value % (1024 * 1024) == 0:
        return f"{value // (1024 * 1024)}T"
    if value >= 1024 and value % 1024 == 0:
        return f"{value // 1024}G"
    if value >= 1024:
        return f"{value / 1024:.1f}G"
    return f"{value}M"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [
        max(len(row[i]) for row in [headers, *rows]) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[i]) for i, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[i]) for i, value in enumerate(row)))
