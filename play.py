import asyncio
import base64
import json
import sys
from threading import Thread
from time import perf_counter, sleep

import numpy as np
import websockets
from zstandard import ZstdDecompressor


class  LineReader:
    def __init__(self, filename):
        self.lastidx = -1
        self.lastframe = {"idx":-1}
        self.lasttime = 0
        self.frametimes = []
        self.fp = open(filename, "r", encoding="utf-8")
        self.decompressor = ZstdDecompressor()
        self.metadata = json.loads(self.fp.readline())
        self.framerate = self.metadata["framerate"]
        self.wait = 1/self.framerate
        self.newlines = []
        self._scan_newlines()
        # first line is metadata, last line is empty
        self.metadata["nframes"] = len(self.newlines) - 2
    
    def _scan_newlines(self):
        self.fp.seek(0)
        offset = 0
        chunksize = 8192
        while True:
            chunk = self.fp.read(chunksize)
            if not chunk:
                break
            actual_chunk_size = len(chunk)
            newlines = []
            for i, char in enumerate(chunk):
                if char == "\n":
                    newlines.append(offset + i)
            self.newlines.extend(newlines)
            offset += actual_chunk_size

    def decompress(self, lineidx:int) -> dict:
        # line 0 is metadata
        # lineidx=0 -> newlines[1]
        lineidx += 1
        # read line
        start = self.newlines[lineidx] + lineidx
        end = self.newlines[lineidx+1] + lineidx + 1
        self.fp.seek(start)
        data = self.fp.read(end-start).strip()
        # b64 decode
        compressed = base64.b64decode(data.encode("utf-8"))
        # decompress
        line = self.decompressor.decompress(compressed)
        return json.loads(line)

    def stats(self):
        if self.lastidx % (int(self.framerate) * 5) == 0:
            frametimes = np.array(self.frametimes)
            avg = np.average(frametimes)
            std = np.std(frametimes)
            min = np.min(frametimes)
            max = np.max(frametimes)
            print(f"[STATS] frametimes: {avg:.5f} +- {std:.5f} max: {max:.5f} min: {min:.5f}")
            self.frametimes = []

    def loader_thread(self):
        self.lasttime = perf_counter()
        while True:
            nextidx = (self.lastidx + 1) % self.metadata["nframes"]
            frame = self.decompress(nextidx)
            frame["idx"] = nextidx
            while True:
                now = perf_counter()
                if (now - self.lasttime) >= self.wait:
                    self.lastframe = frame
                    self.frametimes.append(now-self.lasttime)
                    self.stats()
                    break
                sleep(0.0001)
            self.lastidx = nextidx
            self.lasttime = now

    def play(self):
        self.thread = Thread(target=self.loader_thread)
        self.thread.start()

    async def get_frame(self, message:str):
        request = json.loads(message)
        idx = request["idx"]
        name = request["name"]
        while True:
            if self.lastframe["idx"] != idx:
                return json.dumps({k:self.lastframe[k] for k in ("idx", name)})
            await asyncio.sleep(0.0001)

filename = sys.argv[1]
Reader = LineReader(filename)
print(Reader.metadata)
Reader.play()
    
async def getdata(websocket, path=None):
    async for message in websocket:
        await websocket.send(await Reader.get_frame(message))

async def main():
    data_server = await websockets.serve(getdata, "localhost", 6789)
    await asyncio.gather(data_server.wait_closed())

asyncio.run(main())
