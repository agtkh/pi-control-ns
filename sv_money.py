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

slack_token = os.getenv('SLACK_API_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL_ID')


def send_to_slack():
    now = datetime.now()
    d_str = now.strftime('%Y/%m/%d %H:%M:%S')
    title = f'ss of pokemon sv at {d_str}'
    try:
        slack = slack_sdk.WebClient(token=slack_token)
        slack.files_upload_v2(channel=slack_channel,
                              file='ss.jpg',
                              title=title,
                              initial_comment=title)
    except slack_sdk.errors.SlackApiError as e:
        print('Slack APIのエラー', e)


def screen_shot_loop():
    while True:
        if cb.screenshot('ss.jpg'):
            send_to_slack()
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
