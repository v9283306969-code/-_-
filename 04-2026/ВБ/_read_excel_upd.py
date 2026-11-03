#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальное чтение Excel-файлов уведомлений о выкупе и УПД.
"""

import openpyxl
import pdfplumber
import glob
import os
import json

BASE_DIR = r"C:\Users\Proff\Desktop\Бухгалтерия_АУСН\04-2026\ВБ"

def read_excel(filepath):
    fname = os.path.basename(filepath)
    wb = openpyxl.load_workbook(filepath, data_only=True)
    result = {"file": fname, "sheets": {}}
    for sn in wb.sheetnames:
        ws = wb[sn]
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append(list(row))
        result["sheets"][sn] = rows
    return result

def read_upd(filepath):
    fname = os.path.basename(filepath)
    result = {"file": fname, "text": "", "table": []}
    try:
        with pdfplumber.open(filepath) as pdf:
            page = pdf.pages[0]
            result["text"] = page.extract_text() or ""
            tables = page.extract_tables()
            if tables:
                result["table"] = tables[0]
    except Exception as e:
        result["text"] = f"ОШИБКА: {e}"
    return result

# === ЧИТАЕМ EXCEL ===
print("=" * 100)
print("УВЕДОМЛЕНИЯ О ВЫКУПЕ (Excel)")
print("=" * 100)

excel_files = sorted(glob.glob(os.path.join(BASE_DIR, "Уведомление*.xlsx")))
all_excel_data = []
for f in excel_files:
    data = read_excel(f)
    all_excel_data.append(data)
    print(f"\n{'='*80}")
    print(f"ФАЙЛ: {data['file']}")
    print(f"{'='*80}")
    for sn, rows in data["sheets"].items():
        print(f"\n--- Лист: {sn} (всего строк: {len(rows)}) ---")
        for i, row in enumerate(rows):
            # Пропускаем полностью пустые
            if all(c is None for c in row):
                continue
            print(f"  [{i}] {row}")

# === ЧИТАЕМ УПД (те, что не попали в первый анализ — но в папке их больше 12) ===
print("\n" + "=" * 100)
print("УПД — ПОЛНЫЙ СПИСОК И СУММЫ")
print("=" * 100)

upd_files = sorted(glob.glob(os.path.join(BASE_DIR, "УПД*.pdf")))
print(f"\nНайдено УПД: {len(upd_files)}")

import re
from decimal import Decimal

def parse_amt(s):
    if s is None or s == '—' or str(s).strip() in ('Х', 'X', ''):
        return Decimal('0')
    s = str(s).replace(' ', '').replace(',', '.')
    try:
        return Decimal(s)
    except:
        return Decimal('0')

upd_summary = []
for f in upd_files:
    fname = os.path.basename(f)
    with pdfplumber.open(f) as pdf:
        text = pdf.pages[0].extract_text() or ""
    
    # Дата УПД
    date_m = re.search(r"от (\d{2}\.\d{2}\.\d{4})", text)
    upd_date = date_m.group(1) if date_m else "?"
    
    # Номер УПД
    num_m = re.search(r"Счет-фактура №\s*(\S+)", text)
    upd_num = num_m.group(1) if num_m else "?"
    
    # Сумма
    total_m = re.search(r"Всего к оплате:\s*([\d\s,]+)", text)
    upd_total = parse_amt(total_m.group(1).strip()) if total_m else Decimal('0')
    
    # Услуги (тип)
    services = []
    if "возмещение за выдачу и возврат товаров на ПВЗ" in text.lower():
        services.append("ПВЗ")
    if "возмещение расходов по перевозке" in text.lower():
        services.append("Перевозка")
    if "штраф" in text.lower():
        services.append("Штраф")
    if "комисси" in text.lower():
        services.append("Комиссия")
    if "услуга" in text.lower() and not services:
        services.append("Услуга (общая)")
    
    # Отчёт-источник
    report_m = re.search(r"по отчету (\d+)", text)
    report_id = report_m.group(1) if report_m else ""
    
    # Период в УПД
    period_m = re.search(r"c (\d{2}\.\d{2}\.\d{4})\s+по\s+(\d{2}\.\d{2}\.\d{4})", text)
    period = f"{period_m.group(1)}-{period_m.group(2)}" if period_m else ""
    
    upd_summary.append({
        "file": fname,
        "date": upd_date,
        "num": upd_num,
        "total": str(upd_total),
        "services": services,
        "report_id": report_id,
        "period": period
    })
    
    m = "✅" if upd_date in ("05.04.2026","11.04.2026","12.04.2026","16.04.2026","19.04.2026","26.04.2026","30.04.2026") else "❌"
    print(f"  {m} {fname} | №{upd_num} от {upd_date} | {upd_total:>12,.2f} | {', '.join(services)} | отчёт {report_id} | {period}")

# Сохраняем
out = {"excel": all_excel_data, "upd_summary": upd_summary}
out_path = os.path.join(BASE_DIR, "_excel_and_upd.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=str)
print(f"\n>>> Данные сохранены в: {out_path}")
