"""
提词器 WebSocket 房间中继 - Render.com 部署版
只做 WebSocket 广播，无 HTTP 文件服务（静态文件托管在 GitHub Pages）
"""
import asyncio
import json
import os
import signal
import threading

PORT = int(os.environ.get("PORT", 10000))

rooms = {}
rooms_lock = threading.Lock()


async def ws_handler(websocket):
    current_room = None
    alive = True

    async def heartbeat():
        """每 30 秒发送 ping 保持连接不中断"""
        while alive:
            await asyncio.sleep(30)
            try:
                await websocket.ping()
            except Exception:
                break

    hb_task = asyncio.create_task(heartbeat())

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue

            if data.get("type") == "join":
                room = data.get("room", "").strip().upper()
                if not room:
                    continue
                with rooms_lock:
                    if current_room and current_room in rooms:
                        rooms[current_room].discard(websocket)
                        if not rooms[current_room]:
                            del rooms[current_room]
                    if room not in rooms:
                        rooms[room] = set()
                    rooms[room].add(websocket)
                    current_room = room
                    count = len(rooms[room])
                await _broadcast(room, {
                    "type": "join_notify",
                    "count": count
                }, exclude=websocket)
                # 通知加入者当前房间人数
                await websocket.send(json.dumps({"type":"join_notify","count":count}))
                print(f"[WS] join room {room} ({count} peers)")

            elif data.get("type") == "cmd" and current_room:
                await _broadcast(current_room, data, exclude=websocket)
                print(f"[WS] room {current_room} cmd: {data.get('action')}")

            elif data.get("type") == "state" and current_room:
                await _broadcast(current_room, data, exclude=websocket)

    except Exception as e:
        print(f"[WS] connection error: {type(e).__name__}: {e}")
    finally:
        alive = False
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass
        if current_room:
            with rooms_lock:
                if current_room in rooms:
                    rooms[current_room].discard(websocket)
                    count = len(rooms[current_room])
                    if count == 0:
                        del rooms[current_room]
                        print(f"[WS] room {current_room} empty, removed")
                    else:
                        msg = json.dumps({"type": "join_notify", "count": count})
                        for ws in list(rooms[current_room]):
                            try:
                                await ws.send(msg)
                            except Exception:
                                pass


async def _broadcast(room, message, exclude=None):
    with rooms_lock:
        members = list(rooms.get(room, set()))
    msg_str = json.dumps(message, ensure_ascii=False)
    for ws in members:
        if ws != exclude:
            try:
                await ws.send(msg_str)
            except Exception:
                pass


async def main():
    import websockets
    async with websockets.serve(
        ws_handler, "0.0.0.0", PORT,
        ping_interval=25,
        ping_timeout=15,
        close_timeout=5
    ):
        print(f"[WS] relay running on port {PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
