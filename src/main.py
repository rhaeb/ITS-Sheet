import os
import sys
from pathlib import Path

import openpyxl

from db import fetch_sheet_rows
from template_config import TEMPLATES


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


def get_template_config(template_name: str) -> dict:
    config = TEMPLATES.get(template_name.lower())
    if not config:
        available = ", ".join(sorted(TEMPLATES))
        raise ValueError(
            f"Unknown template '{template_name}'. Available templates: {available}"
        )
    return config


def load_template_workbook(template_name: str, config: dict):
    template_path = BASE_DIR / "templates" / config["file"]
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    if template_path.suffix.lower() != ".xlsx":
        raise ValueError(
            f"Template '{template_name}' uses '{template_path.suffix}' format. "
            "Please convert it to .xlsx before using openpyxl."
        )

    workbook = openpyxl.load_workbook(template_path)
    return workbook, template_path


def populate_sheet(sheet, cell_map: dict, data: dict) -> None:
    for field_name, cell_address in cell_map.items():
        sheet[cell_address] = data.get(field_name, "")


def build_output_path(template_name: str, config: dict) -> Path:
    file_stub = config.get("output_name") or f"{template_name.lower()}_generated"
    safe_stub = "".join(
        char if char.isalnum() or char in ("-", "_") else "_" for char in file_stub
    ).strip("_")
    final_name = f"{safe_stub or template_name.lower()}.xlsx"
    return OUTPUT_DIR / final_name


def generate_file(template_name: str) -> Path:
    config = get_template_config(template_name)
    workbook, _template_path = load_template_workbook(template_name, config)
    template_sheet_name = config.get("template_sheet")
    if not template_sheet_name:
        raise ValueError(
            f"No template_sheet configured for template '{template_name}'."
        )
    if template_sheet_name not in workbook.sheetnames:
        raise KeyError(
            f"Template sheet '{template_sheet_name}' not found in template '{template_name}'."
        )

    cell_map = config.get("cells", {})
    if not cell_map:
        raise ValueError(f"No cells configured for template '{template_name}'.")

    sheets = fetch_sheet_rows(config) if config.get("use_database") else config.get("sheets", {})
    if not sheets:
        raise ValueError(f"No sheets configured for template '{template_name}'.")

    template_sheet = workbook[template_sheet_name]
    first_sheet = True
    for sheet_name, data in sheets.items():
        if first_sheet:
            sheet = template_sheet
            sheet.title = sheet_name
            first_sheet = False
        else:
            sheet = workbook.copy_worksheet(template_sheet)
            sheet.title = sheet_name
        populate_sheet(sheet, cell_map, data)

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = build_output_path(template_name, config)
    workbook.save(output_path)
    return output_path


def main() -> int:
    if len(sys.argv) < 2:
        available = ", ".join(sorted(TEMPLATES))
        print(f"Usage: python src/main.py <template_name>")
        print(f"Available templates: {available}")
        return 1

    template_name = sys.argv[1]

    try:
        output_path = generate_file(template_name)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"Error: {exc}")
        return 1

    relative_output = os.path.relpath(output_path, BASE_DIR)
    print(f"Generated Excel file saved to {relative_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
