import telebot
import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import math

# ========== ВАШ КАЛЬКУЛЯТОР ==========
@dataclass
class ApartmentParams:
    """Параметры квартиры"""
    area: float                    # площадь в м²
    district: str                  # район
    build_year: int                # год постройки
    house_type: str                # тип дома
    repair: str                    # ремонт
    floor: int                     # этаж квартиры
    total_floors: int              # всего этажей
    has_balcony: bool              # балкон/лоджия
    heating: str                   # отопление
    infrastructure: List[str]      # инфраструктура
    view: str = "стандартный"      # вид
    urgency: bool = False          # срочная продажа

class PriceCalculator:
    """Калькулятор стоимости недвижимости"""
    
    BASE_PRICE_PER_M2 = 110000
    
    COEF_DISTRICT = {
        "центр": 1.32, "приморье": 1.25, "калараша": 1.11,
        "звездная": 1.04, "уральская": 0.96, "барсовая": 0.92,
        "грознефть": 0.88, "сортировка": 0.85, "кроянское": 0.81,
        "кадош": 0.86
    }
    
    COEF_BUILD_YEAR = {
        "2020+": 1.30, "2010-2019": 1.19, "2000-2009": 1.10,
        "1990-1999": 1.03, "1980-1989": 0.97, "1970-1979": 0.91,
        "1960-1969": 0.86, "1950-1959": 0.82, "до 1950": 0.76
    }
    
    COEF_REPAIR = {
        "евро": 1.26, "косметика": 1.05, "предчистовая": 0.86, "нет": 0.72
    }
    
    COEF_HOUSE_TYPE = {
        "монолит-кирпич": 1.19, "монолитный": 1.15, "кирпич": 1.07,
        "блочный": 1.02, "панельный": 0.94
    }
    
    COEF_HEATING = {
        "индивид_газ": 1.11, "автономное": 1.06, "центральные": 1.00
    }
    
    COEF_INFRASTRUCTURE = {
        "море_шаг": 0.16, "школа_шаг": 0.07, "садик_шаг": 0.06,
        "больница_шаг": 0.04, "магазины_шаг": 0.03, "транспорт_10мин": 0.04,
        "пробки": -0.12, "туристический": 0.08, "спальный": 0.05,
        "нефтезавод": -0.14
    }
    
    COEF_VIEW = {
        "на море": 1.07, "на город": 1.03, "стандартный": 1.00
    }
    
    def __init__(self):
        self.season_coef = self._get_season_coefficient()
        
    def _get_season_coefficient(self) -> float:
        month = datetime.now().month
        if 5 <= month <= 9:
            return 1.10
        elif 11 <= month <= 2:
            return 0.95
        else:
            return 1.00
    
    def _get_year_category(self, year: int) -> str:
        if year >= 2020:
            return "2020+"
        elif 2010 <= year < 2020:
            return "2010-2019"
        elif 2000 <= year < 2010:
            return "2000-2009"
        elif 1990 <= year < 2000:
            return "1990-1999"
        elif 1980 <= year < 1990:
            return "1980-1989"
        elif 1970 <= year < 1980:
            return "1970-1979"
        elif 1960 <= year < 1970:
            return "1960-1969"
        elif 1950 <= year < 1960:
            return "1950-1959"
        else:
            return "до 1950"
    
    def _calculate_floor_coefficient(self, floor: int, total_floors: int) -> float:
        if floor == 1:
            floor_num_coef = 0.85
        elif floor == 2:
            floor_num_coef = 1.08
        elif floor == 3:
            floor_num_coef = 1.12
        elif floor == 4:
            floor_num_coef = 1.05
        elif floor == 5:
            floor_num_coef = 1.02
        else:
            floor_num_coef = 1.06
        
        if floor == 1:
            position_coef = 0.90
        elif floor == total_floors:
            position_coef = 0.95
        elif floor == total_floors - 1:
            position_coef = 1.05
        else:
            position_coef = 1.15
        
        if total_floors <= 2:
            height_coef = 0.92
        elif 3 <= total_floors <= 5:
            height_coef = 1.10
        elif 6 <= total_floors <= 9:
            height_coef = 1.06
        else:
            height_coef = 1.14
        
        return (floor_num_coef * 0.5 + position_coef * 0.3 + height_coef * 0.2)
    
    def calculate(self, params: ApartmentParams) -> Dict[str, float]:
        if params.area <= 0:
            raise ValueError("Площадь должна быть положительной")
        
        base_price = self.BASE_PRICE_PER_M2 * params.area
        
        district_coef = self.COEF_DISTRICT.get(params.district.lower(), 1.0)
        
        year_category = self._get_year_category(params.build_year)
        year_coef = self.COEF_BUILD_YEAR.get(year_category, 1.0)
        
        repair_coef = self.COEF_REPAIR.get(params.repair.lower(), 1.0)
        
        house_type_coef = self.COEF_HOUSE_TYPE.get(params.house_type.lower(), 1.0)
        
        floor_coef = self._calculate_floor_coefficient(params.floor, params.total_floors)
        
        infra_coef = 1.0
        for infra in params.infrastructure:
            if infra in self.COEF_INFRASTRUCTURE:
                infra_coef += self.COEF_INFRASTRUCTURE[infra]
        
        balcony_coef = 1.06 if params.has_balcony else 1.0
        heating_coef = self.COEF_HEATING.get(params.heating.lower(), 1.0)
        view_coef = self.COEF_VIEW.get(params.view.lower(), 1.0)
        
        total_coefficient = (
            district_coef *
            year_coef *
            repair_coef *
            house_type_coef *
            floor_coef *
            infra_coef *
            balcony_coef *
            heating_coef *
            view_coef *
            self.season_coef
        )
        
        if params.urgency:
            total_coefficient *= 0.90
        
        final_price = base_price * total_coefficient
        price_per_m2 = final_price / params.area
        
        return {
            "price_total": round(final_price, 2),
            "price_per_m2": round(price_per_m2, 2),
            "base_price": round(base_price, 2),
            "total_coefficient": round(total_coefficient, 3),
            "price_breakdown": {
                "district": round(district_coef, 3),
                "year": round(year_coef, 3),
                "repair": round(repair_coef, 3),
                "house_type": round(house_type_coef, 3),
                "floor": round(floor_coef, 3),
                "infrastructure": round(infra_coef, 3),
                "balcony": round(balcony_coef, 3),
                "heating": round(heating_coef, 3),
                "view": round(view_coef, 3),
                "season": round(self.season_coef, 3)
            }
        }

