import base64
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image
from tqdm import tqdm
from usearch.index import Index
from zstandard import ZstdCompressor

assert len(sys.argv) == 3, f"Usage: {sys.argv[0]} video framerate"

framerate = float(sys.argv[2])

offset = 0.3
N = 3  # width
M = 2  # height
width = 121 * N
height = 81 * M
chunk_width = 121
chunk_height = 81
monitor_names = []

for i in range(M):
    for j in range(N):
        monitor_names.append(f"monitor_{j:02}_{i:02}")

try:
    shutil.rmtree("temp")
except:
    pass
os.makedirs("temp")
os.system(f'ffmpeg -i "{sys.argv[1]}" -vf "fps={framerate},pad=iw:iw:(ow-iw)/2:(ow-ih)/2:color=black,scale={width}:{height}" -q:v 3 ./temp/%07d.jpg')
os.system(f'ffmpeg -i "{sys.argv[1]}" -ac 1 -ar 48000 -f s8 ./temp/audio.raw')

index = Index.restore("colors.index")
with open("colors.json", "r") as f:
    labels = json.load(f)


def closest_color(rgb):
    rgb_vec = np.array(rgb, dtype=np.float32)
    results = index.search(rgb_vec, 1)
    idx = results.keys[0]
    return labels[idx]


def chunk_colors(colors):
    chunks = []
    for i in range(M):
        for j in range(N):
            left = j * chunk_width
            upper = i * chunk_height
            right = left + chunk_width
            lower = upper + chunk_height

            chunk = colors[upper:lower, left:right]
            chunks.append(chunk.flatten())
    return chunks


def _convert(image: Image.Image) -> list:
    # Convert image to RGB just in case it's not
    image = image.convert("RGB")
    image = np.array(image, dtype=np.float16).reshape(-1, 3)
    results = index.search(image, 1)
    results = results.keys.reshape(height, width)
    chunked = chunk_colors(results)
    color_strings = []
    for chunk in chunked:
        colors = [labels[idx] for idx in chunk]
        c, t, b = zip(*colors)
        result = ["".join(c), "".join(t), "".join(b)]
        color_strings.append(result)
    return color_strings

def convert(image):
    if isinstance(image, list):
        return image
    if not image.endswith(".jpg"):
        return
    image = Image.open("./temp/" + image)
    return _convert(image)

files = os.listdir("./temp")
black_frames = [_convert(Image.new("RGB", (width, height)))] * int(offset * framerate)
files = black_frames + files

with open("./temp/audio.raw", "rb") as f:
    audio = f.read()
    audio = np.frombuffer(audio, dtype=np.int8).tolist()
n = int(48000.0 / framerate)
audio_chunks = [audio[i:i + n] for i in range(0, len(audio), n)]

meta = {"framerate":framerate, "monitors": f"{N}x{M}"}
with open(sys.argv[1] + ".ccv", "w") as f:
    f.write(json.dumps(meta) + "\n")
    compressor = ZstdCompressor()
    for file, audio_chunk in tqdm(zip(files, audio_chunks), total=len(files)):
        frame = convert(file)
        if (not frame) or (not audio_chunk): break
        data = {monitor_names[i]:frame[i] for i in range(len(monitor_names))}
        data["speaker_center"] = audio_chunk
        data = (json.dumps(data)+"\n").encode("utf-8")
        compressed = compressor.compress(data)
        b64 = base64.b64encode(compressed).decode("utf-8")
        f.write(b64 + "\n")
