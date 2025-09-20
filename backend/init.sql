-- Инициализация базы данных для AEProject

-- Создание схемы если не существует
CREATE SCHEMA IF NOT EXISTS aeproject;

-- Создание таблицы пользователей (пример)
CREATE TABLE IF NOT EXISTS aeproject.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы логов приложения
CREATE TABLE IF NOT EXISTS aeproject.app_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    module VARCHAR(100),
    function_name VARCHAR(100),
    line_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_app_logs_level ON aeproject.app_logs(level);
CREATE INDEX IF NOT EXISTS idx_app_logs_created_at ON aeproject.app_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_users_username ON aeproject.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON aeproject.users(email);

-- Создание пользователя для приложения (если нужно)
-- CREATE USER aeproject_user WITH PASSWORD 'aeproject_password';
-- GRANT ALL PRIVILEGES ON SCHEMA aeproject TO aeproject_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA aeproject TO aeproject_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA aeproject TO aeproject_user;
