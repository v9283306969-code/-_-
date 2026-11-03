---
name: wb-ausn-accounting-workflow
description: Workflow for processing Wildberries accounting documents (PDF reports, Excel buyouts, UPD) for AUSN tax calculation
source: auto-skill
extracted_at: '2026-06-06T21:17:20.732Z'
---

# Wildberries AUSN Accounting — Document Processing Workflow

## Problem context

When processing WB documents for AUSN "Доходы минус расходы" (20% rate), multiple document types must be cross-referenced. A common mistake is treating buyout notifications as separate income.

## Document types and their role

| Document type | Format | Role in accounting |
|---|---|---|
| **Отчет о реализации** (weekly) | PDF | **Primary source** for income and expense recognition. Date of report = recognition date. |
| **Уведомление о выкупе** | Excel | WB buys seller's goods. **Already included** in "стоимость реализованного товара" in the weekly report. Do NOT add as separate income. |
| **УПД** (закрывающий документ) | PDF | Confirms expenses (commission, logistics, PVZ). Used for cross-checking report figures. |

## Critical rule: Buyouts are NOT separate income

**Why:** When WB buys out seller goods (ООО "РВБ" purchases), the transaction is recorded in the weekly realization report as a regular sale. The buyout notification is just a formal notice.

**How to apply:**
1. Read buyout Excel files to verify they match report periods
2. Do NOT add buyout amounts to income separately
3. Flag any buyout that has no corresponding report (missing report = missing income recognition)

## Tooling setup

PDF and Excel files on Windows require:
```bash
pip install pdfplumber openpyxl
```

Standard `read_file` tool cannot parse PDF or binary Excel files directly.

## Reconciliation checks to always perform

1. **Math balance per report:** `Доход - Все удержания` should equal `Итого к перечислению` (within ±1 руб, tolerance for loyalty compensation)
2. **Commission cross-check:** Sum of УПД "комиссия" vs поз. 2.1 in reports — large differences mean extra УПД cover other services (ads, storage) hidden in "Прочие удержания" (поз. 2.10)
3. **Logistics cross-check:** УПД "Перевозка + ПВЗ" should match поз. 2.7 + поз. 2.8 in the corresponding report
4. **Missing reports:** Check if the last week of the month has a report — if not, income/expenses for those days are in the next month's report

## AUSN recognition rules

- **Recognition date** = date the report is generated (column "Дата" in the report table), NOT the sale period
- **VDS (НДС)** in reports is informational only — AUSN payers don't pay VAT. Expense amounts should be taken WITHOUT VAT (поз. 2.1 is "без НДС")
- Report dated outside the reporting month → exclude from current month calculation, flag separately
