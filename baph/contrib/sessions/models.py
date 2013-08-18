from sqlalchemy import *

from baph.db.orm import ORM


orm = ORM.get()
Base = orm.Base

class Session(Base):
    __tablename__ = 'baph_session'
    session_key = Column(String(40), primary_key=True)
    session_data = Column(Text)
    expire_date = Column(DateTime, index=True)
    
    def get_decoded(self):
        return SessionStore().decode(self.session_data)
        
from baph.contrib.sessions.backends.db import SessionStore
