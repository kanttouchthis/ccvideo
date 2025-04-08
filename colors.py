from usearch.index import Index
import numpy as np
import json

PIXELS = float(9*6)

colors = "0123456789abcdef"
chars = {"+": 13.0,
        "*" : 6.0,
        "x": 9.0,
        "#": 20.0,
        "@" : 25.0,
        "0" : 19.0,
        "%" : 10.0,
}

color_palette = {
    (240, 240, 240): " 00",  # white
    (242, 178, 51): " 11",  # orange
    (229, 127, 216): " 22",  # magenta
    (153, 178, 242): " 33",  # light blue
    (222, 222, 108): " 44",  # yellow
    (127, 204, 25): " 55",  # lime
    (242, 178, 204): " 66",  # pink
    (76, 76, 76): " 77",  # gray
    (153, 153, 153): " 88",  # light gray
    (76, 153, 178): " 99",  # cyan
    (178, 102, 229): " aa",  # purple
    (51, 102, 204): " bb",  # blue
    (127, 102, 76): " cc",  # brown
    (87, 166, 78): " dd",  # green
    (204, 76, 76): " ee",  # red
    (17, 17, 17): " ff",  # black
}

color_keys = list(color_palette.keys())
for char in chars:
    for i, text_color in enumerate(colors):
        for j, bg_color in enumerate(colors):
            if i == j:
                continue
            color_string = char + colors[i] + colors[j]
            pixels = chars[char]
            text = color_keys[i]
            bg = color_keys[j]
            ratio = pixels/PIXELS
            inverse = 1-ratio
            r = int(text[0] * ratio + bg[0] * inverse)
            g = int(text[1] * ratio + bg[1] * inverse)
            b = int(text[2] * ratio + bg[2] * inverse)
            rgb = (r, g ,b)
            if rgb in color_palette:
                pass
            else:
                color_palette[rgb] = color_string


color_vectors = np.array(list(color_palette.keys()), dtype=np.float32)
labels = list(color_palette.values())

index = Index(ndim=3, metric="l2sq", dtype="f32")  # L2 squared distance
for i, vec in enumerate(color_vectors):
    index.add(i, vec)

index.save("colors.index")
with open("colors.json", "w") as f:
    json.dump(labels, f, indent=4)


