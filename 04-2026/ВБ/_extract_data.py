#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт извлечения данных из отчётов Wildberries (PDF + Excel)
для бухгалтерского учёта АУСН.
"""

import os
import glob
import pdfplumber
import openpyxl
import json

BASE_DIR = r"C:\Users\Proff\Desktop\Бухгалтерия_АУСН\04-2026\ВБ"

def extract_pdf_text(filepath):
    """Извлечь весь текст из PDF, постранично."""
    result = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                tables = page.extract_tables()
                result.append({
                    "page": i + 1,
                    "text": text or "(нет текста)",
                    "tables": tables or []
                })
    except Exception as e:
        result = [{"page": 0, "text": f"ОШИБКА: {e}", "tables": []}]
    return result

def extract_excel_data(filepath):
    """Извлечь данные из всех листов Excel файла."""
    result = {}
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = []
            for row in ws.iter_rows(values_only=True):
                rows.append(list(row))
            result[sheet_name] = rows
    except Exception as e:
        result = {"_ERROR_": [f"ОШИБКА: {e}"]}
    return result

def main():
    output = {"pdf_reports": [], "purchase_notifications": [], "upd_documents": []}

    # 1. Отчёты (PDF)
    for f in sorted(glob.glob(os.path.join(BASE_DIR, "Отчет*.pdf"))):
        fname = os.path.basename(f)
        print(f"\n{'='*80}")
        print(f"ФАЙЛ: {fname}")
        print(f"{'='*80}")
        data = extract_pdf_text(f)
        for page_data in data:
            print(f"\n--- СТРАНИЦА {page_data['page']} ---")
            print(page_data['text'])
            if page_data['tables']:
                for t_idx, table in enumerate(page_data['tables']):
                    print(f"\n  [ТАБЛИЦА {t_idx+1}]")
                    for r_idx, row in enumerate(table):
                        print(f"    Строка {r_idx}: {row}")
        output["pdf_reports"].append({"file": fname, "pages": data})

    # 2. Уведомления о выкупе (Excel)
    for f in sorted(glob.glob(os.path.join(BASE_DIR, "Уведомление*.xlsx"))):
        fname = os.path.basename(f)
        print(f"\n{'='*80}")
        print(f"ФАЙЛ: {fname}")
        print(f"{'='*80}")
        data = extract_excel_data(f)
        for sheet_name, rows in data.items():
            print(f"\n--- ЛИСТ: {sheet_name} ---")
            for r_idx, row in enumerate(rows):
                print(f"  Строка {r_idx}: {row}")
        output["purchase_notifications"].append({"file": fname, "sheets": data})

    # 3. УПД (PDF)
    for f in sorted(glob.glob(os.path.join(BASE_DIR, "УПД*.pdf"))):
        fname = os.path.basename(f)
        print(f"\n{'='*80}")
        print(f"ФАЙЛ: {fname}")
        print(f"{'='*80}")
        data = extract_pdf_text(f)
        for page_data in data:
            print(f"\n--- СТРАНИЦА {page_data['page']} ---")
            print(page_data['text'])
            if page_data['tables']:
                for t_idx, table in enumerate(page_data['tables']):
                    print(f"\n  [ТАБЛИЦА {t_idx+1}]")
                    for r_idx, row in enumerate(table):
                        print(f"    Строка {r_idx}: {row}")
        output["upd_documents"].append({"file": fname, "pages": data})

    # Сохраняем сырые данные в JSON для дальнейшего анализа
    json_path = os.path.join(BASE_DIR, "_extracted_data.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(output, jf, ensure_ascii=False, indent=2, default=str)
    print(f"\n\n>>> Сырые данные сохранены в: {json_path}")

if __name__ == "__main__":
    main()
