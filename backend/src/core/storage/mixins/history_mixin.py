from typing import (
    Any, 
    Dict, 
    List, 
    Optional,
    Union
)
from datetime import datetime
import json

from ...base.utils import Utils


class HistoryMixin:
    """Миксин для работы с таблицей истории"""
    
    HISTORY_SCHEMA = "aeproject"
    HISTORY_TABLE = "history"
    
    async def insert_history_record(self, history_data: Dict[str, Any]) -> int:
        """
        Вставка одной записи истории
        
        Args:
            history_data (Dict[str, Any]): Данные истории
                - text (str): Текст запроса/сообщения
                - intent (str, optional): Намерение
                - confidence (float, optional): Уверенность
                - entities (dict/list, optional): Извлеченные сущности
                - timestamp (datetime, optional): Время события
            
        Returns:
            int: ID вставленной записи
            
        Example:
            >>> record = {
            ...     "text": "Покажи контракты за последний месяц",
            ...     "intent": "search_contracts",
            ...     "confidence": 0.95,
            ...     "entities": {"date_range": "last_month", "type": "contracts"}
            ... }
            >>> await storage.insert_history_record(record)
        """
        try:
            # Устанавливаем timestamp если не указан
            if 'timestamp' not in history_data or history_data['timestamp'] is None:
                history_data['timestamp'] = datetime.now()
            
            # Конвертируем entities в JSON если это dict/list
            if 'entities' in history_data and history_data['entities'] is not None:
                if not isinstance(history_data['entities'], str):
                    history_data['entities'] = json.dumps(history_data['entities'], ensure_ascii=False)
            
            history_data['created_at'] = datetime.now()
            history_data.pop('id', None)
            
            result = await self.execute_insert(
                f"{self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}",
                history_data
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Запись истории добавлена: {history_data.get('text', '')[:50]}..."
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка вставки записи истории: {e}"
            )
            raise
    
    async def insert_history_bulk(self, history_data: List[Dict[str, Any]]) -> int:
        """
        Массовая вставка записей истории
        
        Args:
            history_data (List[Dict[str, Any]]): Список данных истории
            
        Returns:
            int: Количество вставленных записей
            
        Example:
            >>> records = [
            ...     {"text": "Запрос 1", "intent": "search", "confidence": 0.9},
            ...     {"text": "Запрос 2", "intent": "filter", "confidence": 0.85}
            ... ]
            >>> count = await storage.insert_history_bulk(records)
        """
        try:
            current_time = datetime.now()
            
            for record in history_data:
                if 'timestamp' not in record or record['timestamp'] is None:
                    record['timestamp'] = current_time
                
                if 'entities' in record and record['entities'] is not None:
                    if not isinstance(record['entities'], str):
                        record['entities'] = json.dumps(record['entities'], ensure_ascii=False)
                
                record['created_at'] = current_time
                record.pop('id', None)
            
            result = await self.execute_insert(
                f"{self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}",
                history_data
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Массовая вставка: {result} записей истории"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка массовой вставки записей истории: {e}"
            )
            raise
    
    async def get_history_by_id(self, history_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение записи истории по ID
        
        Args:
            history_id (int): ID записи
            
        Returns:
            Optional[Dict[str, Any]]: Данные записи или None
            
        Example:
            >>> record = await storage.get_history_by_id(123)
            >>> if record:
            ...     print(f"Текст: {record['text']}")
        """
        query = f"""
            SELECT * FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
            WHERE id = :history_id
        """
        
        try:
            result = await self.execute_query(query, {'history_id': history_id})
            if result:
                record = result[0]
                # Парсим JSON entities если есть
                if record.get('entities') and isinstance(record['entities'], str):
                    try:
                        record['entities'] = json.loads(record['entities'])
                    except json.JSONDecodeError:
                        pass
                return record
            return None
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения записи истории по ID {history_id}: {e}"
            )
            raise
    
    async def get_history_by_intent(self, intent: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение записей истории по намерению
        
        Args:
            intent (str): Намерение для поиска
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список записей
            
        Example:
            >>> records = await storage.get_history_by_intent("search_contracts", limit=50)
            >>> print(f"Найдено {len(records)} записей")
        """
        query = f"""
            SELECT * FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
            WHERE intent = :intent
            ORDER BY timestamp DESC
            LIMIT :limit
        """
        
        try:
            result = await self.execute_query(query, {
                'intent': intent,
                'limit': limit
            })
            
            # Парсим JSON entities для всех записей
            for record in result:
                if record.get('entities') and isinstance(record['entities'], str):
                    try:
                        record['entities'] = json.loads(record['entities'])
                    except json.JSONDecodeError:
                        pass
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения записей по намерению {intent}: {e}"
            )
            raise
    
    async def get_history_by_confidence_range(
        self, 
        min_confidence: float, 
        max_confidence: float,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Получение записей истории по диапазону уверенности
        
        Args:
            min_confidence (float): Минимальная уверенность
            max_confidence (float): Максимальная уверенность
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список записей
        """
        query = f"""
            SELECT * FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
            WHERE confidence BETWEEN :min_confidence AND :max_confidence
            ORDER BY confidence DESC, timestamp DESC
            LIMIT :limit
        """
        
        try:
            result = await self.execute_query(query, {
                'min_confidence': min_confidence,
                'max_confidence': max_confidence,
                'limit': limit
            })
            
            # Парсим JSON entities
            for record in result:
                if record.get('entities') and isinstance(record['entities'], str):
                    try:
                        record['entities'] = json.loads(record['entities'])
                    except json.JSONDecodeError:
                        pass
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения записей по уверенности {min_confidence}-{max_confidence}: {e}"
            )
            raise
    
    async def get_history_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Получение записей истории по диапазону дат
        
        Args:
            start_date (datetime): Начальная дата
            end_date (datetime): Конечная дата
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список записей
        """
        query = f"""
            SELECT * FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
            WHERE timestamp BETWEEN :start_date AND :end_date
            ORDER BY timestamp DESC
            LIMIT :limit
        """
        
        try:
            result = await self.execute_query(query, {
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit
            })
            
            # Парсим JSON entities
            for record in result:
                if record.get('entities') and isinstance(record['entities'], str):
                    try:
                        record['entities'] = json.loads(record['entities'])
                    except json.JSONDecodeError:
                        pass
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения записей по датам {start_date}-{end_date}: {e}"
            )
            raise
    
    async def get_recent_history(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение последних записей истории
        
        Args:
            hours (int): Количество часов назад
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список записей
            
        Example:
            >>> recent = await storage.get_recent_history(hours=48, limit=50)
            >>> print(f"Записей за последние 48 часов: {len(recent)}")
        """
        query = f"""
            SELECT * FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{hours} hours'
            ORDER BY timestamp DESC
            LIMIT :limit
        """
        
        try:
            result = await self.execute_query(query, {'limit': limit})
            
            # Парсим JSON entities
            for record in result:
                if record.get('entities') and isinstance(record['entities'], str):
                    try:
                        record['entities'] = json.loads(record['entities'])
                    except json.JSONDecodeError:
                        pass
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения последних записей за {hours} часов: {e}"
            )
            raise
    
    async def search_history_by_text(
        self, 
        search_term: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Поиск записей истории по тексту
        
        Args:
            search_term (str): Поисковый запрос
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список найденных записей
            
        Example:
            >>> records = await storage.search_history_by_text("контракт", limit=20)
            >>> for record in records:
            ...     print(f"Найдено: {record['text']}")
        """
        query = f"""
            SELECT * FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
            WHERE text ILIKE :search_term
            ORDER BY timestamp DESC
            LIMIT :limit
        """
        
        try:
            result = await self.execute_query(query, {
                'search_term': f'%{search_term}%',
                'limit': limit
            })
            
            # Парсим JSON entities
            for record in result:
                if record.get('entities') and isinstance(record['entities'], str):
                    try:
                        record['entities'] = json.loads(record['entities'])
                    except json.JSONDecodeError:
                        pass
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка поиска по тексту '{search_term}': {e}"
            )
            raise
    
    async def get_history_stats(self) -> Dict[str, Any]:
        """
        Получение статистики по истории
        
        Returns:
            Dict[str, Any]: Статистика записей истории
            
        Example:
            >>> stats = await storage.get_history_stats()
            >>> print(f"Всего записей: {stats['total_count']['total']}")
            >>> print(f"Средняя уверенность: {stats['avg_confidence']['avg']}")
        """
        queries = {
            'total_count': f"SELECT COUNT(*) as total FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}",
            'avg_confidence': f"SELECT AVG(confidence) as avg FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE} WHERE confidence IS NOT NULL",
            'max_confidence': f"SELECT MAX(confidence) as max FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}",
            'min_confidence': f"SELECT MIN(confidence) as min FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE} WHERE confidence IS NOT NULL",
            'by_intent': f"""
                SELECT intent, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
                WHERE intent IS NOT NULL
                GROUP BY intent
                ORDER BY count DESC
            """,
            'recent_activity': f"""
                SELECT COUNT(*) as count
                FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
                WHERE timestamp >= CURRENT_DATE - INTERVAL '24 hours'
            """,
            'daily_stats': f"""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
                WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """,
            'high_confidence': f"""
                SELECT COUNT(*) as count
                FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
                WHERE confidence >= 0.9
            """,
            'low_confidence': f"""
                SELECT COUNT(*) as count
                FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
                WHERE confidence < 0.5
            """
        }
        
        stats = {}
        for key, query in queries.items():
            try:
                result = await self.execute_query(query)
                if key in ['by_intent', 'daily_stats']:
                    stats[key] = result
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
    
    async def get_top_intents(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """
        Получение топ намерений по частоте использования
        
        Args:
            limit (int): Количество записей
            days (int): Период в днях
            
        Returns:
            List[Dict[str, Any]]: Список намерений с статистикой
            
        Example:
            >>> top_intents = await storage.get_top_intents(limit=5, days=7)
            >>> for intent in top_intents:
            ...     print(f"{intent['intent']}: {intent['count']} раз")
        """
        query = f"""
            SELECT 
                intent,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                MAX(timestamp) as last_used
            FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
            WHERE intent IS NOT NULL 
            AND timestamp >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY intent
            ORDER BY count DESC
            LIMIT :limit
        """
        
        try:
            return await self.execute_query(query, {'limit': limit})
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения топ намерений: {e}"
            )
            raise
    
    async def get_entity_usage_stats(self, entity_key: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получение статистики использования сущностей
        
        Args:
            entity_key (str, optional): Ключ сущности для фильтрации
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Статистика сущностей
            
        Example:
            >>> entity_stats = await storage.get_entity_usage_stats()
            >>> filtered = await storage.get_entity_usage_stats("date_range")
        """
        if entity_key:
            query = f"""
                SELECT 
                    JSON_EXTRACT_PATH_TEXT(entities, '{entity_key}') as entity_value,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
                WHERE entities IS NOT NULL 
                AND JSON_EXTRACT_PATH_TEXT(entities, '{entity_key}') IS NOT NULL
                GROUP BY JSON_EXTRACT_PATH_TEXT(entities, '{entity_key}')
                ORDER BY count DESC
                LIMIT :limit
            """
        else:
            query = f"""
                SELECT 
                    JSON_OBJECT_KEYS(entities) as entity_key,
                    COUNT(*) as count
                FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
                WHERE entities IS NOT NULL
                GROUP BY JSON_OBJECT_KEYS(entities)
                ORDER BY count DESC
                LIMIT :limit
            """
        
        try:
            return await self.execute_query(query, {'limit': limit})
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения статистики сущностей: {e}"
            )
            raise
    
    async def cleanup_old_history(self, days_to_keep: int = 90) -> int:
        """
        Очистка старых записей истории
        
        Args:
            days_to_keep (int): Количество дней для хранения
            
        Returns:
            int: Количество удаленных записей
            
        Example:
            >>> deleted = await storage.cleanup_old_history(days_to_keep=30)
            >>> print(f"Удалено {deleted} старых записей")
        """
        query = f"""
            DELETE FROM {self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}
            WHERE timestamp < CURRENT_DATE - INTERVAL '{days_to_keep} days'
        """
        
        try:
            result = await self.execute_delete(
                f"{self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}",
                f"timestamp < CURRENT_DATE - INTERVAL '{days_to_keep} days'"
            )
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Очистка истории: удалено {result} записей старше {days_to_keep} дней"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка очистки старых записей: {e}"
            )
            raise
    
    async def update_history_record(self, history_id: int, update_data: Dict[str, Any]) -> int:
        """
        Обновление записи истории
        
        Args:
            history_id (int): ID записи
            update_data (Dict[str, Any]): Данные для обновления
            
        Returns:
            int: Количество обновленных записей
            
        Example:
            >>> updated = await storage.update_history_record(
            ...     123,
            ...     {"confidence": 0.98, "entities": {"corrected": True}}
            ... )
        """
        try:
            # Конвертируем entities в JSON если нужно
            if 'entities' in update_data and update_data['entities'] is not None:
                if not isinstance(update_data['entities'], str):
                    update_data['entities'] = json.dumps(update_data['entities'], ensure_ascii=False)
            
            result = await self.execute_update(
                f"{self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}",
                update_data,
                "id = :history_id",
                {'history_id': history_id}
            )
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Запись истории {history_id} обновлена"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обновления записи истории {history_id}: {e}"
            )
            raise
    
    async def delete_history_record(self, history_id: int) -> int:
        """
        Удаление записи истории
        
        Args:
            history_id (int): ID записи
            
        Returns:
            int: Количество удаленных записей
            
        Example:
            >>> deleted = await storage.delete_history_record(123)
            >>> if deleted > 0:
            ...     print("Запись удалена успешно")
        """
        try:
            result = await self.execute_delete(
                f"{self.HISTORY_SCHEMA}.{self.HISTORY_TABLE}",
                "id = :history_id",
                {'history_id': history_id}
            )
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Запись истории {history_id} удалена"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка удаления записи истории {history_id}: {e}"
            )
            raise
