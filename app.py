import time
from flask import Flask, request, jsonify
from spellchecker import SpellChecker
from flask_cors import CORS

import models
from models.database import db
from sqlalchemy_utils.functions import database_exists, create_database
from SearchController import ManualIndexer
from models.folder import Folder
from models.folder import Bookmark
from UserController import UserController

app = Flask(__name__)
app.manual_indexer = ManualIndexer()
CORS(app, resources={r'/*': {'origins': '*'}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:045689123@127.0.0.1:3306/ir_pj'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if not database_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
    create_database(app.config["SQLALCHEMY_DATABASE_URI"])

db.init_app(app)

with app.app_context():
    db.create_all()

checker = SpellChecker(language='en')


@app.route('/search', methods=['GET'])
def search():
    start = time.time()
    response_object = {'status': 'success'}
    argList = request.args.to_dict(flat=False)
    query_term = argList['query'][0]
    corrected_query = app.manual_indexer.spell_corrct(query_term)
    results = app.manual_indexer.query(query_term)
    end = time.time()
    total_hit = len(results)
    results_df = results

    response_object['total_hit'] = total_hit
    response_object['results'] = results_df.to_dict('records')
    response_object['elapse'] = end - start
    response_object['corrected_query'] = corrected_query
    return response_object


@app.route('/login', methods=['POST'])
def user_login():
    return UserController.login()


@app.route('/folders', methods=['POST'])
def user_create_folder():
    return models.create_folder()


@app.route('/folders/<int:user_id>', methods=['GET'])
def get_folders_by_user(user_id):
    folders = Folder.query.filter_by(user_id=user_id)
    serialized_folders = [folder.serialize for folder in folders]
    return jsonify(serialized_folders), 200


@app.route('/add_bookmarks', methods=['POST'])
def add_bookmark():
    try:
        data = request.json
        recipe_data = data.get('recipe', {})
        print(recipe_data)
        folder_id = data.get('folder_id')
        user_review = data.get('user_review')
        print(folder_id)
        print(user_review)

        new_bookmark = Bookmark(
            name=recipe_data.get('name'),
            author_id=recipe_data.get('author_id'),
            author_name=recipe_data.get('author_name'),
            image=recipe_data.get('image'),
            recipe_category=recipe_data.get('recipe_category'),
            recipe_id=recipe_data.get('recipe_id'),
            recipe_ingredient=recipe_data.get('recipe_ingredient'),
            recipe_instruction=recipe_data.get('recipe_instruction'),
            review_count=recipe_data.get('review_count'),
            user_review=user_review,
            folder_id=folder_id
        )
        db.session.add(new_bookmark)
        db.session.commit()
        return jsonify({'message': 'Bookmark added successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'message': 'Failed to add bookmark', 'error': str(e)}), 500


@app.route('/folders/bookmark/<int:folder_id>', methods=['GET'])
def get_bookmark_by_folder(folder_id):
    bookmarks = Bookmark.query.filter_by(folder_id=folder_id)
    serialized_bookmarks = [bookmark.serialize for bookmark in bookmarks]
    return jsonify(serialized_bookmarks), 200


@app.route('/delete_folder/<int:folder_id>', methods=['POST'])
def delete_folder_with_bookmarks(folder_id):
    try:
        # Delete bookmarks associated with the specified folder ID
        Bookmark.query.filter_by(folder_id=folder_id).delete()

        # Delete the folder itself
        deleted_count = Folder.query.filter_by(id=folder_id).delete()

        db.session.commit()

        return jsonify({'message': f'{deleted_count} folder and associated bookmarks deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'message': 'Failed to delete folder and bookmarks', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
