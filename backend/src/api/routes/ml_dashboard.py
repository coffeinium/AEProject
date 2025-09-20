"""
Роут для ML Dashboard - веб-интерфейс тестирования ML модели
"""

from fastapi import Request
from fastapi.responses import HTMLResponse

from ...core.base.utils import Utils


async def register_routes(app, **kwargs):
    """
    Регистрация роута для ML Dashboard
    
    Args:
        app: FastAPI приложение
        **kwargs: Дополнительные параметры (templates, logger)
    """
    templates = kwargs.get('templates')
    logger = kwargs.get('logger')
    
    if not templates:
        Utils.writelog(
            logger=logger,
            level="ERROR",
            message="Templates не инициализированы для ML Dashboard"
        )
        return
    
    @app.get(
        "/ml",
        response_class=HTMLResponse,
        summary="ML Dashboard",
        description="Веб-интерфейс для тестирования и мониторинга ML модели классификации намерений",
        tags=["ML Dashboard"]
    )
    async def ml_dashboard(request: Request):
        """Главная страница ML Dashboard"""
        try:
            Utils.writelog(
                logger=logger,
                level="INFO",
                message="Открыт ML Dashboard"
            )
            
            return templates.TemplateResponse(
                "ml_dashboard.html",
                {
                    "request": request,
                    "title": "ML Dashboard - Тестирование нейросети",
                    "description": "Интерактивный интерфейс для тестирования ML модели"
                }
            )
            
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка отображения ML Dashboard: {e}"
            )
            raise
    
    @app.get(
        "/",
        response_class=HTMLResponse,
        summary="Главная страница",
        description="Перенаправление на ML Dashboard",
        tags=["Main"]
    )
    async def root(request: Request):
        """Главная страница - перенаправляет на ML Dashboard"""
        try:
            Utils.writelog(
                logger=logger,
                level="INFO",
                message="Переход на главную страницу -> ML Dashboard"
            )
            
            return templates.TemplateResponse(
                "ml_dashboard.html",
                {
                    "request": request,
                    "title": "AEProject - ML Dashboard",
                    "description": "Система тестирования ML модели классификации намерений"
                }
            )
            
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка отображения главной страницы: {e}"
            )
            raise
    
    Utils.writelog(
        logger=logger,
        level="INFO",
        message="ML Dashboard роуты зарегистрированы: / и /ml"
    )
