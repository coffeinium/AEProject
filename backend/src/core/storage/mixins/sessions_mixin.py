from typing import (
    Any, 
    Dict, 
    List, 
    Optional, 
)
from datetime import datetime
from dateutil import parser

from ...base.utils import Utils


class SessionsMixin:
    """Миксин для работы с таблицей конкурсных сессий"""
    
    SESSIONS_SCHEMA = "aeproject"
    SESSIONS_TABLE = "sessions"
    
    async def insert_session(self, session_data: Dict[str, Any]) -> int:
        """
        Вставка одной конкурсной сессии
        
        Args:
            session_data (Dict[str, Any]): Данные сессии
            
        Returns:
            int: ID вставленной сессии
            
        Example:
            >>> session = {
            ...     "session_name": "Тестовая сессия",
            ...     "session_id": 67890,
            ...     "session_amount": 50000.25,
            ...     "session_created_date": "2025-01-01 10:00:00",
            ...     "session_completed_date": "2025-01-01 15:00:00",
            ...     "customer_name": "ООО Заказчик",
            ...     "customer_inn": 1111111111,
            ...     "supplier_name": "ИП Исполнитель",
            ...     "supplier_inn": 2222222222,
            ...     "law_basis": "44-ФЗ"
            ... }
            >>> await storage.insert_session(session)
        """
        try:
            session_data['created_at'] = datetime.now()
            session_data['updated_at'] = datetime.now()
            session_data.pop('id', None)
            
            result = await self.execute_insert(
                f"{self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
                session_data
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Сессия {session_data.get('session_id')} вставлена"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка вставки сессии: {e}"
            )
            raise
    
    async def insert_sessions_bulk(self, sessions_data: List[Dict[str, Any]]) -> int:
        """
        Массовая вставка конкурсных сессий
        
        Args:
            sessions_data (List[Dict[str, Any]]): Список данных сессий
            
        Returns:
            int: Количество вставленных сессий
            
        Example:
            >>> sessions = [
            ...     {"session_name": "Сессия 1", "session_id": 1001, "session_amount": 10000},
            ...     {"session_name": "Сессия 2", "session_id": 1002, "session_amount": 20000}
            ... ]
            >>> count = await storage.insert_sessions_bulk(sessions)
        """
        try:
            current_time = datetime.now()
            
            for session in sessions_data:
                session['created_at'] = current_time
                session['updated_at'] = current_time
                session.pop('id', None)
            
            result = await self.execute_insert(
                f"{self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
                sessions_data
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Массовая вставка: {result} сессий"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка массовой вставки сессий: {e}"
            )
            raise
    
    async def insert_sessions_from_excel(self, file_path: str) -> int:
        """
        Вставка сессий из Excel файла
        
        Args:
            file_path (str): Путь к Excel файлу
            
        Returns:
            int: Количество вставленных сессий
            
        Example:
            >>> count = storage.insert_sessions_from_excel("sessions.xlsx")
            >>> print(f"Загружено {count} сессий")
        """
        try:
            sessions_data = Utils.universal_conventer_xls_to_json(file_path, self.logger)
            
            if not sessions_data:
                Utils.writelog(
                    logger=self.logger,
                    level="WARNING",
                    message=f"Нет данных для загрузки из файла {file_path}"
                )
                return 0
            
            mapped_sessions = []
            column_mapping = {
                'Наименование КС': 'session_name',
                'ID КС': 'session_id',
                'Сумма КС': 'session_amount',
                'Дата создания КС': 'session_created_date',
                'Дата завершения КС': 'session_completed_date',
                'Категория ПП первой позиции спецификации': 'category_pp_first_position',
                'Наименование заказчика': 'customer_name',
                'ИНН заказчика': 'customer_inn',
                'Наименование поставщика': 'supplier_name',
                'ИНН поставщика': 'supplier_inn',
                'Закон-основание': 'law_basis'
            }
            
            current_time = datetime.now()
            
            for session in sessions_data:
                mapped_session = {}
                date_fields = ['session_created_date', 'session_completed_date']
                
                for excel_col, db_col in column_mapping.items():
                    if excel_col in session and session[excel_col] is not None:
                        value = session[excel_col]
                        if db_col in date_fields and isinstance(value, str):
                            try:
                                value = parser.parse(value)
                            except:
                                value = None
                        mapped_session[db_col] = value
                
                mapped_session['created_at'] = current_time
                mapped_session['updated_at'] = current_time
                mapped_sessions.append(mapped_session)
            
            if mapped_sessions:
                result = await self.execute_insert(
                    f"{self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
                    mapped_sessions,
                    ignore_conflicts=True
                )
            else:
                result = 0
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Загружено {result} сессий из файла {file_path}"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка загрузки сессий из Excel: {e}"
            )
            raise
    
    async def get_session_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение сессии по ID
        
        Args:
            session_id (int): ID сессии
            
        Returns:
            Optional[Dict[str, Any]]: Данные сессии или None
            
        Example:
            >>> session = await storage.get_session_by_id(12345)
            >>> if session:
            ...     print(f"Сессия: {session['session_name']}")
        """
        query = f"""
            SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE session_id = :session_id
        """
        
        try:
            result = await self.execute_query(query, {'session_id': session_id})
            return result[0] if result else None
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения сессии по ID {session_id}: {e}"
            )
            raise
    
    async def get_sessions_by_customer(self, customer_inn: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение сессий по ИНН заказчика
        
        Args:
            customer_inn (int): ИНН заказчика
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список сессий
        """
        query = f"""
            SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE customer_inn = :customer_inn
            ORDER BY session_created_date DESC
            LIMIT :limit
        """
        
        try:
            return await self.execute_query(query, {
                'customer_inn': customer_inn,
                'limit': limit
            })
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения сессий по заказчику {customer_inn}: {e}"
            )
            raise
    
    async def get_sessions_by_supplier(self, supplier_inn: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение сессий по ИНН поставщика
        
        Args:
            supplier_inn (int): ИНН поставщика
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список сессий
        """
        query = f"""
            SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE supplier_inn = :supplier_inn
            ORDER BY session_created_date DESC
            LIMIT :limit
        """
        
        try:
            return await self.execute_query(query, {
                'supplier_inn': supplier_inn,
                'limit': limit
            })
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения сессий по поставщику {supplier_inn}: {e}"
            )
            raise
    
    async def get_active_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение активных сессий (созданных, но не завершенных)
        
        Args:
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список активных сессий
            
        Example:
            >>> active = await storage.get_active_sessions(limit=20)
            >>> print(f"Активных сессий: {len(active)}")
        """
        query = f"""
            SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE session_completed_date > session_created_date
            AND session_completed_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY session_created_date DESC
            LIMIT :limit
        """
        
        try:
            return await self.execute_query(query, {'limit': limit})
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения активных сессий: {e}"
            )
            raise
    
    async def get_sessions_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Получение сессий по диапазону дат создания
        
        Args:
            start_date (datetime): Начальная дата
            end_date (datetime): Конечная дата
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список сессий
        """
        query = f"""
            SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE session_created_date BETWEEN :start_date AND :end_date
            ORDER BY session_created_date DESC
            LIMIT :limit
        """
        
        try:
            return await self.execute_query(query, {
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit
            })
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения сессий по датам {start_date}-{end_date}: {e}"
            )
            raise
    
    async def get_sessions_by_completion_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Получение сессий по диапазону дат завершения
        
        Args:
            start_date (datetime): Начальная дата
            end_date (datetime): Конечная дата
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список сессий
        """
        query = f"""
            SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE session_completed_date BETWEEN :start_date AND :end_date
            ORDER BY session_completed_date DESC
            LIMIT :limit
        """
        
        try:
            return await self.execute_query(query, {
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit
            })
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения сессий по датам завершения {start_date}-{end_date}: {e}"
            )
            raise
    
    async def get_sessions_by_amount_range(
        self, 
        min_amount: float, 
        max_amount: float,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Получение сессий по диапазону сумм
        
        Args:
            min_amount (float): Минимальная сумма
            max_amount (float): Максимальная сумма
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список сессий
        """
        query = f"""
            SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE session_amount BETWEEN :min_amount AND :max_amount
            ORDER BY session_amount DESC
            LIMIT :limit
        """
        
        try:
            return await self.execute_query(query, {
                'min_amount': min_amount,
                'max_amount': max_amount,
                'limit': limit
            })
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения сессий по суммам {min_amount}-{max_amount}: {e}"
            )
            raise
    
    async def get_sessions_stats(self) -> Dict[str, Any]:
        """
        Получение статистики по сессиям
        
        Returns:
            Dict[str, Any]: Статистика сессий
            
        Example:
            >>> stats = await storage.get_sessions_stats()
            >>> print(f"Всего сессий: {stats['total_count']['total']}")
            >>> print(f"Средняя сумма: {stats['avg_amount']['avg']}")
        """
        queries = {
            'total_count': f"SELECT COUNT(*) as total FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
            'total_amount': f"SELECT SUM(session_amount) as total FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
            'avg_amount': f"SELECT AVG(session_amount) as avg FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
            'max_amount': f"SELECT MAX(session_amount) as max FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
            'min_amount': f"SELECT MIN(session_amount) as min FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
            'by_law_basis': f"""
                SELECT law_basis, COUNT(*) as count, SUM(session_amount) as total_amount
                FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
                GROUP BY law_basis
                ORDER BY count DESC
            """,
            'recent_sessions': f"""
                SELECT COUNT(*) as count
                FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
                WHERE session_created_date >= CURRENT_DATE - INTERVAL '30 days'
            """,
            'avg_duration': f"""
                SELECT AVG(EXTRACT(EPOCH FROM (session_completed_date - session_created_date))/3600) as avg_hours
                FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
                WHERE session_completed_date > session_created_date
            """,
            'completion_stats': f"""
                SELECT 
                    COUNT(CASE WHEN session_completed_date > session_created_date THEN 1 END) as completed,
                    COUNT(*) as total,
                    CASE 
                        WHEN COUNT(*) = 0 THEN 0 
                        ELSE ROUND(COUNT(CASE WHEN session_completed_date > session_created_date THEN 1 END) * 100.0 / COUNT(*), 2) 
                    END as completion_rate
                FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            """
        }
        
        stats = {}
        for key, query in queries.items():
            try:
                result = await self.execute_query(query)
                if key in ['by_law_basis', 'completion_stats']:
                    stats[key] = result[0] if result else None
                else:
                    stats[key] = result[0] if result else None
            except Exception as e:
                Utils.writelog(
                    logger=self.logger,
                    level="WARNING",
                    message=f"Не удалось получить статистику {key}: {e}"
                )
                stats[key] = None
        
        return stats
    
    async def search_sessions(
        self, 
        search_term: str, 
        search_fields: List[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Поиск сессий по тексту
        
        Args:
            search_term (str): Поисковый запрос
            search_fields (List[str], optional): Поля для поиска
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список найденных сессий
            
        Example:
            >>> sessions = await storage.search_sessions("мебель", limit=50)
            >>> print(f"Найдено {len(sessions)} сессий")
        """
        if search_fields is None:
            search_fields = ['session_name', 'customer_name', 'supplier_name']
        
        # Создаем условия поиска
        conditions = []
        params = {'search_term': f'%{search_term}%'}
        
        for i, field in enumerate(search_fields):
            conditions.append(f"{field} ILIKE :search_term")
        
        where_clause = ' OR '.join(conditions)
        
        query = f"""
            SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE {where_clause}
            ORDER BY session_created_date DESC
            LIMIT :limit
        """
        
        params['limit'] = limit
        
        try:
            return await self.execute_query(query, params)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка поиска сессий по '{search_term}': {e}"
            )
            raise
    
    async def get_sessions_by_duration(
        self, 
        min_hours: float = None, 
        max_hours: float = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получение сессий по длительности
        
        Args:
            min_hours (float, optional): Минимальная длительность в часах
            max_hours (float, optional): Максимальная длительность в часах
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список сессий
            
        Example:
            >>> sessions = await storage.get_sessions_by_duration(min_hours=2, max_hours=8)
            >>> for session in sessions:
            ...     print(f"Сессия длилась {session['duration_hours']:.2f} часов")
        """
        where_conditions = ["session_completed_date > session_created_date"]
        params = {'limit': limit}
        
        if min_hours is not None:
            where_conditions.append(
                "EXTRACT(EPOCH FROM (session_completed_date - session_created_date))/3600 >= :min_hours"
            )
            params['min_hours'] = min_hours
        
        if max_hours is not None:
            where_conditions.append(
                "EXTRACT(EPOCH FROM (session_completed_date - session_created_date))/3600 <= :max_hours"
            )
            params['max_hours'] = max_hours
        
        where_clause = ' AND '.join(where_conditions)
        
        query = f"""
            SELECT *, 
                   EXTRACT(EPOCH FROM (session_completed_date - session_created_date))/3600 as duration_hours
            FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}
            WHERE {where_clause}
            ORDER BY duration_hours DESC
            LIMIT :limit
        """
        
        try:
            return await self.execute_query(query, params)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения сессий по длительности: {e}"
            )
            raise
    
    async def update_session(self, session_id: int, update_data: Dict[str, Any]) -> int:
        """
        Обновление сессии
        
        Args:
            session_id (int): ID сессии
            update_data (Dict[str, Any]): Данные для обновления
            
        Returns:
            int: Количество обновленных записей
            
        Example:
            >>> updated = await storage.update_session(
            ...     12345,
            ...     {"session_amount": 75000, "session_completed_date": "2025-01-02 10:00:00"}
            ... )
            >>> print(f"Обновлено {updated} записей")
        """
        try:
            update_data['updated_at'] = datetime.now()
            
            result = await self.execute_update(
                f"{self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
                update_data,
                "session_id = :session_id",
                {'session_id': session_id}
            )
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Сессия {session_id} обновлена"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обновления сессии {session_id}: {e}"
            )
            raise
    
    async def get_top_sessions(
        self, 
        criteria: str = "amount", 
        limit: int = 10,
        period_days: int = None
    ) -> List[Dict[str, Any]]:
        """
        Получение топ сессий по различным критериям
        
        Args:
            criteria (str): Критерий сортировки ("amount", "duration", "recent")
            limit (int): Количество записей
            period_days (int, optional): Период в днях для фильтрации
            
        Returns:
            List[Dict[str, Any]]: Список топ сессий
            
        Example:
            >>> top_by_amount = await storage.get_top_sessions("amount", limit=5)
            >>> top_by_duration = await storage.get_top_sessions("duration", limit=3)
            >>> recent = await storage.get_top_sessions("recent", period_days=7)
        """
        base_query = f"SELECT * FROM {self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}"
        where_conditions = []
        
        if period_days:
            where_conditions.append(f"session_created_date >= CURRENT_DATE - INTERVAL '{period_days} days'")
        
        if criteria == "amount":
            order_by = "ORDER BY session_amount DESC"
        elif criteria == "duration":
            where_conditions.append("session_completed_date > session_created_date")
            order_by = "ORDER BY (session_completed_date - session_created_date) DESC"
        elif criteria == "recent":
            order_by = "ORDER BY session_created_date DESC"
        else:
            order_by = "ORDER BY session_created_date DESC"
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        query = f"{base_query}{where_clause} {order_by} LIMIT {limit}"
        
        try:
            return await self.execute_query(query)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения топ сессий по {criteria}: {e}"
            )
            raise
    
    async def delete_session(self, session_id: int) -> int:
        """
        Удаление сессии
        
        Args:
            session_id (int): ID сессии
            
        Returns:
            int: Количество удаленных записей
            
        Example:
            >>> deleted = await storage.delete_session(12345)
            >>> if deleted > 0:
            ...     print("Сессия удалена успешно")
        """
        try:
            result = await self.execute_delete(
                f"{self.SESSIONS_SCHEMA}.{self.SESSIONS_TABLE}",
                "session_id = :session_id",
                {'session_id': session_id}
            )
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Сессия {session_id} удалена"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка удаления сессии {session_id}: {e}"
            )
            raise
