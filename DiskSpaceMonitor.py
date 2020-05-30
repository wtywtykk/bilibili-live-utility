import os
import time
import threading
import traceback

class DiskSpaceMonitor:
    def __init__(self, RecorderInstance):
        self.RecorderInstance = RecorderInstance
        self.WarningEventFired = False
        self.CheckError = False
        self.OccupiedSpace = 0
        threading.Thread(target = self.Run).start()
                
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def IsDiskNearFull(self):
        if self.OccupiedSpace >= self.RecorderInstance.GetConfig().disk_warning_threshold:
            return True
        if self.CheckError == True:
            return True
        return False
            
    def Run(self):
        while True:
            time.sleep(60)
            try:
                i = 0
                for dirpath, dirname, filename in os.walk(os.getcwd()):
                    for ii in filename:
                        i += os.path.getsize(os.path.join(dirpath,ii))
                self.OccupiedSpace = i
                self.CheckError = False
                
                self.PrintLog("Disk size: " + str(i / 1024 / 1024 / 1024) + "G")
                
                if self.IsDiskNearFull():
                    if self.WarningEventFired == False:
                        self.WarningEventFired = True
                        for Callback in self.RecorderInstance.GetCallbackCollection("DiskSpaceMonitor", "OnWarning"):
                            try:
                                Callback()
                            except Exception as pe:
                                self.PrintLog("Plugin exception: " + repr(e))
                                traceback.print_exc()
                else:
                    self.WarningEventFired = False

            except Exception as e:
                self.CheckError = True
                self.PrintLog("Failed to calculate disk use" + repr(e))
                traceback.print_exc()
        