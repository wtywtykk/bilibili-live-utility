import os
import sys
import time
import datetime
import multiprocessing
import RecordNameGenerator
import PluginInterface
import traceback

class RecorderInstance:
    def __init__(self, room_id):
        self.room_id = room_id
        self.Cfg = __import__("config_" + room_id, fromlist=["config_" + room_id])
        self.PluginInterface = PluginInterface.PluginInterface(self)
        self.PluginInterface.LoadPlugins()
        self.RoomTitle = ""
        self.IsLiving = False
        self.LastLiveTime = datetime.datetime.fromtimestamp(0)
        self.IsLivingFiltered = False
    
    def PrintLog(self, content='None'):
        t = time.time()
        current_struct_time = time.localtime(t)
        brackets = '[{}]'
        time_part = brackets.format(time.strftime('%Y-%m-%d %H:%M:%S', current_struct_time))
        room_part = brackets.format(self.room_id)
        print(time_part, room_part, content)
        
    def RegisterCallback(self, Module, Event, Callback):
        return self.PluginInterface.RegisterCallback(Module, Event, Callback)
    
    def GetCallbackCollection(self, Module, Event):
        return self.PluginInterface.GetCallbackCollection(Module, Event)
        
    def SetRoomTitle(self, Title):
        self.RoomTitle = Title
    
    def GetRoomTitle(self):
        return self.RoomTitle
    
    def SetLiveState(self, Status):
        if self.IsLiving == True:
            self.LastLiveTime = datetime.datetime.now()
        self.IsLiving = Status
    
    def GetLiveState(self):
        if self.IsLiving == False:
            if (datetime.datetime.now()-self.LastLiveTime).seconds < 60:
                self.IsLivingFiltered = False
        else:
            self.IsLivingFiltered = True
        return self.IsLivingFiltered
    
    def GetConfig(self):
        return self.Cfg
    
    def RunOtherTasks(self, RunSeq, Tasks, FileNameGen):
        for Task in RunSeq:
            try:
                Tasks[Task].Run(FileNameGen)
            except Exception as e:
                self.PrintLog("Task exception: " + repr(e))
                traceback.print_exc()
        
    def run(self):
        RecordTasks = {"Task_Recorder": None}
        Tasks = {}
        for Task in self.Cfg.tasks_after_record:
            Tasks[Task] = None
        self.PluginInterface.LoadTasks(RecordTasks)
        self.PluginInterface.LoadTasks(Tasks)
        
        while True:
            try:
                FileNameGen = RecordNameGenerator.RecordNameGenerator(os.getcwd(), self.Cfg.room_name)
                
                if self.GetLiveState():
                    for Callback in self.GetCallbackCollection("RecorderInstance", "OnLiveStart"):
                        try:
                            Callback(FileNameGen)
                        except Exception as e:
                            self.PrintLog("Plugin exception: " + repr(e))
                            traceback.print_exc()

                while self.GetLiveState():
                    self.PrintLog("Tasks running")
                    if RecordTasks["Task_Recorder"].Run(FileNameGen):
                        convert_task = multiprocessing.Process(target = self.RunOtherTasks, args = (self.Cfg.tasks_after_record, Tasks, FileNameGen))
                        convert_task.start()
                        convert_task.join(0)
                    time.sleep(1)

                    FileNameGen.regenerate()
                    self.PrintLog("Tasks finished")
                while not self.GetLiveState():
                    time.sleep(1)
            except Exception as e:
                self.PrintLog("Run error! " + repr(e))
                traceback.print_exc()
                
if __name__ == '__main__':
    if len(sys.argv) == 2:
        input_id = str(sys.argv[1])
        RecorderInstance(input_id).run()
    else:
        raise ZeroDivisionError("Room id not specified!")
