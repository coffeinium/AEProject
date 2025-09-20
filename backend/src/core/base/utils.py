from ..services.applogger import Logger
from typing import Optional
import inspect
from typing import List, Dict, Any
import pandas as pd
import re


class Utils:
    @staticmethod
    def writelog(
        logger: Optional[Logger] = None,
        level: Optional[str] = "DEBUG",
        message: Optional[str] = None,
    ) -> bool:
        """
        Записывает сообщение в лог с информацией о месте вызова.
        
        Метод автоматически определяет класс и метод, из которого был вызван,
        и добавляет эту информацию в префикс сообщения в формате [ClassName.method_name].
        Если логгер не передан, сообщение выводится через print.
        
        Args:
            logger (Logger): Объект логгера для записи сообщений. Если None, сообщение будет выведено через print
            level (str): Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL). По умолчанию "DEBUG"
            message (str): Текст сообщения для логирования. Если None, сообщение не будет записано
            
        Returns:
            bool: True если сообщение было успешно записано, False если message равен None
            
        Example:
            >>> Utils.writelog(
            ...     logger=logger,
            ...     level="INFO",
            ...     message="Операция успешно завершена"
            ... )
            # Результат в логе: [MyClass.process_data] Операция успешно завершена
            
            >>> Utils.writelog(
            ...     level="WARNING",
            ...     message="Предупреждение"
            ... )
            # Результат в консоли: [WARNING] Предупреждение
        """
        if message is None:
            return False
            
        stack = inspect.stack()
        caller = None
        for frame in stack[1:]:
            if frame.filename.endswith('base.py') and frame.function == 'writelog':
                continue
            caller = frame
            break
        
        if caller:
            try:
                class_name = None
                if 'self' in caller.frame.f_locals:
                    class_name = caller.frame.f_locals['self'].__class__.__name__
                
                if not class_name:
                    for name, obj in caller.frame.f_locals.items():
                        if inspect.isclass(obj) and isinstance(caller.frame.f_locals.get('self'), obj):
                            class_name = name
                            break
                
                if class_name and class_name not in ['<module>', 'module']:
                    prefix = f"[{class_name}.{caller.function}] "
                else:
                    prefix = ""
            except Exception:
                prefix = ""
        else:
            prefix = ""
        
        if logger is not None:
            if prefix:
                getattr(logger, level.lower())(f"{prefix}{message}")
            else:
                getattr(logger, level.lower())(message)
        else:
            if prefix:
                print(f"[{level}] {prefix}{message}")
            else:
                print(f"[{level}] {message}")
                
        return True
    
    @staticmethod
    def universal_conventer_xls_to_json(
        file_path: str,
        logger: Optional[Logger] = None
    ) -> List[Dict[str, Any]]:
        """
        Конвертирует Excel файл с контрактами в JSON формат.
        
        Args:
            file_path (str): Путь к Excel файлу
            logger (Logger, optional): Объект логгера для записи сообщений
            
        Returns:
            List[Dict[str, Any]]: Список словарей с данными
                
        Example:
            >>> contracts = Utils.universal_conventer_xls_to_json("contracts.xlsx", logger)
            >>> print(f"Загружено {len(contracts)} записей")
        """
        Utils.writelog(
            logger=logger,
            level="INFO",
            message=f"Конвертация Excel файла: {file_path}"
        )
        
        try:
            df = pd.read_excel(file_path)
            
            # Замена NaN значений на None для корректной JSON сериализации
            df = df.where(pd.notnull(df), None)
            
            # Обработка дат
            date_columns = df.select_dtypes(include=['datetime64']).columns
            for col in date_columns:
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S').where(df[col].notnull(), None)
            
            contracts_data = df.to_dict('records')
            
            Utils.writelog(
                logger=logger,
                level="INFO",
                message=f"Конвертировано {len(contracts_data)} записей"
            )
            
            return contracts_data
            
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка конвертации {file_path}: {str(e)}"
            )
            return []
    
    @staticmethod
    def sanitize_input(
        text: str,
        max_length: Optional[int] = 1000,
        allow_special_chars: bool = False,
        logger: Optional[Logger] = None,
    ) -> str:
        """
        Валидация и санитизация входных данных для защиты от инъекций и переполнения.
        
        Args:
            text (str): Входной текст для обработки
            max_length (Optional[int]): Максимальная длина текста. По умолчанию MAX_QUERY_LENGTH
            allow_special_chars (bool): Разрешить специальные символы (по умолчанию False)
            logger (Optional[Logger]): Логгер для записи операций
            
        Returns:
            str: Очищенный и валидированный текст
            
        Raises:
            ValueError: Если текст слишком длинный или содержит недопустимые символы
            TypeError: Если входной параметр не является строкой
            
        Example:
            >>> clean_text = Utils.sanitize_input("Привет <script>", max_length=50)
            >>> print(clean_text)  # "Привет "
            
            >>> Utils.sanitize_input("Очень длинный текст...", max_length=10)
            # Raises ValueError: "Текст слишком длинный"
        """
        try:
            # Проверка типа входных данных
            if not isinstance(text, str):
                raise TypeError(f"Ожидается строка, получен {type(text).__name__}")
            # Проверка длины текста
            if len(text) > max_length:
                Utils.writelog(
                    logger=logger,
                    level="WARNING",
                    message=f"Текст превышает максимальную длину {max_length}: {len(text)} символов"
                )
                raise ValueError(f"Текст слишком длинный: {len(text)} символов (максимум: {max_length})")
            
            # Базовая санитизация - удаление потенциально опасных символов
            if not allow_special_chars:
                # Удаляем HTML/XML теги и потенциально опасные символы
                sanitized = re.sub(r'[<>"\'\\\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
                
                # Удаляем SQL инъекции
                sql_patterns = [
                    r'(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)',
                    r'(?i)(script|javascript|vbscript)',
                    r'--',
                    r'/\*.*?\*/',
                    r';'
                ]
                
                for pattern in sql_patterns:
                    sanitized = re.sub(pattern, '', sanitized)
            else:
                # Минимальная санитизация - только удаление нулевых байтов и управляющих символов
                sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            
            # Удаление лишних пробелов
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()
            
            # Логирование если были изменения
            if sanitized != text:
                Utils.writelog(
                    logger=logger,
                    level="DEBUG",
                    message=f"Текст санитизирован: '{text[:50]}...' -> '{sanitized[:50]}...'"
                )
            
            Utils.writelog(
                logger=logger,
                level="DEBUG",
                message=f"Валидация прошла успешно: длина {len(sanitized)} символов"
            )
            
            return sanitized
            
        except (ValueError, TypeError) as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка валидации входных данных: {e}"
            )
            raise
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Неожиданная ошибка при санитизации: {e}"
            )
            raise ValueError(f"Ошибка обработки входных данных: {e}")
    
    @staticmethod
    def validate_search_query(
        query: str,
        logger: Optional[Logger] = None
    ) -> str:
        """
        Специализированная валидация поисковых запросов.
        
        Args:
            query (str): Поисковый запрос
            logger (Optional[Logger]): Логгер для записи операций
            
        Returns:
            str: Валидированный поисковый запрос
            
        Raises:
            ValueError: Если запрос пустой или содержит недопустимые символы
            
        Example:
            >>> clean_query = Utils.validate_search_query("контракт 2024")
            >>> print(clean_query)  # "контракт 2024"
        """
        try:
            # Санитизация с разрешением некоторых специальных символов для поиска
            sanitized_query = Utils.sanitize_input(
                text=query,
                max_length=1000,
                allow_special_chars=False,
                logger=logger
            )
            
            # Проверка на пустой запрос
            if not sanitized_query or len(sanitized_query.strip()) == 0:
                raise ValueError("Поисковый запрос не может быть пустым")
            
            # Проверка минимальной длины
            if len(sanitized_query.strip()) < 2:
                raise ValueError("Поисковый запрос слишком короткий (минимум 2 символа)")
            
            Utils.writelog(
                logger=logger,
                level="DEBUG",
                message=f"Поисковый запрос валидирован: '{sanitized_query}'"
            )
            
            return sanitized_query
            
        except Exception as e:
            Utils.writelog(
                logger=logger,
                level="ERROR",
                message=f"Ошибка валидации поискового запроса: {e}"
            )
            raise