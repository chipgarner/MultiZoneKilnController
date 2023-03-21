import bottle
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError
import logging
import MessageBroker
import os


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Server")

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
    # @bottle.route('/stats')
    # @bottle.route('/stats/<filename>')
    # def server_static(filename='index.html'):
    #     root = os.path.join(os.path.dirname(__file__), 'stats', 'UI/build')
    #     return bottle.static_file(filename, root=root)

    # Open a persistent websocket to UI
    # @bottle_app.route('/controller')
    # def controller():
    #     log.debug(str(bottle.request.environ))
    #     wsock = get_websocket_from_request()
    #     if not wsock:
    #         return 'Expecting a websocket request'
    #     message = wsock.receive()
    #     broker.update(message)
    #     log.debug(message)

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
                message = wsock.receive()
                wsock.send("Your message was: %r" % message)
            except WebSocketError:
                break
        log.info("websocket (status) closed")

    @bottle_app.post('/start')
    def handle_firing_start():
        broker.controller_start_firing()
    @bottle_app.post('/stop')
    def handle_firing_stop():
        broker.controller_stop_firing()


    @bottle_app.error(404)
    def error404(error):
        return 'You have fallen completely off the edge of the internet. Sorry' + str(error)

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

    server = WSGIServer((ip, port), bottle_app,
                    handler_class=WebSocketHandler)
    server.serve_forever()


if __name__ == '__main__':
    server()