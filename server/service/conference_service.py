from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional,List

# Pydantic 数据模型类
class ConferenceData(BaseModel):
    conference_id: Optional[int] = Field(None, description="会议ID，自动递增")
    conference_name: str = Field(..., description="会议名称")
    host_id: int = Field(..., description="主持人ID，外键")
    password: Optional[str] = Field(None, description="会议密码")
    port: Optional[int] = Field(None, ge=9000, le=65535, description="会议端口")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="创建时间，默认为当前时间")

    @validator("conference_name")
    def validate_conference_name(cls, value):
        if len(value.strip()) == 0:
            raise ValueError("会议名称不能为空或只包含空格")
        return value

    @validator("password")
    def validate_password(cls, value):
        if value is not None and len(value) < 6:
            raise ValueError("会议密码长度不能少于6个字符")
        return value

    @validator("port")
    def validate_port(cls, value):
        if value is not None and (value < 9000 or value > 65535):
            raise ValueError("端口号必须在9000到65535之间")
        return value

    class Config:
        orm_mode = True  # 启用 ORM 模式以支持从数据库模型映射

class MeetingActionPayload(BaseModel):
    action: str = Field(..., description="操作类型")
    data: List[ConferenceData] = Field(..., description="会议数据列表")


class ConferenceService:
    def __init__(self, db_session):
        self.db_session = db_session

    def create_conference(self, conference_data: ConferenceData):
        """创建新的会议记录"""
        new_conference = conference_data.dict(exclude_unset=True)
        self.db_session.add(new_conference)
        self.db_session.commit()
        return new_conference

    def delete_conference(self, conference_id: int):
        """删除会议记录"""
        # 示例: conference = self.db_session.query(ConferenceModel).filter_by(conference_id=conference_id).first()
        conference = {}  # 模拟数据库查询
        if not conference:
            raise ValueError("会议未找到")
        self.db_session.delete(conference)
        self.db_session.commit()
        return {"status": "deleted"}
