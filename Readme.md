# Проект "Онлайн-колледж"

Платформа для онлайн-обучения с курсами и пользователями.

## Технологии

### Frontend
- Vue.js 3
- TypeScript
- Vuex
- Vue Router
- SCSS

### Backend
- FastAPI
- SQLAlchemy
- SQLite

## Структура проекта

```
├── frontend/               # Vue.js frontend
└── backend/                # FastAPI backend
    ├── CourseImg/          # Директория для изображений курсов
    ├── db/                 # Директория с базой данных
    ├── models/             # Модели SQLAlchemy
    ├── routers/            # API маршруты
    ├── schemas/            # Схемы Pydantic
    ├── services/           # Бизнес-логика
    ├── config.py           # Конфигурация приложения
    ├── database.py         # Настройки базы данных
    ├── main.py             # Основной файл приложения
    └── requirements.txt    # Зависимости Python
```

## Установка и запуск

### Backend (FastAPI)

1. Создайте виртуальное окружение Python:
```
python -m venv venv
```

2. Активируйте виртуальное окружение:
```
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Установите зависимости:
```
pip install -r requirements.txt
```

4. Запустите сервер:
```
uvicorn main:app --reload --port 8000
```

5. Откройте Swagger документацию:
```
http://localhost:8000/docs
```

### Frontend (Vue.js)

1. Установите зависимости:
```
npm install
```

2. Запустите сервер разработки:
```
npm run serve
```

3. Сборка для production:
```
npm run build
```

## API endpoints

### Курсы

- `GET /api/courses` - получить список всех курсов
- `GET /api/courses/{course_id}` - получить информацию о конкретном курсе
- `POST /api/courses` - создать новый курс
- `PUT /api/courses/{course_id}` - обновить существующий курс
- `DELETE /api/courses/{course_id}` - удалить курс
- `POST /api/courses/{course_id}/upload-image` - загрузить изображение для курса
- `POST /api/courses/{course_id}/upload-with-data` - загрузить изображение вместе с данными о курсе

## Структура базы данных

### Таблица courses
- id (Integer, PK)
- title (String)
- subtitle (String)
- type (String)
- timetoendL (String)
- color (String)
- icon (String)
- icontype (String)
- titleForCourse (String)

### Таблица course_info
- id (Integer, PK)
- title (String)
- subtitle (Text)
- course_id (Integer, FK)

### Таблица sections
- id (Integer, PK)
- name (String)
- course_id (Integer, FK)

### Таблица lessons
- id (Integer, PK)
- name (String)
- passing (String)
- description (Text)

### Таблица lesson_sections
- section_id (Integer, FK, PK)
- lesson_id (Integer, FK, PK)