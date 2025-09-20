import os
from typing import (
    Any, 
    Dict, 
    List, 
    Optional, 
    Union
)

from rich.table import Table
from rich.console import Console

class EnvReader:
    """
    Класс для работы с переменными окружения.
    
    Этот класс предоставляет удобный интерфейс для чтения и управления
    переменными окружения. Поддерживает автоматическое преобразование типов
    и валидацию обязательных переменных.
    
    Attributes:
        env_data (Dict[str, Any]): Словарь с переменными окружения.
        required_vars (List[str]): Список обязательных переменных окружения.
    
    Examples:
        >>> env = EnvReader(required_vars=["API_KEY"])
        >>> api_key = env.API_KEY
        >>> debug_mode = env.get("DEBUG", False)
    """
    
    def __init__(
        self, 
        required_vars: Optional[List[str]] = None
    ) -> None:
        """
        Инициализация EnvReader.
        
        Args:
            required_vars (Optional[List[str]]): Список обязательных переменных окружения.
        
        Raises:
            ValueError: Если отсутствуют обязательные переменные окружения.
        """
        self.console = Console()
        self.env_data: Dict[str, Any] = {}
        self.required_vars = required_vars or []
        
        self._load_envs()
        self._validate_required_vars()
        self._display_env_table()

    def _load_envs(self) -> None:
        """
        Загрузка всех переменных окружения в env_data.
        
        Автоматически преобразует значения в соответствующие типы данных.
        """
        for name, value in os.environ.items():
            self.env_data[name.strip()] = self._convert_type(value.strip())

    def _convert_type(self, value: str) -> Union[str, bool, int, float, List[str]]:
        """
        Преобразование строкового значения в соответствующий тип данных.
        
        Args:
            value (str): Строковое значение для преобразования.
        
        Returns:
            Union[str, bool, int, float, List[str]]: Преобразованное значение.
            
        Note:
            Поддерживает следующие преобразования:
            - "true"/"false" -> bool
            - Целые числа -> int
            - Числа с плавающей точкой -> float
            - Строки с запятыми -> List[str]
            - Остальные значения -> str
        """
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            pass
        if "," in value:
            return [v.strip() for v in value.split(",")]
        return value

    def _validate_required_vars(self) -> None:
        """
        Проверка наличия всех обязательных переменных окружения.
        
        Raises:
            ValueError: Если отсутствуют обязательные переменные.
        """
        missing_vars = [var for var in self.required_vars if var not in self.env_data]
        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")

    def __getattr__(self, name: str) -> Any:
        """
        Получение значения переменной окружения через атрибут.
        
        Args:
            name (str): Имя переменной окружения.
        
        Returns:
            Any: Значение переменной окружения.
        
        Raises:
            AttributeError: Если переменная не найдена.
        """
        if name in self.env_data:
            return self.env_data[name]
        raise AttributeError(f"Переменная окружения '{name}' не найдена.")

    def get(self, name: str, default: Any = None) -> Any:
        """
        Безопасное получение значения переменной окружения.
        
        Args:
            name (str): Имя переменной окружения.
            default (Any): Значение по умолчанию, если переменная не найдена.
        
        Returns:
            Any: Значение переменной окружения или значение по умолчанию.
        """
        return self.env_data.get(name, default)

    def set(self, name: str, value: Any) -> None:
        """
        Установка значения переменной окружения.
        
        Args:
            name (str): Имя переменной окружения.
            value (Any): Значение для установки.
        """
        self.env_data[name] = value
        os.environ[name] = str(value)

    def update(self, env_dict: Dict[str, Any]) -> None:
        """
        Обновление нескольких переменных окружения.
        
        Args:
            env_dict (Dict[str, Any]): Словарь с переменными для обновления.
        """
        for key, value in env_dict.items():
            self.set(key, value)

    def list_env_vars(self) -> List[str]:
        """
        Получение списка всех переменных окружения.
        
        Returns:
            List[str]: Список имен переменных окружения.
        """
        return list(self.env_data.keys())

    def _display_env_table(self) -> None:
        """
        Отображение таблицы с переменными окружения.
        
        Выводит таблицу с информацией о переменных окружения, включая их значения
        и типы. Чувствительные данные (содержащие TOKEN, KEY, SHA) маскируются.
        """
        table = Table(title="Переменные окружения")
        table.add_column("Переменная", style="bold cyan")
        table.add_column("Значение", style="bold green")
        table.add_column("Тип", style="bold yellow")

        for key, value in self.env_data.items():
            display_value = "*" * len(str(value)) if any(substr in key.upper() for substr in ["TOKEN", "KEY", "SHA"]) else str(value)
            value_type = type(value).__name__
            table.add_row(key, display_value, value_type)

        self.console.print(table)