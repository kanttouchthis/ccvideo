local args = { ... }
local mode = args[1]
if mode == nil then
    print("Usage: ccvideo monitor")
    print("Usage: ccvideo speaker")
    print("Usage: ccvideo play <video>")
    os.queueEvent("terminate")
    os.sleep(1)
end
mode = tostring(mode)

local function getMessage(modem, channel)
    local event, side, receiveChannel, replyChannel, message, distance
    while true do
        event, side, receiveChannel, replyChannel, message, distance = os.pullEvent("modem_message")
        if receiveChannel == channel then
            return message
        end
    end
end

local function playAudio(speaker, audio)
    if speaker == nil then
        return
    end
    if not type(audio) == "table" then
        return
    end
    speaker.playAudio(audio)
end

local function drawFrame(monitor, frame, width, height)
    if monitor == nil then
        return
    end
    if not type(frame) == "string" then
        return
    end
    local char, text, back
    for i = 1, height do
        char = frame[1]:sub((i - 1) * width + 1, (i) * width)
        text = frame[2]:sub((i - 1) * width + 1, (i) * width)
        back = frame[3]:sub((i - 1) * width + 1, (i) * width)
        monitor.setCursorPos(1, i)
        monitor.blit(char, text, back)
    end
end

local function speakerFunction()
    -- speaker setup
    local speaker = peripheral.find("speaker")

    -- modem setup
    local channel = settings.get("channel")
    channel = tonumber(channel)
    local modem = peripheral.find("modem")
    modem.open(channel)
    print("speaker on channel: " .. channel)

    local audio
    while true do
        audio = getMessage(modem, channel)
        if not pcall(playAudio, speaker, audio) then
            print("dropped audio")
        end
    end
end

local function monitorFunction()
    -- monitor setup
    local monitor = peripheral.find("monitor")
    monitor.setTextScale(0.5)
    monitor.setBackgroundColor(colors.black)
    monitor.clear()
    local width, height = monitor.getSize()

    -- modem setup
    local channel = settings.get("channel")
    channel = tonumber(channel)
    local modem = peripheral.find("modem")
    modem.open(channel)
    print("monitor on channel: " .. channel)

    local frame
    while true do
        frame = getMessage(modem, channel)
        if not pcall(drawFrame, monitor, frame, width, height) then
            print("dropped frame")
        end
    end
end

local function transmitFrames(modem, monitors, frames)
    if frames == nil then
        return
    end
    for i = 1, #monitors do
        modem.transmit(tonumber(monitors[i]), 999, frames[i])
    end
end

local function transmitAudio(modem, speaker, audio)
    if audio == nil then
        return
    end
    modem.transmit(tonumber(speaker), 999, audio)
end

local function playFunction()
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

    local response, data, framerate, wait, diff
    while true do
        if data ~= nil then
            transmitAudio(modem, speaker, data["audio_chunk"])
            transmitFrames(modem, monitors, data["frame"])
        end
        response = http.get(url)
        data = response.readAll()
        data = textutils.unserialiseJSON(data)
        if wait == nil then
            framerate = data["framerate"]
            wait = 1 / framerate * 1000
        end
        diff = os.epoch("utc") - time
        time = os.epoch("utc")
        os.sleep(math.max(wait - diff, 0) / 1000)
    end
end

local function loop(func)
    while true do
        func()
    end
end

local modes = { monitor = monitorFunction, speaker = speakerFunction, play = playFunction }

loop(modes[mode])
