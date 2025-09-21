# AEProject API Documentation

Полная документация REST API для системы управления закупками AEProject.

## Базовая информация

- **Базовый URL**: `http://localhost:8000`
- **Формат ответов**: JSON
- **Кодировка**: UTF-8
- **Методы аутентификации**: Не требуется (в текущей версии)

---

## 📋 Содержание

1. [Поиск и анализ запросов](#1-поиск-и-анализ-запросов)
2. [История запросов](#2-история-запросов)
3. [Дополнение данных](#3-дополнение-данных)
4. [Предложения для поиска](#4-предложения-для-поиска)
5. [ML API - Утилиты для обучения и тестирования](#5-ml-api---утилиты-для-обучения-и-тестирования)
   - [POST /api/ml/predict](#post-apimlpredict) - Классификация намерений
   - [POST /api/ml/predict/batch](#post-apimlpredictbatch) - Пакетная классификация
   - [GET /api/ml/info](#get-apimlinfo) - Информация о модели
   - [GET /api/ml/intents](#get-apimlintents) - Доступные намерения
   - [GET /api/ml/health](#get-apimlhealth) - Проверка работоспособности
6. [Модели данных](#6-модели-данных)
7. [Коды ошибок](#7-коды-ошибок)

---

## 1. Поиск и анализ запросов

### GET `/user/search`

Основной endpoint для обработки пользовательских запросов с использованием ML-анализа намерений.

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `query` | string | ✅ | Текст запроса пользователя |
| `detailed` | boolean | ❌ | Возвращать детальную информацию ML-анализа (по умолчанию: false) |
| `write_in_history` | boolean | ❌ | Сохранять запрос в историю (по умолчанию: true) |

#### Примеры запросов

```bash
# Создание контракта
curl -G "http://localhost:8000/user/search" \
  --data-urlencode "query=создай контракт на канцтовары 50000 рублей"

# Поиск документов
curl -G "http://localhost:8000/user/search" \
  --data-urlencode "query=найди контракты ООО Газпром"

# Поиск компании
curl -G "http://localhost:8000/user/search" \
  --data-urlencode "query=покажи информацию о компании ИНН 7736050003"

# Детальный анализ
curl -G "http://localhost:8000/user/search" \
  --data-urlencode "query=создай КС на мебель" \
  --data-urlencode "detailed=true"
```

#### Ответы

##### Успешное создание контракта (требуются дополнительные данные)

```json
{
  "status": "success",
  "response": {
    "type": "create_contract_needs_more_info",
    "data": {
      "type": "create_contract_needs_more_info",
      "status": "needs_more_info",
      "message": "Для создания контракта нужна дополнительная информация",
      "contract_data": {
        "contract_name": "канцтовары",
        "contract_amount": "50000.0",
        "contract_date": "2025-09-21T02:56:10.989222"
      },
      "missing_fields": ["customer_name", "customer_inn"],
      "suggestions": [
        "Укажите название заказчика (например: ООО Ромашка)",
        "Укажите ИНН заказчика (10 или 12 цифр)"
      ]
    }
  },
  "ml_data": {
    "intent": "create_contract",
    "confidence": 0.8456,
    "entities": {
      "contract_name": "канцтовары",
      "amount": "50000.0",
      "category": "канцтовары"
    },
    "details": null
  }
}
```

##### Готовый к созданию контракт

```json
{
  "status": "success",
  "response": {
    "type": "create_contract_ready_to_create",
    "data": {
      "type": "create_contract_ready_to_create",
      "status": "ready_to_create",
      "message": "Контракт готов к созданию",
      "contract_data": {
        "contract_name": "поставка канцтоваров",
        "contract_amount": "50000.0",
        "customer_name": "ООО Ромашка",
        "customer_inn": "1234567890",
        "contract_date": "2025-09-21T02:56:10.989222"
      },
      "next_steps": [
        "Подтвердите данные",
        "Укажите дополнительные параметры"
      ]
    }
  },
  "ml_data": {
    "intent": "create_contract",
    "confidence": 0.9234,
    "entities": {
      "contract_name": "поставка канцтоваров",
      "amount": "50000.0",
      "customer_name": "ООО Ромашка",
      "customer_inn": "1234567890"
    }
  }
}
```

##### Результаты поиска документов

```json
{
  "status": "success",
  "response": {
    "type": "search_contracts_results",
    "data": {
      "type": "search_contracts_results",
      "status": "success",
      "message": "Найдено 3 результатов",
      "results": [
        {
          "type": "contract",
          "data": {
            "id": 1,
            "contract_name": "Поставка канцтоваров",
            "contract_id": 2023001,
            "contract_amount": "150000.00",
            "contract_date": "2023-06-15T10:30:00Z",
            "customer_name": "ООО Газпром",
            "customer_inn": 7736050003,
            "supplier_name": "ООО Поставщик",
            "supplier_inn": 1234567890,
            "law_basis": "44-ФЗ",
            "category_pp_first_position": "канцтовары"
          }
        }
      ],
      "total_count": 3,
      "search_params": {
        "customer_search": "ООО Газпром"
      }
    }
  },
  "ml_data": {
    "intent": "search_docs",
    "confidence": 0.8765,
    "entities": {
      "customer_name": "ООО Газпром"
    }
  }
}
```

##### Поиск компании

```json
{
  "status": "success",
  "response": {
    "type": "company_search_results",
    "data": {
      "type": "company_search_results",
      "status": "success",
      "message": "Найдена информация о компании",
      "company_data": {
        "summary": {
          "name": "ООО Газпром",
          "inn": 7736050003,
          "contracts_count": 15,
          "sessions_count": 8,
          "total_contract_amount": 25000000.0,
          "total_session_amount": 12000000.0
        },
        "contracts": [
          {
            "id": 1,
            "contract_name": "Поставка оборудования",
            "contract_amount": "5000000.00",
            "contract_date": "2023-06-15T10:30:00Z"
          }
        ],
        "sessions": [
          {
            "id": 1,
            "session_name": "КС на канцтовары",
            "session_amount": "300000.00",
            "session_created_date": "2023-07-01T09:00:00Z"
          }
        ]
      },
      "search_params": {
        "inn": 7736050003
      }
    }
  },
  "ml_data": {
    "intent": "search_company",
    "confidence": 0.9123,
    "entities": {
      "inn": "7736050003"
    }
  }
}
```

##### Справочная информация

```json
{
  "status": "success",
  "response": {
    "type": "help_response",
    "data": {
      "type": "help_response",
      "status": "success",
      "message": "Справочная информация",
      "help_sections": [
        {
          "topic": "Создание контракта",
          "description": "Для создания контракта укажите: название, сумму, заказчика",
          "examples": [
            "Создай контракт на канцтовары сумма 50000 рублей для ООО Ромашка",
            "Новый договор поставка мебели 150 тысяч"
          ]
        },
        {
          "topic": "Поиск документов",
          "description": "Для поиска можно использовать: название, ИНН, сумму, категорию",
          "examples": [
            "Найди контракты ООО Ромашка",
            "Покажи договоры на сумму больше 100000",
            "Поиск по ИНН 1234567890"
          ]
        }
      ]
    }
  },
  "ml_data": {
    "intent": "help",
    "confidence": 0.9567,
    "entities": {}
  }
}
```

##### Ошибки

```json
{
  "status": "error",
  "response": {
    "type": "error",
    "data": "ML модель не инициализирована"
  },
  "ml_data": {
    "intent": "error",
    "confidence": 0.0,
    "entities": {}
  }
}
```

---

## 2. История запросов

### GET `/user/history`

Получение истории пользовательских запросов с фильтрацией.

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `limit` | integer | ❌ | Максимальное количество записей (по умолчанию: 100) |
| `hours` | integer | ❌ | Получить записи за последние N часов |
| `intent` | string | ❌ | Фильтр по намерению |
| `min_confidence` | float | ❌ | Минимальная уверенность (0.0-1.0) |

#### Примеры запросов

```bash
# Последние 50 записей
curl "http://localhost:8000/user/history?limit=50"

# За последние 24 часа
curl "http://localhost:8000/user/history?hours=24&limit=100"

# По намерению создания контрактов
curl "http://localhost:8000/user/history?intent=create_contract&limit=20"

# С высокой уверенностью
curl "http://localhost:8000/user/history?min_confidence=0.8&limit=30"
```

#### Ответ

```json
{
  "status": "success",
  "response": {
    "type": "history",
    "data": {
      "records": [
        {
          "id": 1,
          "timestamp": "2025-09-21T02:56:10.989222Z",
          "text": "создай контракт на канцтовары 50000 рублей",
          "intent": "create_contract",
          "confidence": 0.8456,
          "entities": {
            "contract_name": "канцтовары",
            "amount": "50000.0"
          },
          "created_at": "2025-09-21T02:56:10.989222Z"
        }
      ],
      "total_count": 1,
      "filters": {
        "limit": 100,
        "hours": null,
        "intent": null,
        "min_confidence": null
      }
    }
  }
}
```

### GET `/user/history/stats`

Получение статистики по истории запросов.

#### Примеры запросов

```bash
curl "http://localhost:8000/user/history/stats"
```

#### Ответ

```json
{
  "status": "success",
  "response": {
    "type": "history_stats",
    "data": {
      "overview": {
        "total_count": {
          "total": 1250
        },
        "avg_confidence": {
          "avg": 0.7834
        },
        "recent_activity": {
          "count": 45
        }
      },
      "top_intents": [
        {
          "intent": "search_docs",
          "count": 450,
          "percentage": 36.0
        },
        {
          "intent": "create_contract",
          "count": 320,
          "percentage": 25.6
        },
        {
          "intent": "search_company",
          "count": 280,
          "percentage": 22.4
        }
      ],
      "summary": {
        "total_queries": 1250,
        "avg_confidence": 0.7834,
        "recent_activity": 45
      }
    }
  }
}
```

### GET `/user/history/search`

Поиск в истории запросов по тексту.

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `q` | string | ✅ | Поисковый запрос (минимум 2 символа) |
| `limit` | integer | ❌ | Максимальное количество результатов (по умолчанию: 50) |

#### Примеры запросов

```bash
# Поиск по слову "контракт"
curl -G "http://localhost:8000/user/history/search" \
  --data-urlencode "q=контракт" \
  --data-urlencode "limit=20"

# Поиск по ИНН
curl -G "http://localhost:8000/user/history/search" \
  --data-urlencode "q=7736050003"
```

#### Ответ

```json
{
  "status": "success",
  "response": {
    "type": "history_search",
    "data": {
      "query": "контракт",
      "records": [
        {
          "id": 1,
          "timestamp": "2025-09-21T02:56:10.989222Z",
          "text": "создай контракт на канцтовары 50000 рублей",
          "intent": "create_contract",
          "confidence": 0.8456,
          "entities": {
            "contract_name": "канцтовары",
            "amount": "50000.0"
          }
        }
      ],
      "total_count": 1,
      "limit": 20
    }
  }
}
```

### DELETE `/user/history/cleanup`

Очистка старых записей истории.

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `days_to_keep` | integer | ❌ | Количество дней для хранения записей (по умолчанию: 90) |

#### Примеры запросов

```bash
# Удалить записи старше 90 дней
curl -X DELETE "http://localhost:8000/user/history/cleanup"

# Удалить записи старше 30 дней
curl -X DELETE "http://localhost:8000/user/history/cleanup?days_to_keep=30"
```

#### Ответ

```json
{
  "status": "success",
  "response": {
    "type": "history_cleanup",
    "data": {
      "deleted_count": 156,
      "days_to_keep": 90,
      "message": "Удалено 156 записей старше 90 дней"
    }
  }
}
```

---

## 3. Дополнение данных

### POST `/user/complete_data`

Дополнение частичных данных для создания записей.

#### Тело запроса

```json
{
  "data_type": "contract",
  "provided_data": {
    "contract_name": "канцтовары",
    "contract_amount": "50000.0"
  },
  "additional_data": {
    "customer_name": "ООО Ромашка",
    "customer_inn": "1234567890"
  }
}
```

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `data_type` | string | ✅ | Тип данных: "contract", "ks", "company" |
| `provided_data` | object | ✅ | Уже предоставленные данные |
| `additional_data` | object | ✅ | Дополнительные данные от пользователя |

#### Примеры запросов

```bash
# Дополнение данных контракта
curl -X POST "http://localhost:8000/user/complete_data" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "contract",
    "provided_data": {
      "contract_name": "канцтовары",
      "contract_amount": "50000.0"
    },
    "additional_data": {
      "customer_name": "ООО Ромашка",
      "customer_inn": "1234567890"
    }
  }'

# Дополнение данных КС
curl -X POST "http://localhost:8000/user/complete_data" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "ks",
    "provided_data": {
      "session_name": "мебель",
      "session_amount": "100000.0"
    },
    "additional_data": {
      "customer_name": "ПАО Банк"
    }
  }'
```

#### Ответы

##### Нужны дополнительные данные

```json
{
  "status": "needs_more_info",
  "response": {
    "type": "contract_incomplete",
    "data": {
      "provided_data": {
        "contract_name": "канцтовары",
        "contract_amount": "50000.0",
        "customer_name": "ООО Ромашка"
      },
      "missing_fields": ["customer_inn"],
      "suggestions": [
        "Укажите ИНН заказчика (10 или 12 цифр)"
      ]
    }
  }
}
```

##### Данные готовы

```json
{
  "status": "success",
  "response": {
    "type": "contract_ready",
    "data": {
      "message": "Контракт готов к созданию",
      "contract_data": {
        "contract_name": "канцтовары",
        "contract_amount": "50000.0",
        "customer_name": "ООО Ромашка",
        "customer_inn": "1234567890"
      },
      "next_steps": [
        "Подтвердите данные",
        "Создать контракт"
      ]
    }
  }
}
```

---

## 4. Предложения для поиска

### GET `/user/search_suggestions`

Получение предложений для улучшения поиска.

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `query` | string | ✅ | Поисковый запрос |
| `search_type` | string | ❌ | Тип поиска: "contracts", "sessions", "companies", "auto" (по умолчанию: "auto") |

#### Примеры запросов

```bash
# Общие предложения
curl -G "http://localhost:8000/user/search_suggestions" \
  --data-urlencode "query=найди"

# Предложения для поиска контрактов
curl -G "http://localhost:8000/user/search_suggestions" \
  --data-urlencode "query=контракт" \
  --data-urlencode "search_type=contracts"

# Предложения для коротких запросов
curl -G "http://localhost:8000/user/search_suggestions" \
  --data-urlencode "query=кс"
```

#### Ответ

```json
{
  "status": "success",
  "response": {
    "type": "search_suggestions",
    "data": {
      "query": "найди",
      "search_type": "auto",
      "suggestions": [
        "Введите более длинный запрос (минимум 3 символа)",
        "Укажите конкретные параметры: название, ИНН, сумму",
        "Для поиска контрактов укажите: название, заказчика, ИНН или сумму",
        "Примеры: 'контракты ООО Ромашка', 'договоры на 100000 рублей'",
        "Для поиска КС укажите: название, заказчика, ИНН или сумму",
        "Примеры: 'КС на канцтовары', 'котировки по 44-ФЗ'",
        "Для поиска компаний укажите: название или ИНН",
        "Примеры: 'ООО Ромашка', 'ИНН 1234567890'"
      ],
      "examples": [
        "Найди контракты ООО Ромашка",
        "Покажи КС на сумму больше 50000",
        "Создай договор на канцтовары 25000 рублей",
        "Поиск по ИНН 1234567890"
      ]
    }
  }
}
```

---

## 5. ML API - Утилиты для обучения и тестирования

> ⚠️ **Важно**: Эти endpoints предназначены для разработки, отладки и тестирования ML модели. Используйте их для анализа качества предсказаний, обучения модели и диагностики.

### POST `/api/ml/predict`

Прямой вызов ML модели для классификации намерений (без бизнес-логики).

#### Тело запроса

```json
{
  "text": "создай контракт на канцтовары 50000 рублей",
  "detailed": true
}
```

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `text` | string | ✅ | Текст для анализа (1-1000 символов) |
| `detailed` | boolean | ❌ | Возвращать детальный анализ с вероятностями (по умолчанию: false) |

#### Примеры запросов

```bash
# Простая классификация
curl -X POST "http://localhost:8000/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "создай контракт на канцтовары 50000 рублей",
    "detailed": false
  }'

# Детальный анализ с вероятностями
curl -X POST "http://localhost:8000/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "найди компанию ООО Газпром",
    "detailed": true
  }'
```

#### Ответы

##### Простая классификация

```json
{
  "original_text": "создай контракт на канцтовары 50000 рублей",
  "processed_text": "создай контракт на канцтовары 50000 рублей",
  "intent": "create_contract",
  "intent_name": "Создание контракта",
  "confidence": 0.8456,
  "entities": {
    "contract_name": "канцтовары",
    "amount": "50000",
    "category": "канцтовары"
  },
  "timestamp": "2025-09-21T02:56:10.989222"
}
```

##### Детальный анализ

```json
{
  "original_text": "найди компанию ООО Газпром",
  "processed_text": "найди компанию ооо газпром",
  "intent": "search_company",
  "intent_name": "Поиск по компаниям",
  "confidence": 0.9234,
  "entities": {
    "company_name": "ООО Газпром"
  },
  "timestamp": "2025-09-21T02:56:10.989222",
  "all_probabilities": {
    "search_company": 0.9234,
    "search_docs": 0.0456,
    "create_contract": 0.0234,
    "create_ks": 0.0076
  },
  "top_predictions": [
    {
      "intent": "search_company",
      "intent_name": "Поиск по компаниям",
      "confidence": 0.9234
    },
    {
      "intent": "search_docs",
      "intent_name": "Поиск по документам",
      "confidence": 0.0456
    },
    {
      "intent": "create_contract",
      "intent_name": "Создание контракта",
      "confidence": 0.0234
    }
  ]
}
```

### POST `/api/ml/predict/batch`

Пакетная классификация намерений для нескольких текстов одновременно (до 10 штук).

#### Тело запроса

```json
{
  "texts": [
    "создай контракт на канцтовары",
    "найди ООО Газпром",
    "помощь по созданию КС",
    "покажи документ 12345"
  ]
}
```

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `texts` | array[string] | ✅ | Массив текстов для анализа (1-10 элементов, каждый до 1000 символов) |

#### Примеры запросов

```bash
# Пакетная обработка
curl -X POST "http://localhost:8000/api/ml/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "создай контракт на канцтовары",
      "найди ООО Газпром",
      "помощь по созданию КС"
    ]
  }'
```

#### Ответ

```json
{
  "results": [
    {
      "original_text": "создай контракт на канцтовары",
      "processed_text": "создай контракт на канцтовары",
      "intent": "create_contract",
      "intent_name": "Создание контракта",
      "confidence": 0.8456,
      "entities": {
        "contract_name": "канцтовары",
        "category": "канцтовары"
      },
      "timestamp": "2025-09-21T02:56:10.989222"
    },
    {
      "original_text": "найди ООО Газпром",
      "processed_text": "найди ооо газпром",
      "intent": "search_company",
      "intent_name": "Поиск по компаниям",
      "confidence": 0.9234,
      "entities": {
        "company_name": "ООО Газпром"
      },
      "timestamp": "2025-09-21T02:56:10.989222"
    },
    {
      "original_text": "помощь по созданию КС",
      "processed_text": "помощь по созданию кс",
      "intent": "help",
      "intent_name": "Помощь",
      "confidence": 0.7890,
      "entities": {
        "help_data": "созданию КС"
      },
      "timestamp": "2025-09-21T02:56:10.989222"
    }
  ],
  "total_processed": 3
}
```

### GET `/api/ml/info`

Получение подробной информации о состоянии и возможностях ML модели.

#### Примеры запросов

```bash
curl "http://localhost:8000/api/ml/info"
```

#### Ответ

```json
{
  "is_trained": true,
  "intents": [
    "create_contract",
    "create_ks",
    "search_docs",
    "search_company",
    "create_company_profile",
    "help"
  ],
  "intent_names": [
    "Создание контракта",
    "Создание КС",
    "Поиск по документам",
    "Поиск по компаниям",
    "Создание профиля компании",
    "Помощь"
  ],
  "correction_dictionary_size": 25,
  "entity_patterns": [
    "contract_name",
    "ks_name",
    "customer_name",
    "customer_inn",
    "amount",
    "category",
    "law",
    "document_id",
    "company_name",
    "inn",
    "bik",
    "help_data"
  ]
}
```

### GET `/api/ml/intents`

Получение словаря всех доступных намерений с их человекочитаемыми названиями.

#### Примеры запросов

```bash
curl "http://localhost:8000/api/ml/intents"
```

#### Ответ

```json
{
  "create_contract": "Создание контракта",
  "create_ks": "Создание КС",
  "search_docs": "Поиск по документам",
  "search_company": "Поиск по компаниям",
  "create_company_profile": "Создание профиля компании",
  "help": "Помощь"
}
```

### GET `/api/ml/health`

Проверка работоспособности ML модели с тестовым предсказанием.

#### Примеры запросов

```bash
curl "http://localhost:8000/api/ml/health"
```

#### Ответы

##### Модель работает

```json
{
  "status": "healthy",
  "message": "ML модель работает корректно",
  "test_prediction": "Помощь"
}
```

##### Модель недоступна

```json
{
  "error": "ML модель еще не инициализирована",
  "detail": "Попробуйте позже"
}
```

### Использование ML API для тестирования

#### Тестирование качества модели

```bash
# Тест различных типов запросов
curl -X POST "http://localhost:8000/api/ml/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "создай контракт на канцтовары 50000 рублей для ООО Ромашка ИНН 1234567890",
      "найди все контракты ООО Газпром",
      "покажи КС на мебель больше 100000",
      "помощь по созданию профиля компании",
      "создй кнтракт канцтвары",
      "непонятный текст без смысла"
    ]
  }'
```

#### Анализ уверенности модели

```bash
# Детальный анализ для проблемных случаев
curl -X POST "http://localhost:8000/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "создй кнтракт канцтвары",
    "detailed": true
  }'
```

#### Проверка извлечения сущностей

```bash
# Тест извлечения различных сущностей
curl -X POST "http://localhost:8000/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "создай контракт поставка оборудования заказчик ООО Газпром ИНН 7736050003 сумма 500 тысяч категория оборудование закон 44-ФЗ",
    "detailed": false
  }'
```

### Ошибки ML API

#### 400 - Неверный запрос

```json
{
  "error": "Validation error",
  "detail": "Текст не может быть пустым"
}
```

#### 503 - Модель недоступна

```json
{
  "error": "ML модель еще не инициализирована",
  "detail": "Попробуйте позже"
}
```

#### 500 - Внутренняя ошибка

```json
{
  "error": "Ошибка обработки запроса",
  "detail": "Подробности ошибки"
}
```

---

## 6. Модели данных

### MLData

```json
{
  "intent": "string",
  "confidence": "float | null",
  "entities": "object",
  "details": "any | null"
}
```

### ResponseData

```json
{
  "type": "string",
  "data": "any | null"
}
```

### SearchResponse

```json
{
  "status": "string",
  "response": "ResponseData",
  "ml_data": "MLData"
}
```

### HistoryResponse

```json
{
  "status": "string",
  "response": "ResponseData"
}
```

### Contract

```json
{
  "id": "integer",
  "contract_name": "string",
  "contract_id": "integer",
  "contract_amount": "decimal",
  "contract_date": "datetime",
  "category_pp_first_position": "string | null",
  "customer_name": "string",
  "customer_inn": "integer",
  "supplier_name": "string",
  "supplier_inn": "integer",
  "law_basis": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Session

```json
{
  "id": "integer",
  "session_name": "string",
  "session_id": "integer",
  "session_amount": "decimal",
  "session_created_date": "datetime",
  "session_completed_date": "datetime",
  "category_pp_first_position": "string | null",
  "customer_name": "string",
  "customer_inn": "integer",
  "supplier_name": "string",
  "supplier_inn": "integer",
  "law_basis": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### HistoryRecord

```json
{
  "id": "integer",
  "timestamp": "datetime",
  "text": "string",
  "intent": "string | null",
  "confidence": "float | null",
  "entities": "object",
  "created_at": "datetime"
}
```

### IntentRequest (ML API)

```json
{
  "text": "string",
  "detailed": "boolean"
}
```

### BatchIntentRequest (ML API)

```json
{
  "texts": ["string", "string", "..."]
}
```

### IntentResponse (ML API)

```json
{
  "original_text": "string",
  "processed_text": "string",
  "intent": "string",
  "intent_name": "string",
  "confidence": "float",
  "entities": "object",
  "timestamp": "string",
  "all_probabilities": "object | null",
  "top_predictions": "array | null"
}
```

### BatchIntentResponse (ML API)

```json
{
  "results": ["IntentResponse", "..."],
  "total_processed": "integer"
}
```

### ModelInfoResponse (ML API)

```json
{
  "is_trained": "boolean",
  "intents": ["string", "..."],
  "intent_names": ["string", "..."],
  "correction_dictionary_size": "integer",
  "entity_patterns": ["string", "..."]
}
```

---

## 6. Коды ошибок

### HTTP статус коды

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Неверный запрос |
| 404 | Ресурс не найден |
| 500 | Внутренняя ошибка сервера |

### Типы ошибок в ответах

#### Ошибка валидации

```json
{
  "status": "error",
  "response": {
    "type": "error",
    "data": "Поисковый запрос должен содержать минимум 2 символа"
  }
}
```

#### Ошибка ML модели

```json
{
  "status": "error",
  "response": {
    "type": "error",
    "data": "ML модель не инициализирована"
  },
  "ml_data": {
    "intent": "error",
    "confidence": 0.0,
    "entities": {}
  }
}
```

#### Ошибка базы данных

```json
{
  "status": "error",
  "response": {
    "type": "error",
    "data": "Storage недоступен"
  }
}
```

---

## 8. Типы намерений (Intents)

### Поддерживаемые намерения

| Intent | Описание | Примеры запросов |
|--------|----------|------------------|
| `create_contract` | Создание контракта | "создай контракт на канцтовары", "новый договор мебель" |
| `create_ks` | Создание КС | "создай КС на оборудование", "котировка услуги" |
| `search_docs` | Поиск документов | "найди контракты ООО Газпром", "покажи документ 12345" |
| `search_company` | Поиск компаний | "найди компанию ИНН 7736050003", "ООО Ромашка" |
| `create_company_profile` | Создание профиля компании | "создай профиль ООО Рога ИНН 1234567890" |
| `help` | Справочная информация | "помощь", "как создать контракт" |

### Извлекаемые сущности (Entities)

| Entity | Описание | Примеры |
|--------|----------|---------|
| `contract_name` | Название контракта | "поставка канцтоваров", "услуги уборки" |
| `ks_name` | Название КС | "КС на мебель", "котировка оборудования" |
| `customer_name` | Название заказчика | "ООО Газпром", "ПАО Сбербанк" |
| `customer_inn` | ИНН заказчика | "7736050003", "1234567890" |
| `amount` | Сумма | "50000", "100к", "1.5 млн" |
| `category` | Категория | "канцтовары", "мебель", "оборудование" |
| `law` | Закон-основание | "44-ФЗ", "223-ФЗ" |
| `document_id` | ID документа | "12345", "67890" |
| `company_name` | Название компании | "ООО Ромашка", "АО Энерго" |
| `inn` | ИНН | "7736050003", "1234567890" |
| `bik` | БИК | "044525225" |

---

## 9. Примеры интеграции

### JavaScript (Fetch API)

```javascript
// Поиск
async function search(query) {
  const response = await fetch(`/user/search?${new URLSearchParams({
    query: query,
    detailed: true
  })}`);
  return await response.json();
}

// История
async function getHistory(limit = 100) {
  const response = await fetch(`/user/history?limit=${limit}`);
  return await response.json();
}

// Дополнение данных
async function completeData(dataType, providedData, additionalData) {
  const response = await fetch('/user/complete_data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      data_type: dataType,
      provided_data: providedData,
      additional_data: additionalData
    })
  });
  return await response.json();
}

// ML API функции
async function mlPredict(text, detailed = false) {
  const response = await fetch('/api/ml/predict', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: text,
      detailed: detailed
    })
  });
  return await response.json();
}

async function mlPredictBatch(texts) {
  const response = await fetch('/api/ml/predict/batch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      texts: texts
    })
  });
  return await response.json();
}

async function mlGetInfo() {
  const response = await fetch('/api/ml/info');
  return await response.json();
}

async function mlHealthCheck() {
  const response = await fetch('/api/ml/health');
  return await response.json();
}
```

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

def search(query, detailed=False):
    params = {
        'query': query,
        'detailed': detailed
    }
    response = requests.get(f"{BASE_URL}/user/search", params=params)
    return response.json()

def get_history(limit=100, hours=None, intent=None):
    params = {'limit': limit}
    if hours:
        params['hours'] = hours
    if intent:
        params['intent'] = intent
    
    response = requests.get(f"{BASE_URL}/user/history", params=params)
    return response.json()

def complete_data(data_type, provided_data, additional_data):
    payload = {
        'data_type': data_type,
        'provided_data': provided_data,
        'additional_data': additional_data
    }
    response = requests.post(f"{BASE_URL}/user/complete_data", json=payload)
    return response.json()

# ML API функции
def ml_predict(text, detailed=False):
    payload = {
        'text': text,
        'detailed': detailed
    }
    response = requests.post(f"{BASE_URL}/api/ml/predict", json=payload)
    return response.json()

def ml_predict_batch(texts):
    payload = {'texts': texts}
    response = requests.post(f"{BASE_URL}/api/ml/predict/batch", json=payload)
    return response.json()

def ml_get_info():
    response = requests.get(f"{BASE_URL}/api/ml/info")
    return response.json()

def ml_health_check():
    response = requests.get(f"{BASE_URL}/api/ml/health")
    return response.json()
```

---

## 10. Конфигурация и настройки

### Переменные окружения

Основные настройки системы управляются через переменные окружения:

```bash
# Пути к файлам
AEAPISETTINGS_HANDLER_TEXT_PATH=src/assets/texts.json
AEAPISETTINGS_ML_MODEL_PATH=src/core/ml/assets/cic_model_v2.pkl
AEAPISETTINGS_ML_SETTINGS_PATH=src/core/ml/assets/settings.json
AEAPISETTINGS_ML_DATASET_PATH=src/core/ml/assets/dataset.json

# Константы валидации
AEAPISETTINGS_HANDLER_MIN_INN_LENGTH=10
AEAPISETTINGS_HANDLER_MAX_INN_LENGTH=12
AEAPISETTINGS_HANDLER_BIK_LENGTH=9
AEAPISETTINGS_HANDLER_MIN_AMOUNT=0.01
AEAPISETTINGS_HANDLER_MAX_AMOUNT=999999999999.99
AEAPISETTINGS_HANDLER_AMOUNT_TOLERANCE=0.2
AEAPISETTINGS_HANDLER_MAX_RESULTS=20
AEAPISETTINGS_HANDLER_MAX_STRING_LENGTH=500

# Настройки сервера
AEAPISETTINGS_UVICORN_HOST=0.0.0.0
AEAPISETTINGS_UVICORN_PORT=8000
AEAPISETTINGS_UVICORN_DEBUG=false
```

---

## 11. Лимиты и ограничения

### Ограничения запросов

| Параметр | Ограничение |
|----------|-------------|
| Максимальная длина запроса | 500 символов |
| Максимальное количество результатов поиска | 20 |
| Минимальная длина поискового запроса в истории | 2 символа |
| Максимальный период хранения истории | 90 дней (по умолчанию) |

### Валидация данных

| Поле | Правила валидации |
|------|-------------------|
| ИНН | 10 или 12 цифр |
| БИК | 9 цифр |
| Сумма | От 0.01 до 999,999,999,999.99 |
| Строковые поля | Максимум 500 символов |

---

*Документация обновлена: 21 сентября 2025*
*Версия API: 1.0.0*
