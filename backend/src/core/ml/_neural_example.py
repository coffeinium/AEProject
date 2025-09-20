"""
Простой пример для тестирования AsyncMLModel
"""

import asyncio
from src.core.ml import AsyncMLModel
from src.core.services.applogger import Logger


async def test_ml_model():
    """Простой тест ML модели"""
    
    print("=== Тестирование AsyncMLModel ===\n")
    
    # Инициализация логгера
    logger = Logger('test-ml')
    
    # Настройка намерений (ОБЯЗАТЕЛЬНО)
    intents = {
        'create_ks': 'Создание КС',
        'search_contract': 'Поиск контрактов',
        'search_supplier': 'Поиск поставщиков',
        'help': 'Помощь'
    }
    
    # Словарь для исправления опечаток (ОПЦИОНАЛЬНО)
    corrections = [
        'создай', 'создать', 'сделай',
        'найди', 'найти', 'поиск', 'покажи',
        'кс', 'котировочная', 'котировка',
        'контракт', 'договор', 'соглашение',
        'поставщик', 'подрядчик',
        'помощь', 'справка'
    ]
    
    # Паттерны для сущностей (ОПЦИОНАЛЬНО)
    entities = {
        'amount': [
            r'(\d+(?:\.\d+)?)\s*(?:тыс|руб|рублей|тысяч)',
            r'(\d+)\s*к'
        ],
        'product': [
            r'на\s+([а-яё\s]+?)(?:\s+на|\s*$)',
            r'по\s+([а-яё\s]+?)(?:\s|$)'
        ]
    }
    
    # Создание модели
    print("1. Создание модели...")
    model = AsyncMLModel(
        logger=logger,
        intent_mapping=intents,
        correction_dictionary=corrections,
        entity_patterns=entities
    )
    
    await model.initialize()
    print("   ✓ Модель создана\n")
    
    # Тренировочные данные
    print("2. Подготовка данных...")
    training_data = [
        # Создание КС
        ("Создай КС на канцтовары", "create_ks"),
        ("Сделай котировочную сессию на мебель", "create_ks"),
        ("Новая КС на 500 тыс", "create_ks"),
        
        # Поиск контрактов
        ("Найди контракты с Газпромом", "search_contract"),
        ("Покажи договоры за 2024", "search_contract"),
        ("Поиск соглашений", "search_contract"),
        
        # Поиск поставщиков
        ("Найди поставщиков канцтоваров", "search_supplier"),
        ("Покажи подрядчиков", "search_supplier"),
        ("Поиск исполнителей", "search_supplier"),
        
        # Помощь
        ("Как создать КС", "help"),
        ("Помощь по системе", "help"),
        ("Справка", "help")
    ]
    
    print(f"   ✓ Подготовлено {len(training_data)} примеров\n")
    
    # Обучение
    print("3. Обучение модели...")
    try:
        results = await model.train_async(training_data)
        print(f"   ✓ Модель обучена")
        print(f"   ✓ Точность: {results['train_accuracy']:.3f}")
        print(f"   ✓ Примеров: {results['training_size']}")
        print(f"   ✓ Классов: {results['unique_intents']}\n")
    except Exception as e:
        print(f"   ✗ Ошибка обучения: {e}")
        return
    
    # Тестирование
    print("4. Тестирование предсказаний...")
    test_cases = [
        "Создай КС на канцелярские товары 300 тыс",
        "найди контракт с роснефтью",  # без заглавных
        "покажи поставщиков мебели",
        "создй кс на канцтовары",      # с опечаткой
        "помощь"
    ]
    
    for i, query in enumerate(test_cases, 1):
        try:
            result = await model.predict_async(
                query,
                analysis_config={
                    'extract_entities': True,
                    'return_probabilities': True
                }
            )
            
            print(f"\n   Тест {i}: '{query}'")
            print(f"   → Намерение: {result['intent_name']}")
            print(f"   → Уверенность: {result['confidence']:.3f}")
            
            if result['entities']:
                print(f"   → Сущности: {result['entities']}")
                
        except Exception as e:
            print(f"   ✗ Ошибка для '{query}': {e}")
    
    print("\n=== Тест завершен ===")


if __name__ == "__main__":
    asyncio.run(test_ml_model())
