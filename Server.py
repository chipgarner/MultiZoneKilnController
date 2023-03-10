import bottle
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError
import logging
import MessageBroker


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


    # Open a persistent websocket to UI
    @bottle_app.route('/controller')
    def controller():
        log.debug(str(bottle.request.environ))
        wsock = get_websocket_from_request()
        if not wsock:
            return 'Expecting a websocket request'
        message = wsock.receive()
        broker.update(message)
        log.debug(message)

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


    @bottle_app.error(404)
    def error404(error):
        return 'You have fallen completely off the edge of the internet. Sorry' + str(error)



    ip = "0.0.0.0"
    port = 8081
    log.info("listening on %s:%d" % (ip, port))

    server = WSGIServer((ip, port), bottle_app,
                    handler_class=WebSocketHandler)
    server.serve_forever()

if __name__ == '__main__':
    server()