from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
import uuid

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        room = request.form.get('room') or str(uuid.uuid4())
        sign = request.form.get('sign')
        return redirect(url_for('game', room=room, name=name, sign=sign))
    return render_template('index.html')

@app.route('/game')
def game():
    room = request.args.get('room')
    name = request.args.get('name')
    sign = request.args.get('sign')
    return render_template('game.html', room=room, name=name, sign=sign)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('player_joined', data, to=room)

@socketio.on('move')
def on_move(data):
    room = data['room']
    emit('update_board', data, to=room)

@socketio.on('chat')
def on_chat(data):
    room = data['room']
    emit('new_chat', data, to=room)

@socketio.on('restart_game')
def on_restart(data):
    room = data['room']
    emit('game_restarted', to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
