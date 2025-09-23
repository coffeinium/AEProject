# AEProject - Development Guide

## 🏆 TenderHack Самара 2025 - ПОБЕДИТЕЛИ!

Проект создан командой **AEternum Team** для хакатона [TenderHack](https://tenderhack.ru/) в Самаре (19.09 - 21.09.2025).

🎉 **Команда AEternum Team заняла призовое место!**

### Команда AEternum Team

- **Оксана** - Менеджер проекта, TeamLead
- **Валерий** (rootperemotka) - Fullstack, ML-Engineer, капитан команды
- **Олег** (Oleg4311) - Frontend разработчик
- **Владимир** - ML-Engineer

### Конфигурация ML модели

Оптимальная и финальная модель: `cic_model_v2_production.pkl`

Для работы необходимо указать в `.env` файле:

```env
AEAPISETTINGS_ML_MODEL_PATH=src/core/ml/assets/cic_model_v2_production.pkl
```

⚠️ **Примечание**: Сейчас модель не указана для тестирования обучения.

## 📚 Документация

- **[API Documentation](API.md)** - Полная документация REST API с примерами запросов и ответов
- **[ML API Documentation](API.md#5-ml-api---утилиты-для-обучения-и-тестирования)** - Утилиты для обучения и тестирования ML модели

## Структура проекта

```
AEProject/
├── backend/                 # Backend API (FastAPI)
│   ├── main.py             # Главный файл приложения
│   ├── API.md              # Полная документация API
│   ├── requirements.txt    # Python зависимости
│   ├── Dockerfile.dev      # Dockerfile для разработки
│   ├── init.sql           # SQL скрипт инициализации БД
│   └── src/               # Исходный код
├── frontend/              # Frontend (React + Vite)
│   ├── Dockerfile.dev     # Dockerfile для разработки
│   ├── package.json       # Node.js зависимости
│   └── src/               # Исходный код
├── compose.dev.yaml                    # Docker Compose для разработки
├── compose.dev.for-ports-error.yaml   # Альтернативная конфигурация (другие порты)
├── .env                               # Переменные окружения
└── README.md                         # Основная документация
```

## Запуск в режиме разработки

### Предварительные требования

- Docker и Docker Compose
- Git

### Быстрый старт

#### Стандартный запуск (Linux/macOS):

1. **Клонируйте репозиторий и перейдите в директорию:**

   ```bash
   cd AEProject
   ```
2. **Запустите все сервисы:**

   ```bash
   docker-compose -f compose.dev.yaml up --build
   ```
3. **Доступ к приложению:**

   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - PostgreSQL: localhost:5432

#### Альтернативный запуск (при конфликтах портов):

Если стандартные порты заняты, используйте альтернативную конфигурацию:

1. **Запустите с альтернативными портами:**

   ```bash
   docker-compose -f compose.dev.for-ports-error.yaml up --build
   ```
2. **Доступ к приложению:**

   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - PostgreSQL: localhost:5433 (изменен порт)

#### Основные API endpoints:

- `GET /user/search` - Поиск и анализ запросов с ML
- `GET /user/history` - История запросов
- `POST /user/complete_data` - Дополнение частичных данных
- `GET /api/ml/predict` - Прямая классификация намерений
- `GET /api/ml/health` - Проверка состояния ML модели

### Сервисы

#### PostgreSQL Database

- **Контейнер:** `ae-project-postgres`
- **Порт:** 5432
- **База данных:** `aeproject_dev`
- **Пользователь:** `postgres`
- **Пароль:** `postgres`
- **Подсеть:** `172.20.0.0/16`

#### Backend API

- **Контейнер:** `ae-project-backend`
- **Порт:** 8000
- **Автоперезагрузка:** Включена (файлы монтируются)
- **Логи:** Сохраняются в volume `backend_logs`

#### Frontend

- **Контейнер:** `ae-project-frontend`
- **Порт:** 5173
- **Hot Reload:** Включен (файлы монтируются)
- **API URL:** http://localhost:8000

### Полезные команды

```bash
# Запуск всех сервисов
docker-compose -f compose.dev.yaml up

# Запуск в фоновом режиме
docker-compose -f compose.dev.yaml up -d

# Остановка всех сервисов
docker-compose -f compose.dev.yaml down

# Пересборка и запуск
docker-compose -f compose.dev.yaml up --build

# Просмотр логов
docker-compose -f compose.dev.yaml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f compose.dev.yaml logs -f backend

# Выполнение команд в контейнере
docker-compose -f compose.dev.yaml exec backend bash
docker-compose -f compose.dev.yaml exec postgres psql -U postgres -d aeproject_dev
```

### Переменные окружения

Основные переменные в файле `.env`:

```env
# Database
POSTGRES_DB=aeproject_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/aeproject_dev

# API
AEAPISETTINGS_UVICORN_HOST=0.0.0.0
AEAPISETTINGS_UVICORN_PORT=8000
AEAPISETTINGS_UVICORN_DEBUG=False
```

### Volumes

- `postgres_data` - Данные PostgreSQL
- `backend_logs` - Логи backend приложения
- Локальные файлы монтируются для hot reload в режиме разработки

### Отладка

1. **Проверка статуса контейнеров:**

   ```bash
   docker-compose -f compose.dev.yaml ps
   ```
2. **Подключение к PostgreSQL:**

   ```bash
   docker-compose -f compose.dev.yaml exec postgres psql -U postgres -d aeproject_dev
   ```
3. **Просмотр логов конкретного сервиса:**

   ```bash
   docker-compose -f compose.dev.yaml logs backend
   ```

### Остановка и очистка

```bash
# Остановка сервисов
docker-compose -f compose.dev.yaml down

# Остановка и удаление volumes (ВНИМАНИЕ: удалит данные БД!)
docker-compose -f compose.dev.yaml down -v

# Удаление образов
docker-compose -f compose.dev.yaml down --rmi all
```
