import os
import uuid
import logging
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)

# Load secure configurations from environment variables (adjust these in your production environment)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'replace-with-a-secure-secret-key')
app.config['SESSION_COOKIE_SECURE'] = True      # Ensures cookies are only sent over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True      # Helps mitigate the risk of client side script accessing the protected cookie

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Configure Socket.IO with proper CORS settings
# For production, set CORS_ALLOWED_ORIGINS to your actual domain, e.g., "https://yourdomain.com"
socketio = SocketIO(app, cors_allowed_origins=os.environ.get('CORS_ALLOWED_ORIGINS', '*'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get and validate the user's name and chosen sign
        name = request.form.get('name', '').strip()
        sign = request.form.get('sign', '').strip().upper()
        if not name or sign not in ['X', 'O']:
            # Optionally, you can flash an error message to the user here.
            return redirect(url_for('index'))
        # Auto-create a new room ID
        room = str(uuid.uuid4())
        return redirect(url_for('game', room=room, name=name, sign=sign))
    return render_template('index.html')

@app.route('/game')
def game():
    # Retrieve parameters and perform basic validation
    room = request.args.get('room', '').strip()
    name = request.args.get('name', '').strip()
    sign = request.args.get('sign', '').strip().upper()
    if not room or not name or sign not in ['X', 'O']:
        return redirect(url_for('index'))
    return render_template('game.html', room=room, name=name, sign=sign)

@socketio.on('join')
def on_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        app.logger.info(f"Player {data.get('playerName', 'Unknown')} joined room {room}")
        emit('player_joined', data, to=room)

@socketio.on('move')
def on_move(data):
    room = data.get('room')
    if room:
        # Optionally, validate the move details here.
        emit('update_board', data, to=room)

@socketio.on('chat')
def on_chat(data):
    room = data.get('room')
    if room:
        # Optionally, sanitize data.get('message') here to prevent XSS.
        emit('new_chat', data, to=room)

@socketio.on('restart_game')
def on_restart(data):
    room = data.get('room')
    if room:
        emit('game_restarted', to=room)

# New event: broadcast rematch responses to everyone in the room.
@socketio.on('rematch_response')
def on_rematch_response(data):
    room = data.get('room')
    if room:
        emit('rematch_response', data, to=room)

# New event: when a rematch is agreed upon, start it by broadcasting a rematch start event.
@socketio.on('start_rematch')
def on_start_rematch(data):
    room = data.get('room')
    if room:
        emit('rematch_start', to=room)

if __name__ == '__main__':
    # For production, debug mode must be disabled.
    socketio.run(app, debug=False)