import os
import threading

class PluginInterface():
    def __init__(self, RecorderInstance):
        self.PluginCalls = {}
        self.DependencyClasses = {}
        self.RecorderInstance = RecorderInstance
        
    def LoadPlugins(self):
        for filename in os.listdir("."):
            if filename.endswith(".py") and filename.startswith("Plugin_"):
                PluginName = os.path.splitext(filename)[0]
                self.RecorderInstance.PrintLog("[PluginInterface] Loading plugin: " + PluginName)
                PluginModule = __import__(PluginName, fromlist=[PluginName])
                PluginClass = getattr(PluginModule, PluginName)(self.RecorderInstance)
                self.InitRequirements(PluginClass)
                
        self.RecorderInstance.PrintLog("[PluginInterface] Load plugin finished!")
        
    def LoadTasks(self, TaskDict):
        for TaskName in TaskDict.keys():
            self.RecorderInstance.PrintLog("[PluginInterface] Loading task: " + TaskName)
            TaskModule = __import__(TaskName, fromlist=[TaskName])
            TaskClass = getattr(TaskModule, TaskName)(self.RecorderInstance)
            self.InitRequirements(TaskClass)
            TaskDict[TaskName] = TaskClass
            
        self.RecorderInstance.PrintLog("[PluginInterface] Load task finished!")
    
    def InitRequirements(self, Class):
        for Dependency in Class.requirements.keys():
            if not self.DependencyClasses.__contains__(Dependency):
                self.RecorderInstance.PrintLog("[PluginInterface] Loading dependency: " + Dependency)
                DependencyModule = __import__(Dependency, fromlist=[Dependency])
                DepClass = getattr(DependencyModule, Dependency)(self.RecorderInstance)
                self.DependencyClasses[Dependency] = DepClass
            Class.requirements[Dependency] = self.DependencyClasses[Dependency]
    
    def StartRequirements(self):
        for DepClass in self.DependencyClasses.values():
            t = threading.Thread(target = DepClass.Run)
            t.daemon = True
            t.start()
    
    def RegisterCallback(self, Module, Event, Callback):
        if not self.PluginCalls.__contains__(Module):
            self.PluginCalls[Module] = {}
        if not self.PluginCalls[Module].__contains__(Event):
            self.PluginCalls[Module][Event] = []
        self.PluginCalls[Module][Event].append(Callback)
    
    def GetCallbackCollection(self, Module, Event):
        if not self.PluginCalls.__contains__(Module):
            return []
        if not self.PluginCalls[Module].__contains__(Event):
            return []
        return self.PluginCalls[Module][Event]
