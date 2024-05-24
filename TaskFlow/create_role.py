from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    level = Column(Integer, nullable=False)



database_path = os.path.join(os.getcwd(), 'instance', 'kanban.db')
engine = create_engine(f'sqlite:///{database_path}')
Session = sessionmaker(bind=engine)
session = Session()

roles = [
    Role(name='Executive', level=4),
    Role(name='Manager', level=3),
    Role(name='TeamLead', level=2),
    Role(name='Employee', level=1)
]

for role in roles:
    existing_role = session.query(Role).filter_by(name=role.name).first()
    if not existing_role:
        session.add(role)

session.commit()
print("Roles have been added to the database.")

# Закрыть сессию
session.close()

