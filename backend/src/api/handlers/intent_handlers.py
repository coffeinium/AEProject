from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
from decimal import Decimal, InvalidOperation

from ...core.base.utils import Utils
from ...core.base.text_extractor import TextExtractor


class IntentHandlers:
    """
    Обработчик намерений пользователей для системы закупок.
    
    Обрабатывает различные типы намерений: создание контрактов и КС,
    поиск документов и компаний, создание профилей компаний, справочная система.
    
    Использует TextExtractor для получения всех текстов из конфигурации
    и EnvReader для настройки параметров валидации.
    """
    
    def __init__(self, storage, logger, env_reader):
        """
        Инициализация обработчика намерений.
        
        Args:
            storage: Объект для работы с базой данных
            logger: Логгер для записи событий  
            env_reader: Объект для чтения переменных окружения
        """
        self.storage = storage
        self.logger = logger
        self.env = env_reader
        
        text_path = self.env.get('AEAPISETTINGS_HANDLER_TEXT_PATH', 'src/assets/texts.json')
        self.text_manager = TextExtractor(text_path, logger)
        
        self.MIN_INN_LENGTH = self.env.get('AEAPISETTINGS_HANDLER_MIN_INN_LENGTH', 10)
        self.MAX_INN_LENGTH = self.env.get('AEAPISETTINGS_HANDLER_MAX_INN_LENGTH', 12)
        self.BIK_LENGTH = self.env.get('AEAPISETTINGS_HANDLER_BIK_LENGTH', 9)
        self.MIN_AMOUNT = self.env.get('AEAPISETTINGS_HANDLER_MIN_AMOUNT', 0.01)
        self.MAX_AMOUNT = self.env.get('AEAPISETTINGS_HANDLER_MAX_AMOUNT', 999999999999.99)
        self.AMOUNT_TOLERANCE = self.env.get('AEAPISETTINGS_HANDLER_AMOUNT_TOLERANCE', 0.2)
        self.MAX_RESULTS = self.env.get('AEAPISETTINGS_HANDLER_MAX_RESULTS', 20)
        self.MAX_STRING_LENGTH = self.env.get('AEAPISETTINGS_HANDLER_MAX_STRING_LENGTH', 500)
        
        Utils.writelog(
            logger=self.logger,
            level="DEBUG",
            message="IntentHandlers инициализирован с конфигурацией из ENV"
        )
    
    async def process_intent(self, intent: str, entities: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """
        Главный метод обработки намерений с безопасной маршрутизацией.
        
        Args:
            intent: Тип намерения
            entities: Извлеченные сущности
            original_query: Исходный запрос пользователя
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            if not self._validate_input(intent, entities, original_query):
                return self.text_manager.get_error_response("validation_error", error="Некорректные входные данные")
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Обработка намерения '{intent}' с {len(entities)} сущностями"
            )
            
            intent_handlers = {
                "create_contract": self._handle_create_contract,
                "create_ks": self._handle_create_ks,
                "create_zakupka": self._handle_create_zakupka,
                "search_docs": self._handle_search_docs,
                "search_company": self._handle_search_company,
                "create_company_profile": self._handle_create_company_profile,
                "help": self._handle_help
            }
            
            handler = intent_handlers.get(intent)
            if not handler:
                return self.text_manager.get_error_response("unknown_intent", intent=intent)
            
            return await handler(entities, original_query)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Критическая ошибка обработки намерения '{intent}': {e}"
            )
            return self.text_manager.get_error_response("processing_error", error=str(e))
    
    def _validate_input(self, intent: str, entities: Dict[str, Any], query: str) -> bool:
        """Валидация входных данных."""
        if not isinstance(intent, str) or not intent.strip():
            return False
        
        if not isinstance(entities, dict):
            return False
        
        if not isinstance(query, str) or len(query.strip()) < 1:
            return False
        
        return True
    
    async def _handle_create_contract(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Обработка создания контракта."""
        try:
            contract_data = self._extract_contract_data(entities, query)
            missing_fields = self._validate_contract_data(contract_data)
            
            if missing_fields:
                return self.text_manager.get_creation_response(
                    "contract", "needs_more_info", contract_data, missing_fields
                )
            
            return self.text_manager.get_creation_response(
                "contract", "ready_to_create", contract_data
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка создания контракта: {e}"
            )
            return self.text_manager.get_error_response("processing_error", error=str(e))
    
    async def _handle_create_ks(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Обработка создания КС."""
        try:
            ks_data = self._extract_ks_data(entities, query)
            missing_fields = self._validate_ks_data(ks_data)
            
            if missing_fields:
                return self.text_manager.get_creation_response(
                    "ks", "needs_more_info", ks_data, missing_fields
                )
            
            return self.text_manager.get_creation_response(
                "ks", "ready_to_create", ks_data
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка создания КС: {e}"
            )
            return self.text_manager.get_error_response("processing_error", error=str(e))
    
    async def _handle_create_zakupka(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Обработка создания закупки."""
        try:
            zakupka_data = self._extract_zakupka_data(entities, query)
            missing_fields = self._validate_zakupka_data(zakupka_data)
            
            if missing_fields:
                return self.text_manager.get_creation_response(
                    "zakupka", "needs_more_info", zakupka_data, missing_fields
                )
            
            return self.text_manager.get_creation_response(
                "zakupka", "ready_to_create", zakupka_data
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка создания закупки: {e}"
            )
            return self.text_manager.get_error_response("processing_error", error=str(e))
    
    async def _handle_search_docs(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Обработка поиска документов."""
        try:
            search_params = self._extract_search_params(entities, query)
            
            results = []
            search_type = "unknown"
            
            if self._should_search_contracts(search_params, query):
                contracts = await self._search_contracts_safe(search_params)
                if contracts:
                    results.extend([{"type": "contract", "data": c} for c in contracts])
                    search_type = "contracts"
            
            if self._should_search_sessions(search_params, query):
                sessions = await self._search_sessions_safe(search_params)
                if sessions:
                    results.extend([{"type": "session", "data": s} for s in sessions])
                    search_type = "sessions" if search_type == "unknown" else "mixed"
            
            return self.text_manager.get_search_response(search_type, results, search_params)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка поиска документов: {e}"
            )
            return self.text_manager.get_error_response("database_error", error=str(e))
    
    async def _handle_search_company(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Обработка поиска компаний."""
        try:
            search_params = self._extract_company_search_params(entities, query)
            company_data = await self._search_company_safe(search_params)
            
            return self.text_manager.get_company_response(company_data, search_params)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка поиска компании: {e}"
            )
            return self.text_manager.get_error_response("database_error", error=str(e))
    
    async def _handle_create_company_profile(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Обработка создания профиля компании."""
        try:
            company_data = self._extract_company_data(entities, query)
            missing_fields = self._validate_company_data(company_data)
            
            if missing_fields:
                return self.text_manager.get_creation_response(
                    "company", "needs_more_info", company_data, missing_fields
                )
            
            return self.text_manager.get_creation_response(
                "company", "ready_to_create", company_data
            )
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка создания профиля компании: {e}"
            )
            return self.text_manager.get_error_response("processing_error", error=str(e))
    
    async def _handle_help(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Обработка запросов помощи."""
        try:
            help_topic = entities.get('help_data', query)
            return self.text_manager.get_help_response(help_topic)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка обработки помощи: {e}"
            )
            return self.text_manager.get_error_response("processing_error", error=str(e))
    
    def _extract_contract_data(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Извлечение данных контракта из сущностей."""
        contract_data = {}
        
        contract_name = entities.get('contract_name')
        if contract_name:
            contract_data['contract_name'] = self._sanitize_string(contract_name)
        elif entities.get('category'):
            category = self._sanitize_string(entities['category'])
            contract_data['contract_name'] = f"Контракт на {category}"
        
        amount = self._parse_amount_safe(entities.get('amount'))
        if amount is not None:
            contract_data['contract_amount'] = amount
        
        customer_name = entities.get('customer_name')
        if customer_name:
            contract_data['customer_name'] = self._sanitize_string(customer_name)
        
        customer_inn = self._parse_inn_safe(entities.get('customer_inn') or entities.get('inn'))
        if customer_inn:
            contract_data['customer_inn'] = customer_inn
        
        category = entities.get('category')
        if category:
            contract_data['category_pp_first_position'] = self._sanitize_string(category)
        
        law = entities.get('law')
        if law:
            contract_data['law_basis'] = self._sanitize_string(law)
        
        contract_data['contract_date'] = datetime.now()
        
        return contract_data
    
    def _extract_ks_data(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Извлечение данных КС из сущностей."""
        ks_data = {}
        
        ks_name = entities.get('ks_name')
        if ks_name:
            ks_data['session_name'] = self._sanitize_string(ks_name)
        elif entities.get('category'):
            category = self._sanitize_string(entities['category'])
            ks_data['session_name'] = f"КС на {category}"
        
        amount = self._parse_amount_safe(entities.get('amount'))
        if amount is not None:
            ks_data['session_amount'] = amount
        
        customer_name = entities.get('customer_name')
        if customer_name:
            ks_data['customer_name'] = self._sanitize_string(customer_name)
        
        customer_inn = self._parse_inn_safe(entities.get('customer_inn') or entities.get('inn'))
        if customer_inn:
            ks_data['customer_inn'] = customer_inn
        
        category = entities.get('category')
        if category:
            ks_data['category_pp_first_position'] = self._sanitize_string(category)
        
        law = entities.get('law')
        if law:
            ks_data['law_basis'] = self._sanitize_string(law)
        
        ks_data['session_created_date'] = datetime.now()
        ks_data['session_completed_date'] = datetime.now() + timedelta(days=7)
        
        return ks_data
    
    def _extract_zakupka_data(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Извлечение данных закупки из сущностей."""
        zakupka_data = {}
        
        # Название закупки
        zakupka_name = entities.get('procurement_name') or entities.get('zakupka_name')
        if zakupka_name:
            zakupka_data['procurement_name'] = self._sanitize_string(zakupka_name)
        elif entities.get('category'):
            category = self._sanitize_string(entities['category'])
            zakupka_data['procurement_name'] = f"Закупка {category}"
        
        # Сумма закупки
        amount = self._parse_amount_safe(entities.get('amount') or entities.get('procurement_amount'))
        if amount is not None:
            zakupka_data['procurement_amount'] = amount
        
        # Заказчик
        customer_name = entities.get('customer_name') or entities.get('company_name')
        if customer_name:
            zakupka_data['customer_name'] = self._sanitize_string(customer_name)
        
        # ИНН заказчика
        customer_inn = self._parse_inn_safe(entities.get('customer_inn') or entities.get('inn'))
        if customer_inn:
            zakupka_data['customer_inn'] = customer_inn
        
        # Категория закупки
        category = entities.get('category')
        if category:
            zakupka_data['category'] = self._sanitize_string(category)
        
        # Способ закупки
        procurement_method = entities.get('procurement_method')
        if procurement_method:
            zakupka_data['procurement_method'] = self._sanitize_string(procurement_method)
        
        # Тип закона
        law = entities.get('law') or entities.get('law_type')
        if law:
            zakupka_data['law_type'] = self._sanitize_string(law)
        
        # Описание
        description = entities.get('description')
        if description:
            zakupka_data['description'] = self._sanitize_string(description)
        
        # Требования
        requirements = entities.get('requirements')
        if requirements:
            zakupka_data['requirements'] = self._sanitize_string(requirements)
        
        # Контактные данные
        contact_person = entities.get('contact_person')
        if contact_person:
            zakupka_data['contact_person'] = self._sanitize_string(contact_person)
        
        contact_phone = entities.get('contact_phone') or entities.get('phone')
        if contact_phone:
            zakupka_data['contact_phone'] = self._sanitize_string(contact_phone)
        
        contact_email = entities.get('contact_email') or entities.get('email')
        if contact_email:
            zakupka_data['contact_email'] = self._sanitize_string(contact_email)
        
        # Адрес поставки
        delivery_address = entities.get('delivery_address') or entities.get('address')
        if delivery_address:
            zakupka_data['delivery_address'] = self._sanitize_string(delivery_address)
        
        # Условия поставки
        delivery_terms = entities.get('delivery_terms')
        if delivery_terms:
            zakupka_data['delivery_terms'] = self._sanitize_string(delivery_terms)
        
        # Даты
        zakupka_data['procurement_date'] = datetime.now()
        zakupka_data['deadline_date'] = datetime.now() + timedelta(days=14)  # 2 недели на подачу заявок
        
        return zakupka_data
    
    def _extract_search_params(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Извлечение параметров поиска из сущностей."""
        params = {}
        
        for name_field in ['contract_name', 'ks_name']:
            if entities.get(name_field):
                params['name_search'] = self._sanitize_string(entities[name_field])
                break
        
        for company_field in ['customer_name', 'company_name']:
            if entities.get(company_field):
                params['customer_search'] = self._sanitize_string(entities[company_field])
                break
        
        inn = self._parse_inn_safe(entities.get('customer_inn') or entities.get('inn'))
        if inn:
            params['inn_search'] = inn
        
        amount = self._parse_amount_safe(entities.get('amount'))
        if amount is not None:
            params['amount_search'] = amount
        
        category = entities.get('category')
        if category:
            params['category_search'] = self._sanitize_string(category)
        
        law = entities.get('law')
        if law:
            params['law_search'] = self._sanitize_string(law)
        
        doc_id = self._parse_int_safe(entities.get('document_id'))
        if doc_id:
            params['id_search'] = doc_id
        
        return params
    
    def _extract_company_search_params(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Извлечение параметров поиска компании из сущностей."""
        params = {}
        
        for name_field in ['company_name', 'customer_name']:
            if entities.get(name_field):
                params['name'] = self._sanitize_string(entities[name_field])
                break
        
        inn = self._parse_inn_safe(entities.get('inn') or entities.get('customer_inn'))
        if inn:
            params['inn'] = inn
        
        bik = self._parse_bik_safe(entities.get('bik'))
        if bik:
            params['bik'] = bik
        
        return params
    
    def _extract_company_data(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Извлечение данных компании для создания профиля."""
        company_data = {}
        
        company_name = entities.get('company_name')
        if company_name:
            company_data['name'] = self._sanitize_string(company_name)
        
        inn = self._parse_inn_safe(entities.get('inn'))
        if inn:
            company_data['inn'] = inn
        
        bik = self._parse_bik_safe(entities.get('bik'))
        if bik:
            company_data['bik'] = bik
        
        return company_data
    
    def _validate_contract_data(self, contract_data: Dict[str, Any]) -> List[str]:
        """Проверка обязательных полей контракта."""
        required_fields = ['contract_name', 'contract_amount', 'customer_name', 'customer_inn']
        return [field for field in required_fields if not contract_data.get(field)]
    
    def _validate_ks_data(self, ks_data: Dict[str, Any]) -> List[str]:
        """Проверка обязательных полей КС."""
        required_fields = ['session_name', 'session_amount', 'customer_name', 'customer_inn']
        return [field for field in required_fields if not ks_data.get(field)]
    
    def _validate_company_data(self, company_data: Dict[str, Any]) -> List[str]:
        """Проверка обязательных полей компании."""
        required_fields = ['name', 'inn']
        return [field for field in required_fields if not company_data.get(field)]
    
    def _validate_zakupka_data(self, zakupka_data: Dict[str, Any]) -> List[str]:
        """Проверка обязательных полей закупки."""
        required_fields = ['procurement_name', 'procurement_amount', 'customer_name', 'customer_inn']
        return [field for field in required_fields if not zakupka_data.get(field)]
    
    async def _search_contracts_safe(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Безопасный поиск контрактов с обработкой ошибок."""
        try:
            if not self.storage:
                return []
            
            results = []
            
            if 'id_search' in params:
                contract = await self.storage.get_contract_by_id(params['id_search'])
                return [contract] if contract else []
            
            if 'inn_search' in params:
                contracts = await self.storage.get_contracts_by_customer(
                    params['inn_search'], limit=50
                )
                results.extend(contracts)
            
            if 'name_search' in params:
                contracts = await self.storage.search_contracts(
                    params['name_search'], limit=50
                )
                results.extend(contracts)
            
            if 'customer_search' in params:
                contracts = await self.storage.search_contracts(
                    params['customer_search'], 
                    search_fields=['customer_name', 'supplier_name'],
                    limit=50
                )
                results.extend(contracts)
            
            if 'amount_search' in params:
                amount = float(params['amount_search'])
                min_amount = amount * (1 - self.AMOUNT_TOLERANCE)
                max_amount = amount * (1 + self.AMOUNT_TOLERANCE)
                contracts = await self.storage.get_contracts_by_amount_range(
                    min_amount, max_amount, limit=50
                )
                results.extend(contracts)
            
            return self._deduplicate_results(results)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка безопасного поиска контрактов: {e}"
            )
            return []
    
    async def _search_sessions_safe(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Безопасный поиск сессий с обработкой ошибок."""
        try:
            if not self.storage:
                return []
            
            results = []
            
            if 'id_search' in params:
                session = await self.storage.get_session_by_id(params['id_search'])
                return [session] if session else []
            
            if 'inn_search' in params:
                sessions = await self.storage.get_sessions_by_customer(
                    params['inn_search'], limit=50
                )
                results.extend(sessions)
            
            if 'name_search' in params:
                sessions = await self.storage.search_sessions(
                    params['name_search'], limit=50
                )
                results.extend(sessions)
            
            if 'customer_search' in params:
                sessions = await self.storage.search_sessions(
                    params['customer_search'],
                    search_fields=['customer_name', 'supplier_name'],
                    limit=50
                )
                results.extend(sessions)
            
            if 'amount_search' in params:
                amount = float(params['amount_search'])
                min_amount = amount * (1 - self.AMOUNT_TOLERANCE)
                max_amount = amount * (1 + self.AMOUNT_TOLERANCE)
                sessions = await self.storage.get_sessions_by_amount_range(
                    min_amount, max_amount, limit=50
                )
                results.extend(sessions)
            
            return self._deduplicate_results(results)
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка безопасного поиска сессий: {e}"
            )
            return []
    
    async def _search_company_safe(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Безопасный поиск компании с обработкой ошибок."""
        try:
            if not self.storage:
                return None
            
            company_info = {
                "contracts": [],
                "sessions": [],
                "summary": {}
            }
            
            if 'inn' in params:
                inn = params['inn']
                contracts = await self.storage.get_contracts_by_customer(inn, limit=100)
                sessions = await self.storage.get_sessions_by_customer(inn, limit=100)
                
                if contracts or sessions:
                    company_info["contracts"] = contracts
                    company_info["sessions"] = sessions
                    
                    company_name = None
                    if contracts:
                        company_name = contracts[0].get('customer_name')
                    elif sessions:
                        company_name = sessions[0].get('customer_name')
                    
                    company_info["summary"] = self._build_company_summary(
                        company_name, inn, contracts, sessions
                    )
                    
                    return company_info
            
            if 'name' in params:
                name = params['name']
                contracts = await self.storage.search_contracts(
                    name, search_fields=['customer_name', 'supplier_name'], limit=100
                )
                sessions = await self.storage.search_sessions(
                    name, search_fields=['customer_name', 'supplier_name'], limit=100
                )
                
                if contracts or sessions:
                    company_info["contracts"] = contracts
                    company_info["sessions"] = sessions
                    
                    inn = None
                    if contracts:
                        inn = contracts[0].get('customer_inn')
                    elif sessions:
                        inn = sessions[0].get('customer_inn')
                    
                    company_info["summary"] = self._build_company_summary(
                        name, inn, contracts, sessions
                    )
                    
                    return company_info
            
            return None
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка безопасного поиска компании: {e}"
            )
            return None
    
    def _should_search_contracts(self, params: Dict[str, Any], query: str) -> bool:
        """Определяет необходимость поиска контрактов."""
        contract_keywords = ['контракт', 'договор', 'соглашение']
        session_keywords = ['кс', 'котировк', 'сессия']
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in contract_keywords):
            return True
        
        if 'contract_name' in params:
            return True
        
        if not any(keyword in query_lower for keyword in session_keywords):
            return True
        
        return False
    
    def _should_search_sessions(self, params: Dict[str, Any], query: str) -> bool:
        """Определяет необходимость поиска сессий."""
        session_keywords = ['кс', 'котировк', 'сессия']
        contract_keywords = ['контракт', 'договор']
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in session_keywords):
            return True
        
        if 'ks_name' in params:
            return True
        
        if not any(keyword in query_lower for keyword in contract_keywords):
            return True
        
        return False
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаляет дубликаты из результатов поиска."""
        seen_ids = set()
        unique_results = []
        
        for item in results:
            item_id = item.get('id')
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_results.append(item)
        
        return unique_results[:self.MAX_RESULTS]
    
    def _build_company_summary(self, name: str, inn: Optional[int], 
                             contracts: List[Dict], sessions: List[Dict]) -> Dict[str, Any]:
        """Создает сводную информацию по компании."""
        return {
            "name": name,
            "inn": inn,
            "contracts_count": len(contracts),
            "sessions_count": len(sessions),
            "total_contract_amount": sum(
                float(c.get('contract_amount', 0)) for c in contracts
            ),
            "total_session_amount": sum(
                float(s.get('session_amount', 0)) for s in sessions
            )
        }
    
    def _sanitize_string(self, value: Any) -> str:
        """Очистка и валидация строковых значений."""
        if not value:
            return ""
        
        clean_str = str(value).strip()
        
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
        for char in dangerous_chars:
            clean_str = clean_str.replace(char, '')
        
        return clean_str[:self.MAX_STRING_LENGTH]
    
    def _parse_amount_safe(self, amount_str: Any) -> Optional[Decimal]:
        """Безопасный парсинг денежных сумм."""
        if not amount_str:
            return None
        
        try:
            clean_amount = re.sub(r'[^\d.,]', '', str(amount_str))
            if not clean_amount:
                return None
            
            clean_amount = clean_amount.replace(',', '.')
            amount = Decimal(clean_amount)
            
            original_str = str(amount_str).lower()
            if any(word in original_str for word in ['тыс', 'k']):
                amount *= 1000
            elif any(word in original_str for word in ['млн', 'миллион', 'm']):
                amount *= 1000000
            
            if self.MIN_AMOUNT <= amount <= self.MAX_AMOUNT:
                return amount
            
            return None
            
        except (ValueError, InvalidOperation, OverflowError):
            return None
    
    def _parse_inn_safe(self, inn_str: Any) -> Optional[int]:
        """Безопасный парсинг ИНН с валидацией."""
        if not inn_str:
            return None
        
        try:
            clean_inn = re.sub(r'[^\d]', '', str(inn_str))
            
            if len(clean_inn) not in [self.MIN_INN_LENGTH, self.MAX_INN_LENGTH]:
                return None
            
            inn = int(clean_inn)
            
            if clean_inn in ['0' * len(clean_inn), '1' * len(clean_inn)]:
                return None
            
            return inn
            
        except (ValueError, OverflowError):
            return None
    
    def _parse_bik_safe(self, bik_str: Any) -> Optional[str]:
        """Безопасный парсинг БИК с валидацией."""
        if not bik_str:
            return None
        
        try:
            clean_bik = re.sub(r'[^\d]', '', str(bik_str))
            
            if len(clean_bik) != self.BIK_LENGTH:
                return None
            
            if clean_bik in ['0' * self.BIK_LENGTH, '1' * self.BIK_LENGTH]:
                return None
            
            return clean_bik
            
        except Exception:
            return None
    
    def _parse_int_safe(self, value: Any) -> Optional[int]:
        """Безопасный парсинг целых чисел."""
        if not value:
            return None
        
        try:
            clean_value = re.sub(r'[^\d]', '', str(value))
            if not clean_value:
                return None
            
            result = int(clean_value)
            
            if 1 <= result <= 2147483647:
                return result
            
            return None
            
        except (ValueError, OverflowError):
            return None