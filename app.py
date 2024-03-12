import time
from flask import Flask, request
from flask_cors import CORS
from models.database import db
from sqlalchemy_utils.functions import database_exists, create_database
from SearchController import ManualIndexer

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


@app.route('/search', methods=['GET'])
def search():
    start = time.time()
    response_object = {'status': 'success'}
    argList = request.args.to_dict(flat=False)
    query_term = argList['query'][0]

    results = app.manual_indexer.query(query_term)
    end = time.time()
    total_hit = len(results)
    results_df = results

    response_object['total_hit'] = total_hit
    response_object['results'] = results_df.to_dict('records')
    response_object['elapse'] = end-start
    return response_object


if __name__ == '__main__':
    app.run(debug=True)
    