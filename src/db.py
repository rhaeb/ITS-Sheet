import os

import mysql.connector


INVALID_SHEET_CHARS = set(r'[]:*?/\\')


def get_db_settings(config: dict) -> dict:
    db_config = config.get("db", {})
    return {
        "host": os.getenv("DB_HOST", db_config.get("host", "127.0.0.1")),
        "port": int(os.getenv("DB_PORT", db_config.get("port", 3306))),
        "user": os.getenv("DB_USER", db_config.get("user", "root")),
        "password": os.getenv("DB_PASSWORD", db_config.get("password", "")),
        "database": os.getenv("DB_NAME", db_config.get("database", "")),
    }


def sanitize_sheet_name(name: str, fallback: str) -> str:
    cleaned = "".join("_" if char in INVALID_SHEET_CHARS else char for char in str(name))
    cleaned = cleaned.strip().strip("'")
    if not cleaned:
        cleaned = fallback
    return cleaned[:31]


def make_unique_sheet_name(base_name: str, used_names: set[str]) -> str:
    if base_name not in used_names:
        used_names.add(base_name)
        return base_name

    suffix = 2
    while True:
        suffix_text = f"_{suffix}"
        candidate = f"{base_name[:31 - len(suffix_text)]}{suffix_text}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        suffix += 1


def fetch_sheet_rows(config: dict) -> dict:
    db_config = config.get("db", {})
    query = db_config.get("query")
    if not query:
        raise ValueError("Database query is not configured for this template.")

    sheet_name_field = db_config.get("sheet_name_field", "sheet_name")
    settings = get_db_settings(config)
    if not settings["database"]:
        raise ValueError("Database name is missing. Set DB_NAME or config['db']['database'].")

    connection = mysql.connector.connect(**settings)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        connection.close()

    used_names = set()
    sheets = {}
    for index, row in enumerate(rows, start=1):
        fallback = f"Sheet{index}"
        raw_name = row.get(sheet_name_field, fallback)
        safe_name = sanitize_sheet_name(raw_name, fallback)
        unique_name = make_unique_sheet_name(safe_name, used_names)
        sheets[unique_name] = row
    return sheets
