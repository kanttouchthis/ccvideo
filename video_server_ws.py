import asyncio
import sys
import gzip
import json
import websockets

video = sys.argv[1]
data = gzip.open(video, "r").readlines()
data = [json.loads(line) for line in data]

async def audio(websocket, path=None):
    async for message in websocket:
        # message = frame
        idx = int(message)
        await websocket.send(json.dumps(data[idx]["audio_chunk"]))

def get_frame(message):
    idx, chunk = message.split(",")
    idx = int(idx)
    chunk = int(chunk)
    return json.dumps(data[idx]["frame"][chunk])
    

async def frame(websocket, path=None):
    async for message in websocket:
        # message = frame, chunk
        await websocket.send(get_frame(message))


async def meta(websocket, path=None):
    async for message in websocket:
        await websocket.send(json.dumps({"framerate":data[0]["framerate"], "nframes": len(data)}))

async def main():
    chat_server = await websockets.serve(meta, "localhost", 6788)
    chat_server = await websockets.serve(audio, "localhost", 6789)
    notif_server = await websockets.serve(frame, "localhost", 6790)

    print("Servers started: Audio on 6789, Frame on 6790")
    await asyncio.gather(chat_server.wait_closed(), notif_server.wait_closed())

asyncio.run(main())
