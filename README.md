# Anti-Fraud System

> **REST API для обнаружения мошеннических транзакций**  
> Backend-сервис, который принимает финансовые операции, проверяет их по набору правил и решает — одобрить или отклонить как подозрительные.

---

## 📋 Описание проекта
Backend‑сервис, который **принимает финансовые транзакции и автоматически проверяет, мошеннические они или нормальные**.

- Пользователь отправляет данные операции.  
- Система проверяет её по набору заранее заданных правил (например, «слишком большая сумма» или «подозрительный канал платежа»).  
- В ответ она выдаёт статус `APPROVED` (операция ок) или `DECLINED` (подозрительно, лучше отклонить).

Проект показывает, как строить реальный антифрод‑движок на FastAPI:  
- регистрация и логин пользователей,  
- админ‑панель и статистика,  
- обработка операций по‑одному и пачками,  
- хранение и применение правил мошенничества.

---

## 🛠 Стек технологий

| Категория | Технология |
|---|---|
| **Язык** | Python 3.12 |
| **Фреймворк** | FastAPI 0.120.2 |
| **ORM** | SQLAlchemy 2.0 (async) |
| **База данных** | PostgreSQL 16 (asyncpg) |
| **Кэш** | Redis 7 |
| **Миграции** | Alembic 1.17.2 |
| **Контейнеризация** | Docker + docker-compose |
| **Тесты** | pytest + внешний antifraud-checker |
| **Линтеры** | black, flake8, mypy |
| **ASGI-сервер** | Uvicorn 0.38.0 |

---

## ⚡ Функциональность

Что умеет делать проект:

- ✅ **Регистрация и авторизация** — JWT-токены, хэширование паролей (bcrypt)
- ✅ **Управление пользователями** — админ может просматривать, блокировать и разблокировать пользователей
- ✅ **Создание транзакций** — одиночные и batch-запросы (multi-status 207)
- ✅ **Фрауд-правила (DSL-движок)** — создание и валидация правил вида `amount > 1000`, `channel == MOBILE`, которые автоматически оценивают каждую транзакцию
- ✅ **Статистика (Admin only)** — overview, временные ряды, риск-профили мерчантов и пользователей
- ✅ **Валидация запросов** — кастомный обработчик ошибок с понятными сообщениями
- ✅ **Swagger/OpenAPI** — интерактивная документация на `/docs`
- ✅ **Health-check** — эндпоинт `/api/v1/ping`

---

## 🏗 Архитектура

| Компонент | Роль |
|---|---|
| **FastAPI** (порт 8080) | Основной REST API, запущен через **Uvicorn** |
| **Postgres 16** | Хранение пользователей, транзакций, фрауд-правил |
| **Redis 7** | Кэширование ответов (готов к включению) |
| **antifraud-checker** | Внешний тестировщик, который автоматически проверяет решение |

### Как это работает

```
Пользователь регистрируется → Создаёт транзакцию → 
Система проверяет по fraud-правилам → APPROVED / DECLINED
```

**Пример правила:** если сумма транзакции > 100 000 ₽ — пометить как подозрительную. Или если транзакция совершена из необычной геолокации.

---

## 📁 Структура проекта

```
solution/app/
├── main.py                 # Точка входа FastAPI, routers, exception handlers
├── config.py               # Настройки из переменных окружения
├── database.py             # SQLAlchemy async engine и сессия
├── dependencies.py         # JWT-декораторы, get_current_user/admin
├── exceptions.py           # Кастомные HTTPException
├── users/                  # Регистрация, логин, аутентификация
├── user_management/        # Админские CRUD-эндпоинты
├── transactions/           # CRUD транзакций + fraud evaluation pipeline
├── fraudrules/             # CRUD правил + DSL rule engine
├── statistics/             # Аналитика (overview, timeseries, risk profiles)
├── dao/                    # Базовый DAO паттерн (CRUD)
├── enums/                  # Доменные перечисления
├── utils/                  # Утилиты (admin, auth, DSL validator)
└── migrations/             # Alembic миграций
```

### API Endpoints

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Регистрация |
| `POST` | `/api/v1/auth/login` | Логин |
| `GET` | `/api/v1/users` | Список пользователей (Admin) |
| `PATCH` | `/api/v1/users/{id}` | Обновить пользователя |
| `PATCH` | `/api/v1/users/{id}/block` | Заблокировать |
| `PATCH` | `/api/v1/users/{id}/unblock` | Разблокировать |
| `POST` | `/api/v1/fraud-rules` | Создать фрауд-правило |
| `GET` | `/api/v1/fraud-rules` | Список правил |
| `POST` | `/api/v1/fraud-rules/validate` | Валидировать DSL |
| `POST` | `/api/v1/transactions` | Создать транзакцию |
| `GET` | `/api/v1/transactions/{id}` | Получить транзакцию |
| `POST` | `/api/v1/transactions/batch` | Batch-создание (207) |
| `GET` | `/api/v1/stats/overview` | Обзор статистики (Admin) |
| `GET` | `/api/v1/stats/transactions/timeseries` | Временные ряды (Admin) |
| `GET` | `/api/v1/ping` | Health-check |

---

## 🚀 Как запустить локально

### Через Docker (рекомендуется)

```bash
git clone https://github.com/ArtemBibikov/antiford-system.git
cd antiford-system
docker compose up -d
```

API откроется на **http://localhost:8080**  
Swagger-документация — **http://localhost:8080/docs**

### Локальная разработка (без Docker)

1. Убедитесь, что установлены **Postgres** и **Redis**
2. Установите зависимости:

```bash
pip install -r solution/requirements.txt
```

3. Запустите приложение через **Uvicorn**:

```bash
uvicorn solution.app.main:app --host 0.0.0.0 --port 8080 --reload
```

4. Переменные окружения (если нужны отличные от дефолтных):

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=testdb
export DB_USER=postgres
export DB_PASSWORD=postgres
export REDIS_HOST=localhost
export REDIS_PORT=6379
export SERVER_PORT=8080
```

---

## 👤 Default-админ

При первом запуске автоматически создаётся администратор:

| Поле | Значение |
|---|---|
| **Email** | `admin@mail.ru` |
| **Пароль** | `123123123aA!` |
---

## 🧪 Тестирование

Проект проверяется внешним **antifraud-checker**, который запускается через docker-compose и генерирует отчёт в `./reports/junit.xml`.

```bash
docker compose up -d
# Checker запустится автоматически и проверит все эндпоинты
```

---

## 📝 CI/CD

Проект настроен для **GitLab CI/CD** (`.gitlab-ci.yml`):

1. **build** — сборка Docker-образа через Kaniko
2. **test** — запуск docker-compose с checker'ом
3. **export** — отправка результатов в judging API

---

## 📄 Лицензия

Учебный проект, созданный для участия в **PROD 2026 Backend Olympiad**.
