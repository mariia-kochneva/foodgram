```markdown
# Kittygram

[![CI/CD](https://github.com/mariia-kochneva/kittygram_final/actions/workflows/main.yml/badge.svg)](https://github.com/mariia-kochneva/kittygram_final/actions/workflows/main.yml)

Проект "Kittygram" — социальная сеть для публикации фотографий котов.

## Ссылка на развернутый проект

[Kittygram](https://kittygrami.ru)

## Автор

Мария Кочнева

## Технологии

- Python 3.12
- Django 5.1.1
- Django REST Framework
- PostgreSQL 13
- React
- Docker / Docker Compose
- Nginx
- GitHub Actions (CI/CD)

## Особенности

- Регистрация и аутентификация пользователей
- Публикация фотографий котов
- Комментирование
- Оценка (лайки/дизлайки)
- Пагинация

## Развертывание

### Локальный запуск (разработка)

1. Клонировать репозиторий:
   ```bash
   git clone git@github.com:mariia-kochneva/kittygram_final.git
   cd kittygram_final
   ```

2. Создать файл `.env` на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Заполните переменные окружения:
   - `SECRET_KEY` — секретный ключ Django
   - `DEBUG` — режим отладки (True/False)
   - `ALLOWED_HOSTS` — разрешённые хосты
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` — данные для PostgreSQL
   - `DB_HOST`, `DB_PORT` — хост и порт базы данных

3. Запустить контейнеры:
   ```bash
   docker-compose up -d
   ```

4. Применить миграции и собрать статику:
   ```bash
   docker-compose exec backend python manage.py migrate
   docker-compose exec backend python manage.py collectstatic --noinput
   ```

5. Проект будет доступен по адресу: `http://localhost:9000`

### Удаленный запуск (продакшен)

Для развертывания на сервере используется `docker-compose.production.yml`.

#### Подготовка сервера

1. Установите Docker и Docker Compose.
2. Создайте директорию `~/kittygram`.
3. Настройте Nginx на сервере:
   - Запросы к `kittygrami.ru` должны проксироваться на `http://127.0.0.1:9000`
   - Пример конфигурации:
   ```nginx
   server {
       server_name kittygrami.ru;
       location / {
           proxy_pass http://127.0.0.1:9000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

#### Настройка CI/CD (GitHub Actions)

В репозитории необходимо добавить секреты (Settings → Secrets and variables → Actions):

- `DOCKER_USERNAME` — логин Docker Hub
- `DOCKER_PASSWORD` — пароль или токен Docker Hub
- `HOST` — IP-адрес сервера
- `USER` — имя пользователя на сервере
- `SSH_KEY` — приватный SSH-ключ для подключения к серверу
- `TELEGRAM_TO` — ID чата Telegram
- `TELEGRAM_TOKEN` — токен Telegram бота

#### Автоматический деплой

При пуше в ветку `main` GitHub Actions автоматически:
- Запускает тесты (flake8, pytest, тесты фронтенда)
- Собирает и загружает образы на Docker Hub:
  - `username/kittygram_backend:latest`
  - `username/kittygram_frontend:latest`
  - `username/kittygram_gateway:latest`
- Подключается к серверу по SSH
- Обновляет контейнеры через `docker-compose.production.yml`
- Выполняет миграции и собирает статику
- Отправляет уведомление в Telegram

### Отличия версий

| Файл | Назначение |
|------|------------|
| `docker-compose.yml` | Для локальной разработки. Использует `build` для сборки образов из исходного кода. |
| `docker-compose.production.yml` | Для продакшена. Использует готовые образы с Docker Hub, что ускоряет развертывание на сервере. |

## Проверка CI/CD

Статус последнего workflow: [![CI/CD](https://github.com/mariia-kochneva/kittygram_final/actions/workflows/main.yml/badge.svg)](https://github.com/mariia-kochneva/kittygram_final/actions/workflows/main.yml)

Успешный деплой подтверждается зелёным бейджем и сообщением в Telegram.
```