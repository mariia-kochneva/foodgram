# Foodgram

Проект "Foodgram" — сайт, на котором пользователи публикуют рецепты, добавляют чужие рецепты в избранное и подписываются на публикации других авторов. Доступен сервис «Список покупок» для создания перечня продуктов.

## Ссылка на развернутый проект

[Foodgram](http://foodgrami.ddns.net)

**Важно:** ВМ отключается через 4 часа. Если сайт недоступен, необходима перезагрузка ВМ. (p.s. как правильно это организовать, не знаю)

## Автор

Мария Кочнева

## Технологии

- Python 3.12
- Django 5.1.1
- Django REST Framework
- Djoser
- PostgreSQL 13
- React
- Docker / Docker Compose
- Nginx
- GitHub Actions (CI/CD)

## Особенности

- Регистрация и аутентификация пользователей по email
- Публикация рецептов с изображениями (Base64)
- Добавление рецептов в избранное
- Подписка на авторов
- Список покупок с суммированием ингредиентов
- Скачивание списка покупок в PDF
- Фильтрация рецептов по тегам
- Короткие ссылки на рецепты

## Развертывание

### Локальный запуск (разработка)

1. Клонировать репозиторий:
   ```bash
   git clone git@github.com:mariia-kochneva/foodgram.git
   cd foodgram
   ```

2. Создать файл `.env` на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```
   
   Заполните переменные окружения:
   - `SECRET_KEY` — секретный ключ Django
   - `DEBUG` — режим отладки (True/False)
   - `ALLOWED_HOSTS` — разрешённые хосты
   - `POSTGRES_DB` — имя базы данных
   - `POSTGRES_USER` — пользователь PostgreSQL
   - `POSTGRES_PASSWORD` — пароль PostgreSQL
   - `DB_HOST` — хост базы данных
   - `DB_PORT` — порт базы данных

3. Запустить контейнеры:
   ```bash
   cd infra
   docker compose up -d
   ```

4. Применить миграции и собрать статику:
   ```bash
   docker compose exec backend python manage.py migrate
   docker compose exec backend python manage.py collectstatic --noinput
   docker compose exec backend python manage.py load_ingredients
   ```

5. Создать суперпользователя:
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

6. Проект будет доступен по адресу: `http://localhost`

### Удаленный запуск (продакшен)

Для развертывания на сервере используется `docker-compose.production.yml`.

#### Подготовка сервера

1. Установите Docker и Docker Compose.
2. Создайте директорию `~/foodgram`.
3. Настройте DNS-запись для домена (например, `foodgrami.ddns.net`).
4. Получите SSL-сертификат Let's Encrypt (опционально).

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
- Запускает проверку стиля кода (flake8)
- Собирает и загружает образы на Docker Hub:
  - `username/foodgram_backend:latest`
  - `username/foodgram_frontend:latest`
  - `username/foodgram_gateway:latest`
- Подключается к серверу по SSH
- Обновляет контейнеры через `docker-compose.production.yml`
- Выполняет миграции, собирает статику, загружает ингредиенты
- Отправляет уведомление в Telegram

### Отличия версий

| Файл | Назначение |
|------|------------|
| `infra/docker-compose.yml` | Для локальной разработки. Использует `build` для сборки образов из исходного кода. |
| `docker-compose.production.yml` | Для продакшена. Использует готовые образы с Docker Hub, что ускоряет развертывание на сервере. |

## API

Документация API доступна по адресу `/api/docs/` после запуска проекта.

## Проверка CI/CD

Статус последнего workflow: [![CI/CD](https://github.com/mariia-kochneva/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/mariia-kochneva/foodgram/actions/workflows/main.yml)

Успешный деплой подтверждается зелёным бейджем и сообщением в Telegram.
