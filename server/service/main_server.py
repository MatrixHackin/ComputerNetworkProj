import asyncio
import datetime
import uvicorn
from fastapi import HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from server.model.database_init import ManageDB
from sqlalchemy.orm import Session
from server.model.models import DBConferences, DBUserConferenceRelation
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional,List,Dict
from server.service.user_service import UserService
from server.service.conf_server import ConferenceServer
from websocket import WebSocket


"""
this file defines main_server service, return transfer_data
"""
    
    
class MainServer:
    def __init__(self):
        self.main_server = None
        self.confereces = dict()
        db_manager=ManageDB()
        self.db=db_manager.create_session()

    def create_meeting(self, conference_name, conference_password, conference_hostid):
        # 创建会议
        time=datetime.now()
        new_conference = DBConferences(conference_name=conference_name,password=conference_password,host_id=conference_hostid,created_at=time)
        self.db.add(new_conference)
        self.db.commit()
        self.db.refresh(new_conference)
        server=ConferenceServer(new_conference.conference_id)
        self.confereces[new_conference.conference_id] = {
            'name':new_conference.conference_name,
            'created_at':new_conference.created_at,
            'participants':0,
            'server':server
        }

    def join_meeting(self, user_id, conference_name, conference_password):
        # 加入会议
        db_conference=self.db.query(DBConferences).filter(DBConferences.conference_name==conference_name).first()
        if db_conference is None:
            raise HTTPException(status_code=404, detail="Conference not found")
        if db_conference.password!=conference_password:
            raise HTTPException(status_code=403, detail="Password incorrect")
        conference_id=db_conference.conference_id
        user_id=user_id
        return conference_id
            
    def get_conference_list(self):
        db_conferences=self.db.query(DBConferences).all()
        return db_conferences
    
    def get_selfcreated_conferencelist(self,user_id):
        db_conferences=self.db.query(DBConferences).filter(DBConferences.host_id==user_id).all()
        return db_conferences

    def get_canjoin_conferencelist(self, user_id):
        db_conference_ids = self.db.query(DBUserConferenceRelation.conference_id).filter(DBUserConferenceRelation.user_id == user_id).all()
        conference_ids = [item[0] for item in db_conference_ids]
        db_conference = self.db.query(DBConferences).filter(DBConferences.conference_id.notin_(conference_ids)).all()
        return db_conference

    def get_joined_conferencelist(self, user_id):
        db_conference_ids = self.db.query(DBUserConferenceRelation.conference_id).filter(
            DBUserConferenceRelation.user_id == user_id).all()
        conference_ids = [item[0] for item in db_conference_ids]
        db_conference = self.db.query(DBConferences).filter(DBConferences.conference_id.in_(conference_ids)).all()
        return db_conference

    


