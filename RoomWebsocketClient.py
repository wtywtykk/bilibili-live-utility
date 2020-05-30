import asyncio
import random
import json
from struct import *
import re
import zlib
import time
import requests
import traceback

class RoomWebsocketClient():
    def __init__(self, RecorderInstance):
        self.op_name = {
            2 : "WS_OP_HEARTBEAT",
            3 : "WS_OP_HEARTBEAT_REPLY",
            5 : "WS_OP_MESSAGE",
            7 : "WS_OP_USER_AUTHENTICATION",
            8 : "WS_OP_CONNECT_SUCCESS"
        }

        self.WS_OP_HEARTBEAT=2
        self.WS_OP_HEARTBEAT_REPLY=3
        self.WS_OP_MESSAGE=5
        self.WS_OP_USER_AUTHENTICATION=7
        self.WS_OP_CONNECT_SUCCESS=8
        
        self.WS_PACKAGE_HEADER_TOTAL_LENGTH=16
        self.WS_PACKAGE_OFFSET=0
        self.WS_HEADER_OFFSET=4
        self.WS_VERSION_OFFSET=6
        self.WS_OPERATION_OFFSET=8
        self.WS_SEQUENCE_OFFSET=12
        
        self.WS_BODY_PROTOCOL_VERSION_NORMAL=0
        self.WS_BODY_PROTOCOL_VERSION_DEFLATE=2
        
        self.WS_HEADER_DEFAULT_VERSION=1
        self.WS_HEADER_DEFAULT_OPERATION=1
        self.WS_HEADER_DEFAULT_SEQUENCE=1
        
        self.WS_AUTH_OK=0
        self.WS_AUTH_TOKEN_ERROR=-101
        
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
        }
        session = requests.session()
        
        self.RecorderInstance = RecorderInstance
        
        room_info_url = 'https://api.live.bilibili.com/room/v1/Room/get_info'
        response = session.get(room_info_url, headers=headers, params={'room_id': RecorderInstance.room_id}, verify=True, timeout=(30,60)).json()
        self.real_roomid = response['data']['room_id']
        
        danmu_conf_url = 'https://api.live.bilibili.com/room/v1/Danmu/getConf'
        response = session.get(danmu_conf_url, headers=headers, params={'room_id': self.real_roomid}, verify=True, timeout=(30,60)).json()
        
        self.server_address = response['data']['host']
        self.server_port = response['data']['port']
        self._uid = (int)(100000000000000.0 + 200000000000000.0*random.random())
        
        self.connected = False
        self._reader = None
        self._writer = None
    
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))
        
    def Run(self):
        tasks = [
            self.ConnectLoop(),
            self.HeartbeatLoop()
        ]
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(asyncio.wait(tasks))
        except KeyboardInterrupt:
            for task in asyncio.Task.all_tasks():
                task.cancel()
            loop.stop()
        loop.close()
        
    async def ConnectLoop(self):
        self.PrintLog('id=' + str(self.real_roomid))
        self.PrintLog('addr=' + str(self.server_address))
        self.PrintLog('port=' + str(self.server_port))
        
        while True:
            if self.connected == False:
                try:
                    self.PrintLog('connecting')
                    if self._writer != None:
                        self._writer.close()
                    reader, writer = await asyncio.open_connection(self.server_address, self.server_port)
                    self._reader = reader
                    self._writer = writer
                    if (await self.send_joinchannel()) == True:
                        self.connected = True
                except:
                    pass
                
            while self.connected == True:
                await self.ReceiveSocketData()

            await asyncio.sleep(1)

        if self._writer != None:
            self._writer.close()

    async def HeartbeatLoop(self):
        while True:
            if self.connected == True:
                await self.send_heartbeat()
                await asyncio.sleep(30)
            else:
                await asyncio.sleep(0.5)

    async def send_joinchannel(self):
        self.PrintLog('send auth')
        try:
            body = '{"roomid":%s,"uid":%s,"protover":%s}' % (self.real_roomid, self._uid, 2)
            await self.SendSocketData(self.WS_OP_USER_AUTHENTICATION, body)
            return True
        except Exception as e:
            self.PrintLog("joinchannel error:" + repr(e))
            traceback.self.print_exc()
            return False
        
    async def send_heartbeat(self):
        try:
            await self.SendSocketData(self.WS_OP_HEARTBEAT, "")
        except Exception as e:
            self.connected=False
            self.PrintLog("heartbeat error:" + repr(e))
            traceback.print_exc()

    async def SendSocketData(self, op, body):
        bodybytes = body.encode('utf-8')
        packetlength = len(bodybytes) + self.WS_PACKAGE_HEADER_TOTAL_LENGTH
        sendbytes = pack('!IHHII', packetlength, self.WS_PACKAGE_HEADER_TOTAL_LENGTH, self.WS_HEADER_DEFAULT_VERSION, op, self.WS_HEADER_DEFAULT_SEQUENCE)
        if len(bodybytes) != 0:
            sendbytes = sendbytes + bodybytes
        self._writer.write(sendbytes)
        await self._writer.drain()
            
    async def ReceiveSocketData(self):
        try:
            lendata = await self._reader.read(4)#WS_PACKAGE
            packageLen, = unpack('!I', lendata)
            data = await self._reader.read(packageLen-4)
            self.onRecv(lendata+data)
        except Exception as e:
            self.connected=False
            self.PrintLog("receive loop error:" + repr(e))
            traceback.print_exc()

    def onRecv(self,data):
        try:
            i=0
            while i<len(data):
                packageLen,headerLen,ver,op,seq = unpack('!IHHII', data[i:i+self.WS_PACKAGE_HEADER_TOTAL_LENGTH])
                assert(headerLen==self.WS_PACKAGE_HEADER_TOTAL_LENGTH)
                body=data[i+headerLen:i+packageLen]
                if op == self.WS_OP_HEARTBEAT_REPLY:
                    count,=unpack('!I', body)
                    self.onMessage(op,count)
                elif op == self.WS_OP_MESSAGE or op == self.WS_OP_CONNECT_SUCCESS:
                    if ver == self.WS_BODY_PROTOCOL_VERSION_DEFLATE:
                        self.onRecv(zlib.decompress(body))
                    else:
                        self.onMessage(op,body.decode('utf-8'))
                else:
                    self.connected = False
                    self.PrintLog('error op!!!')
                i+=packageLen
        except Exception as e:
            self.connected=False
            self.PrintLog("decode body error:" + repr(e))
            traceback.print_exc()

    def onMessage(self,op,body):
        try:
            SrvMsg = {"rcv_ts" : str(int(round(time.time() * 1000))), "op" : self.op_name[op], "body" : None}
            if op == self.WS_OP_HEARTBEAT_REPLY:
                pass
            elif op == self.WS_OP_MESSAGE:
                try:
                    SrvMsg["body"] = json.loads(body)
                except:
                    pass
            elif op == self.WS_OP_CONNECT_SUCCESS:
                if len(body):
                    try:
                        dic = json.loads(body)
                        SrvMsg["body"] = dic
                        if dic['code'] == self.WS_AUTH_OK:
                            self.PrintLog('auth ok')
                            #self.send_heartbeat()
                            #this.heartBeat();
                        elif dic['code'] == self.WS_AUTH_TOKEN_ERROR:
                            self.connected = False
                            self.PrintLog('auth token error')
                            #retry = False
                            #onReceiveAuthRes();
                        else:
                            self.connected = False
                            self.PrintLog('auth failure')
                            #onClose()
                    except:
                        return
                else:
                    pass
                    #self.send_heartbeat()
                    #this.heartBeat()
            else:
                self.connected = False
                self.PrintLog('error op!!!')
                
            for Callback in self.RecorderInstance.GetCallbackCollection("RoomWebsocketClient", "OnMessage"):
                try:
                    Callback(SrvMsg)
                except Exception as pe:
                    self.PrintLog("Plugin exception: " + repr(e))
                    traceback.print_exc()

        except Exception as e:
            self.connected = False
            self.PrintLog("WebSocket Error:" + repr(e))
            traceback.print_exc()
