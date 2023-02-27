# SPDX-FileCopyrightText: 2023 K.Agata
# SPDX-License-Identifier: GPL-3.0
"""
ポケモンSVでAボタン連打することで学校最強大会を周回して金策する。
30分ごとSlackにスクリーンショットを送って敗退していないか見る。
"""

import time, sys, os
import threading
from datetime import datetime
from . import switch
from . import captureboard as cb
import slack_sdk

SLACK_TOKEN = os.getenv('SLACK_API_TOKEN')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL_ID')


def send_msg_to_slack(msg_text):
    try:
        slack_cl = slack_sdk.WebClient(token=SLACK_TOKEN)
        slack_cl.chat_postMessage(text=msg_text, channel=SLACK_CHANNEL)
    except slack_sdk.errors.SlackApiError as e:
        print('Slack APIのエラー', e)


def send_img_to_slack(msg_text, file_path='ss.jpg'):
    try:
        slack_cl = slack_sdk.WebClient(token=SLACK_TOKEN)
        slack_cl.files_upload_v2(channel=SLACK_CHANNEL,
                                 file=file_path,
                                 title=msg_text,
                                 initial_comment=msg_text)
    except slack_sdk.errors.SlackApiError as e:
        print('Slack APIのエラー', e)


def screen_shot_loop():
    while True:
        if cb.screenshot('ss.jpg'):
            date_str = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            send_img_to_slack(date_str, 'ss.jpg')
        time.sleep(60 * 30)  # 30 mins



if __name__ == '__main__':
    keymap = {
        'x': 'button_x',
        'y': 'button_y',
        'h': 'button_home',
        'c': 'button_capture',
        '': 'button_a',
        ' ': 'button_b',
        '\x1b': 'button_home',
        '\x1b[C': 'dpad_right',
        '\x1b[D': 'dpad_left',
        '\x1b[A': 'dpad_up',
        '\x1b[B': 'dpad_down',
        'd': 'dpad_right',
        'a': 'dpad_left',
        'w': 'dpad_up',
        's': 'dpad_down',
        '-': 'button_minus',
        '=': 'button_plus',
        '+': 'button_plus',
    }
    try:
        con = switch.Con()
        con.start()

        while True:
            # 自由に操作
            btn = input('key:')
            if btn == 'start':
                # 自由な操作をやめて、マクロループに移行
                break
            key = keymap.get(btn, btn).lower()
            con.push_button(key, delay=0.2)

        # 定期的にスクリーンショットを送る
        h = threading.Thread(target=screen_shot_loop)
        h.start()

        while True:
            # マクロループ開始
            con.push_button('button_a', delay=0.2)

    except KeyboardInterrupt as e:
        print("\nCtrl-Cなどで終了")
    except Exception as e:
        print('不明なエラー', e)
    finally:
        con.close()
        sys.exit()
