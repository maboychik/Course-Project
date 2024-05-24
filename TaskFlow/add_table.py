from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'YourSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'  # Замените на ваш URI базы данных
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# SQL-запрос для создания таблицы PerformanceLevel
create_table_query = """
CREATE TABLE IF NOT EXISTS PerformanceLevel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES user (id),
    FOREIGN KEY (task_id) REFERENCES task (id)
);
"""

with app.app_context():
    # Получение соединения с базой данных
    with db.engine.connect() as connection:
        # Выполнение SQL-запроса для создания таблицы
        connection.execute(text(create_table_query))
    print("Таблица PerformanceLevel была успешно добавлена в базу данных.")
