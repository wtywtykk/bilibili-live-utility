import config
import subprocess
import multiprocessing
import RecorderInstance
import traceback

if __name__ == '__main__':
    mp = multiprocessing.Process
    tasks = [mp(target=BiliBiliLiveRecorder(room_id).run) for room_id in config.rooms]
    for i in tasks:
        i.start()
    for i in tasks:
        i.join()
