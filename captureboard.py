# SPDX-FileCopyrightText: 2023 K.Agata
# SPDX-License-Identifier: GPL-3.0

import cv2
import time
"""
ラズパイに接続したキャプチャボードを処理する。
"""



def decode_fourcc(v):
    # https://amdkkj.blogspot.com/2017/06/opencv-python-for-windows-playing-videos_17.html
    v = int(v)
    return "".join([chr((v >> 8 * i) & 0xFF) for i in range(4)])


def screenshot(save_path='ss.jpg'):
    print('start screenshot')
    start = time.time()

    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 遅延削減対策
    time.sleep(0.3)

    print(
        f"[{decode_fourcc(cap.get(cv2.CAP_PROP_FOURCC))} "
        f"{cap.get(cv2.CAP_PROP_FPS):.1f}fps "
        f"{cap.get(cv2.CAP_PROP_FRAME_WIDTH):.0f}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT):.0f}]"
    )

    if not cap.isOpened():
        print('Could not open device.')
        return False

    for i in range(4):
        # dummy
        _, cv2_img = cap.read()

    ret, cv2_img = cap.read()
    if not ret:
        print('Could not get a screenshot.')
        return False

    # リサイズ
    # height = cv2_img.shape[0]
    # width = cv2_img.shape[1]
    # cv2_img = cv2.resize(cv2_img, (int(width * 0.5), int(height * 0.5)))

    # 保存
    # cv2.imwrite(save_path, cv2_img, [int(cv2.IMWRITE_JPEG_QUALITY), q])
    cv2.imwrite(save_path, cv2_img)

    # メモリ上で圧縮
    # ret, img = cv2.imencode(".jpg", cv2_img, (cv2.IMWRITE_JPEG_QUALITY, 10))
    # decoded = cv2.imdecode(cv2_img, flags=cv2.IMREAD_COLOR)

    cap.release()
    cv2.destroyAllWindows()

    end = time.time()

    print(f'done screenshot ({(end - start) * 1000:.2f}ms)')
    return True


if __name__ == '__main__':
    screenshot('test.jpg')