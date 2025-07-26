def log_data(chunk: dict, sections: list[str]):
    for section in sections:
        summary = chunk.get(section, {}).get("summary")
        if summary:
            print(summary)
            print("\n")
