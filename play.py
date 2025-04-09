import asyncio
import base64
import json
import sys
import aiofiles
from time import perf_counter

import numpy as np
import websockets
from zstandard import ZstdDecompressor


class  LineReader:
    def __init__(self, filename):
        self.filename = filename
        self.lastidx = -1
        self.lastframe = {"idx":-1}
        self.frames = {}
        self.lasttime = 0
        self.frametimes = []
        self.decompressor = ZstdDecompressor()
        self.queue = asyncio.Queue(64)
    
    async def setup(self):
        await self._setup()
        self.framerate = self.metadata["framerate"]
        self.wait = 1/self.framerate -0.005
        return self
    
    async def _setup(self):
        self.fp = await aiofiles.open(self.filename, "rb")
        self.metadata = json.loads((await self.fp.readline()).decode("utf-8"))

    async def decompress(self, lineidx:int) -> dict:
        # read line
        t0 = perf_counter()
        chunk = await self.fp.readline()
        if not chunk:
            await self.fp.seek(0)
            await self.fp.readline()
            return self.decompress(self, lineidx)
        # b64 decode
        compressed = base64.b64decode(chunk)
        # decompress
        line = self.decompressor.decompress(compressed)
        frame = json.loads(line)
        frame["idx"] = lineidx
        return frame

    async def stats(self):
        if self.lastidx % (int(self.framerate) * 5) == 0:
            frametimes = np.array(self.frametimes)
            avg = np.average(frametimes)
            std = np.std(frametimes)
            min = np.min(frametimes)
            max = np.max(frametimes)
            print(f"[STATS] frametimes: {avg:.5f} +- {std:.5f} max: {max:.5f} min: {min:.5f}")
            self.frametimes = []

    async def load(self):
        i = 0
        while True:
            await self.queue.put(await self.decompress(i))
            i+=1

    async def play(self):
        self.lasttime = perf_counter()
        while True:
            nextidx = (self.lastidx + 1) 
            while True:
                now = perf_counter()
                if (now - self.lasttime) >= self.wait:
                    self.lastframe = await self.queue.get()
                    self.frametimes.append(now-self.lasttime)
                    stats = self.stats()
                    break
                await asyncio.sleep(0.0001)
            self.lastidx = nextidx
            self.lasttime = now
            await stats

    async def get_frame(self, message:str):
        request = json.loads(message)
        idx = request["idx"]
        name = request["name"]
        while True:
            if self.lastframe["idx"] != idx:
                return json.dumps({k:self.lastframe[k] for k in ("idx", name)})
            await asyncio.sleep(0.0001)


async def main():
    filename = sys.argv[1]
    Reader = await LineReader(filename).setup()

    async def getdata(websocket, path=None):
        async for message in websocket:
            await websocket.send(await Reader.get_frame(message))

    data_server = await websockets.serve(getdata, "localhost", 6789)
    asyncio.gather(Reader.load(), Reader.play())
    await data_server.wait_closed()

asyncio.run(main())
