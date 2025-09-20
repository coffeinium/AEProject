-- Инициализация базы данных для AEProject

-- Создание схемы если не существует
CREATE SCHEMA IF NOT EXISTS aeproject;

-- Создание таблицы контрактов
CREATE TABLE IF NOT EXISTS aeproject.contracts (
    id SERIAL PRIMARY KEY,
    contract_name TEXT NOT NULL,
    contract_id BIGINT UNIQUE NOT NULL,
    contract_amount DECIMAL(15, 5) NOT NULL,
    contract_date TIMESTAMP WITH TIME ZONE NOT NULL,
    category_pp_first_position TEXT,
    customer_name TEXT NOT NULL,
    customer_inn BIGINT NOT NULL,
    supplier_name TEXT NOT NULL,
    supplier_inn BIGINT NOT NULL,
    law_basis VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы конкурсных сессий (КС)
CREATE TABLE IF NOT EXISTS aeproject.sessions (
    id SERIAL PRIMARY KEY,
    session_name TEXT NOT NULL,
    session_id BIGINT UNIQUE NOT NULL,
    session_amount DECIMAL(15, 5) NOT NULL,
    session_created_date TIMESTAMP WITH TIME ZONE NOT NULL,
    session_completed_date TIMESTAMP WITH TIME ZONE NOT NULL,
    category_pp_first_position TEXT,
    customer_name TEXT NOT NULL,
    customer_inn BIGINT NOT NULL,
    supplier_name TEXT NOT NULL,
    supplier_inn BIGINT NOT NULL,
    law_basis VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для производительности

-- Индексы для таблицы контрактов
CREATE INDEX IF NOT EXISTS idx_contracts_contract_id ON aeproject.contracts(contract_id);
CREATE INDEX IF NOT EXISTS idx_contracts_contract_date ON aeproject.contracts(contract_date);
CREATE INDEX IF NOT EXISTS idx_contracts_customer_inn ON aeproject.contracts(customer_inn);
CREATE INDEX IF NOT EXISTS idx_contracts_supplier_inn ON aeproject.contracts(supplier_inn);
CREATE INDEX IF NOT EXISTS idx_contracts_law_basis ON aeproject.contracts(law_basis);
CREATE INDEX IF NOT EXISTS idx_contracts_amount ON aeproject.contracts(contract_amount);
CREATE INDEX IF NOT EXISTS idx_contracts_created_at ON aeproject.contracts(created_at);

-- Индексы для таблицы конкурсных сессий
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON aeproject.sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_date ON aeproject.sessions(session_created_date);
CREATE INDEX IF NOT EXISTS idx_sessions_completed_date ON aeproject.sessions(session_completed_date);
CREATE INDEX IF NOT EXISTS idx_sessions_customer_inn ON aeproject.sessions(customer_inn);
CREATE INDEX IF NOT EXISTS idx_sessions_supplier_inn ON aeproject.sessions(supplier_inn);
CREATE INDEX IF NOT EXISTS idx_sessions_law_basis ON aeproject.sessions(law_basis);
CREATE INDEX IF NOT EXISTS idx_sessions_amount ON aeproject.sessions(session_amount);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON aeproject.sessions(created_at);