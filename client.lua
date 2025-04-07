local channel = settings.get("channel")
channel = tonumber(channel)
print("running on channel: " .. channel)

-- modem
local modem = peripheral.find("modem")
modem.open(channel)

-- monitor
local width, height = 121, 81
local monitor = peripheral.find("monitor")
if monitor ~= nil then
    monitor.setTextScale(0.5)
    monitor.setBackgroundColor(colors.black)
    monitor.clear()
    width, height = monitor.getSize()
end
local empty = string.rep(" ", width)
local black = string.rep("0", width)

-- speaker
local speaker = peripheral.find("speaker")

-- exit if no monitor or speaker is found
if (monitor == nil) and (speaker == nil) then
    print("no monitor or speaker connected")
    os.queueEvent("terminate")
    os.sleep(1)
end

local function drawFrame(frame)
    if monitor == nil then
        return
    end
    if not type(frame) == "string" then
        return
    end
    local line
    for i = 1, height do
        line = frame:sub((i - 1) * width + 1, (i) * width)
        monitor.setCursorPos(1, i)
        monitor.blit(empty, black, line)
    end
end

local function playAudio(audio)
    if speaker == nil then
        return
    end
    if not type(audio) == "table" then
        return
    end
    speaker.playAudio(audio)
end

local event, side, receiveChannel, replyChannel, message, distance
while true do
    event, side, receiveChannel, replyChannel, message, distance = os.pullEvent("modem_message")
    if receiveChannel == channel then
        drawFrame(message)
        playAudio(message)
    end
end
