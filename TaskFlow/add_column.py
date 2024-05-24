from sqlalchemy import create_engine, inspect, text

# Замените путь к базе данных на ваш путь
DATABASE_URL = 'sqlite:///instance/kanban.db'

# Создаем подключение к базе данных
engine = create_engine(DATABASE_URL)

def upgrade():
    # Подключаемся к базе данных
    with engine.connect() as connection:
        # Проверяем, существует ли столбец description
        inspector = inspect(engine)
        columns = [column['name'] for column in inspector.get_columns('task')]
        if 'label' in columns:
            # Добавляем столбец description в таблицу project
            connection.execute(text('ALTER TABLE task DROP COLUMN label'))
            print("Столбец 'description' успешно добавлен в таблицу 'project'.")
        else:
            print("Столбец 'description' уже существует в таблице 'project'.")

if __name__ == '__main__':
    upgrade()
