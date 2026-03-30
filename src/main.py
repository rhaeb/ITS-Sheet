import openpyxl
import os

# Paths
template_path = "../templates/my_template.xlsx"
output_path = "../output/generated_file.xlsx"

# Load the template
wb = openpyxl.load_workbook(template_path)
sheet = wb.active

# Example: Fill some cells
sheet["A1"] = "Hello"
sheet["B2"] = 123

# Save the new Excel file
os.makedirs("../output", exist_ok=True)
wb.save(output_path)

print(f"Generated Excel file saved to {output_path}")