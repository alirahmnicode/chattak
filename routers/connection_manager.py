import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def set_notification_socket(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        sockets_obj = self.get_user_socket_object(websocket)
        self.active_connections[user_id] = sockets_obj

    async def set_chat_socket(
        self, websocket: WebSocket, user_id: int, target_user_id: int
    ) -> None:
        await websocket.accept()
        self.active_connections[user_id]["chat_socket"] = {target_user_id: websocket}

    async def set_connection_socket(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self.active_connections.get(user_id)["connection_socket"] = websocket

    async def send_notification(
        self,
        text: str,
        receiver_id: int,
        sender_id: int,
        sender_username: str,
        chat_id: int,
    ):
        user_sockets = self.active_connections.get(receiver_id)
        if user_sockets:
            json_message = json.dumps(
                {
                    "message": text,
                    "chat_id": chat_id,
                    "sender_id": sender_id,
                    "sender_username": sender_username,
                }
            )
            ntf_socket: WebSocket = user_sockets.get("notification_socket")
            await ntf_socket.send_json(json_message)

    def is_user_online(self, user_id: int) -> bool:
        return self.active_connections.get(user_id, False) and True

    def has_user_chat_socket(self, user_id: int, target_user_id: int) -> bool:
        socket_obj = self.active_connections.get(target_user_id)
        if socket_obj:
            chat_socket = socket_obj.get("chat_socket")
            if chat_socket:
                return user_id in chat_socket

    def user_has_notification_socket(self, target_user_id: int):
        return self.active_connections.get(target_user_id, False) and True

    def disconnect(self, socket_type: str, user_id: int):
        socket_obj = self.active_connections.get(user_id)

        if socket_type == "chat":
            socket_obj["chat_socket"] = None
        elif socket_type == "notification":
            socket_obj["notification"] = None

    async def send_personal_message(
        self, message: str, target_user_id: int, user_id: int
    ):
        websocket: WebSocket = (
            self.active_connections.get(target_user_id).get("chat_socket").get(user_id)
        )
        json_message = json.dumps(
            {"message": message, "receiver_id": target_user_id, "sender_id": user_id}
        )
        await websocket.send_json(json_message)

    async def send_connection_info(self, message: str, target_user_id: int) -> None:
        socket_obj = self.active_connections.get(target_user_id)

        if socket_obj:
            websocket: WebSocket = socket_obj.get("connection_socket")
            if websocket:
                await websocket.send_text(message)

    def get_user_socket_object(self, notification_socket: WebSocket):
        return {
            "notification_socket": notification_socket,
            "chat_socket": None,
            "connection_socket": None,
        }
