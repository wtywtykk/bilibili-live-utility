from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Face, Plain, Image, At, AtAll
from graia.application.friend import Friend
from graia.application.group import Group, Member

import asyncio
import threading
import datetime
import random
import emoji
import traceback

class Plugin_QQ:
    def __init__(self, RecorderInstance):
        self.requirements = {
            "DiskSpaceMonitor": None,
            "RoomPollingClient": None
        }
        self.RecorderInstance = RecorderInstance
        if self.RecorderInstance.GetConfig().plugin_notifybot_qq_number != 0:
            t = threading.Thread(target = self.MiraiRun)
            t.daemon = True
            t.start()
            
    def PrintLog(self, content='None'):
        self.RecorderInstance.PrintLog("[" + __name__ + "] " + str(content))

    def MiraiRun(self):
        Cfg = self.RecorderInstance.GetConfig
        
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

        bcc = Broadcast(loop=loop)
        app = GraiaMiraiApplication(
            broadcast=bcc,
            connect_info=Session(
                host="http://" + Cfg().plugin_notifybot_mirai_api_http_locate, # 填入 httpapi 服务运行的地址
                authKey=Cfg().plugin_notifybot_authkey, # 填入 authKey
                account=Cfg().plugin_notifybot_qq_number, # 你的机器人的 qq 号
                websocket=True # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
            )
        )

        @bcc.receiver("FriendMessage")
        async def event_fm(app: GraiaMiraiApplication, friend: Friend, msg: MessageChain):
            self.PrintLog("Receive friend message: " + str(msg))
            for Callback in self.RecorderInstance.GetCallbackCollection("QQInterface", "OnFriendMessage"):
                try:
                    Callback(room_info)
                except Exception as pe:
                    self.PrintLog("Plugin exception: " + repr(e))
                    traceback.print_exc()
            await app.sendFriendMessage(friend, MessageChain.create([
                Plain(text="机器人没有私聊功能")
            ]))
            
        def GetSelfName():
            Names = Cfg().plugin_notifybot_say_selfname
            if len(Names)>0:
                return Names[random.randint(0, len(Names) - 1)]
            else:
                return ""

        def GetCalendarMessage():
            try:
                TxtResult = []
                CalData = self.requirements["RoomPollingClient"].GetLiveCalendar()
                ts = CalData["now"]
                rts = datetime.datetime.fromtimestamp(ts)
                
                prog_today_passed = None
                prog_scheduled = None
                for prog in CalData["programs"]:
                    prog_ts = prog["ts"]
                    prog_rts = datetime.datetime.fromtimestamp(prog_ts)
                    if prog_ts < ts and prog_rts.day == rts.day:
                        prog_today_passed = prog
                    if prog_ts >= ts:
                        prog_scheduled = prog
                        break
                TxtResult.append("让我康康直播日历,")
                if prog_scheduled:
                    prog_ts = prog_scheduled["ts"]
                    prog_rts = datetime.datetime.fromtimestamp(prog_ts)
                    if prog_rts.day == rts.day:
                        TxtResult.append("今天 " + prog_rts.strftime("%H:%M") + " 有直播哦！标题：" + prog_scheduled["title"])
                    else:
                        if prog_today_passed:
                            TxtResult.append("今天播过了！标题：" + prog_today_passed["title"])
                            TxtResult.append("今天接下来没有了！下一场：" + prog_rts.strftime("%m-%d %H:%M") + " 标题：" + prog_scheduled["title"])
                        else:
                            TxtResult.append("今天没有！下一场：" + prog_rts.strftime("%m-%d %H:%M") + " 标题：" + prog_scheduled["title"])
                else:
                    if prog_today_passed:
                        TxtResult.append("今天播过了！标题：" + prog_today_passed["title"])
                        TxtResult.append("之后的日历全是空的！")
                    else:
                        TxtResult.append("今天没有！之后的日历也全是空的！")
                return "\n".join(TxtResult)
            except Exception as e:
                self.PrintLog("Query calendar failed: " + repr(e))
                traceback.print_exc()
                return "不知道咋回事，出错了"
                
        def IsInvolved(msg):
            for i in msg.get(At):
                if i.target == Cfg().plugin_notifybot_qq_number:
                    return True
            return False
        
        async def ProcessRevoke(group, msg):
            Ret = False
            if IsInvolved(msg):
                msgtxt = msg.asDisplay()
                if "撤回" in msgtxt:
                    if self.LastSentMsgId[group.id] != 0:
                        await app.revokeMessage(self.LastSentMsgId[group.id])
                    self.LastSentMsgId[group.id] = 0
                    Ret = True
            return Ret
            
        async def SendGroupMsg(group, msg):
            BotMsg = await app.sendGroupMessage(group, MessageChain.create(msg))
            self.LastSentMsgId[group] = BotMsg.messageId

        async def ProcessAnyLiveMsg(group, msg):
            Ret = False
            msgtxt = msg.asDisplay()
            Matched = False
            for Keyword in Cfg().plugin_notifybot_recognise_selfname:
                if Keyword in msgtxt:
                    if "播吗" in msgtxt:
                        Matched = True
                        break
                    if "播嘛" in msgtxt:
                        Matched = True
                        break
            for Keyword in Cfg().plugin_notifybot_anylive_keyword:
                if Keyword in msgtxt:
                    Matched = True
                    break
            if Matched == True:
                if (datetime.datetime.now()-self.LastAnyLiveReportTime[group.id]).seconds > 60:
                    await SendGroupMsg(group.id, [Plain(GetCalendarMessage())])
                    Ret = True
                self.LastAnyLiveReportTime[group.id] = datetime.datetime.now()
            return Ret
                
        async def ProcessConversations(group, member, msg):
            Ret = False
            SenderID = member.id
            if Cfg().plugin_notifybot_conversation_blacklist.__contains__(SenderID):
                if random.random() >= Cfg().plugin_notifybot_conversation_blacklist[SenderID]:
                    return Ret
            msgtxt = msg.asDisplay()
            for Conv in Cfg().plugin_notifybot_conversations:
                IsKeywordFound = False
                for Keyword in Conv[0]:
                    if Keyword in msgtxt:
                        IsKeywordFound = True
                        break
                if IsKeywordFound == True:
                    if len(Conv[1]) != 0:
                        while True:
                            RandItem = Conv[1][random.randint(0, len(Conv[1]) - 1)]
                            if random.random() <= RandItem[0]:
                                if RandItem[1] != "":
                                    NewOvertalkCounter = self.OvertalkCounter[group.id] - (datetime.datetime.now() - self.LastTalkTime[group.id]).seconds / 60
                                    if NewOvertalkCounter < 0:
                                        NewOvertalkCounter = 0
                                    NewOvertalkCounter += 1
                                    self.LastTalkTime[group.id] = datetime.datetime.now()
                                    if NewOvertalkCounter > Cfg().plugin_notifybot_overtalk_threshold:
                                        if self.OvertalkCounter[group.id] <= Cfg().plugin_notifybot_overtalk_threshold:
                                            await SendGroupMsg(group.id, [Plain(emoji.emojize(Cfg().plugin_notifybot_overtalk_word, use_aliases=True))])
                                    else:
                                        await SendGroupMsg(group.id, [Plain(emoji.emojize(RandItem[1], use_aliases=True))])
                                    self.OvertalkCounter[group.id] = NewOvertalkCounter
                                    Ret = True
                                break
                    break
            return Ret
        
        async def ProcessRepeat(group, msg):
            Ret = False
            msgtxt = msg.include(Plain, Face, Image).asSerializationString()
            if msgtxt == self.LastRepeatMsg[group.id]:
                Matched = False
                for Keyword in Cfg().plugin_notifybot_repeat_keyword:
                    if Keyword in msgtxt:
                        if random.random() < Cfg().plugin_notifybot_repeat_keyword_prob:
                            Matched = True
                        break
                if random.random() < Cfg().plugin_notifybot_repeat_prob:
                    Matched = True
                for Keyword in Cfg().plugin_notifybot_repeat_blacklist:
                    if Keyword in msgtxt:
                        Matched = False
                        break
                if Matched == True:
                    NewMsg = msg.include(Face, Plain, Image).__root__
                    if len(NewMsg):
                        await SendGroupMsg(group.id, NewMsg)
                        Ret = True
            self.LastRepeatMsg[group.id] = msgtxt
            return Ret
                
        @bcc.receiver("GroupMessage")
        async def event_gm(app: GraiaMiraiApplication, group: Group, member: Member, msg: MessageChain):
            try:
                if Cfg().plugin_notifybot_group_number.__contains__(group.id):
                    MsgSent = False
                    if MsgSent == False:
                        MsgSent = await ProcessRevoke(group, msg)
                    if MsgSent == False:
                        MsgSent = await ProcessAnyLiveMsg(group, msg)
                    if MsgSent == False:
                        MsgSent = await ProcessConversations(group, member, msg)
                    if MsgSent == False:
                        MsgSent = await ProcessRepeat(group, msg)
            except Exception as e:
                self.PrintLog("Exception in gm processing: " + repr(e))
                traceback.print_exc()
            
        @bcc.receiver("TempMessage")
        async def event_tm(app: GraiaMiraiApplication, group: Group, member: Member, msg: MessageChain):
            await app.sendTempMessage(group, member, MessageChain.create([
                Plain(text="机器人没有私聊功能")
            ]))
        
        async def SendLiveOnMessageAsync():
            for Grp in Cfg().plugin_notifybot_group_number:
                if Cfg().plugin_notifybot_atall:
                    Message = [
                        Plain(text=GetSelfName() + "开播了！ " + self.RecorderInstance.GetRoomTitle() + "https://live.bilibili.com/" + self.RecorderInstance.room_id),
                        AtAll()
                    ]
                else:
                    Message = [
                        Plain(text=GetSelfName() + "开播了！ " + self.RecorderInstance.GetRoomTitle() + "https://live.bilibili.com/" + self.RecorderInstance.room_id),
                    ]
                try:
                    await SendGroupMsg(Grp, Message)
                except Exception as e:
                    self.PrintLog("Send QQ live notify message failed: " + repr(e))
                    traceback.print_exc()

        def SendLiveOnMessage():
            try:
                fut=asyncio.run_coroutine_threadsafe(SendLiveOnMessageAsync(),loop)
            except Exception as e:
                self.PrintLog("Send QQ live notify message failed: " + repr(e))
                traceback.print_exc()
            
        def ProcessLiveStartEvent(FileNameGen):
            t = threading.Thread(target = SendLiveOnMessage)
            t.daemon = True
            t.start()
        
        async def SendDiskWarningMessageAsync():
            for MgrQQ in Cfg().plugin_notifybot_manager_qq_number:
                try:
                    await app.sendFriendMessage(MgrQQ, MessageChain.create([
                        Plain(text="磁盘空间紧张！")
                    ]))   
                    await asyncio.sleep(2)
                except Exception as e:
                    self.PrintLog("Send disk warning message failed: " + repr(e))
                    traceback.print_exc()
        
        def DiskWarning():
            try:
                fut=asyncio.run_coroutine_threadsafe(SendDiskWarningMessageAsync(),loop)
            except Exception as e:
                self.PrintLog("Send disk warning message failed: " + repr(e))
                traceback.print_exc()
        
        self.app = app

        self.RecorderInstance.RegisterCallback("RecorderInstance", "OnLiveStart", ProcessLiveStartEvent)
        self.RecorderInstance.RegisterCallback("DiskSpaceMonitor", "OnWarning", DiskWarning)
        
        self.LastAnyLiveReportTime = {}
        self.LastTalkTime = {}
        self.OvertalkCounter = {}
        self.LastSentMsgId = {}
        self.LastRepeatMsg = {}
        for GrpNum in Cfg().plugin_notifybot_group_number:
            self.LastAnyLiveReportTime[GrpNum] = datetime.datetime.fromtimestamp(0)
            self.LastTalkTime[GrpNum] = datetime.datetime.now()
            self.OvertalkCounter[GrpNum] = 0
            self.LastSentMsgId[GrpNum] = 0
            self.LastRepeatMsg[GrpNum] = ""

        app.launch_blocking()
