import os
import subprocess
import multiprocessing
import traceback

class Task_Recorder:
    def __init__(self, RecorderInstance):
        self.requirements = {
            "RoomPollingClient" : None,
        }
        self.RecorderInstance = RecorderInstance
                
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def SaveRoomTitle(self, PathGen):
        try:
            file_obj = open(PathGen.get(".txt"), "w", True, "utf-8")
            file_obj.write(self.RecorderInstance.GetRoomTitle())
            file_obj.close();
        except Exception as e:
            self.PrintLog("Failed to save room title" + repr(e))
            traceback.print_exc()
    
    def Run(self, PathGen):
        try:
            Url = self.requirements["RoomPollingClient"].GetLiveURLs()
            record_path=PathGen.get(".flv")
            self.PrintLog("Download from: " + Url[0])
            self.PrintLog("Save to: " + record_path)
            subprocess.call("wget --timeout=5 -t 2 -U \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36\" --referer \"https://live.bilibili.com/" + self.RecorderInstance.room_id + "\" -O \"" + record_path + "\" \"" + Url[0] + "\"",shell=True)
            if os.path.exists(record_path):
                if os.path.getsize(record_path):
                    self.SaveRoomTitle(PathGen)
                    return True
                else:
                    os.remove(record_path)
        except Exception as e:
            self.PrintLog("Error while recording: " + repr(e))
            traceback.print_exc()
        return False
        