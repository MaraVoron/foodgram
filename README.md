# Документация API
http://foodgramfinal0.hopto.org/api/docs/

# Foodgram

Сервис для публикации рецептов.

## Стек
- Python, Django, DRF, Djoser
- PostgreSQL
- Docker, docker-compose
- Nginx
- GitHub Actions (CI/CD)

## Адрес
http://foodgramfinal0.hopto.org/
http://81.26.176.231/

## Админка
http://81.26.176.231/admin/

## Данные для проверки
- Email: review@admin.ru
- Пароль: review1admin

## Автор
Горина Мария
GitHub: https://github.com/MaraVoron

## Развёртывание в Docker

### Требования
- Docker
- docker-compose

### Установка

#### Клонируйте репозиторий
git clone https://github.com/mararaven/foodgram.git
cd foodgram

#### Создайте .env файл в корне проекта
cat > .env << 'EOF'
SECRET_KEY=ваш_секретный_ключ
DEBUG=False
ALLOWED_HOSTS=ваш_домен,ваш_ip,localhost,127.0.0.1,backend
DB_ENGINE=postgresql
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=ваш_пароль
DB_HOST=db
DB_PORT=5432
EOF

#### Запустите контейнеры
sudo docker compose -f docker-compose.production.yml up -d --build

#### Примените миграции
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate

#### Загрузите ингредиенты и теги
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_data

#### Соберите статику
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput

#### Создайте суперпользователя
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser

## Пример запросов/ответов
### Регистрация
#### Запрос
POST /api/users/
{
    "email": "user@example.com",
    "username": "username",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "password": "пароль"
}

#### Ответ:
Ответ (201 Created):
{
    "email": "user@example.com",
    "id": 5,
    "username": "username",
    "first_name": "Имя",
    "last_name": "Фамилия"
}

### Получение токена
#### Запрос
POST /api/auth/token/login/
{
    "email": "<ваша почта>",
    "password": "<ваш пароль>"
}

#### Ответ:
Ответ (200 OK):
{
    "auth_token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4"
}