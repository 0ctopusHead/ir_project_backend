import bcrypt
from sqlalchemy import event
from .user import User
from .database import db


@event.listens_for(User.__table__, 'after_create')
def create_user(*args, **kwargs):
    db.session.add(
        User(username='user1', password=bcrypt.hashpw('12345'.encode('utf-8'), bcrypt.gensalt(10)), email='user1@gmai.com'))
    db.session.commit()