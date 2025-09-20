import os
import sys
import signal
import asyncio
import importlib
import traceback
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.core import (
    Utils,
    EnvReader,
    Logger,
    ReportManager,
    PostgresStorage,
    MLCICInitializer
)

class AEProjectCore:
    def __init__(self) -> None:
        self.env = EnvReader()
        (
            self.logger,
            self.report_manager,
            self.storage,
            self.ml_cic_interface
        ) = self._init_main_components()
        
        self.app: Optional[FastAPI] = None
        self.templates: Optional[Jinja2Templates] = None
        
    def _init_main_components(self) -> tuple[Logger, ReportManager, PostgresStorage, MLCICInitializer]:
        try:
            logger_settings = {
                key.replace('LOGGER_', '').lower(): value
                for key, value in self.env.env_data.items()
                if key.startswith('LOGGER_')
            }
            
            ml_cic_settings = {
                key.replace('AEAPISETTINGS_ML_', '').lower(): value
                for key, value in self.env.env_data.items()
                if key.startswith('AEAPISETTINGS_ML_')
            }
            
            logger = Logger(**logger_settings)
            report_manager = ReportManager(self.env)
            ml_cic_interface = MLCICInitializer(**ml_cic_settings, logger=logger)
            
            database_url = getattr(self.env, 'POSTGRES_DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/aeproject_dev')
            postgres_storage = PostgresStorage(database_url, logger)
            
            return logger, report_manager, postgres_storage, ml_cic_interface
        except Exception as e:
            Utils.writelog(
                level="CRITICAL",
                message=f"Ошибка при инициализации компонентов: {e}"
            )
            exit(1)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        try:
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Запуск FastAPI приложения {self.__class__.__name__}"
            )
            
            yield
            
        except Exception as e:
            self._handle_critical_error(e)
        finally:
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Завершение работы FastAPI приложения {self.__class__.__name__}"
            )
            
    async def _initialize_storage(self):
        try:
            await self.storage.initialize()
            Utils.writelog(
                logger=self.logger,
                    level="INFO",
                    message="PostgresStorage инициализирован"
                )
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка инициализации PostgresStorage: {e}"
        )
            
    async def _initialize_ml_cic_interface(self):
        try:
            await self.ml_cic_interface.initialize()
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message="MLCICInitializer инициализирован"
            )
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка инициализации MLCICInitializer: {e}"
            )

    def _create_app(self) -> FastAPI:
        app = FastAPI(
            title=getattr(self.env, 'AEAPISETTINGS_TITLE', 'Web Application') ,
            description=getattr(self.env, 'AEAPISETTINGS_DESCRIPTION', '-'),
            version=getattr(self.env, 'AEAPISETTINGS_VERSION', '1.0.0'),
            lifespan=self.lifespan
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        templates_path = getattr(self.env, 'AEAPISETTINGS_TEMPLATES_PATH', 'templates')
        static_path = getattr(self.env, 'AEAPISETTINGS_STATIC_PATH', 'static')
        
        if os.path.exists(templates_path):
            self.templates = Jinja2Templates(directory=templates_path)
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Шаблоны инициализированы: {templates_path}"
            )
        
        if os.path.exists(static_path):
            app.mount("/static", StaticFiles(directory=static_path), name="static")
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Статические файлы подключены: {static_path}"
            )
        
        return app
    
    def _get_common_kwargs(self) -> dict:
        return {
            "env": self.env,
            "templates": self.templates,
            "logger": self.logger,
            "report_manager": self.report_manager,
            "storage": self.storage,
            "ml_cic_interface": self.ml_cic_interface
        }

    async def _register_middlewares(self, app: FastAPI):
        middlewares_path = getattr(self.env, 'AEAPISETTINGS_MIDDLEWARES_PATH', 'middlewares')
        
        if not os.path.exists(middlewares_path):
            Utils.writelog(
                logger=self.logger,
                level="WARNING",
                message=f"Директория middleware не найдена: {middlewares_path}"
            )
            return

        middleware_files = [
            f for f in os.listdir(middlewares_path)
            if f.endswith(".py") and not f.startswith("__")
        ]
        
        for filename in middleware_files:
            module_name = f"{middlewares_path.replace('/', '.')}.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "register_middleware"):
                    Utils.writelog(
                        logger=self.logger,
                        level="INFO",
                        message=f"Регистрация middleware из {module_name}"
                    )
                    await module.register_middleware(
                        app, 
                        **self._get_common_kwargs()
                    )
                    Utils.writelog(
                        logger=self.logger,
                        level="INFO",
                        message=f"Middleware зарегистрирован успешно: {module_name}"
                    )
            except Exception as e:
                Utils.writelog(
                    logger=self.logger,
                    level="ERROR",
                    message=f"Ошибка регистрации middleware {module_name}: {e}"
                )

    async def _register_routes(self, app: FastAPI):
        routes_path = getattr(self.env, 'AEAPISETTINGS_ROUTES_PATH', 'routes')
        
        if not os.path.exists(routes_path):
            Utils.writelog(
                logger=self.logger,
                level="WARNING",
                message=f"Директория маршрутов не найдена: {routes_path}"
            )
            return

        route_files = [
            f for f in os.listdir(routes_path)
            if f.endswith(".py") and not f.startswith("__")
        ]
        
        if not route_files:
            Utils.writelog(
                logger=self.logger,
                level="WARNING",
                message=f"Нет доступных файлов маршрутов в {routes_path}"
            )
            return

        for filename in route_files:
            module_name = f"{routes_path.replace('/', '.')}.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "register_routes"):
                    Utils.writelog(
                        logger=self.logger,
                        level="INFO",
                        message=f"Регистрация маршрутов из {module_name}"
                    )
                    await module.register_routes(
                        app,
                        **self._get_common_kwargs()
                    )
                    Utils.writelog(
                        logger=self.logger,
                        level="INFO",
                        message=f"Маршруты зарегистрированы успешно: {module_name}"
                    )
            except Exception as e:
                Utils.writelog(
                    logger=self.logger,
                    level="ERROR",
                    message=f"Ошибка регистрации маршрутов {module_name}: {e}"
                )

    async def _register_exception_handlers(self, app: FastAPI):
        @app.exception_handler(500)
        async def internal_server_error_handler(request: Request, exc: Exception):
            error_report = self.report_manager.generate_error_report(exc, traceback.format_exc())
            self.report_manager.save_error_report(error_report)
            
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Внутренняя ошибка сервера: {exc}"
            )
            
            if self.templates:
                return self.templates.TemplateResponse(
                    getattr(self.env, 'AEAPISETTINGS_MULTI_ERROR_PAGE', 'error.html'),
                    {
                        "request": request,
                        "error_type": "500",
                        "error_title": "Внутренняя ошибка",
                        "error_message": "Произошла неожиданная ошибка. Мы уже работаем над её устранением.",
                        "error_icon": "⚠️"
                    },
                    status_code=500
                )
            return JSONResponse(
                content={"error": "Внутренняя ошибка сервера"},
                status_code=500
            )

        @app.exception_handler(404)
        async def not_found_handler(request: Request, exc: Exception):
            if self.templates:
                return self.templates.TemplateResponse(
                    getattr(self.env, 'AEAPISETTINGS_MULTI_ERROR_PAGE', 'error.html'),
                    {
                        "request": request,
                        "error_type": "404",
                        "error_title": "Страница не найдена",
                        "error_message": "Запрашиваемая страница не существует или была перемещена.",
                        "error_icon": "🔍"
                    },
                    status_code=404
                )
            return JSONResponse(
                content={"error": "Страница не найдена"},
                status_code=404
            )
        
        @app.exception_handler(400)
        async def bad_request_handler(request: Request, exc: Exception):
            if self.templates:
                return self.templates.TemplateResponse(
                    getattr(self.env, 'AEAPISETTINGS_MULTI_ERROR_PAGE', 'error.html'),
                    {
                        "request": request,
                        "error_type": "400",
                        "error_title": "Неверный запрос",
                        "error_message": "Неверный запрос. Пожалуйста, проверьте ваш запрос и попробуйте снова.",
                        "error_icon": "❌"
                    },
                    status_code=400
                )
            return JSONResponse(
                content={"error": "Неверный запрос"},
                status_code=400
            )

    def _handle_critical_error(self, error: Exception):
        error_report = self.report_manager.generate_error_report(error, traceback.format_exc())
        self.report_manager.save_error_report(error_report)
        self._restart_application()

    def _restart_application(self):
        Utils.writelog(
            logger=self.logger,
            level="CRITICAL",
            message=f"Перезапуск проекта ... {self.__class__.__name__}"
        )
        python = sys.executable
        os.execl(python, python, *sys.argv)

    async def run(self):
        try:
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Запуск проекта: {self.__class__.__name__}"
            )
            
            await self._initialize_storage()
            
            await self._initialize_ml_cic_interface()
                
            self.app = self._create_app()
            
            await self._register_middlewares(self.app)
            
            await self._register_exception_handlers(self.app)
            
            await self._register_routes(self.app)
            
            host = getattr(self.env, 'AEAPISETTINGS_UVICORN_HOST', '0.0.0.0')
            port = int(getattr(self.env, 'AEAPISETTINGS_UVICORN_PORT', 8000))
            debug = getattr(self.env, 'AEAPISETTINGS_UVICORN_DEBUG', False)
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"FastAPI приложение запущено на {host}:{port}"
            )
            
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info" if debug else "warning",
                reload=debug
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            self._handle_critical_error(e)


def setup_signal_handlers(app_instance: AEProjectCore):
    def signal_handler(signum, frame):
        Utils.writelog(
            logger=app_instance.logger,
            level="INFO",
            message=f"Получен сигнал {signum}, завершение работы..."
        )
        
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    app = AEProjectCore()
    setup_signal_handlers(app)
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        Utils.writelog(
            logger=app.logger,
            level="INFO",
            message="Приложение остановлено пользователем"
        )
    except Exception as e:
        Utils.writelog(
            logger=app.logger,
            level="CRITICAL",
            message=f"Критическая ошибка: {e}"
        )
    finally:        
        Utils.writelog(
            logger=app.logger,
            level="INFO",
            message=f"Завершение работы {app.__class__.__name__}"
        )