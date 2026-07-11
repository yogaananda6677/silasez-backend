from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(
        self,
        room_id: str,
        websocket: WebSocket,
    ):
        await websocket.accept()
        self.rooms[room_id].append(websocket)

    def disconnect(
        self,
        room_id: str,
        websocket: WebSocket,
    ):
        if websocket in self.rooms[room_id]:
            self.rooms[room_id].remove(websocket)

            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(
        self,
        room_id: str,
        data: dict,
    ):
        dead_connections = []

        for websocket in self.rooms.get(room_id, []):
            try:
                await websocket.send_json(data)
            except Exception:
                dead_connections.append(websocket)

        for websocket in dead_connections:
            self.disconnect(room_id, websocket)


manager = ConnectionManager()