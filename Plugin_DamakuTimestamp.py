import datetime

class Plugin_DamakuTimestamp:
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
            self.fo = open(FileNameGen.get(".dmts.txt"), 'a', encoding="utf-8")
        except Exception as e:
            self.PrintLog("Open file error! " + repr(e))
            traceback.print_exc()
        
    def ProcessServerMessage(self, SrvData):
        if SrvData["op"] == "WS_OP_MESSAGE":
            if SrvData["body"]:
                if SrvData["body"]["cmd"] == "DANMU_MSG":
                    DanmakuTimestamp = SrvData["body"]["info"][0][4]
                    DanmakuText = SrvData["body"]["info"][1]
                    DamakuSender = SrvData["body"]["info"][2][0]
                    
                    ReadableTime = datetime.datetime.fromtimestamp(DanmakuTimestamp / 1000)
                    
                    IsTimestamp = True
                    Cfg = self.RecorderInstance.GetConfig()
                    if len(Cfg.plugin_danmakutimestamp_whitelist) == 0 and len(Cfg.plugin_danmakutimestamp_keyword) == 0:
                        IsTimestamp = False
                    if len(Cfg.plugin_danmakutimestamp_whitelist) !=0 and not Cfg.plugin_danmakutimestamp_whitelist.__contains__(DamakuSender):
                        IsTimestamp = False
                    if len(Cfg.plugin_danmakutimestamp_keyword) != 0:
                        AnyKeyword = False
                        for keyword in Cfg.plugin_danmakutimestamp_keyword:
                            if DanmakuText.endswith(keyword):
                                AnyKeyword = True
                        IsTimestamp = IsTimestamp and AnyKeyword
                    
                    if IsTimestamp == True:
                        ReadableText = str(ReadableTime) + " " + str(DamakuSender) + " " + str(DanmakuText)
                        self.PrintLog(ReadableText)
                    
                        self.Buffer.append(ReadableText)
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

