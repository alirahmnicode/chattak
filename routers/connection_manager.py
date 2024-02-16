from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        sockets_obj = self.get_user_socket_object(websocket)
        self.active_connections[user_id] = sockets_obj

    async def set_connection_socket(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self.active_connections.get(user_id)["connection_socket"] = websocket
        print(self.active_connections)

    def is_user_online(self, user_id: int) -> bool:
        return self.active_connections.get(user_id, False) and True

    def disconnect(self, user_id: int):
        del self.active_connections[user_id]

    async def send_personal_message(self, message: str, target_user_id: int):
        websocket: WebSocket = self.active_connections.get(target_user_id).get(
            "message_socket"
        )
        await websocket.send_text(message)

    async def send_connection_info(self, message: str, target_user_id: int) -> None:
        websocket: WebSocket = self.active_connections.get(target_user_id).get(
            "connection_socket"
        )
        await websocket.send_text(message)

    def get_user_socket_object(self, user_websocket: WebSocket):
        return {"message_socket": user_websocket, "connection_socket": None}
