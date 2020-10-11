import shutil
import subprocess
import traceback

class Task_VideoFixer:
    def __init__(self, RecorderInstance):
        self.requirements = {"DiskSpaceMonitor": None}
        self.RecorderInstance = RecorderInstance
                
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def Run(self, PathGen):
        try:
            if self.requirements["DiskSpaceMonitor"].IsDiskNearFull():
                raise ZeroDivisionError("Disk near full! Aborting video convert!")
            subprocess.call(self.RecorderInstance.GetConfig().ffmpeg_path + " -y -i \"" + PathGen.get(".flv") + "\" -acodec copy -vcodec copy \"" + PathGen.get_temp("fix.mp4") + "\"",shell=True)
            shutil.move(PathGen.get_temp("fix.mp4"), PathGen.get("fix.mp4"))
        except Exception as e:
            self.PrintLog("Error in VideoFixer" + repr(e))
            traceback.print_exc()