# ========== TELEGRAM БОТ ==========
# Получаем токен из переменных окружения (Render добавит)
TOKEN = os.getenv('7983712081:AAHhDZcFrKCFcXPcdFDg6PM_Rpl5mhAxPOE')
if not TOKEN:
    print("ОШИБКА: Токен не найден!")
    print("Добавьте переменную 7983712081:AAHhDZcFrKCFcXPcdFDg6PM_Rpl5mhAxPOE в Render")
    print("Текущие переменные окружения:", os.environ.keys())
    exit(1)

bot = telebot.TeleBot(TOKEN)
calculator = PriceCalculator()

# Словарь для хранения состояний пользователей
user_states = {}

# ========== КОМАНДЫ БОТА ==========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = ""
 *ОЦЕНЩИК НЕДВИЖИМОСТИ*

Я помогу оценить стоимость квартиры в вашем городе на основе:
• Района
• Площади
• Года постройки
• Типа дома
• Ремонта
• Этажа
• Инфраструктуры

*Доступные команды:*
/start - приветственное сообщение
/calculate - начать расчет
/help - справка по использованию
/example - пример расчета
/districts - список районов
/infra - список инфраструктуры

*Для расчета используйте команду /calculate*
""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = ""
 *КАК ПОЛЬЗОВАТЬСЯ БОТОМ:*

1. Начните с команды /calculate
2. Будет предложено ввести параметры в формате JSON
3. Пример формата:
```json
{
  "area": 45.0,
  "district": "центр",
  "build_year": 2018,
  "house_type": "монолитный",
  "repair": "евро",
  "floor": 5,
  "total_floors": 10,
  "has_balcony": true,
  "heating": "индивид_газ",
  "infrastructure": ["море_шаг", "школа_шаг"],
  "view": "на море",
  "urgency": false
}

  




