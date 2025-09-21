import os
from ...core.base.utils import Utils


async def register_routes(app, **kwargs):
    """
    Автоматическая загрузка данных в БД если их еще нет
    
    Args:
        app: FastAPI приложение
        **kwargs: Дополнительные параметры (env, templates, logger, report_manager, storage)
    """
    env = kwargs.get('env')
    logger = kwargs.get('logger')
    storage = kwargs.get('storage')
    
    if not storage:
        Utils.writelog(logger=logger, level="ERROR", message="Storage не инициализирован")
        return
    
    try:
        contracts_count, sessions_count = await _get_current_counts(storage)
        
        Utils.writelog(
            logger=logger,
            level="INFO",
            message=f"Текущее состояние БД: контрактов={contracts_count}, сессий={sessions_count}"
        )
        
        contracts_file = getattr(env, 'AEAPISETTINGS_API_IMITATION_CONTRACTS_PATH', None)
        sessions_file = getattr(env, 'AEAPISETTINGS_API_IMITATION_SESSIONS_PATH', None)
        
        await _load_contracts_if_needed(storage, logger, contracts_count, contracts_file)
        await _load_sessions_if_needed(storage, logger, sessions_count, sessions_file)
        
        final_contracts_count, final_sessions_count = await _get_current_counts(storage)
        
        Utils.writelog(
            logger=logger,
            level="INFO",
            message=f"Инициализация БД завершена: контрактов={final_contracts_count}, сессий={final_sessions_count}"
        )
        
    except Exception as e:
        Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка инициализации данных БД: {e}")


async def _get_current_counts(storage):
    """Получение текущего количества записей в БД"""
    contracts_stats = await storage.get_contracts_stats()
    sessions_stats = await storage.get_sessions_stats()
    
    contracts_count = _extract_count(contracts_stats)
    sessions_count = _extract_count(sessions_stats)
    
    return contracts_count, sessions_count


def _extract_count(stats):
    """Извлечение количества записей из статистики"""
    return stats.get('total_count', {}).get('total', 0) if stats and stats.get('total_count') else 0


async def _load_contracts_if_needed(storage, logger, current_count, file_path):
    """Загрузка контрактов если их нет в БД"""
    if current_count > 0 or not file_path or not os.path.exists(file_path):
        return
    
    if not _is_excel_file(file_path):
        Utils.writelog(logger=logger, level="WARNING", message=f"Файл {file_path} не является Excel файлом")
        return
    
    try:
        loaded_count = await storage.insert_contracts_from_excel(file_path)
        Utils.writelog(logger=logger, level="INFO", message=f"Загружено {loaded_count} контрактов из {file_path}")
    except Exception as e:
        Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка загрузки контрактов из {file_path}: {e}")


async def _load_sessions_if_needed(storage, logger, current_count, file_path):
    """Загрузка сессий если их нет в БД"""
    if current_count > 0 or not file_path or not os.path.exists(file_path):
        return
    
    if not _is_excel_file(file_path):
        Utils.writelog(logger=logger, level="WARNING", message=f"Файл {file_path} не является Excel файлом")
        return
    
    try:
        loaded_count = await storage.insert_sessions_from_excel(file_path)
        Utils.writelog(logger=logger, level="INFO", message=f"Загружено {loaded_count} сессий из {file_path}")
    except Exception as e:
        Utils.writelog(logger=logger, level="ERROR", message=f"Ошибка загрузки сессий из {file_path}: {e}")


def _is_excel_file(file_path):
    """Проверка является ли файл Excel файлом"""
    return file_path.endswith(('.xlsx', '.xls'))
