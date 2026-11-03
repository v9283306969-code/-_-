#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализатор данных Wildberries для АУСН «Доходы минус расходы».
Читает _extracted_data.json, формирует сводный регистр и аудит.
"""

import json
import os
from decimal import Decimal

BASE_DIR = r"C:\Users\Proff\Desktop\Бухгалтерия_АУСН\04-2026\ВБ"

def parse_amount(s):
    """Преобразует строку '141 515,00' в Decimal."""
    if s is None or s == '—' or s == '' or s.strip() in ('Х', 'X', 'x', 'h'):
        return Decimal('0')
    s = s.replace(' ', '').replace(',', '.')
    try:
        return Decimal(s)
    except:
        return Decimal('0')

def find_row(data_list, keyword):
    """Находит строку в таблице по ключевому слову."""
    for row in data_list:
        if len(row) >= 2 and keyword.lower() in str(row[1]).lower():
            return row
    return None

def analyze():
    json_path = os.path.join(BASE_DIR, "_extracted_data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 100)
    print("АНАЛИЗ ДАННЫХ WILDBERRIES — АУСН «ДОХОДЫ МИНУС РАСХОДЫ» (20%)")
    print(f"Отчетный период: Апрель 2026")
    print("=" * 100)

    # ============================
    # 1. ОТЧЁТЫ О РЕАЛИЗАЦИИ (PDF)
    # ============================
    reports = data.get("pdf_reports", [])
    upd_docs = data.get("upd_documents", [])
    
    # Структура для накопления
    total_income = Decimal('0')
    total_expenses = Decimal('0')
    total_nds = Decimal('0')
    rows_for_table = []
    audit_notes = []

    for rpt in reports:
        fname = rpt["file"]
        pages = rpt.get("pages", [])
        if not pages:
            continue
        
        table = pages[0].get("tables", [])
        if not table:
            continue
        
        data_rows = table[0]  # первая таблица = сводная
        
        # Дата формирования отчета (признания)
        report_date_row = find_row(data_rows, "Итого стоимость реализованного товара и услуг")
        report_date = report_date_row[3] if report_date_row else "?"
        
        # Проверяем период
        period_match = None
        for row in data_rows:
            if len(row) >= 2 and "за период" in str(row[1]).lower():
                period_match = row[1]
                break

        # 1. ДОХОД: Итого стоимость реализованного товара и услуг (строка 1)
        row1 = find_row(data_rows, "Итого стоимость реализованного товара и услуг")
        income_total = parse_amount(row1[5]) if row1 else Decimal('0')
        
        # 1.1 Всего стоимость реализованного товара
        row1_1 = find_row(data_rows, "Всего стоимость реализованного товара")
        goods_income = parse_amount(row1_1[5]) if row1_1 else Decimal('0')
        
        # 1.4 Компенсация скидки
        row1_4 = find_row(data_rows, "Компенсация скидки")
        loyalty_comp = parse_amount(row1_4[5]) if row1_4 else Decimal('0')
        
        # 2. Итого зачтено
        row2 = find_row(data_rows, "Итого зачтено из стоимости")
        total_deducted = parse_amount(row2[5]) if row2 else Decimal('0')
        total_nds_in_report = parse_amount(row2[6]) if row2 else Decimal('0')
        
        # 2.1 Вознаграждение Вайлдберриз (без НДС) — это КОМИССИЯ
        row2_1 = find_row(data_rows, "Сумма вознаграждения Вайлдберриз за текущий период")
        wb_commission = parse_amount(row2_1[5]) if row2_1 else Decimal('0')
        
        # 2.2 НДС с вознаграждения
        row2_2 = find_row(data_rows, "НДС с вознаграждения")
        commission_nds = parse_amount(row2_2[5]) if row2_2 else Decimal('0')
        
        # 2.6 Обеспечение организации платежа
        row2_6 = find_row(data_rows, "Сумма, удержанная в счёт обеспечения")
        payment_org = parse_amount(row2_6[5]) if row2_6 else Decimal('0')
        
        # 2.7 Возмещение расходов по перевозке
        row2_7 = find_row(data_rows, "Возмещение расходов по перевозке")
        transport_reimb = parse_amount(row2_7[5]) if row2_7 else Decimal('0')
        
        # 2.8 Возмещение за выдачу и возврат товаров на ПВЗ
        row2_8 = find_row(data_rows, "Возмещение за выдачу и возврат товаров на ПВЗ")
        pvz_reimb = parse_amount(row2_8[5]) if row2_8 else Decimal('0')
        
        # 2.9 Штрафы
        row2_9 = find_row(data_rows, "Штрафы")
        fines = parse_amount(row2_9[5]) if row2_9 else Decimal('0')
        
        # 2.10 Прочие удержания
        row2_10 = find_row(data_rows, "Прочие удержания")
        other_deductions = parse_amount(row2_10[5]) if row2_10 else Decimal('0')
        
        # 3. Удержания в пользу третьих лиц
        row3 = find_row(data_rows, "Удержания в пользу третьих лиц")
        third_party = parse_amount(row3[5]) if row3 else Decimal('0')
        
        # 8. Итого к перечислению
        row8 = find_row(data_rows, "Итого к перечислению Продавцу")
        to_pay = parse_amount(row8[5]) if row8 else Decimal('0')
        
        # Итого вознаграждение (из итоговой части отчёта)
        total_wb_reward = Decimal('0')
        text = pages[0].get("text", "")
        import re
        reward_match = re.search(r"Итого Вознаграждение Вайлдберриз.*?\n([\d\s]+,?\d*)", text)
        if reward_match:
            total_wb_reward = parse_amount(reward_match.group(1).strip())
        
        # --- Проверка математики ---
        expected_balance = goods_income - wb_commission - commission_nds - payment_org - transport_reimb - pvz_reimb - fines - other_deductions - third_party
        balance_diff = to_pay - expected_balance
        
        if abs(balance_diff) > Decimal('1'):
            audit_notes.append(
                f"⚠ {fname}: Математический дисбаланс! "
                f"Итого к перечислению ({to_pay}) ≠ Расчётное ({expected_balance}). "
                f"Разница: {balance_diff:+,.2f} руб. "
                f"Проверьте: доход={goods_income}, удержания={(wb_commission+commission_nds+payment_org+transport_reimb+pvz_reimb+fines+other_deductions+third_party)}"
            )
        
        # --- Определяем период признания ---
        # Дата отчёта = дата формирования (признания дохода/расходов)
        from datetime import datetime
        report_dt = datetime.strptime(report_date, "%Y-%m-%d") if report_date != "?" else None
        period_in_april = True
        period_note = ""
        if report_dt:
            if report_dt.month != 4:
                period_in_april = False
                period_note = f"⚠ ДАТА ОТЧЁТА {report_date} — НЕ АПРЕЛЬ! Исключено из расчёта."

        if period_in_april:
            # ДОХОД
            total_income += goods_income
            rows_for_table.append({
                "block": "ДОХОДЫ",
                "desc": "Реализация товаров",
                "amount": f"+{goods_income:,.2f}",
                "platform": "Wildberries",
                "source": fname,
                "location": f"Стр. 1, табл., поз. 1.1"
            })
            
            if loyalty_comp > 0:
                total_income += loyalty_comp
                rows_for_table.append({
                    "block": "ДОХОДЫ",
                    "desc": "Компенсация скидки по программе лояльности",
                    "amount": f"+{loyalty_comp:,.2f}",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 1.4"
                })
            
            # РАСХОДЫ
            if wb_commission > 0:
                total_expenses += wb_commission
                rows_for_table.append({
                    "block": "РАСХОДЫ",
                    "desc": "Комиссия Вайлдберриз (без НДС)",
                    "amount": f"-{wb_commission:,.2f}",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 2.1"
                })
            
            total_nds += commission_nds
            if commission_nds > 0:
                rows_for_table.append({
                    "block": "СПРАВОЧНО",
                    "desc": "НДС с вознаграждения Вайлдберриз (не учитывается при АУСН)",
                    "amount": f"({commission_nds:,.2f})",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 2.2"
                })
            
            if payment_org > 0:
                total_expenses += payment_org
                rows_for_table.append({
                    "block": "РАСХОДЫ",
                    "desc": "Обеспечение организации платежа",
                    "amount": f"-{payment_org:,.2f}",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 2.6"
                })
            
            if transport_reimb > 0:
                total_expenses += transport_reimb
                rows_for_table.append({
                    "block": "РАСХОДЫ",
                    "desc": "Возмещение расходов по перевозке (логистика)",
                    "amount": f"-{transport_reimb:,.2f}",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 2.7"
                })
            
            if pvz_reimb > 0:
                total_expenses += pvz_reimb
                rows_for_table.append({
                    "block": "РАСХОДЫ",
                    "desc": "Возмещение за выдачу/возврат товаров на ПВЗ",
                    "amount": f"-{pvz_reimb:,.2f}",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 2.8"
                })
            
            if fines > 0:
                total_expenses += fines
                rows_for_table.append({
                    "block": "РАСХОДЫ",
                    "desc": "Штрафы",
                    "amount": f"-{fines:,.2f}",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 2.9"
                })
            
            if other_deductions > 0:
                total_expenses += other_deductions
                rows_for_table.append({
                    "block": "РАСХОДЫ",
                    "desc": "Прочие удержания",
                    "amount": f"-{other_deductions:,.2f}",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 2.10"
                })
            
            if third_party > 0:
                total_expenses += third_party
                rows_for_table.append({
                    "block": "РАСХОДЫ",
                    "desc": "Удержания в пользу третьих лиц",
                    "amount": f"-{third_party:,.2f}",
                    "platform": "Wildberries",
                    "source": fname,
                    "location": f"Стр. 1, табл., поз. 3"
                })
            
        else:
            audit_notes.append(period_note)
        
        # Детальная проверка
        print(f"\n--- {fname} ---")
        print(f"  Дата отчёта: {report_date}")
        print(f"  Период: {period_match}")
        print(f"  Доход (товар): {goods_income:,.2f}")
        print(f"  Комиссия ВВ: {wb_commission:,.2f}")
        print(f"  НДС комиссии: {commission_nds:,.2f}")
        print(f"  Обеспечение платежа: {payment_org:,.2f}")
        print(f"  Перевозка: {transport_reimb:,.2f}")
        print(f"  ПВЗ: {pvz_reimb:,.2f}")
        print(f"  Штрафы: {fines:,.2f}")
        print(f"  Прочие: {other_deductions:,.2f}")
        print(f"  Третьи лица: {third_party:,.2f}")
        print(f"  Итого к перечислению: {to_pay:,.2f}")
        print(f"  Баланс (расчётный): {expected_balance:,.2f}")
        print(f"  Разница: {balance_diff:+,.2f}")

    print("\n" + "=" * 100)

    # ============================
    # 2. УПД (анализ документов)
    # ============================
    print("\nУПД — АНАЛИЗ ЗАКРЫВАЮЩИХ ДОКУМЕНТОВ")
    print("=" * 100)
    
    upd_april = []
    upd_non_april = []
    
    for upd in upd_docs:
        fname = upd["file"]
        pages = upd.get("pages", [])
        if not pages:
            continue
        
        text = pages[0].get("text", "")
        
        # Извлекаем дату УПД
        upd_date_match = re.search(r"№.*?от (\d{2}\.\d{2}\.\d{4})", text)
        upd_date = upd_date_match.group(1) if upd_date_match else "?"
        
        # Проверяем месяц
        try:
            dt = datetime.strptime(upd_date, "%d.%m.%Y")
            is_april = (dt.month == 4)
        except:
            is_april = True
        
        # Сумма по УПД
        total_match = re.search(r"Всего к оплате:\s*([\d\s,]+)", text)
        upd_total = parse_amount(total_match.group(1).strip()) if total_match else Decimal('0')
        
        # Услуги
        services = []
        if "возмещение за выдачу и возврат товаров на ПВЗ" in text.lower():
            services.append("ПВЗ")
        if "возмещение расходов по перевозке" in text.lower():
            services.append("Перевозка")
        if "штраф" in text.lower():
            services.append("Штраф")
        
        status = "✅ АПРЕЛЬ" if is_april else "❌ НЕ АПРЕЛЬ"
        print(f"  {fname} | Дата: {upd_date} | {status} | Сумма: {upd_total:,.2f} | Услуги: {', '.join(services)}")
        
        if is_april:
            upd_april.append({"file": fname, "date": upd_date, "total": upd_total, "services": services})
        else:
            upd_non_april.append({"file": fname, "date": upd_date, "total": upd_total, "services": services})
    
    # Добавляем УПД в расходы (если они подтверждают расходы из отчётов)
    # УПД — это закрывающие документы для подтвержения расходов на логистику и ПВЗ
    
    # ============================
    # 3. СВОДНАЯ ТАБЛИЦА
    # ============================
    print("\n" + "=" * 100)
    print("СВОДНЫЙ БУХГАЛТЕРСКИЙ РЕГИСТР — АПРЕЛЬ 2026")
    print("=" * 100)
    
    # Заголовок
    header = f"{'Блок':<12} | {'Расшифровка операции':<48} | {'Сумма (руб.)':<15} | {'Площадка':<12} | {'Документ-источник':<30} | {'Лист/Строка'}"
    print(header)
    print("-" * len(header))
    
    for row in rows_for_table:
        line = f"{row['block']:<12} | {row['desc']:<48} | {row['amount']:>14} | {row['platform']:<12} | {row['source']:<30} | {row['location']}"
        print(line)
    
    print("-" * len(header))
    
    # ИТОГО
    tax_base = total_income - total_expenses
    tax_amount = tax_base * Decimal('0.20')
    
    print(f"\nИТОГО ДОХОДЫ:          +{total_income:,.2f} руб.")
    print(f"ИТОГО РАСХОДЫ:         -{total_expenses:,.2f} руб.")
    print(f"НАЛОГОВАЯ БАЗА:         {tax_base:,.2f} руб.")
    print(f"НАЛОГ АУСН (20%):       {tax_amount:,.2f} руб.")
    print(f"НДС (справочно):        {total_nds:,.2f} руб. — не учитывается при АУСН")
    
    # ============================
    # 4. АУДИТ И НЕСТЫКОВКИ
    # ============================
    print("\n" + "=" * 100)
    print("АУДИТ И НЕСТЫКОВКИ")
    print("=" * 100)
    
    if audit_notes:
        for note in audit_notes:
            print(f"  {note}")
    else:
        print("  ✅ Математических дисбалансов не обнаружено.")
    
    # Проверка недостающих документов
    print(f"\n  📋 ЗАПРОС ДОКУМЕНТОВ:")
    if upd_non_april:
        print(f"    - {len(upd_non_april)} УПД с датами НЕ в апреле (справочно):")
        for u in upd_non_april:
            print(f"      • {u['file']} от {u['date']} — {u['total']:,.2f} руб.")
    
    print(f"\n  📋 ТРЕБУЕТСЯ СВЕРКА:")
    print(f"    - Сверить суммы логистики в отчётах с УПД за апрель ({len(upd_april)} документов)")
    print(f"    - Проверить, все ли еженедельные отчёты WB загружены (последний отчёт в папке: 20.04.2026)")
    print(f"    - Запросить отчёт WB за неделю 21-27.04.2026 (если есть)")
    print(f"    - Проверить эквайринг — в текущих отчётах отдельная строка эквайринга отсутствует")
    
    # ============================
    # 5. РАСШИФРОВКА
    # ============================
    print("\n" + "=" * 100)
    print("РАСШИФРОВКА РАСЧЁТА")
    print("=" * 100)
    print(f"""
  1. Доходы берутся из еженедельных отчётов WB (поз. 1.1 — стоимость реализованного товара).
  2. Расходы — все удержания из поз. 2.x и 3 отчётов.
  3. НДС (поз. 2.2) — СПРАВОЧНО. При АУСН НДС не уплачивается, суммы расходов берутся без НДС.
  4. Период признания — по ДАТЕ ФОРМИРОВАНИЯ ОТЧЁТА (колонка «Дата» в отчёте), не по периоду продаж.
  5. УПД используются как закрывающие документы для подтверждения расходов (логистика, ПВЗ).
  6. Формула налога: (Доходы - Расходы) × 20% = ({total_income:,.2f} - {total_expenses:,.2f}) × 20% = {tax_amount:,.2f} руб.
  
  ⚠️ ВАЖНО: Это база для отправки в ЛК ФНС по АУСН. Перед отправкой сверить с актуальным состоянием ЛК!
    """)

    # Сохраняем результат
    result_path = os.path.join(BASE_DIR, "_accounting_register.txt")
    import sys
    class Tee:
        def __init__(self, *streams):
            self.streams = streams
        def write(self, data):
            for s in self.streams:
                s.write(data)
        def flush(self):
            for s in self.streams:
                s.flush()
    
    # Вывод уже в консоль, сохраняем ключевые цифры
    summary = {
        "total_income": str(total_income),
        "total_expenses": str(total_expenses),
        "tax_base": str(tax_base),
        "tax_amount": str(tax_amount),
        "total_nds": str(total_nds),
        "reports_analyzed": len(reports),
        "upd_april": len(upd_april),
        "upd_non_april": len(upd_non_april),
        "audit_notes": audit_notes,
        "rows": rows_for_table
    }
    
    summary_path = os.path.join(BASE_DIR, "_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n>>> Сводка сохранена в: {summary_path}")

if __name__ == "__main__":
    analyze()
