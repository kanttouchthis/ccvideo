from flask import Flask, request
import json
import gzip
import sys
app = Flask("ccserver")

video = sys.argv[1]
f = gzip.open(video, "r")

@app.route("/get", methods=["GET"])
def get():
    global f
    line = f.readline()
    if not line:
        f.close()
        f = gzip.open(video, "r")
        line = f.readline()
    data = json.loads(line.decode("utf-8"))
    return data

app.run()

