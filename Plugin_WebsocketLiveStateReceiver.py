class Plugin_WebsocketLiveStateReceiver:
    def __init__(self, RecorderInstance):
        self.requirements = {
            "RoomWebsocketClient" : None,
        }
        self.RecorderInstance = RecorderInstance
        RecorderInstance.RegisterCallback("RoomWebsocketClient", "OnMessage", self.ProcessServerMessage)
            
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def ProcessServerMessage(self, SrvData):
        if SrvData["op"] == "WS_OP_MESSAGE":
            if SrvData["body"]:
                if SrvData["body"]["cmd"] == "ROOM_CHANGE":
                    self.PrintLog("ROOM_CHANGE Title: " + SrvData["body"]["data"]["title"])
                    self.RecorderInstance.SetRoomTitle(SrvData["body"]["data"]["title"])
                if SrvData["body"]["cmd"] == "LIVE":
                    self.PrintLog("Live start")
                    self.RecorderInstance.SetLiveState(True)
                if SrvData["body"]["cmd"] == "PREPARING":
                    self.PrintLog("Live stop")
                    self.RecorderInstance.SetLiveState(False)
