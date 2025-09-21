from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator

from ...core.base.utils import Utils


class IntentRequest(BaseModel):
    """Запрос для классификации намерения"""
    text: str = Field(..., min_length=1, max_length=1000, description="Текст для анализа")
    detailed: bool = Field(default=False, description="Возвращать ли детальный анализ")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Текст не может быть пустым')
        return v.strip()


class BatchIntentRequest(BaseModel):
    """Запрос для пакетной классификации намерений"""
    texts: List[str] = Field(..., min_items=1, max_items=10, description="Список текстов для анализа")
    
    @validator('texts')
    def validate_texts(cls, v):
        if not v:
            raise ValueError('Список текстов не может быть пустым')
        
        validated_texts = []
        for text in v:
            if not text or not text.strip():
                continue
            if len(text.strip()) > 1000:
                raise ValueError('Текст не может быть длиннее 1000 символов')
            validated_texts.append(text.strip())
        
        if not validated_texts:
            raise ValueError('Нет валидных текстов для анализа')
        
        return validated_texts


class IntentResponse(BaseModel):
    """Ответ классификации намерения"""
    original_text: str = Field(..., description="Исходный текст")
    processed_text: str = Field(..., description="Обработанный текст")
    intent: str = Field(..., description="Код намерения")
    intent_name: str = Field(..., description="Название намерения")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность модели")
    entities: Dict[str, str] = Field(default_factory=dict, description="Извлеченные сущности")
    timestamp: str = Field(..., description="Время обработки")
    
    # Дополнительные поля для детального анализа
    all_probabilities: Optional[Dict[str, float]] = Field(None, description="Все вероятности")
    top_predictions: Optional[List[Dict[str, Any]]] = Field(None, description="Топ предсказания")


class BatchIntentResponse(BaseModel):
    """Ответ пакетной классификации"""
    results: List[IntentResponse] = Field(..., description="Результаты анализа")
    total_processed: int = Field(..., description="Количество обработанных текстов")


class ModelInfoResponse(BaseModel):
    """Информация о модели"""
    is_trained: bool = Field(..., description="Обучена ли модель")
    intents: List[str] = Field(..., description="Доступные намерения")
    intent_names: List[str] = Field(..., description="Названия намерений")
    correction_dictionary_size: int = Field(..., description="Размер словаря исправлений")
    entity_patterns: List[str] = Field(..., description="Типы сущностей")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    error: str = Field(..., description="Описание ошибки")
    detail: Optional[str] = Field(None, description="Детали ошибки")


