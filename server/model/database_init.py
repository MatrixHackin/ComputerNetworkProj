import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class ManageDB:
    # 从环境变量中获取数据库密码
    DATABASE_USER = "postgres"
    DATABASE_PASSWORD = "123456"  # 20040502
    DATABASE_HOST = "localhost"
    DATABASE_NAME = "computer_network_proj"

    # 拼接数据库连接 URL
    # DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}"
    DATABASE_URL = f"postgresql://postgres:123456@localhost:5432/computer_network_proj"
    def __init__(self):
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_session(self):
        return self.SessionLocal()
