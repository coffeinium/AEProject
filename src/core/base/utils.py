from ..services.applogger import Logger
from typing import Optional
import inspect
from datetime import datetime

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