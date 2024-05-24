from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# Конфигурация базы данных
DATABASE_URI = 'sqlite:///instance/kanban.db'  # Замените на ваш URI базы данных в папке instance

# Создание движка и сессии
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Загрузка метаданных
metadata = MetaData()
metadata.reflect(bind=engine)

# Проверка доступных таблиц
print("Available tables:", metadata.tables.keys())

# Получение таблицы task
task_table = metadata.tables.get('project')
if task_table is None:
    print("Table 'team' not found in the database.")
else:
    # Удаление всех записей из таблицы task
    with engine.connect() as connection:
        try:
            delete_stmt = task_table.delete()
            result = connection.execute(delete_stmt)
            print(f'Deleted {result.rowcount} rows from task table.')

            # Явное подтверждение транзакции
            connection.commit()
        except Exception as e:
            print(f'Error occurred: {e}')
            connection.rollback()
        finally:
            connection.close()

# Закрытие сессии
session.close()
