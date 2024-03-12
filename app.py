import time
from flask import Flask, request
from SearchController import ManualIndexer
from utils import preProcess

app = Flask(__name__)
app.manual_indexer = ManualIndexer()


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
