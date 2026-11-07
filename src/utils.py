"""Small formatting helpers shared by the analysis and dashboard modules."""


def format_hour_ranges(hours):
    """Format hours as ranges, e.g. [18, 19, 20] -> '18:00-21:00'."""
    ranges, start, previous = [], None, None
    for hour in sorted(hours):
        if start is None:
            start = previous = hour
        elif hour == previous + 1:
            previous = hour
        else:
            ranges.append((start, previous))
            start = previous = hour
    if start is not None:
        ranges.append((start, previous))
    return ", ".join(f"{first}:00-{last + 1}:00" for first, last in ranges)


def format_percent_change(value_a, value_b):
    """Formatted % change from `value_a` to `value_b` ('n/a' if `value_a` is zero)."""
    if value_a == 0:
        return "n/a"
    return f"{(value_b - value_a) / value_a * 100:+.1f}%"