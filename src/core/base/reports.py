import os
import sys
import platform
from datetime import datetime
from typing import List
from pathlib import Path

class ReportManager:
    """
    Менеджер системы отчетов для обработки и сохранения информации об ошибках.
    
    Класс предоставляет функционал для генерации красиво отформатированных отчетов
    об ошибках, их сохранения в файлы и получения списка последних отчетов.
    
    Настройки менеджера загружаются из переменных окружения с префиксом 'REPORT_':
        - REPORT_ERROR_REPORTS_PATH: путь для сохранения отчетов (по умолчанию: 'reports/errors')
        - REPORT_ERROR_REPORT_PREFIX: префикс для имен файлов (по умолчанию: 'error')
        - REPORT_ERROR_REPORT_EXTENSION: расширение файлов (по умолчанию: 'report')
        - REPORT_ERROR_REPORT_FORMAT: формат временной метки (по умолчанию: '%Y-%m-%d_%H-%M-%S')
    
    Пример использования:
        >>> from components.modules import EnvLoader, ReportManager
        >>> env = EnvLoader()
        >>> report_manager = ReportManager(env)
        >>> 
        >>> try:
        ...     # Код, который может вызвать ошибку
        ...     raise ValueError("Пример ошибки")
        ... except Exception as e:
        ...     report = report_manager.generate_error_report(e, traceback.format_exc())
        ...     filepath = report_manager.save_error_report(report)
        ...     print(f"Отчет сохранен в: {filepath}")
        ...
        >>> # Получение последних отчетов
        >>> latest_reports = report_manager.get_latest_error_reports(limit=3)
        >>> for report in latest_reports:
        ...     print(f"Найден отчет: {report}")
    """

    def __init__(self, env) -> None:
        """
        Инициализация менеджера отчетов.

        Args:
            env: Объект с настройками окружения, содержащий переменные с префиксом 'REPORT_'

        Example:
            >>> env = EnvLoader()
            >>> report_manager = ReportManager(env)
            >>> print(report_manager.settings)
            {'error_reports_path': 'reports/errors', ...}
        """
        self.settings = {
            key.replace('REPORT_', '').lower(): value
            for key, value in env.env_data.items()
            if key.startswith('REPORT_')
        }

    def generate_error_report(self, error: Exception, traceback_str: str) -> str:
        """
        Генерирует отчет об ошибке в читаемом формате с красивым форматированием.

        Args:
            error: Объект исключения, содержащий информацию об ошибке
            traceback_str: Строка с полным трейсбеком ошибки

        Returns:
            str: Отформатированный отчет об ошибке с рамкой и структурированной информацией
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_type = error.__class__.__name__
        error_msg = str(error)
        
        # Системная информация
        system_info = {
            "Python Version": sys.version.split()[0],
            "Platform": platform.platform(),
            "Working Directory": os.getcwd(),
            "Process ID": os.getpid()
        }
        
        # Форматируем трейсбек
        formatted_traceback = []
        for line in traceback_str.split('\n'):
            if line.strip():
                if line.startswith('  File'):
                    # Выделяем файл и строку
                    parts = line.split(',')
                    if len(parts) >= 2:
                        file_part = parts[0].strip()
                        line_part = parts[1].strip()
                        formatted_traceback.append(f"│ {file_part}")
                        formatted_traceback.append(f"│ {line_part}")
                    else:
                        formatted_traceback.append(f"│ {line}")
                else:
                    formatted_traceback.append(f"│ {line}")
        
        # Собираем отчет
        report = [
            "┌" + "─" * 80,
            "│ ОТЧЕТ ОБ ОШИБКЕ",
            "├" + "─" * 80,
            f"│ Время:    {timestamp}",
            f"│ Тип:      {error_type}",
            f"│ Ошибка:   {error_msg}",
            "├" + "─" * 80,
            "│ СИСТЕМНАЯ ИНФОРМАЦИЯ:"
        ]
        
        # Добавляем системную информацию
        for key, value in system_info.items():
            report.append(f"│ {key:<15}: {value}")
            
        report.extend([
            "├" + "─" * 80,
            "│ ТРЕЙСБЕК:"
        ])
        
        # Добавляем трейсбек
        report.extend(formatted_traceback)
        report.append("└" + "─" * 80)
        
        return "\n".join(report)

    def save_error_report(self, report: str) -> str:
        """
        Сохраняет отчет об ошибке в файл с уникальным именем, основанным на временной метке.

        Args:
            report: Текст отчета для сохранения

        Returns:
            str: Абсолютный путь к сохраненному файлу отчета

        Raises:
            OSError: При ошибке создания директории или сохранения файла

        Example:
            >>> report = "Пример отчета"
            >>> filepath = report_manager.save_error_report(report)
            >>> print(f"Отчет сохранен в: {filepath}")
            Отчет сохранен в: /path/to/reports/errors/error_2024-01-20_15-30-45.report
        """
        reports_path = self.settings.get('error_reports_path', 'reports/errors')
        os.makedirs(reports_path, exist_ok=True)
        
        timestamp = datetime.now().strftime(self.settings.get('error_report_format', '%Y-%m-%d_%H-%M-%S'))
        prefix = self.settings.get('error_report_prefix', 'error')
        extension = self.settings.get('error_report_extension', 'report')
        filename = f"{prefix}_{timestamp}.{extension}"
        filepath = os.path.join(reports_path, filename)
        
        with open(filepath, "w", encoding='utf-8') as file:
            file.write(report)
            
        return filepath

    def get_latest_error_reports(self, limit: int = 5) -> List[Path]:
        """
        Получает список последних отчетов об ошибках, отсортированных по времени создания.

        Args:
            limit: Максимальное количество отчетов для возврата (по умолчанию: 5)

        Returns:
            List[Path]: Список путей к файлам отчетов, отсортированный по времени создания
                       (самые новые сначала). Если директория с отчетами не существует,
                       возвращается пустой список.

        Example:
            >>> reports = report_manager.get_latest_error_reports(limit=3)
            >>> for report in reports:
            ...     print(f"Найден отчет: {report}")
            Найден отчет: /path/to/reports/errors/error_2024-01-20_15-30-45.report
            Найден отчет: /path/to/reports/errors/error_2024-01-20_15-25-30.report
            Найден отчет: /path/to/reports/errors/error_2024-01-20_15-20-15.report
        """
        reports_path = self.settings.get('error_reports_path', 'reports/errors')
        reports_dir = Path(reports_path)
        if not reports_dir.exists():
            return []
            
        prefix = self.settings.get('error_report_prefix', 'error')
        extension = self.settings.get('error_report_extension', 'report')
        reports = sorted(
            reports_dir.glob(f"{prefix}_*.{extension}"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        return reports[:limit]
