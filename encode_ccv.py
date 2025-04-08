from PIL import Image
import sys
import os
import shutil
import json
import tqdm
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import gzip
from usearch.index import Index

assert len(sys.argv) == 3, f"Usage: {sys.argv[0]} video framerate"

framerate = float(sys.argv[2])

offset = 0.5
N = 3  # width
M = 2  # height
width = 121 * N
height = 81 * M
chunk_width = 121
chunk_height = 81

try:
    shutil.rmtree("temp")
except:
    pass
os.makedirs("temp")
os.system(
    f'ffmpeg -i "{sys.argv[1]}" -t 00:01:00 -vf "fps={framerate},pad=iw:iw:(ow-iw)/2:(ow-ih)/2:color=black,scale={width}:{height}:flags=neighbor" -q:v 3 ./temp/%07d.jpg'
)
os.system(f'ffmpeg -i "{sys.argv[1]}" -ac 1 -t 00:01:00 -ar 48000 -f s8 ./temp/audio.raw')

index = Index.restore("colors.index")
with open("colors.json", "r") as f:
    labels = json.load(f)

def closest_color(rgb):
    rgb_vec = np.array(rgb, dtype=np.float32)
    results = index.search(rgb_vec, 1)
    idx = results.keys[0]
    return labels[idx]


def image_to_hex_list(image: Image.Image) -> list:
    # Convert image to RGB just in case it's not
    image = image.convert("RGB")
    image = np.array(image, dtype=np.float32).reshape(-1, 3)
    results = index.search(image, 1)
    colors = [labels[int(key[0])] for key in results.keys]
    c, t, b = zip(*colors)
    result = ["".join(c), "".join(t), "".join(b)]
    return result


def chunk_image(image):
    chunks = []
    for i in range(M):
        for j in range(N):
            left = j * chunk_width
            upper = i * chunk_height
            right = left + chunk_width
            lower = upper + chunk_height

            chunk = image.crop((left, upper, right, lower))
            chunks.append(chunk)
    return chunks


frames = []


def convert(imagepath):
    if not imagepath.endswith(".jpg"):
        return
    image = Image.open("./temp/" + imagepath)
    chunks = chunk_image(image)
    chunks = [image_to_hex_list(chunk) for chunk in chunks]
    return chunks


files = os.listdir("./temp")

with ThreadPoolExecutor(max_workers=16) as ex:
    frames = list(tqdm.tqdm(ex.map(convert, files), total=len(files)))

with open("./temp/audio.raw", "rb") as f:
    audio = f.read()
    audio = np.frombuffer(audio, dtype=np.int8).tolist()
n = int(48000.0 / framerate)
audio_chunks = [audio[i:i + n] for i in range(0, len(audio), n)]

with gzip.open(sys.argv[1] + ".ccv", "w") as f:
    for frame, audio_chunk in zip(frames, audio_chunks):
        f.write(
            (
                json.dumps(
                    {"framerate": framerate, "frame": frame, "audio_chunk": audio_chunk}
                )
                + "\n"
            ).encode("utf-8")
        )
