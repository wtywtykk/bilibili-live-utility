import traceback

class Plugin_WebsocketDataDumper:
    def __init__(self, RecorderInstance):
        self.requirements = {
            "RoomWebsocketClient" : None,
        }
        self.RecorderInstance = RecorderInstance
        self.fo = None
        self.Buffer = []
        RecorderInstance.RegisterCallback("RecorderInstance", "OnLiveStart", self.ProcessLiveStartEvent)
        RecorderInstance.RegisterCallback("RoomWebsocketClient", "OnMessage", self.ProcessServerMessage)
            
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def ProcessLiveStartEvent(self, FileNameGen):
        try:
            self.PrintLog("Reopening file")
            if self.fo:
                self.fo.close()
            self.fo = open(FileNameGen.get(".dm.txt"), 'a', encoding="utf-8")
        except Exception as e:
            self.PrintLog("Open file error! " + repr(e))
            traceback.print_exc()

    def ProcessServerMessage(self, SrvData):
        self.Buffer.append(str(SrvData))
        if self.fo:
            try:
                while len(self.Buffer) > 0:
                    LineData = self.Buffer[0]
                    self.fo.writelines([LineData,"\n"])
                    self.fo.flush()
                    self.Buffer.pop(0)
            except Exception as e:
                self.PrintLog("Write error! " + repr(e))
                traceback.print_exc()
