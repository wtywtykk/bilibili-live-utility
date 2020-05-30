class Plugin_PollingLiveStateReceiver:
    def __init__(self, RecorderInstance):
        self.requirements = {
            "RoomPollingClient" : None,
        }
        self.RecorderInstance = RecorderInstance
        RecorderInstance.RegisterCallback("RoomPollingClient", "OnMessage", self.ProcessServerMessage)
            
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def ProcessServerMessage(self, data):
        try:
            self.PrintLog("Polling title: " + data['roomname'])
            self.PrintLog("Polling state: " + str(data['status']))
            
            self.RecorderInstance.SetRoomTitle(data['roomname'])
            self.RecorderInstance.SetLiveState(data['status'])
        except:
            pass
