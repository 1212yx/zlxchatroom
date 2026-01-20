import websocket
import json
import threading
import time

def on_message(ws, message):
    print(f"Received: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Closed")

def on_open(ws):
    print("Opened connection")
    # Join
    ws.send(json.dumps({
        'type': 'join',
        'user': 'TestUser',
        'room': 'TestRoom'
    }))
    
    def send_loop():
        time.sleep(1)
        ws.send(json.dumps({
            'type': 'chat',
            'content': 'Hello World'
        }))
        time.sleep(1)
        ws.close()
        
    threading.Thread(target=send_loop).start()

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:5555/chat/ws",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.run_forever()
