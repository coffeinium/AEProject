from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel

from ...core.base.utils import Utils
from ..handlers.intent_handlers import IntentHandlers

class MLData(BaseModel):
    intent: str
    confidence: Optional[float]
    entities: Dict[str, Any]
    details: Optional[Any] = None

class ResponseData(BaseModel):
    type: str
    data: Optional[Any] = None

class SearchResponse(BaseModel):
    status: str
    response: ResponseData
    ml_data: MLData

class HistoryResponse(BaseModel):
    status: str
    response: ResponseData

# Дополнительные модели для обработки частичных данных

class PartialDataResponse(BaseModel):
    """Ответ для случаев, когда нужны дополнительные данные"""
    type: str
    status: str = "needs_more_info"
    message: str
    provided_data: Dict[str, Any]
    missing_fields: List[str]
    suggestions: List[str]

class SearchResultItem(BaseModel):
    """Элемент результата поиска"""
    type: str  # "contract" или "session"
    data: Dict[str, Any]

class SearchResultsResponse(BaseModel):
    """Ответ с результатами поиска"""
    type: str
    status: str = "success"
    message: str
    results: List[SearchResultItem]
    total_count: int
    search_params: Dict[str, Any]

class CompanyInfo(BaseModel):
    """Информация о компании"""
    name: Optional[str] = None
    inn: Optional[Union[str, int]] = None
    contracts_count: int = 0
    sessions_count: int = 0
    total_contract_amount: float = 0.0
    total_session_amount: float = 0.0

class CompanySearchResponse(BaseModel):
    """Ответ поиска компании"""
    type: str
    status: str = "success"
    message: str
    company_data: Dict[str, Any]
    search_params: Dict[str, Any]

class HelpSection(BaseModel):
    """Секция справки"""
    topic: str
    description: str
    examples: Optional[List[str]] = None
    commands: Optional[List[str]] = None

class HelpResponse(BaseModel):
    """Ответ справочной системы"""
    type: str = "help_response"
    status: str = "success"
    message: str
    help_sections: List[HelpSection]

class CreationResponse(BaseModel):
    """Ответ для создания записей"""
    type: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    next_steps: Optional[List[str]] = None

