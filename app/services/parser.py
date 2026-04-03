import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Tuple, Any, Optional
import re


class ExcelParser:
    """
    Парсер для файла затрат в формате:
    - Столбцы: ВСЕГО, алкоголь, продукты, лекарства, машина, хобби, дача, квартира, лечение, образование, подарки, работа, тлф, ПК
    - Строки: месяцы (июнь, июль, август, сент)
    - Последняя строка: ВСЕГО по столбцам
    """
    
    # Маппинг русских категорий из файла на системные
    DEFAULT_CATEGORY_MAPPING = {
        'алкоголь': 'Вредные привычки',
        'продукты': 'Продукты',
        'лекарства': 'Здоровье',
        'машина': 'Транспорт (личный)',
        'хобби': 'Развлечения / Хобби',
        'дача': 'Дом / Дача',
        'квартира': 'ЖКХ / Квартплата',
        'лечение': 'Здоровье (платное)',
        'образование': 'Образование',
        'подарки': 'Подарки / Благотворительность',
        'работа': 'Профессиональные расходы',
        'тлф, ПК': 'Техника / Связь',
    }
    
    # Соответствие названий месяцев номерам
    MONTH_MAP = {
        'июнь': 6,
        'июль': 7,
        'август': 8,
        'сент': 9,
        'сентябрь': 9,
        'октябрь': 10,
        'ноябрь': 11,
        'декабрь': 12,
        'январь': 1,
        'февраль': 2,
        'март': 3,
        'апрель': 4,
        'май': 5,
    }
    
    def __init__(self, file_path: str, year: int = 2024):
        self.file_path = file_path
        self.year = year
        self.df = None
        self.months = []
        self.categories = []
        
    def load(self) -> 'ExcelParser':
        """Загружает и парсит Excel файл"""
        # Читаем файл, header=1 означает, что заголовки на второй строке
        self.df = pd.read_excel(self.file_path, sheet_name='Лист3', header=1)
        return self
    
    def extract_months(self) -> List[str]:
        """Извлекает названия месяцев из первого столбца"""
        # Берём первый столбец, отбрасываем NaN и строку 'ВСЕГО'
        months_raw = self.df.iloc[:, 0].dropna().tolist()
        self.months = [
            m for m in months_raw 
            if isinstance(m, str) and not m.startswith('ВСЕГО') and m.strip()
        ]
        return self.months
    
    def extract_categories(self) -> List[str]:
        """Извлекает названия категорий из заголовков столбцов"""
        # Столбцы с 1 по последний (индекс 1), исключая 'ВСЕГО' и пустые
        categories_raw = self.df.columns[1:].tolist()
        self.categories = [
            c for c in categories_raw 
            if c and c != 'ВСЕГО' and not pd.isna(c)
        ]
        return self.categories
    
    def get_month_date(self, month_name: str) -> date:
        """Преобразует название месяца в дату (первое число месяца)"""
        month_num = self.MONTH_MAP.get(month_name.lower()[:4], 1)
        return date(self.year, month_num, 1)
    
    def parse_transactions(
        self, 
        category_mapping: Optional[Dict[str, str]] = None,
        exclude_anomalies: bool = True,
        anomaly_threshold: float = 100000
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Парсит транзакции из файла.
        
        Args:
            category_mapping: словарь для переопределения маппинга категорий
            exclude_anomalies: исключать ли аномальные суммы из транзакций
            anomaly_threshold: порог для определения аномалий
            
        Returns:
            tuple: (transactions, anomalies)
        """
        if self.df is None:
            self.load()
        
        if not self.months:
            self.extract_months()
        if not self.categories:
            self.extract_categories()
        
        transactions = []
        anomalies = []
        
        mapping = category_mapping or self.DEFAULT_CATEGORY_MAPPING
        
        for i, month_name in enumerate(self.months):
            month_date = self.get_month_date(month_name)
            
            for j, cat in enumerate(self.categories):
                # Сумма в столбце j+1 (первый столбец B)
                amount = self.df.iloc[i, j + 1]
                
                if pd.isna(amount) or amount == 0:
                    continue
                
                # Проверяем на аномалию
                is_anomaly = amount > anomaly_threshold
                
                # Определяем системную категорию
                system_category = mapping.get(cat.lower(), cat)
                
                transaction = {
                    'amount': -float(amount),  # расход (отрицательное число)
                    'category_name': system_category,
                    'date': month_date.isoformat(),
                    'description': f"Импорт: {cat} за {month_name}",
                    'source': 'excel_import',
                    'original_category': cat,
                    'month': month_name,
                }
                
                if is_anomaly:
                    anomaly = {
                        'month': month_name,
                        'category': cat,
                        'amount': amount,
                        'reason': f'Сумма {amount:,.0f} ₽ превышает порог {anomaly_threshold:,.0f} ₽',
                        'index': i,
                    }
                    anomalies.append(anomaly)
                    
                    if exclude_anomalies:
                        continue
                
                transactions.append(transaction)
        
        return transactions, anomalies
    
    def get_preview_data(self) -> Dict[str, Any]:
        """Получает данные для предпросмотра перед импортом"""
        if not self.months:
            self.extract_months()
        if not self.categories:
            self.extract_categories()
        
        # Получаем транзакции без исключения аномалий для предпросмотра
        transactions, anomalies = self.parse_transactions(
            exclude_anomalies=False,
            anomaly_threshold=50000  # ниже порог для предпросмотра
        )
        
        total_amount = sum(abs(t['amount']) for t in transactions)
        
        # Собираем статистику по категориям
        category_stats = {}
        for t in transactions:
            cat = t['original_category']
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'count': 0}
            category_stats[cat]['total'] += abs(t['amount'])
            category_stats[cat]['count'] += 1
        
        return {
            'months': self.months,
            'categories': self.categories,
            'total_amount': total_amount,
            'total_transactions': len(transactions),
            'anomalies': anomalies,
            'category_stats': category_stats,
            'suggested_mapping': self.DEFAULT_CATEGORY_MAPPING,
        }
    
    def calculate_monthly_average(
        self, 
        transactions: List[Dict],
        category_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Рассчитывает среднемесячные траты по категориям"""
        if not transactions:
            transactions, _ = self.parse_transactions(category_mapping)
        
        mapping = category_mapping or self.DEFAULT_CATEGORY_MAPPING
        months_count = len(self.months) or 1
        
        category_totals = {}
        for t in transactions:
            cat = t['category_name']
            category_totals[cat] = category_totals.get(cat, 0) + abs(t['amount'])
        
        monthly_avg = {
            cat: round(total / months_count, 0) 
            for cat, total in category_totals.items()
        }
        
        return monthly_avg
    
    def get_spending_by_month(self) -> Dict[str, Dict[str, float]]:
        """Получает разбивку расходов по месяцам и категориям"""
        transactions, _ = self.parse_transactions(exclude_anomalies=False)
        
        spending = {}
        for t in transactions:
            month = t['month']
            cat = t['category_name']
            amount = abs(t['amount'])
            
            if month not in spending:
                spending[month] = {}
            spending[month][cat] = spending[month].get(cat, 0) + amount
        
        return spending


# Утилитарные функции
def quick_parse(file_path: str, year: int = 2024) -> Dict[str, Any]:
    """
    Быстрый парсинг файла с затратами.
    Возвращает готовую структуру для импорта в БД.
    """
    parser = ExcelParser(file_path, year)
    parser.load()
    parser.extract_months()
    parser.extract_categories()
    
    transactions, anomalies = parser.parse_transactions()
    monthly_avg = parser.calculate_monthly_average(transactions)
    spending_by_month = parser.get_spending_by_month()
    preview = parser.get_preview_data()
    
    return {
        'transactions': transactions,
        'anomalies': anomalies,
        'months': parser.months,
        'categories': parser.categories,
        'monthly_average': monthly_avg,
        'spending_by_month': spending_by_month,
        'total_period': preview['total_amount'],
        'preview': preview,
    }
