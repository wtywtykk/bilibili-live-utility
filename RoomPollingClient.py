import requests
import time
import random
import traceback

class RoomPollingClient:
    def __init__(self, RecorderInstance):
        self.RecorderInstance = RecorderInstance
        self.session = requests.session()
        self.room_id = self.RecorderInstance.room_id
        self.parsed_room_id = self.room_id
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "referer": "https://live.bilibili.com/" + self.room_id
        }
        self.Enabled = True
            
    def PrintLog(self, content="None"):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def common_request(self, method, url, params=None, data=None):
        connection = None
        if method == "GET":
            connection = self.session.get(url, headers=self.headers, params=params, timeout=(30,60))
        if method == "POST":
            connection = self.session.post(url, headers=self.headers, params=params, data=data, timeout=(30,60))
        return connection

    def GetRoomInfo(self):
        data = {}
        room_info_url = "https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom"
        response = self.common_request("GET", room_info_url, {"room_id": self.room_id}).json()
        if response["code"] == 0:
            data["roomname"] = response["data"]["room_info"]["title"]
            data["status"] = response["data"]["room_info"]["live_status"] == 1
            self.parsed_room_id = str(response["data"]["room_info"]["room_id"])
            data["uid"] = response["data"]["room_info"]["uid"]
            data["hostname"] = response["data"]["anchor_info"]["base_info"]["uname"]
        return data

    def GetLiveURLs(self):
        live_urls = []
        url = "https://api.live.bilibili.com/xlive/web-room/v1/playUrl/playUrl"
        stream_info = self.common_request("GET", url, {
            "cid": self.parsed_room_id,
            "qn": 10000,
            "platform": "web",
            "https_url_req": 1
        }).json()
        best_quality=stream_info["data"]["quality_description"][0]["qn"]
        if best_quality != 10000:
            stream_info = self.common_request("GET", url, {
                "cid": self.parsed_room_id,
                "qn": best_quality,
                "platform": "web",
                "https_url_req": 1
            }).json()
        for durl in stream_info["data"]["durl"]:
            live_urls.append(durl["url"])
        return live_urls
        
    def GetLiveCalendar(self):
        calendar_data = {}
        roominfo = self.GetRoomInfo()
        calendar_url = "https://api.live.bilibili.com/xlive/web-ucenter/v2/calendar/GetProgramList"
        response = self.common_request("GET", calendar_url, {"type": 3,"ruids": roominfo["uid"]}).json()
        if response["code"] == 0:
            allprog = []
            for day in response["data"]["program_infos"].values():
                for prog in day["program_list"]:
                    allprog.append({"ts": prog["start_time"],"title": prog["title"]})
            calendar_data["programs"] = sorted(allprog, key=lambda p: p["ts"])
            calendar_data["now"] = response["data"]["timestamp"]
        return calendar_data
        
    def Run(self):
        while True:
            try:
                if self.Enabled == True:
                    room_info = self.GetRoomInfo()
                    for Callback in self.RecorderInstance.GetCallbackCollection("RoomPollingClient", "OnMessage"):
                        try:
                            Callback(room_info)
                        except Exception as pe:
                            self.PrintLog("Plugin exception: " + repr(e))
                            traceback.print_exc()
            except Exception as e:
                self.PrintLog("Failed to pull room info: " + repr(e))
                traceback.print_exc()
            time.sleep(self.RecorderInstance.GetConfig().polling_check_interval * (1 + random.random()))
