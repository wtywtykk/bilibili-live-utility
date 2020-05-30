room_name = "xxxx"

tasks_after_record = ["Task_AudioExtractor", "Task_VideoFixer"]

polling_check_interval = 60

disk_warning_threshold = 14 * 1024 * 1024 * 1024

plugin_danmakutimestamp_whitelist = []
plugin_danmakutimestamp_keyword = [".."]

plugin_notifybot_qq_number = 123456
plugin_notifybot_authkey = "AUTHKEY"
plugin_notifybot_group_number = [123456]
plugin_notifybot_manager_qq_number = [123456]
plugin_notifybot_mirai_api_http_locate = 'localhost:8080/' # websocket模式好像有问题，不要用
plugin_notifybot_atall = False
plugin_notifybot_say_selfname = ["xxx", "xxxxxx"]
plugin_notifybot_recognise_selfname = ["xxxxxxx"]
plugin_notifybot_conversations = [
    [
        ["keyword"],
        [
            [1 , "reply"],
            [0.3 , "reply2"]
        ]
    ]
]

ffmpeg_path = "./ffmpeg-4.2.2-amd64-static/ffmpeg"
