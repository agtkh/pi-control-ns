# SPDX-FileCopyrightText: 2023 K.Agata
# SPDX-License-Identifier: GPL-3.0

import cv2
import time

"""
ラズパイに接続したキャプチャボードを処理する。
"""

def screenshot(save_path='ss.jpg'):
    print('start screenshot')
    start = time.time()

    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 遅延削減対策

    time.sleep(0.2)
    if not cap.isOpened():
        print('Could not open device.')
        return None

    for i in range(100):
        ret, cv2_img = cap.read()
        if not ret: continue
        cnt_non_zero = cv2.countNonZero(cv2_img[0])
        # print(f'[{i:2d}] shape:{cv2_img.shape}, cnt non zero: {cnt_non_zero}')
        if cnt_non_zero > 0: break

    if not cnt_non_zero > 0:
        # タイムアウト
        print('Request timed out')
        return False

    # リサイズ
    # height = cv2_img.shape[0]
    # width = cv2_img.shape[1]
    # cv2_img = cv2.resize(cv2_img, (int(width * 0.5), int(height * 0.5)))

    # 保存
    q = 10
    cv2.imwrite(save_path, cv2_img, [int(cv2.IMWRITE_JPEG_QUALITY), q])

    # メモリ上で圧縮
    # ret, img = cv2.imencode(".jpg", cv2_img, (cv2.IMWRITE_JPEG_QUALITY, 10))
    # decoded = cv2.imdecode(cv2_img, flags=cv2.IMREAD_COLOR)

    cap.release()

    end = time.time()

    print(f'done screenshot ({(end - start) * 1000:.2f}ms)')
    return True

if __name__ == '__main__':
    screenshot('test.jpg')