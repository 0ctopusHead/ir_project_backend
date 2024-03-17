import bcrypt
from sqlalchemy import event
from flask import request, jsonify
from .user import User
from .folder import Folder
from .database import db


@event.listens_for(User.__table__, 'after_create')
def create_user(*args, **kwargs):
    db.session.add(
        User(username='user1', password=bcrypt.hashpw('12345'.encode('utf-8'), bcrypt.gensalt(10)), email='user1@gmai.com'))
    db.session.commit()


@event.listens_for(Folder.__table__, 'after_create')
def create_folder():
    data = request.json
    new_folder = Folder(user_id=data['user_id'], name=data['name'])
    db.session.add(new_folder)
    db.session.commit()
    return jsonify({'message': 'Folder created successfully'}), 201
