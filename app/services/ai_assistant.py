
import httpx
import json
from typing import Dict, List, Optional, Any
from app.config import settings


class AIAssistant:
    """Сервис для работы с AI (OpenAI или локальная LLM)"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    async def get_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None
    ) -> str:
        """Получение ответа от OpenAI"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не задан в переменных окружения")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60.0
            )
            data = response.json()
            
            if "error" in data:
                raise Exception(f"OpenAI API error: {data['error']}")
            
            return data["choices"][0]["message"]["content"]
    
    def get_system_prompt(self, user_data: Dict[str, Any]) -> str:
        """Генерация системного промпта на основе данных пользователя"""
        
        # Форматируем данные для промпта
        profile_info = ""
        if user_data.get('profile'):
            p = user_data['profile']
            profile_info = f"""
Имя: {p.get('first_name', 'не указано')}
Возраст: {p.get('age', 'не указан')}
Профессия: {p.get('occupation', 'не указана')}
Хобби: {', '.join(p.get('hobbies', [])) or 'не указаны'}
Семья: {len(p.get('family_members', []))} человек
Финансовые цели: {', '.join(p.get('financial_goals', [])) or 'не указаны'}
"""
        
        budget_info = ""
        if user_data.get('budget_limits'):
            limits = user_data['budget_limits']
            top_limits = sorted(limits.items(), key=lambda x: -x[1])[:5]
            budget_info = "\nБюджетные лимиты:\n" + "\n".join(
                f"- {cat}: {limit:,.0f} ₽" for cat, limit in top_limits
            )
        
        spending_info = ""
        if user_data.get('monthly_spending'):
            s = user_data['monthly_spending']
            top_spending = sorted(s.items(), key=lambda x: -x[1])[:5]
            spending_info = "\nТекущие расходы за месяц:\n" + "\n".join(
                f"- {cat}: {amount:,.0f} ₽" for cat, amount in top_spending
            )
        
        goals_info = ""
        if user_data.get('goals'):
            goals_info = "\nАктивные цели:\n" + "\n".join(
                f"- {g['name']}: {g['current_amount']:,.0f} / {g['target_amount']:,.0f} ₽"
                for g in user_data['goals']
            )
        
        return f"""Ты — финансовый ассистент «ФинНавигатор» и карьерный консультант.

Твоя задача — помогать пользователю управлять личными финансами, планировать бюджет, достигать целей, а также предлагать возможности для развития и смены деятельности на основе его интересов.

## Данные пользователя:
{profile_info}
{budget_info}
{spending_info}
{goals_info}

## Твои возможности:
1. Отвечать на вопросы о финансах, используя реальные данные
2. Предупреждать о перерасходе и рисках
3. Помогать ставить и отслеживать цели
4. Отвечать на вопрос "Могу ли я позволить себе X?"
5. Анализировать интересы и предлагать варианты дополнительного образования
6. Рекомендовать возможности монетизации хобби
7. Помогать планировать смену деятельности

## Правила ответов:
- Всегда обосновывай рекомендации цифрами из данных
- Если данных недостаточно — запроси их, не выдумывай
- При предложении образования/смены деятельности включай:
  * ориентировочную стоимость
  * сроки
  * потенциальный доход/окупаемость
- Будь дружелюбным, конкретным и практичным
- Не давай инвестиционных советов (акции, криптовалюты)
- Отвечай на русском языке

Ты — активный ассистент. Если видишь возможность улучшить финансовое положение пользователя, предлагай её, даже если он не спрашивал напрямую.
"""
    
    async def chat(
        self, 
        message: str, 
        user_data: Dict[str, Any],
        history: List[Dict[str, str]] = None
    ) -> str:
        """Основной метод для чата"""
        system_prompt = self.get_system_prompt(user_data)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history[-10:])  # последние 10 сообщений для контекста
        
        messages.append({"role": "user", "content": message})
        
        return await self.get_completion(messages)