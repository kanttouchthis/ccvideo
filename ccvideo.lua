local name = settings.get("name")

local function playAudio(speaker, audio)
    speaker.playAudio(audio)
end

local function drawFrame(monitor, frame, width, height)
    local char, text, back
    for i = 1, height do
        char = frame[1]:sub((i - 1) * width + 1, (i) * width)
        text = frame[2]:sub((i - 1) * width + 1, (i) * width)
        back = frame[3]:sub((i - 1) * width + 1, (i) * width)
        monitor.setCursorPos(1, i)
        monitor.blit(char, text, back)
    end
end

local function getData(ws, idx)
    local data
    ws.send(textutils.serializeJSON({idx=idx, name=name}))
    data = ws.receive()
    if data ~= nil then
        return textutils.unserializeJSON(data)
    else
        return nil
    end
end

local function Client()
    local clientType, data, frame

    local ws = assert(http.websocket("ws://localhost:6789"))
    local speaker = peripheral.find("speaker")
    local monitor = peripheral.find("monitor")

    local width, height = 121, 81
    if speaker ~= nil then
        clientType = "speaker"
    elseif monitor ~= nil then
        clientType = "monitor"
        monitor.setTextScale(0.5)
        monitor.setBackgroundColor(colors.black)
        monitor.clear()
        width, height = monitor.getSize()
    end

    local idx = -1
    while true do
        data = getData(ws, idx)
        if data ~= nil then
            idx = data["idx"]
            frame = data[name]
            if clientType == "speaker" then
                if not pcall(playAudio, speaker, frame) then
                    print("dropped audio")
                end
            elseif clientType == "monitor" then
                if not pcall(drawFrame, monitor, frame, width, height) then
                    print("dropped frame")
                end
            end
        end
    end
end

while true do
    pcall(Client)
    os.sleep(1)
end