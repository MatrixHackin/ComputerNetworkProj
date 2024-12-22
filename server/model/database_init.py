import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class ManageDB:
    # 从环境变量中获取数据库密码
    DATABASE_USER = "postgres"
    DATABASE_PASSWORD = "20040502"
    DATABASE_HOST = "localhost"
    DATABASE_NAME = "network"

    # 拼接数据库连接 URL
    DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}"

    def __init__(self):
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
