import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from .utils import Utils


class TextExtractor:
    """
    Менеджер для работы с текстами и сообщениями системы.
    
    Загружает конфигурацию из JSON файла и предоставляет методы для получения
    текстов, сообщений, предложений и справочной информации.
    """
    
    def __init__(self, text_path: str, logger: Optional[Any] = None):
        """
        Инициализирует экстрактор текстов.
        
        Args:
            text_path: Путь к JSON файлу с текстами
            logger: Логгер для записи сообщений (опционально)
        """
        self.logger = logger
        self.texts: Dict[str, Any] = {}
        self.text_path = text_path
        
        self._load_texts()
        
        Utils.writelog(
            logger=self.logger,
            level="DEBUG",
            message=f"TextManager инициализирован с файлом: {self.text_path}"
        )
    
    def _load_texts(self) -> None:
        """
        Загружает тексты из JSON файла.
        
        Обрабатывает как абсолютные, так и относительные пути.
        В случае ошибки загружает базовые тексты как fallback.
        """
        try:
            if Path(self.text_path).is_absolute():
                full_path = Path(self.text_path)
            else:
                project_root = Path(__file__).parent.parent.parent.parent
                full_path = project_root / self.text_path
            
            if not full_path.exists():
                raise FileNotFoundError(f"Файл с текстами не найден: {full_path}")
            
            with open(full_path, 'r', encoding='utf-8') as f:
                self.texts = json.load(f)
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Тексты загружены из файла: {full_path}"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка загрузки текстов из {self.text_path}: {e}"
            )
            self.texts = self._get_fallback_texts()
    
    def _get_fallback_texts(self) -> Dict[str, Any]:
        """
        Возвращает базовые тексты в случае ошибки загрузки основного файла.
        
        Returns:
            Dict[str, Any]: Базовые тексты с минимальным набором сообщений
        """
        return {
            "messages": {
                "errors": {
                    "processing_error": "Ошибка обработки запроса",
                    "unknown_intent": "Неизвестное намерение"
                }
            },
            "suggestions": {
                "general": ["Попробуйте уточнить запрос"]
            }
        }
    
    def get_message(self, category: str, key: str, **kwargs) -> str:
        """
        Получает сообщение по категории и ключу с поддержкой форматирования.
        
        Args:
            category: Категория сообщения (contract_creation, search, errors и т.д.)
            key: Ключ сообщения
            **kwargs: Параметры для форматирования строки
            
        Returns:
            str: Отформатированное сообщение или сообщение об ошибке
        """
        try:
            message = self.texts.get("messages", {}).get(category, {}).get(key, "")
            if message and kwargs:
                return message.format(**kwargs)
            return message or f"Сообщение не найдено: {category}.{key}"
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="WARNING",
                message=f"Ошибка форматирования сообщения {category}.{key}: {e}"
            )
            return f"Ошибка получения сообщения: {category}.{key}"
    
    def get_suggestions(self, category: str, field: Optional[str] = None) -> List[str]:
        """
        Получает список предложений по категории.
        
        Args:
            category: Категория предложений
            field: Конкретное поле (опционально)
            
        Returns:
            List[str]: Список предложений или сообщение об ошибке
        """
        try:
            suggestions_data = self.texts.get("suggestions", {}).get(category, {})
            
            if field and isinstance(suggestions_data, dict):
                return [suggestions_data.get(field, f"Предложение для {field} не найдено")]
            elif isinstance(suggestions_data, list):
                return suggestions_data
            elif isinstance(suggestions_data, dict):
                return list(suggestions_data.values())
            else:
                return ["Предложения не найдены"]
                
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="WARNING",
                message=f"Ошибка получения предложений {category}: {e}"
            )
            return ["Ошибка получения предложений"]
    
    def get_field_suggestions(self, data_type: str, missing_fields: List[str]) -> List[str]:
        """
        Получает предложения для недостающих полей.
        
        Args:
            data_type: Тип данных (contract_fields, ks_fields, company_fields)
            missing_fields: Список недостающих полей
            
        Returns:
            List[str]: Список предложений для полей
        """
        suggestions = []
        field_suggestions = self.texts.get("suggestions", {}).get(data_type, {})
        
        for field in missing_fields:
            suggestion = field_suggestions.get(field, f"Укажите {field}")
            suggestions.append(suggestion)
        
        return suggestions
    
    def get_help_content(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Получает содержимое справки.
        
        Args:
            topic: Конкретная тема справки (опционально)
            
        Returns:
            Dict[str, Any]: Содержимое справки
        """
        help_data = self.texts.get("help_content", {})
        
        if topic and topic in help_data:
            return help_data[topic]
        
        return help_data
    
    def get_next_steps(self, step_type: str) -> List[str]:
        """
        Получает следующие шаги для процесса.
        
        Args:
            step_type: Тип процесса (contract, ks, company)
            
        Returns:
            List[str]: Список следующих шагов
        """
        return self.texts.get("next_steps", {}).get(step_type, ["Продолжите процесс"])
    
    def get_examples(self, example_type: str = "search") -> List[str]:
        """
        Получает примеры использования.
        
        Args:
            example_type: Тип примеров
            
        Returns:
            List[str]: Список примеров
        """
        return self.texts.get("examples", {}).get(example_type, [])
    
    def get_creation_response(self, data_type: str, status: str, data: Dict[str, Any], 
                            missing_fields: List[str] = None) -> Dict[str, Any]:
        """
        Формирует ответ для создания записей.
        
        Args:
            data_type: Тип данных (contract, ks, company)
            status: Статус (needs_more_info, ready_to_create, created_successfully)
            data: Данные записи
            missing_fields: Недостающие поля (для статуса needs_more_info)
            
        Returns:
            Dict[str, Any]: Сформированный ответ
        """
        category_map = {
            "contract": "contract_creation",
            "ks": "ks_creation", 
            "company": "company_creation"
        }
        
        field_map = {
            "contract": "contract_fields",
            "ks": "ks_fields",
            "company": "company_fields"
        }
        
        category = category_map.get(data_type, "contract_creation")
        message = self.get_message(category, status)
        
        response = {
            "type": f"create_{data_type}_{status}",
            "status": status,
            "message": message,
            f"{data_type}_data": data
        }
        
        if status == "needs_more_info" and missing_fields:
            response["missing_fields"] = missing_fields
            response["suggestions"] = self.get_field_suggestions(
                field_map.get(data_type, "contract_fields"), 
                missing_fields
            )
        elif status in ["ready_to_create", "created_successfully"]:
            response["next_steps"] = self.get_next_steps(data_type)
        
        return response
    
    def get_search_response(self, search_type: str, results: List[Dict[str, Any]], 
                          search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Формирует ответ для результатов поиска.
        
        Args:
            search_type: Тип поиска (contracts, sessions, mixed)
            results: Результаты поиска
            search_params: Параметры поиска
            
        Returns:
            Dict[str, Any]: Сформированный ответ
        """
        if not results:
            return {
                "type": "search_no_results",
                "status": "no_results",
                "message": self.get_message("search", "no_results"),
                "search_params": search_params,
                "suggestions": self.get_suggestions("search_improvement", "general")
            }
        
        return {
            "type": f"search_{search_type}_results",
            "status": "success",
            "message": self.get_message("search", "results_found", count=len(results)),
            "results": results,
            "total_count": len(results),
            "search_params": search_params
        }
    
    def get_company_response(self, company_data: Optional[Dict[str, Any]], 
                           search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Формирует ответ для поиска компании.
        
        Args:
            company_data: Данные компании (None если не найдена)
            search_params: Параметры поиска
            
        Returns:
            Dict[str, Any]: Сформированный ответ
        """
        if not company_data:
            return {
                "type": "company_search_no_results",
                "status": "no_results",
                "message": self.get_message("search", "company_not_found"),
                "search_params": search_params,
                "suggestions": self.get_suggestions("search_improvement", "company_search")
            }
        
        return {
            "type": "company_search_results",
            "status": "success",
            "message": self.get_message("search", "company_found"),
            "company_data": company_data,
            "search_params": search_params
        }
    
    def get_help_response(self, help_topic: str = "") -> Dict[str, Any]:
        """
        Формирует ответ справочной системы.
        
        Args:
            help_topic: Тема справки
            
        Returns:
            Dict[str, Any]: Ответ справочной системы
        """
        help_sections = []
        help_content = self.get_help_content()
        
        topic_lower = help_topic.lower()
        
        if any(word in topic_lower for word in ['создани', 'контракт']):
            if 'contract_creation' in help_content:
                help_sections.append(help_content['contract_creation'])
        
        if any(word in topic_lower for word in ['поиск', 'найти']):
            if 'search' in help_content:
                help_sections.append(help_content['search'])
        
        if any(word in topic_lower for word in ['кс', 'котировк', 'сессия']):
            if 'ks_creation' in help_content:
                help_sections.append(help_content['ks_creation'])
        
        if not help_sections and 'general' in help_content:
            help_sections.append(help_content['general'])
        
        return {
            "type": "help_response",
            "status": "success",
            "message": "Справочная информация",
            "help_sections": help_sections
        }
    
    def get_error_response(self, error_type: str, **kwargs) -> Dict[str, Any]:
        """
        Формирует ответ об ошибке.
        
        Args:
            error_type: Тип ошибки
            **kwargs: Параметры для форматирования
            
        Returns:
            Dict[str, Any]: Ответ об ошибке
        """
        return {
            "type": "error",
            "status": "error",
            "message": self.get_message("errors", error_type, **kwargs)
        }