from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


class manage_db:
    DATABASE_URL = "postgresql://postgres:Cookiegu12210255@localhost/computer_network_proj"

    def __init__(self):
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
