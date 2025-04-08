local ccstrings = require("cc.strings")
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
    speaker.playAudio(audio)
end

local function drawFrame(monitor, frame, width, height)
    if monitor == nil then
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
    local ws = assert(http.websocket("ws://localhost:6789"))

    local idx, audio
    while true do
        idx = getMessage(modem, channel)
        ws.send(tostring(idx))
        audio = ws.receive()
        audio = textutils.unserializeJSON(audio)
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
    local ws = assert(http.websocket("ws://localhost:6790"))

    local message, idx, chunk, frame
    while true do
        message = getMessage(modem, channel)
        idx = message[1]
        chunk = message[2]
        ws.send(idx..","..chunk)
        frame = ws.receive()
        frame = textutils.unserializeJSON(frame)
        if not pcall(drawFrame, monitor, frame, width, height) then
            print("dropped frame")
        end
    end
end

local function sendFrameIdx(modem, monitors, idx)
    if idx == nil then
        return
    end
    for i = 1, #monitors do
        modem.transmit(tonumber(monitors[i]), 999, {idx, i-1})
    end
end

local function sendAudioIdx(modem, speaker, idx)
    if idx == nil then
        return
    end
    modem.transmit(tonumber(speaker), 999, idx)
end

local function playFunction()
    local monitors = settings.get("monitors")
    monitors = ccstrings.split(monitors, ",")

    local speaker = settings.get("speaker")

    local ws = assert(http.websocket("ws://localhost:6788"))

    local modem = peripheral.find("modem")

    ws.send("")
    local meta = ws.receive()
    meta = textutils.unserializeJSON(meta)
    ws.close()
    local framerate = tonumber(meta["framerate"])
    local nframes = tonumber(meta["nframes"])
    local wait = 1.0/framerate
    while true do
        for idx = 0, nframes - 2 do
            sendAudioIdx(modem, speaker, idx)
            sendFrameIdx(modem, monitors, idx)
            os.sleep(wait)
        end
    end
end

local function loop(func)
    while true do
        func()
    end
end

local modes = { monitor = monitorFunction, speaker = speakerFunction, play = playFunction }

loop(modes[mode])
