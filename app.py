import time
from flask import Flask, request, jsonify
from spellchecker import SpellChecker
from flask_cors import CORS
from sqlalchemy import desc, func
import models
from models.database import db
from sqlalchemy_utils.functions import database_exists, create_database
from SearchController import ManualIndexer
from models.folder import Folder
from models.folder import Bookmark
from UserController import UserController
import pickle
from pathlib import Path
import os
from RecommendController import RecommendController
import pandas as pd


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

stored_folder = Path(os.path.abspath('')) / "data" / "processed" / "cleaned_df.pkl"
recipe = pickle.load(open(stored_folder, 'rb'))


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
    folders = (
        Folder.query
        .filter_by(user_id=user_id)
        .outerjoin(Bookmark)  # Use outer join instead of inner join
        .group_by(Folder.id)
        .order_by(func.avg(Bookmark.user_review).desc() if Bookmark else None)  # Order by average user_review descending if there are bookmarks
    )
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
        user_id = data.get('user_id')
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
            folder_id=folder_id,
            user_id=user_id
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
    bookmarks = Bookmark.query.filter_by(folder_id=folder_id).order_by(desc(Bookmark.user_review))
    serialized_bookmarks = [bookmark.serialize for bookmark in bookmarks]
    return jsonify(serialized_bookmarks), 200


@app.route('/delete_folder/<int:folder_id>', methods=['POST'])
def delete_folder(folder_id):
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


@app.route('/delete_bookmark/<int:bookmark_id>', methods=['POST'])
def delete_bookmark(bookmark_id):
    try:
        bookmark = Bookmark.query.filter_by(id=bookmark_id).first()
        if bookmark:
            db.session.delete(bookmark)
            db.session.commit()
            return jsonify({'message': 'Bookmark deleted successfully'}), 200
        else:
            return jsonify({'message': 'Bookmark not found'}), 404
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'message': 'Failed to delete bookmark', 'error': str(e)}), 500


@app.route('/recommend/<int:user_id>', methods=['GET'])
def get_recommend(user_id):
    user_df = Bookmark.query.filter_by(user_id=user_id).all()
    user_df = pd.DataFrame({
        'user_id': [bookmark.user_id for bookmark in user_df],
        'recipe_id': [bookmark.recipe_id for bookmark in user_df],
        'rating': [bookmark.user_review for bookmark in user_df],
        'author_id': [bookmark.author_id for bookmark in user_df]
    })
    if user_df.empty:
        return jsonify({'error': 'User not found'}), 404

    user_df = RecommendController.make_user_feature(user_df)
    top_recommendations = RecommendController.predict(user_df, 10)

    # Check for NaN values in the DataFrame
    if top_recommendations.isnull().values.any():
        return jsonify(), 200

    # Convert top recommendations DataFrame to a list of dictionaries
    recommendations_list = top_recommendations.to_dict(orient='records')

    # Construct the response object
    response_object = {
        'recommendations': recommendations_list
    }

    return jsonify(recommendations_list), 200


if __name__ == '__main__':
    app.run(debug=True)
