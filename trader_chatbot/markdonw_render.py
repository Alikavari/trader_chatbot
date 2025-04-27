def json_to_markdown_table(json_data):
    # Check if the JSON is a list of dictionaries
    if not isinstance(json_data, list) or not all(
        isinstance(item, dict) for item in json_data
    ):
        raise ValueError("Input should be a list of dictionaries")

    # Get the headers from the keys of the first dictionary in the list
    headers = json_data[0].keys()

    # Create the table header row
    markdown_table = (
        "| Parameter   | "
        + " | ".join([f"Value " for i in range(len(json_data))])
        + " |\n"
    )

    # Create the separator row for Markdown
    markdown_table += (
        "| ----------- | " + " | ".join(["---" for _ in range(len(json_data))]) + " |\n"
    )

    # Loop through each key and create the table rows
    for key in headers:
        markdown_table += (
            f"| {key}        | "
            + " | ".join(str(row[key]) for row in json_data)
            + " |\n"
        )

    return markdown_table
