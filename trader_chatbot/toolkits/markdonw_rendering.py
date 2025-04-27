def render_md(prefix: str, data: dict, suffix: str) -> str:
    if not data:
        return f"{prefix}\n\n_No data to display._\n\n{suffix}"

    headers = "| Parameter | Value |"
    separator = "|-----------|-------|"
    rows = [f"| {key} | {value} |" for key, value in data.items()]
    table = "\n".join([headers, separator] + rows)

    return f"{prefix}\n\n{table}\n\n{suffix}"
