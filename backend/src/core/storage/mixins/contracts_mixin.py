from typing import (
    Any, 
    Dict, 
    List, 
    Optional, 
)
from datetime import datetime
from dateutil import parser

from ...base.utils import Utils


class ContractsMixin:
    """Миксин для работы с таблицей контрактов"""
    
    CONTRACTS_SCHEMA = "aeproject"
    CONTRACTS_TABLE = "contracts"
    
    async def insert_contract(self, contract_data: Dict[str, Any]) -> int:
        """
        Вставка одного контракта
        
        Args:
            contract_data (Dict[str, Any]): Данные контракта
            
        Returns:
            int: ID вставленного контракта
            
        Example:
            >>> contract = {
            ...     "contract_name": "Тестовый контракт",
            ...     "contract_id": 12345,
            ...     "contract_amount": 100000.50,
            ...     "contract_date": "2025-01-01",
            ...     "customer_name": "ООО Тест",
            ...     "customer_inn": 1234567890,
            ...     "supplier_name": "ИП Поставщик",
            ...     "supplier_inn": 9876543210,
            ...     "law_basis": "44-ФЗ"
            ... }
            >>> await storage.insert_contract(contract)
        """
        try:
            contract_data['created_at'] = datetime.now()
            contract_data['updated_at'] = datetime.now()
            
            contract_data.pop('id', None)
            
            result = await self.execute_insert(
                f"{self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
                contract_data
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Контракт {contract_data.get('contract_id')} вставлен"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка вставки контракта: {e}"
            )
            raise
    
    async def insert_contracts_bulk(self, contracts_data: List[Dict[str, Any]]) -> int:
        """
        Массовая вставка контрактов
        
        Args:
            contracts_data (List[Dict[str, Any]]): Список данных контрактов
            
        Returns:
            int: Количество вставленных контрактов
        """
        try:
            current_time = datetime.now()
            
            for contract in contracts_data:
                contract['created_at'] = current_time
                contract['updated_at'] = current_time
                contract.pop('id', None)
            
            result = await self.execute_insert(
                f"{self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
                contracts_data
            )
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Массовая вставка: {result} контрактов"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка массовой вставки контрактов: {e}"
            )
            raise
    
    async def insert_contracts_from_excel(self, file_path: str) -> int:
        """
        Вставка контрактов из Excel файла
        
        Args:
            file_path (str): Путь к Excel файлу
            
        Returns:
            int: Количество вставленных контрактов
            
        Example:
            >>> count = storage.insert_contracts_from_excel("contracts.xlsx")
            >>> print(f"Загружено {count} контрактов")
        """
        try:
            contracts_data = Utils.universal_conventer_xls_to_json(file_path, self.logger)
            
            if not contracts_data:
                Utils.writelog(
                    logger=self.logger,
                    level="WARNING",
                    message=f"Нет данных для загрузки из файла {file_path}"
                )
                return 0
            
            mapped_contracts = []
            column_mapping = {
                'Наименование контракта': 'contract_name',
                'ID контракта': 'contract_id',
                'Сумма контракта': 'contract_amount',
                'Дата заключения контракта': 'contract_date',
                'Категория ПП первой позиции спецификации': 'category_pp_first_position',
                'Наименование заказчика': 'customer_name',
                'ИНН заказчика': 'customer_inn',
                'Наименование поставщика': 'supplier_name',
                'ИНН поставщика': 'supplier_inn',
                'Закон-основание': 'law_basis'
            }
            
            current_time = datetime.now()
            
            for contract in contracts_data:
                mapped_contract = {}
                
                for excel_col, db_col in column_mapping.items():
                    if excel_col in contract and contract[excel_col] is not None:
                        value = contract[excel_col]
                        if db_col == 'contract_date' and isinstance(value, str):
                            try:
                                value = parser.parse(value)
                            except:
                                value = None
                        mapped_contract[db_col] = value
                
                mapped_contract['created_at'] = current_time
                mapped_contract['updated_at'] = current_time
                mapped_contracts.append(mapped_contract)
            
            if mapped_contracts:
                result = await self.execute_insert(
                    f"{self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
                    mapped_contracts,
                    ignore_conflicts=True
                )
            else:
                result = 0
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Загружено {result} контрактов из файла {file_path}"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка загрузки контрактов из Excel: {e}"
            )
            raise
    
    async def get_contract_by_id(self, contract_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение контракта по ID
        
        Args:
            contract_id (int): ID контракта
            
        Returns:
            Optional[Dict[str, Any]]: Данные контракта или None
        """
        query = f"""
            SELECT * FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}
            WHERE contract_id = :contract_id
        """
        
        try:
            result = await self.execute_query(query, {'contract_id': contract_id})
            return result[0] if result else None
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка получения контракта по ID {contract_id}: {e}"
            )
            raise
    
    async def get_contracts_by_customer(self, customer_inn: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение контрактов по ИНН заказчика
        
        Args:
            customer_inn (int): ИНН заказчика
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список контрактов
        """
        query = f"""
            SELECT * FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}
            WHERE customer_inn = :customer_inn
            ORDER BY contract_date DESC
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
                message=f"Ошибка получения контрактов по заказчику {customer_inn}: {e}"
            )
            raise
    
    async def get_contracts_by_supplier(self, supplier_inn: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение контрактов по ИНН поставщика
        
        Args:
            supplier_inn (int): ИНН поставщика
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список контрактов
        """
        query = f"""
            SELECT * FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}
            WHERE supplier_inn = :supplier_inn
            ORDER BY contract_date DESC
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
                message=f"Ошибка получения контрактов по поставщику {supplier_inn}: {e}"
            )
            raise
    
    async def get_contracts_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Получение контрактов по диапазону дат
        
        Args:
            start_date (datetime): Начальная дата
            end_date (datetime): Конечная дата
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список контрактов
        """
        query = f"""
            SELECT * FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}
            WHERE contract_date BETWEEN :start_date AND :end_date
            ORDER BY contract_date DESC
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
                message=f"Ошибка получения контрактов по датам {start_date}-{end_date}: {e}"
            )
            raise
    
    async def get_contracts_by_amount_range(
        self, 
        min_amount: float, 
        max_amount: float,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Получение контрактов по диапазону сумм
        
        Args:
            min_amount (float): Минимальная сумма
            max_amount (float): Максимальная сумма
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список контрактов
        """
        query = f"""
            SELECT * FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}
            WHERE contract_amount BETWEEN :min_amount AND :max_amount
            ORDER BY contract_amount DESC
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
                message=f"Ошибка получения контрактов по суммам {min_amount}-{max_amount}: {e}"
            )
            raise
    
    async def get_contracts_stats(self) -> Dict[str, Any]:
        """
        Получение статистики по контрактам
        
        Returns:
            Dict[str, Any]: Статистика контрактов
        """
        queries = {
            'total_count': f"SELECT COUNT(*) as total FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
            'total_amount': f"SELECT SUM(contract_amount) as total FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
            'avg_amount': f"SELECT AVG(contract_amount) as avg FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
            'max_amount': f"SELECT MAX(contract_amount) as max FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
            'min_amount': f"SELECT MIN(contract_amount) as min FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
            'by_law_basis': f"""
                SELECT law_basis, COUNT(*) as count, SUM(contract_amount) as total_amount
                FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}
                GROUP BY law_basis
                ORDER BY count DESC
            """,
            'recent_contracts': f"""
                SELECT COUNT(*) as count
                FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}
                WHERE contract_date >= CURRENT_DATE - INTERVAL '30 days'
            """
        }
        
        stats = {}
        for key, query in queries.items():
            try:
                result = await self.execute_query(query)
                if key == 'by_law_basis':
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
    
    async def search_contracts(
        self, 
        search_term: str, 
        search_fields: List[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Поиск контрактов по тексту
        
        Args:
            search_term (str): Поисковый запрос
            search_fields (List[str], optional): Поля для поиска
            limit (int): Лимит записей
            
        Returns:
            List[Dict[str, Any]]: Список найденных контрактов
            
        Example:
            >>> contracts = await storage.search_contracts("мебель", limit=50)
            >>> print(f"Найдено {len(contracts)} контрактов")
        """
        if search_fields is None:
            search_fields = ['contract_name', 'customer_name', 'supplier_name']
        
        conditions = []
        params = {'search_term': f'%{search_term}%'}
        
        for i, field in enumerate(search_fields):
            conditions.append(f"{field} ILIKE :search_term")
        
        where_clause = ' OR '.join(conditions)
        
        query = f"""
            SELECT * FROM {self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}
            WHERE {where_clause}
            ORDER BY contract_date DESC
            LIMIT :limit
        """
        
        params['limit'] = limit
        
        try:
            return await self.execute_query(query, params)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка поиска контрактов по '{search_term}': {e}"
            )
            raise
    
    async def update_contract(self, contract_id: int, update_data: Dict[str, Any]) -> int:
        """
        Обновление контракта
        
        Args:
            contract_id (int): ID контракта
            update_data (Dict[str, Any]): Данные для обновления
            
        Returns:
            int: Количество обновленных записей
        """
        try:
            update_data['updated_at'] = datetime.now()
            
            result = await self.execute_update(
                f"{self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
                update_data,
                "contract_id = :contract_id",
                {'contract_id': contract_id}
            )
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Контракт {contract_id} обновлен"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обновления контракта {contract_id}: {e}"
            )
            raise
    
    async def delete_contract(self, contract_id: int) -> int:
        """
        Удаление контракта
        
        Args:
            contract_id (int): ID контракта
            
        Returns:
            int: Количество удаленных записей
        """
        try:
            result = await self.execute_delete(
                f"{self.CONTRACTS_SCHEMA}.{self.CONTRACTS_TABLE}",
                "contract_id = :contract_id",
                {'contract_id': contract_id}
            )
            
            Utils.writelog(
                logger=self.logger,
                level="INFO",
                message=f"Контракт {contract_id} удален"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка удаления контракта {contract_id}: {e}"
            )
            raise