async def register_routes(app, **kwargs):
    """
    Регистрация API роутов для ML модели
    
    Args:
        app: FastAPI приложение
        **kwargs: Дополнительные параметры (logger, ml_cic_interface)
    """
    logger = kwargs.get('logger')
    ml_cic_interface = kwargs.get('ml_cic_interface')
    
    if not ml_cic_interface:
        Utils.writelog(
            logger=logger,
            level="ERROR",
            message="ML интерфейс не инициализирован"
        )
        return
    
    @app.post(
        "/api/ml/predict",
        response_model=IntentResponse,
        responses={
            400: {"model": ErrorResponse, "description": "Неверный запрос"},
            500: {"model": ErrorResponse, "description": "Ошибка сервера"},
            503: {"model": ErrorResponse, "description": "ML модель недоступна"}
        },
        summary="Классификация намерения",
        description="Анализирует текст и определяет намерение пользователя с извлечением сущностей"
    )
    async def predict_intent(request: IntentRequest):
        """Предсказание намерения для одного текста"""
        try:
            # Проверяем готовность ML модели
            if not ml_cic_interface.is_initialized:
                Utils.writelog(
                    logger=logger,
                    level="WARNING",
                    message=f"Попытка использования неинициализированной ML модели: '{request.text}'"
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель еще не инициализирована. Попробуйте позже."
                )
            
            # Получаем интерфейс модели
            model_interface = ml_cic_interface.model_interface
            if not model_interface:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель недоступна"
                )
            
            # Выполняем предсказание
            result = await model_interface.predict(request.text, detailed=request.detailed)
            
            Utils.writelog(
                logger=logger,
                level="INFO",
                message=f"ML предсказание: '{request.text}' → {result['intent_name']} ({result['confidence']:.3f})"
            )
            
            return IntentResponse(**result)
            
        except HTTPException:
            raise
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка ML предсказания для '{request.text}': {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка обработки запроса: {str(e)}"
            )
    
    @app.post(
        "/api/ml/predict/batch",
        response_model=BatchIntentResponse,
        responses={
            400: {"model": ErrorResponse, "description": "Неверный запрос"},
            500: {"model": ErrorResponse, "description": "Ошибка сервера"},
            503: {"model": ErrorResponse, "description": "ML модель недоступна"}
        },
        summary="Пакетная классификация намерений",
        description="Анализирует несколько текстов одновременно (до 10 штук)"
    )
    async def predict_batch_intents(request: BatchIntentRequest):
        """Пакетное предсказание намерений"""
        try:
            # Проверяем готовность ML модели
            if not ml_cic_interface.is_initialized:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель еще не инициализирована"
                )
            
            model_interface = ml_cic_interface.model_interface
            if not model_interface:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель недоступна"
                )
            
            # Выполняем пакетное предсказание
            results = await model_interface.predict_batch(request.texts)
            
            Utils.writelog(
                logger=logger,
                level="INFO",
                message=f"Пакетное ML предсказание: {len(request.texts)} текстов обработано"
            )
            
            return BatchIntentResponse(
                results=[IntentResponse(**result) for result in results],
                total_processed=len(results)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка пакетного ML предсказания: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка пакетной обработки: {str(e)}"
            )
    
    @app.get(
        "/api/ml/info",
        response_model=ModelInfoResponse,
        responses={
            503: {"model": ErrorResponse, "description": "ML модель недоступна"}
        },
        summary="Информация о ML модели",
        description="Возвращает информацию о доступных намерениях и состоянии модели"
    )
    async def get_model_info():
        """Получение информации о модели"""
        try:
            if not ml_cic_interface.is_initialized:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель еще не инициализирована"
                )
            
            model_interface = ml_cic_interface.model_interface
            if not model_interface:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель недоступна"
                )
            
            info = model_interface.get_model_info()
            intents_mapping = model_interface.get_available_intents()
            
            return ModelInfoResponse(
                is_trained=info['is_trained'],
                intents=info['intents'],
                intent_names=info['intent_names'],
                correction_dictionary_size=info['correction_dictionary_size'],
                entity_patterns=info['entity_patterns']
            )
            
        except HTTPException:
            raise
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка получения информации о модели: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка получения информации: {str(e)}"
            )
    
    @app.get(
        "/api/ml/intents",
        response_model=Dict[str, str],
        responses={
            503: {"model": ErrorResponse, "description": "ML модель недоступна"}
        },
        summary="Доступные намерения",
        description="Возвращает словарь всех доступных намерений с их названиями"
    )
    async def get_available_intents():
        """Получение доступных намерений"""
        try:
            if not ml_cic_interface.is_initialized:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель еще не инициализирована"
                )
            
            model_interface = ml_cic_interface.model_interface
            if not model_interface:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель недоступна"
                )
            
            return model_interface.get_available_intents()
            
        except HTTPException:
            raise
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка получения намерений: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка получения намерений: {str(e)}"
            )
    
    @app.get(
        "/api/ml/health",
        responses={
            200: {"description": "ML модель работает"},
            503: {"model": ErrorResponse, "description": "ML модель недоступна"}
        },
        summary="Проверка состояния ML модели",
        description="Простая проверка доступности ML модели"
    )
    async def ml_health_check():
        """Проверка здоровья ML модели"""
        try:
            if not ml_cic_interface.is_initialized:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель еще не инициализирована"
                )
            
            model_interface = ml_cic_interface.model_interface
            if not model_interface:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML модель недоступна"
                )
            
            # Простой тест модели
            test_result = await model_interface.predict("тест")
            
            return {
                "status": "healthy",
                "message": "ML модель работает корректно",
                "test_prediction": test_result['intent_name']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка проверки здоровья ML модели: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"ML модель недоступна: {str(e)}"
            )
    
    Utils.writelog(
        logger=logger,
        level="INFO",
        message="ML API роуты зарегистрированы: /api/ml/*"
    )
