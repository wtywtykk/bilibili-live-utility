import os, sys, shutil
import subprocess
import traceback

class Task_AudioExtractor:
    def __init__(self, RecorderInstance):
        self.requirements = {}
        self.RecorderInstance = RecorderInstance
                
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def Run(self, PathGen):
        try:
            subprocess.call(self.RecorderInstance.GetConfig().ffmpeg_path + " -y -i \"" + PathGen.get(".flv") + "\" -acodec mp3 -vn \"" + PathGen.get_temp(".mp3") + "\"",shell=True)
            shutil.move(PathGen.get_temp(".mp3"), PathGen.get(".mp3"))
        except Exception as e:
            self.PrintLog("Error in AudioExtractor" + repr(e))
            traceback.print_exc()
