import asyncio
import pickle
import json
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from ...services.applogger import Logger
from ...base.utils import Utils
from .levenshtein import LevenshteinCalculator


class ConfigurableIntentClassifier:
    """
    Гибкая асинхронная ML модель для классификации намерений с расширенными возможностями конфигурации.
    
    Основные возможности:
    - Полностью конфигурируемые намерения и словари
    - Гибкая система извлечения сущностей
    - Продвинутая предобработка текста
    - Асинхронное обучение и предсказание
    - Система валидации и метрик
    - Автоматическое исправление опечаток
    
    Пример базового использования:
        >>> # Обязательная конфигурация намерений
        >>> intents = {
        ...     'create_ks': 'Создание КС',
        ...     'search_contract': 'Поиск контрактов'
        ... }
        >>> model = ConfigurableIntentClassifier(logger=logger, intent_mapping=intents)
        >>> await model.initialize()
        >>> 
        >>> # Простое обучение
        >>> training_data = [
        ...     ("Создай КС на канцтовары", "create_ks"),
        ...     ("Найди контракты", "search_contract")
        ... ]
        >>> await model.train_async(training_data)
        >>> result = await model.predict_async("Создай котировку")
    
    Пример продвинутого использования:
        >>> # Кастомная конфигурация
        >>> custom_intents = {
        ...     'create_tender': 'Создание тендера',
        ...     'search_docs': 'Поиск документов',
        ...     'approve_contract': 'Утверждение контракта'
        ... }
        >>> 
        >>> custom_dictionary = ['тендер', 'документ', 'утверждение', 'контракт']
        >>> 
        >>> custom_entities = {
        ...     'amount': [r'(\d+(?:\.\d+)?)\s*(?:тыс|руб|рублей)', r'(\d+)к'],
        ...     'document_type': [r'(тендер|договор|контракт)', r'(документ|файл)'],
        ...     'deadline': [r'до\s+(\d{1,2}\.\d{1,2}\.\d{4})']
        ... }
        >>> 
        >>> model = ConfigurableIntentClassifier(
        ...     logger=logger,
        ...     intent_mapping=custom_intents,
        ...     correction_dictionary=custom_dictionary,
        ...     entity_patterns=custom_entities,
        ...     model_config={
        ...         'tfidf_max_features': 5000,
        ...         'ngram_range': (1, 4),
        ...         'test_size': 0.15
        ...     }
        ... )
        >>> 
        >>> # Обучение с продвинутыми параметрами
        >>> training_data = [
        ...     ("Создай тендер на поставку оборудования на 500 тыс", "create_tender"),
        ...     ("Найди документы по контракту до 15.12.2024", "search_docs"),
        ...     ("Утверди договор с ООО Поставщик", "approve_contract")
        ... ]
        >>> 
        >>> results = await model.train_async(
        ...     training_data=training_data,
        ...     validation_config={
        ...         'cross_validation': True,
        ...         'cv_folds': 5,
        ...         'stratify': True
        ...     }
        ... )
        >>> 
        >>> # Предсказание с детальным анализом
        >>> result = await model.predict_async(
        ...     "Создай тендр на оборудование 300к до 20.11.2024",
        ...     analysis_config={
        ...         'return_probabilities': True,
        ...         'extract_entities': True,
        ...         'correct_typos': True,
        ...         'confidence_threshold': 0.7
        ...     }
        ... )
    
    Пример интеграции с датасетом:
        >>> # Загрузка из различных источников
        >>> dataset_config = {
        ...     'source_type': 'pandas',  # 'pandas', 'json', 'csv', 'excel'
        ...     'text_column': 'query_text',
        ...     'label_column': 'intent_label',
        ...     'preprocessing': {
        ...         'lowercase': True,
        ...         'remove_punctuation': False,
        ...         'correct_typos': True
        ...     }
        ... }
        >>> 
        >>> # Из DataFrame
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'query_text': ['Создай КС', 'Найди договор'],
        ...     'intent_label': ['create_ks', 'search_contract']
        ... })
        >>> await model.train_from_dataset(df, dataset_config)
        >>> 
        >>> # Из JSON файла
        >>> dataset_config['source_type'] = 'json'
        >>> await model.train_from_file('training_data.json', dataset_config)
    """
    
    def __init__(self, 
                 logger: Optional[Logger] = None,
                 model_path: Optional[str] = None,
                 intent_mapping: Optional[Dict[str, str]] = None,
                 correction_dictionary: Optional[List[str]] = None,
                 entity_patterns: Optional[Dict[str, List[str]]] = None,
                 model_config: Optional[Dict[str, Any]] = None,
                 levenshtein_threshold: float = 0.6):
        """
        Инициализация гибкой асинхронной ML модели
        
        Args:
            logger (Optional[Logger]): Логгер для записи операций
            model_path (Optional[str]): Путь для сохранения/загрузки модели
            intent_mapping (Optional[Dict[str, str]]): Маппинг намерений {intent_id: human_name}
            correction_dictionary (Optional[List[str]]): Словарь для исправления опечаток
            entity_patterns (Optional[Dict[str, List[str]]]): Паттерны для извлечения сущностей
            model_config (Optional[Dict[str, Any]]): Конфигурация модели ML
            levenshtein_threshold (float): Порог для алгоритма Левенштейна
        """
        self.logger = logger
        self.model_path = model_path or "models/intent_classifier.pkl"
        self.pipeline = None
        self.is_trained = False
        self.training_history = []
        self.model_metadata = {}
        
        # Инициализируем калькулятор Левенштейна
        self.levenshtein_calc = LevenshteinCalculator(
            logger=logger, 
            threshold=levenshtein_threshold
        )
        
        # Полностью конфигурируемые компоненты (без базовых значений)
        self.intent_mapping = intent_mapping or {}
        self.correction_dictionary = correction_dictionary or []
        self.entity_patterns = entity_patterns or {}
        
        # Конфигурация ML модели
        self.model_config = self._merge_model_config(model_config or {})
        
        Utils.writelog(
            logger=self.logger,
            level="DEBUG",
            message=f"{self.__class__.__name__} инициализирован: намерений={len(self.intent_mapping)}, "
                   f"словарь={len(self.correction_dictionary)}, сущностей={len(self.entity_patterns)}"
        )
    
    async def initialize(self) -> None:
        """
        Асинхронная инициализация модели
        
        Пытается загрузить существующую модель, если она есть
        """
        try:
            await self.load_model_async()
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message="Модель успешно загружена при инициализации"
            )
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="WARNING",
                message=f"Не удалось загрузить модель при инициализации: {e}"
            )
    
    
    def _merge_model_config(self, custom_config: Dict[str, Any]) -> Dict[str, Any]:
        """Объединяет пользовательскую конфигурацию с базовой"""
        default_config = {
            'tfidf_max_features': 2000,
            'ngram_range': (1, 3),
            'min_df': 1,
            'max_df': 0.8,
            'lr_random_state': 42,
            'lr_max_iter': 2000,
            'lr_c': 10.0,
            'lr_class_weight': 'balanced',
            'test_size': 0.2,
            'random_state': 42
        }
        
        # Объединяем конфигурации
        merged_config = default_config.copy()
        merged_config.update(custom_config)
        
        return merged_config
    
    async def preprocess_text_async(self, text: str) -> str:
        """
        Продвинутая асинхронная предобработка текста с множественными нормализациями
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Обработанный текст
        """
        try:
            # Валидация входных данных
            sanitized_text = Utils.sanitize_input(
                text=text,
                max_length=1000,
                allow_special_chars=False,
                logger=self.logger
            )
            
            # Приводим к нижнему регистру
            processed_text = sanitized_text.lower()
            
            # Исправляем опечатки асинхронно
            corrected_text = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._correct_typos_sync, 
                processed_text
            )
            
            # Продвинутая нормализация
            normalized_text = await asyncio.get_event_loop().run_in_executor(
                None,
                self._advanced_normalize_sync,
                corrected_text
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Текст обработан: '{text}' -> '{normalized_text}'"
            )
            
            return normalized_text
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка предобработки текста: {e}"
            )
            raise
    
    def _correct_typos_sync(self, text: str) -> str:
        """Синхронное исправление опечаток для выполнения в executor"""
        if not self.correction_dictionary:
            # Если словарь пустой, возвращаем текст как есть
            return text
        
        result = self.levenshtein_calc.correct_text(
            text=text,
            dictionary=self.correction_dictionary,
            case_sensitive=False
        )
        return result['corrected_text']
    
    def _advanced_normalize_sync(self, text: str) -> str:
        """
        Продвинутая синхронная нормализация текста
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Нормализованный текст
        """
        try:
            normalized = text
            
            # Нормализация сумм и денежных значений
            normalized = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:тыс\.?|тысяч|к)', r'\1 тысяч', normalized)
            normalized = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:млн\.?|миллионов?)', r'\1 млн', normalized)
            normalized = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:руб\.?|рублей)', r'\1 рублей', normalized)
            
            # Нормализация форм организаций
            normalized = re.sub(r'\bооо\b', 'ООО', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bао\b', 'АО', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bпао\b', 'ПАО', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bзао\b', 'ЗАО', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bип\b', 'ИП', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bгуп\b', 'ГУП', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bмуп\b', 'МУП', normalized, flags=re.IGNORECASE)
            
            # Нормализация ключевых терминов
            normalized = re.sub(r'\bкс\b', 'КС', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bинн\b', 'ИНН', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bбик\b', 'БИК', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bit\b', 'IT', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'\bид\b', 'ID', normalized, flags=re.IGNORECASE)
            
            # Нормализация действий
            normalized = re.sub(r'\b(?:создай|создать|сделай|оформи|оформить)\b', 'создать', normalized)
            normalized = re.sub(r'\b(?:найди|найти|покажи|показать|поиск)\b', 'найти', normalized)
            normalized = re.sub(r'\b(?:требуется|нужен|нужна|необходим|необходимо)\b', 'нужен', normalized)
            
            # Нормализация типов документов
            normalized = re.sub(r'\b(?:контракт|договор|соглашение)\b', 'контракт', normalized)
            normalized = re.sub(r'\b(?:котировк[ауые]?|котировочн[ауые]?\s*сесси[яие])\b', 'котировка', normalized)
            
            # Нормализация категорий
            normalized = re.sub(r'\b(?:канцтовары|канцелярские\s*товары)\b', 'канцтовары', normalized)
            normalized = re.sub(r'\b(?:продукты\s*питания)\b', 'продукты', normalized)
            normalized = re.sub(r'\b(?:консультаци[ие])\b', 'консультации', normalized)
            
            # Стандартизация пробелов и знаков препинания
            normalized = re.sub(r'[,;:]\s*', ' ', normalized)  # Убираем знаки препинания
            normalized = re.sub(r'\s+', ' ', normalized)  # Множественные пробелы в один
            normalized = normalized.strip()
            
            # Замена числовых значений на стандартные токены для лучшего обобщения
            normalized = re.sub(r'\b\d{4,}\b', 'NUMBER', normalized)  # Большие числа
            normalized = re.sub(r'\b\d{1,3}(?:[.,]\d+)?\s*(?:тысяч|млн|рублей|к)\b', 'AMOUNT', normalized)  # Суммы
            
            return normalized
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка продвинутой нормализации: {e}"
            )
            return text
    
    async def train_async(self, 
                         training_data: List[Tuple[str, str]], 
                         test_size: Optional[float] = None,
                         validation_split: bool = True,
                         validation_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Асинхронное обучение модели с расширенными возможностями
        
        Args:
            training_data (List[Tuple[str, str]]): Список кортежей (текст, намерение)
            test_size (Optional[float]): Размер тестовой выборки. Если None, используется из model_config
            validation_split (bool): Разделять ли данные на тренировочную/тестовую выборки
            validation_config (Optional[Dict[str, Any]]): Конфигурация валидации
                - cross_validation (bool): Использовать кросс-валидацию
                - cv_folds (int): Количество фолдов для кросс-валидации
                - stratify (bool): Стратифицированное разделение
                - shuffle (bool): Перемешивать данные
            
        Returns:
            Dict[str, Any]: Результаты обучения с метриками
            
        Example:
            >>> data = [("Создай КС", "create_ks"), ("Найди контракт", "search_contract")]
            >>> results = await model.train_async(
            ...     data, 
            ...     validation_config={'cross_validation': True, 'cv_folds': 5}
            ... )
        """
        try:
            # Валидация конфигурации модели
            if not self.intent_mapping:
                raise ValueError("intent_mapping не может быть пустым. Определите намерения для классификации")
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Начало обучения модели на {len(training_data)} примерах"
            )
            
            # Валидация данных
            if not training_data or len(training_data) < 2:
                raise ValueError("Недостаточно данных для обучения (минимум 2 примера)")
            
            # Проверка, что все намерения из данных есть в маппинге
            data_intents = set(intent for _, intent in training_data)
            missing_intents = data_intents - set(self.intent_mapping.keys())
            if missing_intents:
                raise ValueError(f"Намерения отсутствуют в intent_mapping: {missing_intents}")
            
            # Создаем DataFrame
            df = pd.DataFrame(training_data, columns=['text', 'intent'])
            
            # Предобработка текстов асинхронно
            processed_texts = []
            for text in df['text']:
                processed_text = await self.preprocess_text_async(text)
                processed_texts.append(processed_text)
            
            df['text_processed'] = processed_texts
            
            # Разделение данных
            if validation_split and len(df) >= 4:
                X_train, X_test, y_train, y_test = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: train_test_split(
                        df['text_processed'], 
                        df['intent'], 
                        test_size=test_size, 
                        random_state=42,
                        stratify=df['intent'] if len(df['intent'].unique()) > 1 else None
                    )
                )
            else:
                X_train, y_train = df['text_processed'], df['intent']
                X_test, y_test = None, None
            
            # Создание и обучение pipeline асинхронно
            self.pipeline = await asyncio.get_event_loop().run_in_executor(
                None,
                self._create_and_train_pipeline,
                X_train,
                y_train
            )
            
            # Оценка модели
            train_accuracy = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: accuracy_score(y_train, self.pipeline.predict(X_train))
            )
            
            test_accuracy = None
            if X_test is not None:
                test_accuracy = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: accuracy_score(y_test, self.pipeline.predict(X_test))
                )
            
            # Сохранение истории обучения
            training_record = {
                'timestamp': datetime.now().isoformat(),
                'training_size': len(X_train),
                'test_size': len(X_test) if X_test is not None else 0,
                'train_accuracy': float(train_accuracy),
                'test_accuracy': float(test_accuracy) if test_accuracy else None,
                'unique_intents': len(df['intent'].unique())
            }
            
            self.training_history.append(training_record)
            self.is_trained = True
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Модель обучена успешно. Точность на тренировочной выборке: {train_accuracy:.3f}"
                       f"{f', на тестовой: {test_accuracy:.3f}' if test_accuracy else ''}"
            )
            
            return training_record
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обучения модели: {e}"
            )
            raise
    
    def _create_and_train_pipeline(self, X_train, y_train) -> Pipeline:
        """Создание и обучение optimized pipeline с расширенной конфигурацией"""
        config = self.model_config
        
        # Преобразуем ngram_range из списка в кортеж если нужно
        ngram_range = config['ngram_range']
        if isinstance(ngram_range, list):
            ngram_range = tuple(ngram_range)
        
        # Создаем TfidfVectorizer с расширенными параметрами
        tfidf_params = {
            'max_features': config['tfidf_max_features'],
            'ngram_range': ngram_range,
            'stop_words': None,
            'lowercase': True,
            'min_df': config['min_df'],
            'max_df': config['max_df']
        }
        
        # Добавляем дополнительные параметры если они есть в конфигурации
        if 'use_sublinear_tf' in config:
            tfidf_params['sublinear_tf'] = config['use_sublinear_tf']
        if 'use_idf' in config:
            tfidf_params['use_idf'] = config['use_idf']
        if 'smooth_idf' in config:
            tfidf_params['smooth_idf'] = config['smooth_idf']
        if 'norm' in config:
            tfidf_params['norm'] = config['norm']
        
        # Создаем LogisticRegression с расширенными параметрами
        lr_params = {
            'random_state': config['lr_random_state'],
            'max_iter': config['lr_max_iter'],
            'C': config['lr_c'],
            'class_weight': config['lr_class_weight']
        }
        
        # Добавляем solver если указан
        if 'lr_solver' in config:
            lr_params['solver'] = config['lr_solver']
        
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(**tfidf_params)),
            ('classifier', LogisticRegression(**lr_params))
        ])
        
        Utils.writelog(
            logger=self.logger,
            level="INFO",
            message=f"Pipeline создан с параметрами: TF-IDF features={config['tfidf_max_features']}, "
                   f"n-grams={ngram_range}, C={config['lr_c']}"
        )
        
        pipeline.fit(X_train, y_train)
        return pipeline
    
    async def predict_async(self, 
                           text: str, 
                           return_probabilities: bool = False,
                           analysis_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Асинхронное предсказание намерения с расширенным анализом
        
        Args:
            text (str): Текст для классификации
            return_probabilities (bool): Возвращать ли вероятности для всех классов
            analysis_config (Optional[Dict[str, Any]]): Конфигурация анализа
                - return_probabilities (bool): Возвращать вероятности
                - extract_entities (bool): Извлекать сущности
                - correct_typos (bool): Исправлять опечатки
                - confidence_threshold (float): Минимальный порог уверенности
                - top_predictions (int): Количество топ предсказаний
            
        Returns:
            Dict[str, Any]: Результат предсказания с дополнительным анализом
            
        Example:
            >>> # Простое предсказание
            >>> result = await model.predict_async("Создай КС на канцтовары")
            >>> 
            >>> # Детальный анализ
            >>> result = await model.predict_async(
            ...     "создй кс на канцтовары 500к",
            ...     analysis_config={
            ...         'return_probabilities': True,
            ...         'extract_entities': True,
            ...         'confidence_threshold': 0.7,
            ...         'top_predictions': 3
            ...     }
            ... )
        """
        try:
            if not self.is_trained or not self.pipeline:
                raise ValueError("Модель не обучена. Запустите train_async() сначала")
            
            # Предобработка текста
            processed_text = await self.preprocess_text_async(text)
            
            # Предсказание асинхронно
            intent, probabilities = await asyncio.get_event_loop().run_in_executor(
                None,
                self._predict_sync,
                processed_text
            )
            
            confidence = float(np.max(probabilities))
            
            # Извлечение сущностей
            entities = await self.extract_entities_async(text, intent)
            
            result = {
                'original_text': text,
                'processed_text': processed_text,
                'intent': intent,
                'intent_name': self.intent_mapping.get(intent, intent),
                'confidence': confidence,
                'entities': entities,
                'timestamp': datetime.now().isoformat()
            }
            
            if return_probabilities:
                classes = self.pipeline.classes_
                prob_dict = {
                    classes[i]: float(probabilities[i]) 
                    for i in range(len(classes))
                }
                result['all_probabilities'] = prob_dict
                
                # Топ-3 предсказания
                top_indices = np.argsort(probabilities)[::-1][:3]
                result['top_predictions'] = [
                    {
                        'intent': classes[i],
                        'intent_name': self.intent_mapping.get(classes[i], classes[i]),
                        'probability': float(probabilities[i])
                    }
                    for i in top_indices
                ]
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Предсказание для '{text}': {intent} (уверенность: {confidence:.3f})"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка предсказания: {e}"
            )
            raise
    
    def _predict_sync(self, processed_text: str) -> Tuple[str, np.ndarray]:
        """Синхронное предсказание для выполнения в executor"""
        intent = self.pipeline.predict([processed_text])[0]
        probabilities = self.pipeline.predict_proba([processed_text])[0]
        return intent, probabilities
    
    async def extract_entities_async(self, text: str, intent: str) -> Dict[str, str]:
        """
        Асинхронное извлечение сущностей из текста
        
        Args:
            text (str): Исходный текст
            intent (str): Определенное намерение
            
        Returns:
            Dict[str, str]: Словарь извлеченных сущностей
        """
        try:
            entities = await asyncio.get_event_loop().run_in_executor(
                None,
                self._extract_entities_sync,
                text,
                intent
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Извлечены сущности: {entities}"
            )
            
            return entities
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка извлечения сущностей: {e}"
            )
            return {}
    
    def _extract_entities_sync(self, text: str, intent: str) -> Dict[str, str]:
        """Улучшенное синхронное извлечение сущностей с контекстной валидацией"""
        entities = {}
        
        # Если паттерны не настроены, возвращаем пустой словарь
        if not self.entity_patterns:
            return entities
        
        text_lower = text.lower()
        original_text = text
        
        # Проходим по всем типам сущностей с приоритетом
        entity_priority = ['customer_inn', 'inn', 'bik', 'amount', 'customer_name', 'company_name', 
                          'contract_name', 'ks_name', 'category', 'law', 'document_id', 'deadline', 'priority']
        
        # Сначала обрабатываем приоритетные сущности
        for entity_type in entity_priority:
            if entity_type in self.entity_patterns and entity_type not in entities:
                patterns = self.entity_patterns[entity_type]
                for pattern in patterns:
                    try:
                        # Выбираем подходящий текст для поиска
                        search_text = text_lower
                        if entity_type in ['company_name', 'customer_name', 'contract_name', 'ks_name']:
                            search_text = original_text  # Сохраняем регистр для названий
                        
                        match = re.search(pattern, search_text)
                        if match:
                            extracted_value = match.group(1).strip()
                            
                            # Валидация и нормализация по типам
                            if self._validate_entity(entity_type, extracted_value):
                                normalized_value = self._normalize_entity(entity_type, extracted_value)
                                entities[entity_type] = normalized_value
                                break  # Берем первое валидное значение для каждого типа
                                
                    except re.error as e:
                        Utils.writelog(
                            logger=self.logger,
                            level="WARNING",
                            message=f"Ошибка в регулярном выражении {pattern}: {e}"
                        )
                        continue
        
        # Обрабатываем остальные сущности
        for entity_type, patterns in self.entity_patterns.items():
            if entity_type not in entities and entity_type not in entity_priority:
                for pattern in patterns:
                    try:
                        search_text = text_lower if entity_type not in ['company_name', 'customer_name'] else original_text
                        match = re.search(pattern, search_text)
                        if match:
                            extracted_value = match.group(1).strip()
                            if self._validate_entity(entity_type, extracted_value):
                                normalized_value = self._normalize_entity(entity_type, extracted_value)
                                entities[entity_type] = normalized_value
                                break
                                
                    except re.error as e:
                        continue
        
        return entities
    
    def _validate_entity(self, entity_type: str, value: str) -> bool:
        """Валидация извлеченной сущности"""
        if not value or len(value.strip()) < 1:
            return False
        
        # Специфическая валидация по типам
        if entity_type in ['customer_inn', 'inn']:
            # ИНН должен быть 10 или 12 цифр
            return re.match(r'^\d{10}$|^\d{12}$', value.strip())
        
        elif entity_type == 'bik':
            # БИК должен быть 9 цифр
            return re.match(r'^\d{9}$', value.strip())
        
        elif entity_type == 'amount':
            # Проверяем, что это число
            try:
                float(value.replace(',', '.').replace(' ', ''))
                return True
            except ValueError:
                return False
        
        elif entity_type in ['customer_name', 'company_name']:
            # Название должно быть не слишком коротким и содержать разумные символы
            return len(value.strip()) >= 3 and not re.match(r'^\d+$', value.strip())
        
        elif entity_type in ['contract_name', 'ks_name']:
            # Название контракта/КС должно содержать осмысленные слова
            return len(value.strip()) >= 3 and not re.match(r'^\d+$', value.strip())
        
        elif entity_type == 'document_id':
            # ID документа должен быть числом
            return re.match(r'^\d+$', value.strip())
        
        elif entity_type == 'deadline':
            # Дата должна быть в формате дд.мм.гггг или дд/мм/гггг
            return re.match(r'^\d{1,2}[./]\d{1,2}[./]\d{2,4}$', value.strip())
        
        else:
            # Общая валидация - не пустое значение
            return len(value.strip()) >= 1
    
    def _normalize_entity(self, entity_type: str, value: str) -> str:
        """Нормализация извлеченной сущности"""
        normalized = value.strip()
        
        if entity_type == 'amount':
            # Нормализуем числовое значение
            try:
                normalized = normalized.replace(',', '.')
                number = float(normalized)
                # Если число целое, возвращаем без дробной части
                if number.is_integer():
                    return str(int(number))
                else:
                    return str(number)
            except ValueError:
                return normalized
        
        elif entity_type in ['customer_inn', 'inn', 'bik', 'document_id']:
            # Убираем все нецифровые символы
            return re.sub(r'\D', '', normalized)
        
        elif entity_type in ['customer_name', 'company_name', 'contract_name', 'ks_name']:
            # Нормализуем пробелы и кавычки
            normalized = re.sub(r'\s+', ' ', normalized)
            normalized = re.sub(r'["\']', '', normalized)
            return normalized.strip()
        
        elif entity_type == 'law':
            # Стандартизируем формат закона
            if 'фз' in normalized.lower():
                normalized = re.sub(r'[-\s]*фз', '-ФЗ', normalized, flags=re.IGNORECASE)
            return normalized.upper()
        
        elif entity_type == 'category':
            # Приводим к нижнему регистру
            return normalized.lower()
        
        else:
            return normalized
    
    async def save_model_async(self, filepath: Optional[str] = None) -> None:
        """
        Асинхронное сохранение модели
        
        Args:
            filepath (Optional[str]): Путь для сохранения. Если не указан, используется self.model_path
        """
        try:
            if not self.is_trained or not self.pipeline:
                raise ValueError("Нет обученной модели для сохранения")
            
            save_path = filepath or self.model_path
            
            # Создаем директорию если её нет
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Подготавливаем данные для сохранения
            model_data = {
                'pipeline': self.pipeline,
                'intent_mapping': self.intent_mapping,
                'correction_dictionary': self.correction_dictionary,
                'training_history': self.training_history,
                'is_trained': self.is_trained,
                'saved_at': datetime.now().isoformat()
            }
            
            # Сохраняем асинхронно
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._save_model_sync,
                model_data,
                save_path
            )
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Модель сохранена в {save_path}"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка сохранения модели: {e}"
            )
            raise
    
    def _save_model_sync(self, model_data: Dict, filepath: str) -> None:
        """Синхронное сохранение модели"""
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    async def load_model_async(self, filepath: Optional[str] = None) -> None:
        """
        Асинхронная загрузка модели
        
        Args:
            filepath (Optional[str]): Путь к файлу модели. Если не указан, используется self.model_path
        """
        try:
            load_path = filepath or self.model_path
            
            if not Path(load_path).exists():
                raise FileNotFoundError(f"Файл модели не найден: {load_path}")
            
            # Загружаем асинхронно
            model_data = await asyncio.get_event_loop().run_in_executor(
                None,
                self._load_model_sync,
                load_path
            )
            
            # Восстанавливаем состояние
            self.pipeline = model_data['pipeline']
            self.intent_mapping = model_data.get('intent_mapping', self.intent_mapping)
            self.correction_dictionary = model_data.get('correction_dictionary', self.correction_dictionary)
            self.training_history = model_data.get('training_history', [])
            self.is_trained = model_data.get('is_trained', True)
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Модель загружена из {load_path}"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка загрузки модели: {e}"
            )
            raise
    
    def _load_model_sync(self, filepath: str) -> Dict:
        """Синхронная загрузка модели"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    
    async def get_model_info_async(self) -> Dict[str, Any]:
        """
        Асинхронное получение информации о модели
        
        Returns:
            Dict[str, Any]: Информация о модели
        """
        try:
            info = {
                'is_trained': self.is_trained,
                'model_path': self.model_path,
                'training_history': self.training_history,
                'available_intents': list(self.intent_mapping.keys()),
                'correction_dictionary_size': len(self.correction_dictionary)
            }
            
            if self.is_trained and self.pipeline:
                # Получаем информацию о pipeline асинхронно
                pipeline_info = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._get_pipeline_info_sync
                )
                info.update(pipeline_info)
            
            return info
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения информации о модели: {e}"
            )
            raise
    
    def _get_pipeline_info_sync(self) -> Dict[str, Any]:
        """Синхронное получение информации о pipeline"""
        return {
            'classes': list(self.pipeline.classes_),
            'feature_count': self.pipeline['tfidf'].max_features,
            'ngram_range': self.pipeline['tfidf'].ngram_range
        }
    
    def update_correction_dictionary(self, new_words: List[str]) -> None:
        """
        Обновление словаря исправления опечаток
        
        Args:
            new_words (List[str]): Новые слова для добавления в словарь
        """
        try:
            old_size = len(self.correction_dictionary)
            self.correction_dictionary.extend(new_words)
            # Убираем дубликаты
            self.correction_dictionary = list(set(self.correction_dictionary))
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Словарь исправлений обновлен: {old_size} -> {len(self.correction_dictionary)} слов"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обновления словаря: {e}"
            )
            raise
    
    async def train_from_dataset(self, 
                                dataset: Union[pd.DataFrame, List[Dict], str], 
                                dataset_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обучение модели из различных источников данных
        
        Args:
            dataset (Union[pd.DataFrame, List[Dict], str]): Датасет или путь к файлу
            dataset_config (Dict[str, Any]): Конфигурация датасета
                - source_type (str): 'pandas', 'json', 'csv', 'excel'
                - text_column (str): Название колонки с текстом
                - label_column (str): Название колонки с метками
                - preprocessing (Dict): Настройки предобработки
                
        Returns:
            Dict[str, Any]: Результаты обучения
            
        Example:
            >>> # Из DataFrame
            >>> df = pd.DataFrame({
            ...     'text': ['Создай КС', 'Найди договор'], 
            ...     'intent': ['create_ks', 'search_contract']
            ... })
            >>> config = {
            ...     'source_type': 'pandas',
            ...     'text_column': 'text',
            ...     'label_column': 'intent'
            ... }
            >>> results = await model.train_from_dataset(df, config)
        """
        try:
            # Парсим данные в зависимости от типа источника
            training_data = await self._parse_dataset_async(dataset, dataset_config)
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Загружено {len(training_data)} примеров из датасета типа {dataset_config['source_type']}"
            )
            
            # Обучаем модель
            return await self.train_async(training_data)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обучения из датасета: {e}"
            )
            raise
    
    async def _parse_dataset_async(self, 
                                  dataset: Union[pd.DataFrame, List[Dict], str], 
                                  config: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Асинхронный парсинг различных типов датасетов"""
        source_type = config['source_type']
        text_col = config['text_column']
        label_col = config['label_column']
        
        if source_type == 'pandas':
            if not isinstance(dataset, pd.DataFrame):
                raise ValueError("Для source_type='pandas' ожидается DataFrame")
            
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self._parse_dataframe_sync,
                dataset,
                text_col,
                label_col
            )
        
        elif source_type in ['json', 'csv', 'excel']:
            if not isinstance(dataset, str):
                raise ValueError(f"Для source_type='{source_type}' ожидается путь к файлу")
            
            return await asyncio.get_event_loop().run_in_executor(
                None,
                self._parse_file_sync,
                dataset,
                config
            )
        
        else:
            raise ValueError(f"Неподдерживаемый тип источника: {source_type}")
    
    def _parse_dataframe_sync(self, df: pd.DataFrame, text_col: str, label_col: str) -> List[Tuple[str, str]]:
        """Синхронный парсинг DataFrame"""
        if text_col not in df.columns or label_col not in df.columns:
            raise ValueError(f"Колонки {text_col} или {label_col} не найдены в DataFrame")
        
        # Фильтруем пустые значения
        df_clean = df.dropna(subset=[text_col, label_col])
        
        return list(zip(df_clean[text_col].astype(str), df_clean[label_col].astype(str)))
    
    def _parse_file_sync(self, filepath: str, config: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Синхронный парсинг файлов"""
        source_type = config['source_type']
        text_col = config['text_column']
        label_col = config['label_column']
        
        try:
            if source_type == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    return [(item[text_col], item[label_col]) for item in data 
                           if text_col in item and label_col in item]
                else:
                    raise ValueError("JSON файл должен содержать список объектов")
            
            elif source_type == 'csv':
                df = pd.read_csv(filepath)
                return self._parse_dataframe_sync(df, text_col, label_col)
            
            elif source_type == 'excel':
                df = pd.read_excel(filepath)
                return self._parse_dataframe_sync(df, text_col, label_col)
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        except Exception as e:
            raise ValueError(f"Ошибка чтения файла {filepath}: {e}")
    
    def update_intent_mapping(self, new_mapping: Dict[str, str]) -> None:
        """
        Обновление маппинга намерений
        
        Args:
            new_mapping (Dict[str, str]): Новый маппинг намерений
        """
        try:
            old_count = len(self.intent_mapping)
            self.intent_mapping.update(new_mapping)
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Маппинг намерений обновлен: {old_count} -> {len(self.intent_mapping)} намерений"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обновления маппинга намерений: {e}"
            )
            raise
    
    def update_entity_patterns(self, new_patterns: Dict[str, List[str]]) -> None:
        """
        Обновление паттернов извлечения сущностей
        
        Args:
            new_patterns (Dict[str, List[str]]): Новые паттерны сущностей
        """
        try:
            old_count = len(self.entity_patterns)
            self.entity_patterns.update(new_patterns)
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Паттерны сущностей обновлены: {old_count} -> {len(self.entity_patterns)} типов"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обновления паттернов сущностей: {e}"
            )
            raise
    
    async def validate_dataset_async(self, 
                                    dataset: Union[pd.DataFrame, List[Dict], str], 
                                    dataset_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Асинхронная валидация датасета перед обучением
        
        Args:
            dataset: Датасет для валидации
            dataset_config: Конфигурация датасета
            
        Returns:
            Dict[str, Any]: Результаты валидации
        """
        try:
            # Парсим данные
            training_data = await self._parse_dataset_async(dataset, dataset_config)
            
            # Статистика
            texts, labels = zip(*training_data) if training_data else ([], [])
            unique_labels = set(labels)
            
            # Проверка распределения классов
            label_counts = {}
            for label in labels:
                label_counts[label] = label_counts.get(label, 0) + 1
            
            # Проверка качества данных
            empty_texts = sum(1 for text in texts if not text.strip())
            avg_text_length = sum(len(text) for text in texts) / len(texts) if texts else 0
            
            validation_result = {
                'total_samples': len(training_data),
                'unique_labels': len(unique_labels),
                'label_distribution': label_counts,
                'empty_texts': empty_texts,
                'average_text_length': avg_text_length,
                'min_samples_per_class': min(label_counts.values()) if label_counts else 0,
                'max_samples_per_class': max(label_counts.values()) if label_counts else 0,
                'is_valid': len(training_data) >= 2 and empty_texts == 0 and len(unique_labels) >= 2
            }
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Валидация датасета завершена: {validation_result['total_samples']} примеров, "
                       f"{validation_result['unique_labels']} классов, валиден: {validation_result['is_valid']}"
            )
            
            return validation_result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка валидации датасета: {e}"
            )
            raise
