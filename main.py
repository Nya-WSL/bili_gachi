from nicegui import ui, app
from router import Router
from log import logger

import bili_auth_web as bili_auth
import os, requests, uuid, datetime, json, re

if not os.path.exists("config.json"):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump({"uid": 0}, f, ensure_ascii=False, indent=4)

def format_time(seconds):
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}时{minutes:02d}分{seconds:02d}秒"

def get_data():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    url = "https://api.live.bilibili.com/xlive/general-interface/v1/guard/GuardActive"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
        "Cookie": app.storage.user.get("SESSDATA", 0)
    }

    params = {
        "platform": "android",
        "ruid": config.get("uid", "")
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["code"] == 0:
            total_time = data["data"]["watch_time"]
            data_label.set_content(f'主播：{data["data"]["rusername"]}<br>用户：{data["data"]["username"]}<br>观看时长: {format_time(total_time)}<br>弹幕数量：{data["data"]["send_bar"]}条<br>上舰后牌子等级👇<br>舰长：{data["data"]["up_medal"]["guard_level_3"]["level"]} | 提督：{data["data"]["up_medal"]["guard_level_2"]["level"]} | 总督：{data["data"]["up_medal"]["guard_level_1"]["level"]}')
        else:
            data_label.set_content(f"获取时长失败: {data['message']}")
    else:
        data_label.set_content("请求失败，请稍后再试")

def main():
    router = Router()
    page_id = f"{uuid.uuid4()}-{datetime.datetime.now().timestamp()}"

    @router.add('/')
    def index():
        router.open(step)

    @router.add('/nicegui/')
    def index():
        router.open(step)

    @router.add(f'/{page_id}')
    def step():
        global data_label

        def check_auth(loginInfo):
            status = bili_auth.login(loginInfo[0])

            if status == True:
                ui.notify("登录成功", type="positive")
                try:
                    os.remove(loginInfo[1])
                    logger.debug(f"删除{loginInfo[1]}成功")
                except:
                    logger.warning(f"删除{loginInfo[1]}失败")

                get_data()
                stepper.next()

            else:
                ui.notify(status, type="negative")

        def bili_login():
            global qrcode_ui

            auth_button.set_visibility(False)
            loginInfo = bili_auth.get_qrcode("bili_qrcode")

            with auth_step:
                qrcode_ui = ui.image(loginInfo[1])
                ui.label("请使用B站APP扫描二维码登录")
                ui.label("扫码后点击下一步")

                with ui.stepper_navigation():
                    ui.button('下一步', on_click=lambda: check_auth(loginInfo))

        if app.storage.user.get("SESSDATA", "") == "":
            app.storage.user["SESSDATA"] = ""

        with ui.stepper().props('vertical').classes('absolute-center') as stepper:
            # with ui.step('主播UID'):
            #     uid = ui.input("UID")
            #     with ui.stepper_navigation():
            #         ui.button('下一步', on_click=stepper.next)

            with ui.step('登录B站') as auth_step:
                auth_button = ui.button("扫码登录", on_click=lambda: bili_login())

            with ui.step('查看时长'):
                data_label = ui.markdown()
                with ui.stepper_navigation():
                    ui.button('完成', on_click=lambda: ui.navigate.to("/"))

        app.on_disconnect(app.storage.user.clear())

    router.frame().classes('w-full')

@ui.page('/')
def index():
    main()

def remove_qrcode():
    now = datetime.datetime.now()
    if now.minute == 0 or now.minute == 30:
        for file in os.listdir(os.getcwd()):
            if re.match(r'bili_qrcode_*', file):
                try:
                    os.remove(file)
                    logger.debug(f"删除{file}成功")
                except:
                    logger.warning(f"删除{file}失败")

ui.timer(60, lambda: remove_qrcode()) # 定时清理二维码文件

ui.run(title="时长姬", port=65100, storage_secret="Nya-WSL", reload=False, show=False)