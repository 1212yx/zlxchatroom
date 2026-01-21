from flask import request
from flask_socketio import emit, join_room, leave_room
from ..extensions import socketio

# Simple in-memory storage for room management
# room_id -> list of dicts [{'sid': '...', 'role': 'host', 'name': 'User 1'}]
rooms_data = {}
# sid -> room_id
user_rooms = {}

@socketio.on('connect', namespace='/game')
def on_connect():
    print(f"User {request.sid} connected to game namespace")

@socketio.on('disconnect', namespace='/game')
def on_disconnect():
    sid = request.sid
    if sid in user_rooms:
        room = user_rooms[sid]
        if room in rooms_data:
            # Remove player
            rooms_data[room] = [p for p in rooms_data[room] if p['sid'] != sid]
            
            # If room empty, delete
            if not rooms_data[room]:
                del rooms_data[room]
            else:
                # If host left, assign new host
                has_host = any(p['role'] == 'host' for p in rooms_data[room])
                if not has_host and rooms_data[room]:
                    rooms_data[room][0]['role'] = 'host'
                
                # Broadcast update
                emit('update_player_list', {'players': rooms_data[room]}, room=room)
                
        del user_rooms[sid]
    print(f"User {sid} disconnected from game namespace")

@socketio.on('join_game', namespace='/game')
def join_game(data):
    room = data.get('room')
    if not room:
        return
    
    # Initialize room if not exists
    if room not in rooms_data:
        rooms_data[room] = []
    
    # Check room capacity (Max 6 for 3v3)
    if len(rooms_data[room]) >= 6:
        emit('join_error', {'msg': 'Room is full (Max 6 players)'})
        return

    # Determine Role
    role = 'guest'
    if len(rooms_data[room]) == 0:
        role = 'host'

    # Join logic
    join_room(room)
    
    # Add player info
    # For now, use a generic name or get from data if available. 
    # Since we don't have user auth yet, generate "Player N"
    player_name = f"Player {len(rooms_data[room]) + 1}"
    
    player_info = {
        'sid': request.sid,
        'role': role,
        'name': player_name
    }
    rooms_data[room].append(player_info)
    user_rooms[request.sid] = room
    
    print(f"User {request.sid} joined room {room} as {role}. Count: {len(rooms_data[room])}")
    
    # Notify others (Legacy event, maybe keep for chat logs if needed, but UI will use update_player_list)
    emit('player_joined', {
        'sid': request.sid, 
        'msg': f'{player_name} joined ({len(rooms_data[room])}/6)',
        'count': len(rooms_data[room])
    }, room=room)
    
    # Broadcast full player list to sync all clients
    emit('update_player_list', {'players': rooms_data[room]}, room=room)
    
    # Notify self of success
    emit('join_success', {'room': room, 'role': role, 'count': len(rooms_data[room])})

@socketio.on('leave_game', namespace='/game')
def leave_game(data):
    room = data.get('room')
    if room:
        leave_room(room)
        if room in rooms_data:
            rooms_data[room] = [p for p in rooms_data[room] if p['sid'] != request.sid]
            
            if not rooms_data[room]:
                del rooms_data[room]
            else:
                 # If host left, assign new host
                has_host = any(p['role'] == 'host' for p in rooms_data[room])
                if not has_host and rooms_data[room]:
                    rooms_data[room][0]['role'] = 'host'
                
                emit('update_player_list', {'players': rooms_data[room]}, room=room)
        
        if request.sid in user_rooms:
            del user_rooms[request.sid]
            
        print(f"User {request.sid} left room {room}")
        emit('player_left', {'sid': request.sid, 'msg': 'A player has left'}, room=room)

@socketio.on('game_action', namespace='/game')
def game_action(data):
    room = data.get('room')
    if room:
        # Broadcast action to others in the room
        emit('game_action', data, room=room, include_self=False)
