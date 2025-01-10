import asyncio
import datetime
import uvicorn
from fastapi import HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from server.model.database_init import ManageDB
from sqlalchemy.orm import Session
from sqlalchemy import delete
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
        self.connected_clients = set()

    async def websocket_connect(self,websocket:WebSocket):
        try:
            await websocket.accept()
            self.connected_clients.add(websocket)
            print('client connected')
        except Exception as e:
            print(e)
            raise
    
    async def websocket_disconnect(self,websocket:WebSocket):
        self.connected_clients.remove(websocket)
        print('client disconnected')

    async def broadcast(self, message: str):
        print('broadcasting')
        for client in self.connected_clients.copy():
            try:
                await client.send_text(message)
            except:
                self.connected_clients.remove(client)
                print('client disconnected')

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
        self.confereces[conference_id]['participants'] += 1
        relation=DBUserConferenceRelation(user_id=user_id,conference_id=conference_id)
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return conference_id
            
    # def get_can_join_conference_list(self,user_id):
    #     db_conferences=self.db.query(DBConferences).filter(DBConferences.host_id!=user_id).all()
    #     return db_conferences
    
    # def get_joined_conferencelist(self,user_id):
    #     db_conferences=self.db.query(DBConferences).filter(DBConferences.host_id==user_id).all()
    #     return db_conferences

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

    def quit_meeting(self, user_id, conference_id):
        #TODO: 把联表中关系删掉
        db_relation=self.db.query(DBUserConferenceRelation).filter(DBUserConferenceRelation.user_id==user_id).filter(DBUserConferenceRelation.conference_id==conference_id).first()
        self.db.delete(db_relation)
        self.db.commit()
        conf_server = self.confereces[conference_id]['server']
        conf_server.disconnect(str(user_id))
        self.confereces[conference_id]['participants'] -= 1
        if self.confereces[conference_id]['participants'] == 0:
            del self.confereces[conference_id]
        return

    def check_auth(self, user_id, conference_id):
        host_ids = self.db.query(DBConferences.host_id).filter(DBConferences.conference_id == conference_id).all()
        print(f'主持人: {host_ids}')
        for host_id_tuple in host_ids:
            host_id = host_id_tuple[0]  # 提取元组中的第一个元素（host_id）
            if user_id == host_id:
                return True
        return False

    def cancel_meeting(self, conference_id):
        stmt = delete(DBUserConferenceRelation).where(DBUserConferenceRelation.conference_id == conference_id)
        self.db.execute(stmt)
        self.db.commit()
        conference=self.db.query(DBConferences).filter(DBConferences.conference_id==conference_id).first()
        self.db.delete(conference)
        self.db.commit()
        conf_server = self.confereces[conference_id]['server']
        conf_server.close()
        del self.confereces[conference_id]
