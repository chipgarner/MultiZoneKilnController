import bottle

bottle.debug(True)
app = bottle.Bottle()


def check_login(username, password):
    return True

@app.route('/hello/<name>')
def index(name):
    return bottle.template('<b>Hello {{name}}</b>!', name=name)

@app.get('/login') # or @route('/login')
def login():
    return '''
        <form action="/login" method="post">
            Username: <input name="username" type="text" />
            Password: <input name="password" type="password" />
            <input value="Login" type="submit" />
        </form>
    '''

@app.post('/login') # or @route('/login', method='POST')
def do_login():
    username = bottle.request.forms.get('username')
    password = bottle.request.forms.get('password')
    if check_login(username, password):
        return "<p>Your login information was correct.</p>"
    else:
        return "<p>Login failed.</p>"


@app.error(404)
def error404(error):
    return 'Nothing here, sorry'


# app.run(host='localhost', port=8082)
app.run(server='gunicorn', host = '127.0.0.1', port = 8002)
