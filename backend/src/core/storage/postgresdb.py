from typing import (
    Any, 
    Dict, 
    List, 
    Optional, 
    Union
)
from contextlib import asynccontextmanager
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..services.applogger import Logger
from ..base.utils import Utils
from .mixins import (
    ContractsMixin, 
    SessionsMixin,
    HistoryMixin
)


class PostgresStorage(ContractsMixin, SessionsMixin, HistoryMixin):
    """
    Главный класс для работы с PostgreSQL.
    Предоставляет универсальные методы и специализированные методы через миксины.
    
    Example:
        >>> storage = PostgresStorage(database_url, logger)
        >>> await storage.initialize()
        >>> contracts = await storage.search_contracts("тест")
    """
    
    def __init__(self, database_url: str, logger: Optional[Logger] = None):
        self.database_url = database_url
        self.logger = logger
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Инициализация подключений к базе данных"""
        try:
            # Синхронный движок для pandas операций
            self.engine = create_engine(
                self.database_url,
                poolclass=NullPool,
                echo=False
            )
            
            # Асинхронный движок для async операций
            async_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
            self.async_engine = create_async_engine(
                async_url,
                poolclass=NullPool,
                echo=False
            )
            
            self.session_factory = sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message="PostgreSQL подключения инициализированы"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка инициализации PostgreSQL: {e}"
            )
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Контекстный менеджер для получения асинхронной сессии"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Универсальный метод для выполнения SELECT запросов
        
        Args:
            query (str): SQL запрос
            params (Dict, optional): Параметры запроса
            
        Returns:
            List[Dict]: Результаты запроса
            
        Example:
            >>> results = await storage.execute_query(
            ...     "SELECT * FROM aeproject.contracts WHERE contract_amount > :amount",
            ...     {"amount": 100000}
            ... )
        """
        async with self.get_session() as session:
            try:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                
                # Конвертация в список словарей
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
                
            except Exception as e:
                Utils.writelog(
                    logger=self.logger,
                    level="ERROR",
                    message=f"Ошибка выполнения запроса: {e}"
                )
                raise
    
    async def execute_insert(self, table: str, data: Union[Dict, List[Dict]], ignore_conflicts: bool = False) -> int:
        """
        Универсальный метод для вставки данных
        
        Args:
            table (str): Имя таблицы
            data (Union[Dict, List[Dict]]): Данные для вставки
            ignore_conflicts (bool): Игнорировать конфликты уникальности
            
        Returns:
            int: Количество вставленных записей
            
        Example:
            >>> count = await storage.execute_insert(
            ...     "aeproject.contracts",
            ...     {"contract_name": "Test", "contract_amount": 100000},
            ...     ignore_conflicts=True
            ... )
        """
        if isinstance(data, dict):
            data = [data]
        
        if not data:
            return 0
        
        columns = list(data[0].keys())
        columns_str = ', '.join(columns)
        placeholders = ', '.join([f':{col}' for col in columns])
        
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        if ignore_conflicts:
            query += " ON CONFLICT DO NOTHING"
        
        async with self.get_session() as session:
            try:
                result = await session.execute(text(query), data)
                await session.commit()
                
                if ignore_conflicts and (not hasattr(result, 'rowcount') or result.rowcount == -1):
                    inserted_count = len(data)
                    Utils.writelog(
                        logger=self.logger,
                        level="DEBUG",
                        message=f"Обработано {inserted_count} записей в таблицу {table} (с игнорированием конфликтов)"
                    )
                else:
                    inserted_count = result.rowcount if hasattr(result, 'rowcount') else len(data)
                    Utils.writelog(
                        logger=self.logger,
                        level="DEBUG",
                        message=f"Вставлено {inserted_count} записей в таблицу {table}"
                    )
                
                return inserted_count
                
            except Exception as e:
                Utils.writelog(
                    logger=self.logger,
                    level="ERROR",
                    message=f"Ошибка вставки в таблицу {table}: {e}"
                )
                raise
    
    async def execute_update(self, table: str, data: Dict, where_clause: str, where_params: Optional[Dict] = None) -> int:
        """
        Универсальный метод для обновления данных
        
        Args:
            table (str): Имя таблицы
            data (Dict): Данные для обновления
            where_clause (str): WHERE условие
            where_params (Dict, optional): Параметры WHERE условия
            
        Returns:
            int: Количество обновленных записей
            
        Example:
            >>> updated = await storage.execute_update(
            ...     "aeproject.contracts",
            ...     {"contract_amount": 150000},
            ...     "contract_id = :id",
            ...     {"id": 12345}
            ... )
        """
        set_clause = ', '.join([f"{col} = :{col}" for col in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = {**data}
        if where_params:
            params.update(where_params)
        
        async with self.get_session() as session:
            try:
                result = await session.execute(text(query), params)
                await session.commit()
                
                Utils.writelog(
                    logger=self.logger,
                    level="DEBUG",
                    message=f"Обновлено {result.rowcount} записей в таблице {table}"
                )
                
                return result.rowcount
                
            except Exception as e:
                Utils.writelog(
                    logger=self.logger,
                    level="ERROR",
                    message=f"Ошибка обновления таблицы {table}: {e}"
                )
                raise
    
    async def execute_delete(self, table: str, where_clause: str, where_params: Optional[Dict] = None) -> int:
        """
        Универсальный метод для удаления данных
        
        Args:
            table (str): Имя таблицы
            where_clause (str): WHERE условие
            where_params (Dict, optional): Параметры WHERE условия
            
        Returns:
            int: Количество удаленных записей
            
        Example:
            >>> deleted = await storage.execute_delete(
            ...     "aeproject.contracts",
            ...     "contract_id = :id",
            ...     {"id": 12345}
            ... )
        """
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        async with self.get_session() as session:
            try:
                result = await session.execute(text(query), where_params or {})
                await session.commit()
                
                Utils.writelog(
                    logger=self.logger,
                    level="DEBUG",
                    message=f"Удалено {result.rowcount} записей из таблицы {table}"
                )
                
                return result.rowcount
                
            except Exception as e:
                Utils.writelog(
                    logger=self.logger,
                    level="ERROR",
                    message=f"Ошибка удаления из таблицы {table}: {e}"
                )
                raise
    
    def bulk_insert_from_dataframe(self, table: str, df: pd.DataFrame, schema: str = "aeproject") -> int:
        """
        Массовая вставка данных из pandas DataFrame
        
        Args:
            table (str): Имя таблицы
            df (pd.DataFrame): DataFrame с данными
            schema (str): Схема базы данных
            
        Returns:
            int: Количество вставленных записей
            
        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame([{"contract_name": "Test", "contract_amount": 100000}])
            >>> count = storage.bulk_insert_from_dataframe("contracts", df)
        """
        try:
            full_table_name = f"{schema}.{table}" if schema else table
            
            df = df.where(pd.notnull(df), None)
            
            rows_inserted = df.to_sql(
                table,
                self.engine,
                schema=schema,
                if_exists='append',
                index=False,
                method='multi'
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Массовая вставка: {len(df)} записей в таблицу {full_table_name}"
            )
            
            return len(df)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка массовой вставки в таблицу {table}: {e}"
            )
            raise
    
    async def get_table_stats(self, table: str, schema: str = "aeproject") -> Dict[str, Any]:
        """
        Получение статистики по таблице
        
        Args:
            table (str): Имя таблицы
            schema (str): Схема базы данных
            
        Returns:
            Dict[str, Any]: Статистика таблицы
        """
        full_table_name = f"{schema}.{table}"
        
        queries = {
            'count': f"SELECT COUNT(*) as total FROM {full_table_name}",
            'size': f"""
                SELECT pg_size_pretty(pg_total_relation_size('{full_table_name}')) as size
            """,
            'last_updated': f"""
                SELECT MAX(updated_at) as last_updated FROM {full_table_name}
            """
        }
        
        stats = {}
        for key, query in queries.items():
            try:
                result = await self.execute_query(query)
                stats[key] = result[0] if result else None
            except Exception as e:
                Utils.writelog(
                    logger=self.logger,
                    level="WARNING",
                    message=f"Не удалось получить статистику {key} для таблицы {table}: {e}"
                )
                stats[key] = None
        
        return stats
    
    async def close(self):
        """Закрытие подключений к базе данных"""
        try:
            if self.engine:
                self.engine.dispose()
            if self.async_engine:
                await self.async_engine.dispose()
                
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message="PostgreSQL подключения закрыты"
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка закрытия PostgreSQL подключений: {e}"
            )
    
    async def get_database_overview(self) -> dict:
        """
        Получение общего обзора базы данных
        
        Returns:
            dict: Обзор всех таблиц и их статистика
            
        Example:
            >>> overview = await storage.get_database_overview()
            >>> print(f"Всего контрактов: {overview['contracts']['total_count']['total']}")
        """
        try:
            contracts_stats = await self.get_contracts_stats()
            sessions_stats = await self.get_sessions_stats()
            history_stats = await self.get_history_stats()
            
            overview = {
                'contracts': contracts_stats,
                'sessions': sessions_stats,
                'history': history_stats,
                'summary': {
                    'total_contracts': contracts_stats.get('total_count', {}).get('total', 0) if contracts_stats.get('total_count') else 0,
                    'total_sessions': sessions_stats.get('total_count', {}).get('total', 0) if sessions_stats.get('total_count') else 0,
                    'total_history': history_stats.get('total_count', {}).get('total', 0) if history_stats.get('total_count') else 0,
                }
            }
            
            return overview
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения обзора БД: {e}"
            )
            raise
