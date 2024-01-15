import json

import gevent.monkey
gevent.monkey.patch_socket()

import bottle
from bottle import response
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError

import logging
import MessageBroker
import os


log = logging.getLogger(__name__)

# the decorator for cors, allow POST from another computer - not working TODO
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        return fn(*args, **kwargs)

    return _enable_cors



bottle_app =bottle.Bottle()

broker = MessageBroker.MessageBroker()

def server():
    def get_websocket_from_request():
        env = bottle.request.environ
        wsock = env.get('wsgi.websocket')
        return wsock

    @bottle_app.route('/')
    def index():
        log.debug('Redirect to index page')
        root = os.path.join(os.path.dirname(__file__), 'UI/build')
        return bottle.static_file('index.html', root=root)

    # Open a persistent websocket to UI
    @bottle_app.route('/status')
    def handle_status():
        wsock = get_websocket_from_request()
        if not wsock:
            return 'Expecting a websocket request.'
        broker.add_observer(wsock)
        log.info("websocket (status) opened")
        while True:
            try:
                wsock.receive()
            except WebSocketError:
                break
        log.info("websocket (status) closed")

    @bottle_app.post('/start_stop')
    def handle_firing_start_stop():
        broker.start_stop_firing()

    @bottle_app.post('/manual_auto')
    def handle_manual_auto():
        broker.auto_manual()

    @bottle_app.post('/change_power')
    def handle_manual_auto():
        message = bottle.request.body.read()
        message = json.loads(message)

        broker.set_heat_for_zone(int(message['power']), message['zone'])

    @bottle_app.post('/profile')
    def handle_profile():
        message = bottle.request.body.read()
        message = json.loads(message)

        broker.set_profile((message['profile_name']))

    @bottle_app.error(404)
    def error404(error):
        return 'You have fallen completely off the edge of the internet. Sorry.  ' + str(error)

    ### Static Routes, so front end can find the files
    base_path = os.path.abspath(os.path.dirname(__file__))
    build_path = os.path.join(base_path, 'UI', 'build')

    @bottle_app.get("/static/css/<filepath:re:.*\.css>")
    def css(filepath):
        return bottle.static_file(filepath, root=os.path.join(build_path, "static/css"))

    @bottle_app.get("/static/font/<filepath:re:.*\.(eot|otf|svg|ttf|woff|woff2?)>")
    def font(filepath):
        return bottle.static_file(filepath, root=os.path.join(build_path, "static/font"))

    @bottle_app.get("/<filepath:re:.*\.(jpg|png|gif|ico|svg)>")
    def img(filepath):
        return bottle.static_file(filepath, root=os.path.join(build_path))

    @bottle_app.get("/static/js/<filepath:re:.*\.js>")
    def js(filepath):
        return bottle.static_file(filepath, root=os.path.join(build_path, "static/js"))
    ### Static route

    ip = "0.0.0.0"
    port = 8081
    log.info("listening on %s:%d" % (ip, port))

    the_server = WSGIServer((ip, port), bottle_app,
                    handler_class=WebSocketHandler)
    the_server.serve_forever()


if __name__ == '__main__':
    server()