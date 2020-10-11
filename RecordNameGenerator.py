import os
import time

class RecordNameGenerator:
    def __init__(self, basedir, foldername):
        t = time.time()
        current_struct_time = time.localtime(t)
        current_time = time.strftime('%Y%m%d_%H%M', current_struct_time)
        self.session_timestamp = current_time
        self.timestamp = current_time + '-' + str(int(round(t * 1000)))
        self.basedir = basedir
        self.foldername = foldername

    def regenerate(self):
        t = time.time()
        current_struct_time = time.localtime(t)
        current_time = time.strftime('%Y%m%d_%H%M', current_struct_time)
        self.timestamp = current_time + '-' + str(int(round(t * 1000)))
        
    def get_name(self, extension):
        return self.timestamp + extension
        
    def get(self, extension):
        c_directory=os.path.join(self.basedir, 'files', self.foldername, self.session_timestamp)
        if not os.path.exists(c_directory):
            os.makedirs(c_directory)
        return os.path.join(c_directory, self.timestamp + extension)

    def get_temp(self, extension):
        c_directory=os.path.join(self.basedir, 'tmp', self.foldername)
        if not os.path.exists(c_directory):
            os.makedirs(c_directory)
        return os.path.join(c_directory, self.session_timestamp + self.timestamp + extension)
