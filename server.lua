-- example
-- set monitors 473,123,4 
-- set speaker 1241       only mono supported for now
-- set url http://yourserver.com:5000/get (optional)

local ccstrings = require("cc.strings")

local monitors = settings.get("monitors")
monitors = ccstrings.split(monitors, ",")

local speaker = settings.get("speaker")

local url = settings.get("url")
if url == nil then
    url = "http://127.0.0.1:5000/get"
end

local modem = peripheral.find("modem")

local time = os.epoch("utc")

local function drawFrame(frame)
    if frame == nil then
        return
    end
    for i = 1, #monitors do
        modem.transmit(tonumber(monitors[i]), 999, frame[i])
    end
end

local function playAudio(audio)
    if audio == nil then
        return
    end
    modem.transmit(tonumber(speaker), 999, audio)
end

local response, data, framerate, wait, diff
while true do
    response = http.get(url)
    data = response.readAll()
    data = textutils.unserialiseJSON(data)

    drawFrame(data["frame"])
    playAudio(data["audio_chunk"])

    if wait ~= nil then
        framerate = data["framerate"]
        wait = 1 / framerate * 1000
    end
    diff = os.epoch("utc") - time
    time = os.epoch("utc")
    os.sleep(math.max(diff - wait, 0) / 1000)
end
