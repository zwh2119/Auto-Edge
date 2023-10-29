import time

import flask

app = flask.Flask(__name__)


@app.route('/test/<num>', methods=['GET'])
def route_test(num):
    time.sleep(3)
    return flask.jsonify(num)


app.run(host='0.0.0.0', port=8888)
