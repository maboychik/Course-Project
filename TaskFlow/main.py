from sqlalchemy import create_engine, Table, MetaData, Column, Integer
from sqlalchemy.sql import select, update

# Подключение к базе данных
engine = create_engine('sqlite:///kanban.db')  # Обновите путь к базе данных, если это необходимо
metadata = MetaData()

# Отражение существующей схемы базы данных
metadata.reflect(bind=engine)

# Доступ к таблице 'role'
role_table = metadata.tables['role']

# Добавление нового столбца 'level', если он еще не существует
if 'level' not in role_table.c:
    new_column = Column('level', Integer, nullable=False)
    new_column.create(role_table)
    print("Column 'level' added successfully.")
else:
    print("Column 'level' already exists.")

# Обновление существующих данных
connection = engine.connect()
roles_to_update = {
    'Executive': 3,
    'Manager': 2,
    'Employee': 1
}

for role_name, level in roles_to_update.items():
    stmt = update(role_table).where(role_table.c.name == role_name).values(level=level)
    connection.execute(stmt)

print("Roles updated successfully.")
connection.close()
