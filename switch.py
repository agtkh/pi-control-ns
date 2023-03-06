# SPDX-FileCopyrightText: 2023 K.Agata
# SPDX-License-Identifier: GPL-3.0
"""
This is free software.
"""

import os, sys
import threading
import time
from ctypes import LittleEndianStructure, c_uint8


class Con:

    class ControlStruct(LittleEndianStructure):
        # コントロールデータ構造体 (11bytes)
        _fields_ = [
            ('connection_info', c_uint8, 4), ('battery_level', c_uint8, 4),
            ('button_y', c_uint8, 1), ('button_x', c_uint8, 1),
            ('button_b', c_uint8, 1), ('button_a', c_uint8, 1),
            ('button_right_sr', c_uint8, 1), ('button_right_sl', c_uint8, 1),
            ('button_r', c_uint8, 1), ('button_zr', c_uint8, 1),
            ('button_minus', c_uint8, 1), ('button_plus', c_uint8, 1),
            ('button_thumb_r', c_uint8, 1), ('button_thumb_l', c_uint8, 1),
            ('button_home', c_uint8, 1), ('button_capture', c_uint8, 1),
            ('dummy', c_uint8, 1), ('charging_grip', c_uint8, 1),
            ('dpad_down', c_uint8, 1), ('dpad_up', c_uint8, 1),
            ('dpad_right', c_uint8, 1), ('dpad_left', c_uint8, 1),
            ('button_left_sr', c_uint8, 1), ('button_left_sl', c_uint8, 1),
            ('button_l', c_uint8, 1), ('button_zl', c_uint8, 1),
            ('analog', c_uint8 * 6), ('vibrator_input_report', c_uint8)
        ]

    def __init__(self,
                 mac_addr='00005e00535f',
                 usb_gadget_path='/sys/kernel/config/usb_gadget/pi-control-ns',
                 body_color='ff0000',
                 button_color='ffff00',
                 left_grip_color='00ff00',
                 right_grip_color='0000ff'):
        self.control_data = bytearray.fromhex('810000000008800008800c')
        self.control = self.ControlStruct.from_buffer(self.control_data)
        self.counter = 0
        self.mac_addr = mac_addr

        self.input_looping = False
        self.close_req = False
        self.base_path = usb_gadget_path
        self.badget = None

        self.spi_rom = {
            0x60:
            bytearray.fromhex('ffff ffff ffff ffff ffff ffff ffff ffff'
                              'ffff ffff ffff ffff ffff ff02 ffff ffff'
                              'ffff ffff ffff ffff ffff ffff ffff ffff'
                              'ffff ffff ffff ffff ffff ffff fff9 255f'
                              'b217 7903 665f 8357 7201 3661 0e56 66ff'
                              '2c2c c3d1 1515 0e62 27c1 c32c ffff ffff'
                              'ffff ffff ffff ffff ffff ffff ffff ffff'
                              'ffff ffff ffff ffff ffff ffff ffff ffff'
                              '50fd 0000 c60f 0f30 61ae 90d9 d414 5441'
                              '1554 c779 9c33 3663 0f30 61ae 90d9 d414'
                              '5441 1554 c779 9c33 3663'),
            0x80:
            bytearray.fromhex('ffff ffff ffff ffff ffff ffff ffff ffff'
                              'ffff ffff ffff ffff ffff ffff ffff ffff'
                              'ffff ffff ffff b2a1 aeff e7ff ec01 0040'
                              '0040 0040 eaff 0f00 0700 e73b e73b e73b')
        }

        # コントローラ色をカスタム
        self.spi_rom[0x60][0x50:0x53] = bytes.fromhex(body_color)  # body color
        self.spi_rom[0x60][0x53:0x56] = bytes.fromhex(
            button_color)  # button color
        self.spi_rom[0x60][0x56:0x59] = bytes.fromhex(
            left_grip_color)  # left grip color
        self.spi_rom[0x60][0x59:0x5c] = bytes.fromhex(
            right_grip_color)  # right grip color

    def start(self):
        # Re-connect USB Gadget device
        os.system(f'echo > {self.base_path}/UDC')
        os.system(f'ls /sys/class/udc > {self.base_path}/UDC')
        time.sleep(0.8)

        self.gadget = os.open('/dev/hidg0', os.O_RDWR | os.O_NONBLOCK)

        self.reset_magic_packet()

        threading.Thread(target=self.countup).start()
        threading.Thread(target=self.interact_loop).start()

        while not self.input_looping:
            # 通信が始まるまで待機
            time.sleep(0.1)

    def close(self):
        """
        コントローラーを停止する
        """
        self.input_looping = False
        self.close_req = True
        time.sleep(0.5)

        os.close(self.gadget)
        os.system(f'echo > {self.base_path}/UDC')

    def button(self, key, value):
        """
        ボタンの状態の変更や状態の取得用の関数
        """
        if getattr(self.control, key, None) == None:
            print(f'[{key}] is not found.')
            return
        setattr(self.control, key, value)

    def push_button(self, key, hold=0.2, delay=0.2):
        self.control.charging_grip = 1
        self.button(key, 1)
        time.sleep(hold)
        self.button(key, 0)
        time.sleep(delay)

    def reset_magic_packet(self):
        # reset magic packet
        self.usb_send(0x81, 0x03, bytes([]))
        time.sleep(0.05)
        self.usb_send(0x81, 0x01, bytes([0x00, 0x03]))
        time.sleep(0.05)

    def countup(self):
        """カウンターを増やす"""
        while not self.close_req:
            self.counter = (self.counter + 3) % 256
            time.sleep(0.03)

    def pack_shorts(self, short1: int, short2: int) -> int:
        # """2つの12bit(1.5byte)値を3byteのバイト列にする"""
        data = bytearray(3)
        data[0] = short1 & 0xff
        data[1] = ((short2 << 4) & 0xf0) | ((short1 >> 8) & 0x0f)
        data[2] = (short2 >> 4) & 0xff
        return data

    def gen_input_data(self, all_clear=False):
        self.control.battery_level = 0x8
        self.control.connection_info = 0x1

        # アナログスティック
        lx_val = round((1 + 0.0) * 2047.5)  # 12bit(1.5byte)
        ly_val = round((1 + 0.0) * 2047.5)  # 12bit(1.5byte)
        rx_val = round((1 + 0.0) * 2047.5)  # 12bit(1.5byte)
        ry_val = round((1 + 0.0) * 2047.5)  # 12bit(1.5byte)
        analog_left = self.pack_shorts(lx_val, ly_val)  # 3バイト
        analog_right = self.pack_shorts(rx_val, ry_val)  # 3バイト
        self.control.analog[0] = analog_left[0]
        self.control.analog[1] = analog_left[1]
        self.control.analog[2] = analog_left[2]
        self.control.analog[3] = analog_right[0]
        self.control.analog[4] = analog_right[1]
        self.control.analog[5] = analog_right[2]

        self.control.vibrator_input_report = 0x0c

        return bytearray(self.control)

    def usb_send(self, report_id: int, cmd: int, data: bytes):
        """
        report_id:
            0x21: コントローラー入力 + UART応答
            0x30: コントローラー入力のみ
        """

        buf = bytearray([report_id, cmd])
        buf.extend(data)
        buf.extend(bytearray(64 - len(buf)))
        try:
            os.write(self.gadget, buf)
            # print('W:' + buf.hex())
        except BlockingIOError as e:
            # print('except3:', e)
            # バッファが一杯
            pass
        except BrokenPipeError as e:
            print(f'except4:', e)
            pass
        except Exception as e:
            print("except1:", e)
            os._exit(1)

    def uart_send(self, code, subcmd, data):
        # buf = self.gen_input_data(all_clear=True)
        buf = self.control_data.copy()
        buf.extend([code, subcmd])
        buf.extend(data)
        # 0x21: コントローラー入力+UART応答
        self.usb_send(0x21, self.counter, buf)

    def spi_send(self, addr: bytes, data):
        buf = bytearray(addr)
        buf.extend([0x00, 0x00, len(data)])
        buf.extend(data)
        self.uart_send(0x90, 0x10, buf)

    def send_input_loop(self):
        while self.input_looping and not self.close_req:
            # buf = self.gen_input_data()
            buf = self.control_data
            # 0x30: コントローラー入力のみ
            self.usb_send(0x30, self.counter, buf)
            time.sleep(0.03)

    def read_spi_rom(self, spi_addr: bytes, data_len):
        """SPIでのROMの読み込み"""
        try:
            addr1 = spi_addr[1]
            addr2 = spi_addr[0]
            return self.spi_rom[addr1][addr2:addr2 + data_len]
        except IndexError:
            print(f'{spi_addr}({data_len}) is not found')
            return None

    def uart_interact(self, subcmd, data):
        """UARTでの対話"""
        if subcmd == 0x01:
            # Bluetooth manual pairing
            self.uart_send(0x81, subcmd, [0x03, 0x01])
        elif subcmd == 0x02:
            # Request device info
            self.uart_send(
                0x82, subcmd,
                bytes.fromhex('0421 03 02' + self.mac_addr[::-1] + '03 02'))
        elif subcmd == 0x03 or subcmd == 0x08 or subcmd == 0x30 or subcmd == 0x38 or subcmd == 0x40 or subcmd == 0x48:
            self.uart_send(0x80, subcmd, [])
        elif subcmd == 0x04:
            # Trigger buttons elapsed time
            self.uart_send(0x83, subcmd, [])
        elif subcmd == 0x21:
            # Set NFC/IR MCU configuration
            self.uart_send(0xA0, subcmd, bytes.fromhex('0100ff0003000501'))
        elif subcmd == 0x10:
            # SPI flash read
            spi_addr = data[:2]
            data_len = data[4]
            rom_data = self.read_spi_rom(spi_addr, data_len)
            if rom_data != None:
                self.spi_send(spi_addr, rom_data)
        else:
            print('>>> [UART]', subcmd, data.hex())

    def interact_loop(self):
        """
        対話の繰り返し
        """
        while not self.close_req:
            try:
                data = os.read(self.gadget, 128)
                # print('R:' + data.hex())
                if data[0] == 0x80:
                    if data[1] == 0x01:
                        # MACアドレスの要求
                        print('MACアドレスが要求された')
                        self.usb_send(0x81, data[1],
                                      bytes.fromhex('0003' + self.mac_addr))
                    elif data[1] == 0x02:
                        print('ハンドシェイク')
                        self.usb_send(0x81, data[1], [])
                    elif data[1] == 0x03:
                        print('baudrate設定', data[2:].hex())
                    elif data[1] == 0x04:
                        # Enable USB HID Joystick report
                        print('送信の開始の指示された')
                        self.input_looping = True
                        threading.Thread(target=self.send_input_loop).start()
                    elif data[1] == 0x05:
                        # Disable USB HID Joystick report
                        print('送信の終了の指示')
                        self.input_looping = False
                    else:
                        print('>>>', data.hex())
                elif data[0] == 0x01 and len(data) > 16:  # UARTで届いた
                    subcmd = data[10]
                    self.uart_interact(subcmd, data[11:])
                elif data[0] == 0x10 and len(data) == 10:
                    pass
                else:
                    print('>>>', data.hex())
            except BlockingIOError as e:
                # print("except5:", e)
                pass
            # except Exception as e:
            #     print("except2:", e)
            #     os._exit(1)


if __name__ == '__main__':
    try:
        con = Con()
        con.start()

        while True:
            btn = input('key:')
            con.push_button(btn, delay=0.2)

    except KeyboardInterrupt as e:
        print("\nCtrl-Cなどで終了")

    except Exception as e:
        print(f'不明なエラー[{e}]')

    finally:
        con.close()
        sys.exit()
