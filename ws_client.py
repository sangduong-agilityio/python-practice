import asyncio
import sys
import json
import websockets

async def listen(token: str):
    uri = f"ws://localhost:8000/api/v1/notifications/ws?token={token}"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(
            uri,
            extra_headers={"Authorization": f"Bearer {token}"},
        ) as websocket:
            print("Connected! Waiting for notifications...")
            while True:
                message = await websocket.recv()
                print(f"Received notification: {json.dumps(json.loads(message), indent=2)}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed by server: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ws_client.py <jwt_token>")
        sys.exit(1)
        
    token = sys.argv[1]
    asyncio.run(listen(token))