async def register_routes(app, **kwargs):
    logger = kwargs.get('logger')
    storage = kwargs.get('storage')
    ml_cic_interface = kwargs.get('ml_cic_interface')
    env = kwargs.get('env')
    
    # Инициализируем обработчики намерений
    intent_handlers = IntentHandlers(storage, logger, env) if storage and env else None
    
    @app.get("/user/search", response_class=JSONResponse)
    async def search(request: Request, query: str = "", detailed: bool = False, write_in_history: bool = True):
        try:
            if not query or not query.strip():
                return SearchResponse(
                    status="error", 
                    response=ResponseData(type="error", data="Поисковый запрос не может быть пустым"), 
                    ml_data=MLData(intent="error", confidence=0.0, entities={})
                )
            
            if not ml_cic_interface.is_initialized:
                Utils.writelog(logger=logger, level="WARNING", message="ML модель не инициализирована")
                return SearchResponse(status="error", response=ResponseData(type="error", data="ML модель не инициализирована"), ml_data=MLData(intent="error", confidence=0.0, entities={}))
            
            model_interface = ml_cic_interface.model_interface
            if not model_interface:
                Utils.writelog(logger=logger, level="WARNING", message="ML модель недоступна")
                return SearchResponse(status="error", response=ResponseData(type="error", data="ML модель недоступна"), ml_data=MLData(intent="error", confidence=0.0, entities={}))
            
            # Валидация и очистка запроса
            query = Utils.validate_search_query(query, logger=logger)
            
            # Получение предсказания от ML модели
            ml_result = await model_interface.predict(query, detailed=detailed)
            
            # Формирование ответа ML данных
            ml_data = MLData(
                intent=ml_result.get('intent', 'unknown'),
                confidence=ml_result.get('confidence', 0.0),
                entities=ml_result.get('entities', {}),
                details=ml_result if detailed else None
            )
            
            # Обработка намерения с помощью специализированных обработчиков
            intent = ml_result.get('intent', 'unknown')
            entities = ml_result.get('entities', {})
            
            if intent_handlers:
                # Используем обработчики намерений для получения данных из БД
                processed_result = await intent_handlers.process_intent(intent, entities, query)
                response = ResponseData(
                    type=processed_result.get("type", intent),
                    data=processed_result
                )
            else:
                # Fallback если storage недоступен
                response_data = {
                    "type": "storage_unavailable",
                    "status": "error", 
                    "message": "База данных недоступна. Невозможно обработать запрос.",
                    "intent": intent,
                    "entities": entities,
                    "query": query,
                    "confidence": ml_result.get('confidence', 0.0)
                }
                response = ResponseData(type="error", data=response_data)
            
            # Сохранение в историю если включено
            if write_in_history and storage:
                try:
                    history_record = {
                        "text": query,
                        "intent": ml_result.get('intent'),
                        "confidence": ml_result.get('confidence'),
                        "entities": ml_result.get('entities', {}),
                        "timestamp": datetime.now()
                    }
                    await storage.insert_history_record(history_record)
                    
                    Utils.writelog(
                        logger=logger, 
                        level="DEBUG", 
                        message=f"Запрос сохранен в историю: {query[:50]}..."
                    )
                except Exception as history_error:
                    Utils.writelog(
                        logger=logger, 
                        level="WARNING", 
                        message=f"Ошибка сохранения в историю: {history_error}"
                    )
            
            return SearchResponse(status="success", response=response, ml_data=ml_data)
            
        except ValueError as e:
            Utils.writelog(logger=logger, level="WARNING", message=f"Ошибка валидации поискового запроса: {e}")
            return SearchResponse(status="error", response=ResponseData(type="error", data=str(e)), ml_data=MLData(intent="error", confidence=0.0, entities={}))
        
        except Exception as e:
            Utils.writelog(logger=logger, level="WARNING", message=f"Ошибка поиска: {e}")
            return SearchResponse(status="error", response=ResponseData(type="error", data=str(e)), ml_data=MLData(intent="error", confidence=0.0, entities={}))
        
    
    @app.get("/user/history", response_class=JSONResponse)
    async def history(request: Request, limit: int = 100, hours: int = None, intent: str = None, min_confidence: float = None):
        """
        Получение истории запросов
        
        Args:
            limit (int): Максимальное количество записей (по умолчанию 100)
            hours (int): Получить записи за последние N часов
            intent (str): Фильтр по намерению
            min_confidence (float): Минимальная уверенность (0.0-1.0)
        """
        try:
            if not storage:
                Utils.writelog(logger=logger, level="WARNING", message="Storage недоступен")
                return HistoryResponse(status="error", response=ResponseData(type="error", data="Storage недоступен"))
            
            # Получение записей истории в зависимости от параметров
            if hours:
                # За последние N часов
                records = await storage.get_recent_history(hours=hours, limit=limit)
            elif intent:
                # По намерению
                records = await storage.get_history_by_intent(intent=intent, limit=limit)
            elif min_confidence is not None:
                # По диапазону уверенности
                records = await storage.get_history_by_confidence_range(
                    min_confidence=min_confidence, 
                    max_confidence=1.0, 
                    limit=limit
                )
            else:
                # Последние записи
                records = await storage.get_recent_history(hours=24, limit=limit)
            
            # Формирование ответа
            history_data = {
                "records": records,
                "total_count": len(records),
                "filters": {
                    "limit": limit,
                    "hours": hours,
                    "intent": intent,
                    "min_confidence": min_confidence
                }
            }
            
            response = ResponseData(type="history", data=history_data)
            
            Utils.writelog(
                logger=logger, 
                level="DEBUG", 
                message=f"Получена история: {len(records)} записей"
            )
            
            return HistoryResponse(status="success", response=response)
            
        except Exception as e:
            Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка получения истории: {e}")
            return HistoryResponse(status="error", response=ResponseData(type="error", data=str(e)))
    
    @app.get("/user/history/stats", response_class=JSONResponse)
    async def history_stats(request: Request):
        """Получение статистики по истории запросов"""
        try:
            if not storage:
                Utils.writelog(logger=logger, level="WARNING", message="Storage недоступен")
                return HistoryResponse(status="error", response=ResponseData(type="error", data="Storage недоступен"))
            
            # Получение общей статистики
            stats = await storage.get_history_stats()
            
            # Получение топ намерений
            top_intents = await storage.get_top_intents(limit=10, days=30)
            
            # Формирование ответа
            stats_data = {
                "overview": stats,
                "top_intents": top_intents,
                "summary": {
                    "total_queries": stats.get('total_count', {}).get('total', 0) if stats.get('total_count') else 0,
                    "avg_confidence": stats.get('avg_confidence', {}).get('avg', 0) if stats.get('avg_confidence') else 0,
                    "recent_activity": stats.get('recent_activity', {}).get('count', 0) if stats.get('recent_activity') else 0
                }
            }
            
            response = ResponseData(type="history_stats", data=stats_data)
            
            Utils.writelog(logger=logger, level="DEBUG", message="Статистика истории получена")
            
            return HistoryResponse(status="success", response=response)
            
        except Exception as e:
            Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка получения статистики истории: {e}")
            return HistoryResponse(status="error", response=ResponseData(type="error", data=str(e)))
    
    @app.get("/user/history/search", response_class=JSONResponse)
    async def search_history(request: Request, q: str, limit: int = 50):
        """
        Поиск в истории запросов по тексту
        
        Args:
            q (str): Поисковый запрос
            limit (int): Максимальное количество результатов
        """
        try:
            if not storage:
                Utils.writelog(logger=logger, level="WARNING", message="Storage недоступен")
                return HistoryResponse(status="error", response=ResponseData(type="error", data="Storage недоступен"))
            
            if not q or len(q.strip()) < 2:
                return HistoryResponse(status="error", response=ResponseData(type="error", data="Поисковый запрос должен содержать минимум 2 символа"))
            
            # Поиск в истории
            records = await storage.search_history_by_text(q.strip(), limit=limit)
            
            # Формирование ответа
            search_data = {
                "query": q,
                "records": records,
                "total_count": len(records),
                "limit": limit
            }
            
            response = ResponseData(type="history_search", data=search_data)
            
            Utils.writelog(
                logger=logger, 
                level="DEBUG", 
                message=f"Поиск в истории по '{q}': найдено {len(records)} записей"
            )
            
            return HistoryResponse(status="success", response=response)
            
        except Exception as e:
            Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка поиска в истории: {e}")
            return HistoryResponse(status="error", response=ResponseData(type="error", data=str(e)))
    
    @app.delete("/user/history/cleanup", response_class=JSONResponse)
    async def cleanup_history(request: Request, days_to_keep: int = 90):
        """
        Очистка старых записей истории
        
        Args:
            days_to_keep (int): Количество дней для хранения записей (по умолчанию 90)
        """
        try:
            if not storage:
                Utils.writelog(logger=logger, level="WARNING", message="Storage недоступен")
                return HistoryResponse(status="error", response=ResponseData(type="error", data="Storage недоступен"))
            
            if days_to_keep < 1:
                return HistoryResponse(status="error", response=ResponseData(type="error", data="Количество дней должно быть больше 0"))
            
            # Очистка старых записей
            deleted_count = await storage.cleanup_old_history(days_to_keep=days_to_keep)
            
            # Формирование ответа
            cleanup_data = {
                "deleted_count": deleted_count,
                "days_to_keep": days_to_keep,
                "message": f"Удалено {deleted_count} записей старше {days_to_keep} дней"
            }
            
            response = ResponseData(type="history_cleanup", data=cleanup_data)
            
            Utils.writelog(
                logger=logger, 
                level="INFO", 
                message=f"Очистка истории: удалено {deleted_count} записей старше {days_to_keep} дней"
            )
            
            return HistoryResponse(status="success", response=response)
            
        except Exception as e:
            Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка очистки истории: {e}")
            return HistoryResponse(status="error", response=ResponseData(type="error", data=str(e)))
    
    @app.post("/user/complete_data", response_class=JSONResponse)
    async def complete_data(request: Request, data_type: str, provided_data: Dict[str, Any], additional_data: Dict[str, Any]):
        """
        Дополнение частичных данных для создания записей
        
        Args:
            data_type (str): Тип данных ("contract", "ks", "company")
            provided_data (Dict): Уже предоставленные данные
            additional_data (Dict): Дополнительные данные от пользователя
        """
        try:
            if not intent_handlers:
                return HistoryResponse(status="error", response=ResponseData(type="error", data="Обработчики недоступны"))
            
            # Объединяем данные
            complete_data = {**provided_data, **additional_data}
            
            # Обрабатываем в зависимости от типа
            if data_type == "contract":
                missing_fields = intent_handlers._check_required_contract_fields(complete_data)
                if missing_fields:
                    return HistoryResponse(
                        status="needs_more_info",
                        response=ResponseData(
                            type="contract_incomplete",
                            data={
                                "provided_data": complete_data,
                                "missing_fields": missing_fields,
                                "suggestions": intent_handlers._get_contract_suggestions(complete_data)
                            }
                        )
                    )
                else:
                    return HistoryResponse(
                        status="success",
                        response=ResponseData(
                            type="contract_ready",
                            data={
                                "message": "Контракт готов к созданию",
                                "contract_data": complete_data,
                                "next_steps": ["Подтвердите данные", "Создать контракт"]
                            }
                        )
                    )
            
            elif data_type == "ks":
                missing_fields = intent_handlers._check_required_ks_fields(complete_data)
                if missing_fields:
                    return HistoryResponse(
                        status="needs_more_info",
                        response=ResponseData(
                            type="ks_incomplete",
                            data={
                                "provided_data": complete_data,
                                "missing_fields": missing_fields,
                                "suggestions": intent_handlers._get_ks_suggestions(complete_data)
                            }
                        )
                    )
                else:
                    return HistoryResponse(
                        status="success",
                        response=ResponseData(
                            type="ks_ready",
                            data={
                                "message": "КС готова к созданию",
                                "ks_data": complete_data,
                                "next_steps": ["Подтвердите данные", "Создать КС"]
                            }
                        )
                    )
            
            elif data_type == "company":
                missing_fields = intent_handlers._check_required_company_fields(complete_data)
                if missing_fields:
                    return HistoryResponse(
                        status="needs_more_info",
                        response=ResponseData(
                            type="company_incomplete",
                            data={
                                "provided_data": complete_data,
                                "missing_fields": missing_fields,
                                "suggestions": intent_handlers._get_company_creation_suggestions(complete_data)
                            }
                        )
                    )
                else:
                    return HistoryResponse(
                        status="success",
                        response=ResponseData(
                            type="company_ready",
                            data={
                                "message": "Профиль компании готов к созданию",
                                "company_data": complete_data,
                                "next_steps": ["Подтвердите данные", "Создать профиль"]
                            }
                        )
                    )
            
            else:
                return HistoryResponse(status="error", response=ResponseData(type="error", data=f"Неизвестный тип данных: {data_type}"))
                
        except Exception as e:
            Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка дополнения данных: {e}")
            return HistoryResponse(status="error", response=ResponseData(type="error", data=str(e)))
    
    @app.get("/user/search_suggestions", response_class=JSONResponse)
    async def search_suggestions(request: Request, query: str, search_type: str = "auto"):
        """
        Получение предложений для улучшения поиска
        
        Args:
            query (str): Поисковый запрос
            search_type (str): Тип поиска ("contracts", "sessions", "companies", "auto")
        """
        try:
            if not intent_handlers:
                return HistoryResponse(status="error", response=ResponseData(type="error", data="Обработчики недоступны"))
            
            suggestions = []
            
            # Базовые предложения
            if len(query.strip()) < 3:
                suggestions.extend([
                    "Введите более длинный запрос (минимум 3 символа)",
                    "Укажите конкретные параметры: название, ИНН, сумму"
                ])
            
            # Предложения по типу поиска
            if search_type in ["contracts", "auto"]:
                suggestions.extend([
                    "Для поиска контрактов укажите: название, заказчика, ИНН или сумму",
                    "Примеры: 'контракты ООО Ромашка', 'договоры на 100000 рублей'"
                ])
            
            if search_type in ["sessions", "auto"]:
                suggestions.extend([
                    "Для поиска КС укажите: название, заказчика, ИНН или сумму",
                    "Примеры: 'КС на канцтовары', 'котировки по 44-ФЗ'"
                ])
            
            if search_type in ["companies", "auto"]:
                suggestions.extend([
                    "Для поиска компаний укажите: название или ИНН",
                    "Примеры: 'ООО Ромашка', 'ИНН 1234567890'"
                ])
            
            # Анализируем запрос на наличие ключевых слов
            query_lower = query.lower()
            if any(word in query_lower for word in ['создай', 'создать', 'новый']):
                suggestions.append("Для создания укажите все необходимые данные: название, сумму, заказчика")
            
            return HistoryResponse(
                status="success",
                response=ResponseData(
                    type="search_suggestions",
                    data={
                        "query": query,
                        "search_type": search_type,
                        "suggestions": suggestions[:10],  # Ограничиваем количество
                        "examples": [
                            "Найди контракты ООО Ромашка",
                            "Покажи КС на сумму больше 50000",
                            "Создай договор на канцтовары 25000 рублей",
                            "Поиск по ИНН 1234567890"
                        ]
                    }
                )
            )
            
        except Exception as e:
            Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка получения предложений: {e}")
            return HistoryResponse(status="error", response=ResponseData(type="error", data=str(e)))