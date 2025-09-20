import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from ..services.applogger import Logger
from ..base.utils import Utils
from .submodules.cic_model import ConfigurableIntentClassifier


class MLCICInitializer:
    """
    Класс-инициализатор для ML модели классификации намерений.
    
    Принимает все параметры напрямую и:
    - Загружает настройки из settings.json
    - Загружает датасет из dataset.json
    - Проверяет наличие обученной модели
    - Обучает модель если нужно или загружает готовую
    - Предоставляет готовый к работе интерфейс
    
    Example:
        >>> initializer = MLCICInitializer(
        ...     logger=logger,
        ...     model_path="src/core/ml/assets/cic_model_v1.pkl",
        ...     settings_path="src/core/ml/assets/settings.json",
        ...     dataset_path="src/core/ml/assets/dataset.json"
        ... )
        >>> model_interface = await initializer.initialize()
        >>> 
        >>> # Теперь можно использовать
        >>> result = await model_interface.predict("Создай КС на канцтовары")
        >>> print(result['intent_name'])  # "Создание КС"
    """
    
    def __init__(self, 
                 logger: Optional[Logger] = None,
                 model_path: str = None,
                 settings_path: str = None,
                 dataset_path: str = None,
                 **kwargs):
        """
        Инициализация класса
        
        Args:
            logger (Logger): Логгер для записи событий
            model_path (str): Путь к файлу модели
            settings_path (str): Путь к файлу настроек
            dataset_path (str): Путь к файлу датасета
        """
        self.logger = logger or Logger('ml-cic-init')
        self.model_path = model_path
        self.settings_path = settings_path
        self.dataset_path = dataset_path
        self.model: Optional[ConfigurableIntentClassifier] = None
        self.model_interface: Optional['MLModelInterface'] = None
        self.is_initialized = False
        
        Utils.writelog(
            logger=self.logger,
            level="DEBUG",
            message=f"{self.__class__.__name__} создан"
        )
    
    async def initialize(self) -> 'MLModelInterface':
        """
        Полная инициализация ML модели
        
        Returns:
            MLModelInterface: Готовый к работе интерфейс модели
            
        Raises:
            ValueError: Если не удалось загрузить конфигурацию или датасет
            FileNotFoundError: Если не найдены необходимые файлы
        """
        try:
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message="Начало инициализации ML модели"
            )
            
            # 1. Загружаем настройки модели
            settings = await self._load_settings(self.settings_path)
            
            # 2. Загружаем датасет
            dataset = await self._load_dataset(self.dataset_path)
            
            # 3. Создаем модель с настройками
            self.model = await self._create_model(settings, self.model_path)
            
            # 4. Проверяем наличие обученной модели или обучаем новую
            await self._ensure_model_trained(dataset)
            
            # 5. Создаем интерфейс для работы с моделью
            self.model_interface = MLModelInterface(self.model, self.logger)
            
            self.is_initialized = True
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message="ML модель успешно инициализирована и готова к работе"
            )
            
            return self.model_interface
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка инициализации ML модели: {e}"
            )
            raise
    
    
    async def _load_settings(self, settings_path: str) -> Dict[str, Any]:
        """Загружает настройки модели из JSON файла"""
        try:
            full_path = Path(settings_path)
            if not full_path.exists():
                raise FileNotFoundError(f"Файл настроек не найден: {settings_path}")
            
            with open(full_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Валидация обязательных полей
            required_fields = ['procurement_intents']
            for field in required_fields:
                if field not in settings:
                    raise ValueError(f"Отсутствует обязательное поле в настройках: {field}")
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Настройки загружены из {settings_path}: {len(settings['procurement_intents'])} намерений"
            )
            
            return settings
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка загрузки настроек из {settings_path}: {e}"
            )
            raise
    
    async def _load_dataset(self, dataset_path: str) -> List[Tuple[str, str]]:
        """Загружает датасет из JSON файла"""
        try:
            full_path = Path(dataset_path)
            if not full_path.exists():
                raise FileNotFoundError(f"Файл датасета не найден: {dataset_path}")
            
            with open(full_path, 'r', encoding='utf-8') as f:
                dataset_json = json.load(f)
            
            # Проверяем, что это список кортежей [["text", "intent"], ...]
            if not isinstance(dataset_json, list):
                raise ValueError("Датасет должен быть массивом кортежей [['text', 'intent'], ...]")
            
            # Конвертируем в формат для обучения
            training_data = []
            for item in dataset_json:
                if not isinstance(item, list) or len(item) != 2:
                    continue
                text, intent = item
                if isinstance(text, str) and isinstance(intent, str):
                    training_data.append((text, intent))
            
            if len(training_data) < 2:
                raise ValueError("Недостаточно данных для обучения (минимум 2 примера)")
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Датасет загружен из {dataset_path}: {len(training_data)} примеров"
            )
            
            return training_data
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка загрузки датасета из {dataset_path}: {e}"
            )
            raise
    
    async def _create_model(self, settings: Dict[str, Any], model_path: str) -> ConfigurableIntentClassifier:
        """Создает модель с настройками из конфига"""
        try:
            model = ConfigurableIntentClassifier(
                logger=self.logger,
                model_path=model_path,
                intent_mapping=settings['procurement_intents'],
                correction_dictionary=settings.get('correction_dict', []),
                entity_patterns=settings.get('entity_patterns', {}),
                model_config=settings.get('ml_config', {}),
                levenshtein_threshold=settings.get('levenshtein_threshold', 0.6)
            )
            
            await model.initialize()
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message="Модель создана и инициализирована"
            )
            
            return model
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка создания модели: {e}"
            )
            raise
    
    async def _ensure_model_trained(self, training_data: List[Tuple[str, str]]) -> None:
        """Проверяет наличие обученной модели или обучает новую"""
        try:
            # Пытаемся загрузить существующую модель
            try:
                await self.model.load_model_async()
                
                Utils.writelog(
                    logger=self.logger,
                    level="INFO",
                    message="Обученная модель найдена и загружена"
                )
                return
                
            except (FileNotFoundError, Exception) as e:
                Utils.writelog(
                    logger=self.logger,
                    level="WARNING",
                    message=f"Обученная модель не найдена или повреждена: {e}. Начинаем обучение новой модели"
                )
            
            # Обучаем новую модель
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message="Начинаем обучение новой модели..."
            )
            
            results = await self.model.train_async(training_data)
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Модель обучена успешно. Точность: {results['train_accuracy']:.3f}"
            )
            
            # Сохраняем обученную модель
            await self.model.save_model_async()
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message="Обученная модель сохранена"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка при обеспечении обученной модели: {e}"
            )
            raise
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Возвращает статистику модели"""
        if not self.is_initialized or not self.model:
            return {'initialized': False}
        
        return {
            'initialized': True,
            'model_trained': self.model.is_trained,
            'intents_count': len(self.model.intent_mapping),
            'correction_dict_size': len(self.model.correction_dictionary),
            'entity_patterns_count': len(self.model.entity_patterns)
        }


class MLModelInterface:
    """
    Интерфейс для работы с обученной ML моделью.
    
    Предоставляет простые методы для предсказания намерений
    без необходимости знать внутреннее устройство модели.
    """
    
    def __init__(self, model: ConfigurableIntentClassifier, logger: Logger):
        self.model = model
        self.logger = logger
        
        Utils.writelog(
            logger=self.logger,
            level="DEBUG",
            message="MLModelInterface создан"
        )
    
    async def predict(self, text: str, detailed: bool = False) -> Dict[str, Any]:
        """
        Предсказание намерения для текста
        
        Args:
            text (str): Текст для анализа
            detailed (bool): Возвращать ли детальную информацию
            
        Returns:
            Dict[str, Any]: Результат предсказания
            
        Example:
            >>> result = await interface.predict("Создай КС на канцтовары")
            >>> print(result['intent_name'])  # "Создание КС"
        """
        try:
            # Валидация входного текста
            clean_text = Utils.validate_search_query(text, logger=self.logger)
            
            # Конфигурация анализа
            analysis_config = None
            if detailed:
                analysis_config = {
                    'return_probabilities': True,
                    'extract_entities': True,
                    'confidence_threshold': 0.5,
                    'top_predictions': 3
                }
            
            # Предсказание
            result = await self.model.predict_async(
                clean_text, 
                return_probabilities=detailed, 
                analysis_config=analysis_config
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Предсказание выполнено для '{text}': {result['intent']} ({result['confidence']:.3f})"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка предсказания для '{text}': {e}"
            )
            raise
    
    async def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Пакетное предсказание для списка текстов
        
        Args:
            texts (List[str]): Список текстов для анализа
            
        Returns:
            List[Dict[str, Any]]: Список результатов предсказания
        """
        try:
            results = []
            for text in texts:
                result = await self.predict(text)
                results.append(result)
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Пакетное предсказание выполнено для {len(texts)} текстов"
            )
            
            return results
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка пакетного предсказания: {e}"
            )
            raise
    
    def get_available_intents(self) -> Dict[str, str]:
        """Возвращает доступные намерения"""
        return self.model.intent_mapping.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Возвращает информацию о модели"""
        return {
            'is_trained': self.model.is_trained,
            'intents': list(self.model.intent_mapping.keys()),
            'intent_names': list(self.model.intent_mapping.values()),
            'correction_dictionary_size': len(self.model.correction_dictionary),
            'entity_patterns': list(self.model.entity_patterns.keys())
        }
    
    async def retrain(self, new_training_data: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Переобучение модели на новых данных
        
        Args:
            new_training_data (List[Tuple[str, str]]): Новые тренировочные данные
            
        Returns:
            Dict[str, Any]: Результаты переобучения
        """
        try:
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Начинается переобучение модели на {len(new_training_data)} примерах"
            )
            
            results = await self.model.train_async(new_training_data)
            
            # Сохраняем переобученную модель
            await self.model.save_model_async()
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Модель переобучена успешно. Точность: {results['train_accuracy']:.3f}"
            )
            
            return results
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка переобучения модели: {e}"
            )
            raise
