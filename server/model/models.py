from sqlalchemy import Column, Integer, String, ForeignKey, Text, SmallInteger, TIMESTAMP, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

# 用户表
class DBUsers(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    hosted_conferences = relationship("DBConferences", back_populates="host")
    participating_conferences = relationship("DBUserConferenceRelation", back_populates="user")

    def __repr__(self):
        return f"<User(user_id={self.user_id or 'N/A'}, username='{self.username or 'N/A'}')>"

# 会议表
class DBConferences(Base):
    __tablename__ = 'conferences'

    conference_id = Column(Integer, primary_key=True, autoincrement=True)
    conference_name = Column(String(200), nullable=False)
    host_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    password = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime)

    host = relationship("DBUsers", back_populates="hosted_conferences")
    participants = relationship("DBUserConferenceRelation", back_populates="conference")

    def __repr__(self):
        return f"<Conference(conference_id={self.conference_id or 'N/A'}, conference_name='{self.conference_name or 'N/A'}', host_id={self.host_id or 'N/A'})>"


# 用户会议关联表（多对多关系表）
class DBUserConferenceRelation(Base):
    __tablename__ = 'user_conference_relations'

    conference_id = Column(Integer, ForeignKey('conferences.conference_id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)

    conference = relationship("DBConferences", back_populates="participants")
    user = relationship("DBUsers", back_populates="participating_conferences")

    def __repr__(self):
        return f"<UserConferenceRelation(conference_id={self.conference_id}, user_id={self.user_id})>"
