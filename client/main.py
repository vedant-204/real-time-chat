from atomic import AtomicCounter
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.user_counter = AtomicCounter()
        self.active_connections = dict()
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        client_id = self.user_counter.inc()
        self.active_connections[client_id] = websocket

    def disconnect(self, websocket: WebSocket):
        k = self.client_id(websocket)
        if k:
            del self.active_connections[k]

    def client_id(self, websocket: WebSocket):
        return next((uid for uid, ws in self.active_connections.items() if ws == websocket), None)

    async def broadcast(self, message: str, websocket):
        for connection in filter(lambda ws: ws != websocket, self.active_connections.values()):
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get():
    with open('./static/index.html') as f:
        html = f.read()
    return HTMLResponse(content=html)

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"<User#{manager.client_id(websocket)}> : {data}", websocket)
    except WebSocketDisconnect:
        user_id = manager.client_id(websocket)
        manager.disconnect(websocket)
        await manager.broadcast(f"User#{user_id} has left the chat", None)

#from typing import List
#
#from fastapi import FastAPI, WebSocket, WebSocketDisconnect
#from fastapi.responses import HTMLResponse
#
#app = FastAPI()
#
#class ConnectionManager:
#    def __init__(self):
#        self.active_connections: List[WebSocket] = []
#
#    async def connect(self, websocket: WebSocket):
#        await websocket.accept()
#        self.active_connections.append(websocket)
#
#    def disconnect(self, websocket: WebSocket):
#        self.active_connections.remove(websocket)
#
#    async def send_personal_message(self, message: str, websocket: WebSocket):
#        await websocket.send_text(message)
#
#    async def broadcast(self, message: str):
#        for connection in self.active_connections:
#            await connection.send_text(message)
#
#
#manager = ConnectionManager()
#
#
#@app.get("/")
#async def get():
#    with open('./static/index.html') as f:
#        html = f.read()
#    return HTMLResponse(content=html)
#
#@app.websocket("/ws/{client_id}")
#async def websocket_endpoint(websocket: WebSocket, client_id: int):
#    await manager.connect(websocket)
#    try:
#        while True:
#            data = await websocket.receive_text()
#            await manager.send_personal_message(f"You wrote: {data}", websocket)
#            await manager.broadcast(f"Client #{client_id} says: {data}")
#    except WebSocketDisconnect:
#        manager.disconnect(websocket)
#        await manager.broadcast(f"Client #{client_id} left the chat")
