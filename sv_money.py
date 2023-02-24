"""
Copyright(c) 2023 K.Agata
ポケモンSVでAボタン連打することで学校最強大会を周回して金策する。
30分ごとSlackにスクリーンショットを送って敗退していないか見る。
"""

import time, sys, os
import threading
from datetime import datetime
from . import switch
import cv2
import slack_sdk

slack_token = os.getenv('SLACK_API_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL_ID')

def screen_shot():
    print('screen shotting...')
    DEVICE_ID = 0
    CAP_WIDTH = 1920
    CAP_HEIGHT = 1080

    cap = cv2.VideoCapture(DEVICE_ID)

    if not cap:
        return False

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_HEIGHT)
    time.sleep(0.2)

    for i in range(100):
        ret, cv2_img = cap.read()
        if not ret: continue
        cnt_non_zero = cv2.countNonZero(cv2_img[0])
        print(f'[{i:2d}] shape:{cv2_img.shape}, cnt non zero: {cnt_non_zero}')
        if cnt_non_zero > 0: break

    # リサイズ
    # height = cv2_img.shape[0]
    # width = cv2_img.shape[1]
    # cv2_img = cv2.resize(cv2_img, (int(width * 0.5), int(height * 0.5)))

    # 保存
    q = 10
    cv2.imwrite("frame.jpg", cv2_img, [int(cv2.IMWRITE_JPEG_QUALITY), q])

    # メモリ上で圧縮
    # ret, img = cv2.imencode(".jpg", cv2_img, (cv2.IMWRITE_JPEG_QUALITY, 10))
    # decoded = cv2.imdecode(cv2_img, flags=cv2.IMREAD_COLOR)

    cap.release()

    time.sleep(0.2)
    print('done screen shot')
    return True


def send_to_slack():
    now = datetime.now()
    d_str = now.strftime('%Y/%m/%d %H:%M:%S')
    title = f'ss of pokemon sv at {d_str}'
    try:
        slack = slack_sdk.WebClient(token=slack_token)
        slack.files_upload_v2(channel=slack_channel,
                              file='frame.jpg',
                              title=title,
                              initial_comment=title)
    except slack_sdk.errors.SlackApiError as e:
        print('Slack APIのエラー', e)


def screen_shot_loop():
    while screen_shot():
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
