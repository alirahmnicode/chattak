from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates


app = FastAPI()

templates = Jinja2Templates(directory="templates")


users = {5: "reza", 6:"ali"}


class ConnectionManager:
    def __init__(self):
        # self.active_connections: list[WebSocket] = []
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        print(self.active_connections)
        self.active_connections[user_id] = websocket
        print(self.active_connections)

    def is_user_online(self, user_id: int) -> bool:
        return self.active_connections.get(user_id, False) and True

    def disconnect(self, user_id: int):
        del self.active_connections[user_id]

    async def send_personal_message(self, message: str, target_user_id: int):
        websocket = self.active_connections.get(target_user_id)
        print(websocket)
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            print(connection)
            await connection.send_text(message)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"users": users}
    )


@app.get("/pm/{target_user_id}")
async def privet_message(request: Request, target_user_id: int):
    return templates.TemplateResponse(
        request=request,
        name="privet_message.html",
        context={
            "target_user": {"id": target_user_id, "username": users[target_user_id]}
        },
    )

manager = ConnectionManager()

@app.websocket("/ws/{target_user_id}")
async def privet_message_websocket(websocket: WebSocket, target_user_id: int):
    """
    The client send message and the target user recieve the message.
    """
    client_id = 5 if target_user_id == 6 else 6
    
    await manager.connect(websocket=websocket, user_id=client_id)
    # check if target user is online or not
    

    try:
        while True:
            data = await websocket.receive_text()
            is_target_user_is_online = manager.is_user_online(user_id=target_user_id)
            if is_target_user_is_online:
                await manager.send_personal_message(
                    data, target_user_id
                )
            else:
                # save message in db
                print(data)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast(f"Client #{client_id} left the chat")
