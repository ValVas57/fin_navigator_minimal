from typing import Dict, List, Any, Optional
from datetime import date, timedelta
from collections import defaultdict


class BudgetAnalyzer:
    """Анализирует бюджет и расходы пользователя"""
    
    def __init__(self, transactions: List[Dict], budget_limits: Dict[str, float]):
        self.transactions = transactions
        self.budget_limits = budget_limits
    
    def get_monthly_spending(self) -> Dict[str, Dict[str, float]]:
        """Получает расходы по месяцам и категориям"""
        spending = defaultdict(lambda: defaultdict(float))
        
        for t in self.transactions:
            month = t['date'][:7]  # YYYY-MM
            cat = t['category_name']
            amount = abs(t['amount'])
            spending[month][cat] += amount
        
        return spending
    
    def check_budget_compliance(self, month: str) -> Dict[str, Dict]:
        """Проверяет соблюдение бюджета за указанный месяц"""
        monthly_spending = self.get_monthly_spending()
        spending = monthly_spending.get(month, {})
        
        result = {}
        for category, limit in self.budget_limits.items():
            spent = spending.get(category, 0)
            status = 'ok'
            if spent > limit:
                status = 'over'
            elif spent > limit * 0.8:
                status = 'warning'
            
            result[category] = {
                'limit': limit,
                'spent': spent,
                'remaining': max(0, limit - spent),
                'status': status,
                'percent': round(spent / limit * 100, 1) if limit > 0 else 0
            }
        
        return result
    
    def get_top_categories(self, month: str, limit: int = 5) -> List[Dict]:
        """Возвращает топ категорий по расходам за месяц"""
        monthly_spending = self.get_monthly_spending()
        spending = monthly_spending.get(month, {})
        
        sorted_cats = sorted(spending.items(), key=lambda x: -x[1])
        
        return [
            {'category': cat, 'amount': amount}
            for cat, amount in sorted_cats[:limit]
        ]
    
    def detect_spending_patterns(self) -> List[Dict]:
        """Обнаруживает паттерны в расходах (рост, снижение)"""
        monthly_spending = self.get_monthly_spending()
        months = sorted(monthly_spending.keys())
        
        if len(months) < 2:
            return []
        
        patterns = []
        
        for category in set().union(*[set(s.keys()) for s in monthly_spending.values()]):
            values = []
            for month in months:
                values.append(monthly_spending[month].get(category, 0))
            
            if len(values) >= 2:
                # Проверяем рост
                if values[-1] > values[0] * 1.3:
                    patterns.append({
                        'category': category,
                        'type': 'increase',
                        'first': values[0],
                        'last': values[-1],
                        'percent': round((values[-1] - values[0]) / values[0] * 100, 1)
                    })
                # Проверяем снижение
                elif values[-1] < values[0] * 0.7:
                    patterns.append({
                        'category': category,
                        'type': 'decrease',
                        'first': values[0],
                        'last': values[-1],
                        'percent': round((values[0] - values[-1]) / values[0] * 100, 1)
                    })
        
        return patterns
    
    def calculate_free_cash_flow(self, month: str, income: float) -> float:
        """Рассчитывает свободный денежный поток"""
        monthly_spending = self.get_monthly_spending()
        spending = monthly_spending.get(month, {})
        total_spent = sum(spending.values())
        return income - total_spent
    
    def suggest_budget_adjustments(self, month: str, income: float) -> List[Dict]:
        """Предлагает корректировки бюджета на основе данных"""
        budget_compliance = self.check_budget_compliance(month)
        free_cash = self.calculate_free_cash_flow(month, income)
        
        suggestions = []
        
        # Проверяем перерасходы
        for cat, data in budget_compliance.items():
            if data['status'] == 'over':
                suggestions.append({
                    'type': 'reduce',
                    'category': cat,
                    'current_limit': data['limit'],
                    'spent': data['spent'],
                    'over_amount': data['spent'] - data['limit'],
                    'message': f'Перерасход в категории "{cat}" на {data["spent"] - data["limit"]:,.0f} ₽'
                })
        
        # Проверяем возможность накопления
        if free_cash > 0:
            suggestions.append({
                'type': 'save',
                'amount': free_cash,
                'message': f'Свободные средства {free_cash:,.0f} ₽ можно направить на цели'
            })
        elif free_cash < 0:
            suggestions.append({
                'type': 'risk',
                'amount': abs(free_cash),
                'message': f'Дефицит бюджета {abs(free_cash):,.0f} ₽ — риск кассового разрыва'
            })
        
        return suggestions