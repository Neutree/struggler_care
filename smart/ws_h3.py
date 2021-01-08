from fpioa_manager import fm
from board import board_info
from machine import UART
import ustruct
import time

class WS_H3:
    def __init__(self, uart_obj, on_data):
        self.uart = uart_obj
        self.on_data = on_data
        self.data_mode_active = None
        self.active_keys = [
            "name",
            "unit",
            "precision",
            "value",
            "range"
            ]
        self.passive_keys = [
            "cmd",
            "value_ug_m3",
            "rsv",
            "value_ppb"
            ]


    def run(self):
        data = None
        if self.data_mode_active is None:
            # self.set_data_mode(active = True)
            self.data_mode_active = True
        elif self.data_mode_active:
            if self.uart.any():
                read_data = self.uart.read()
                data = self._decode_active(read_data)
                if data["name"] == 0x17:
                    data["name"] = "CH2O"
                if data["unit"] == 0x04:
                    data["unit"] = "ppb"
        else:
            read_data = self.read_passive()
            data = self._decode_passive(read_data)
        if data:
            if self.on_data:
                self.on_data(data)

    def read_passive(self):
        cmd = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'
        return self._send_cmd(cmd)

    def parity(self, raw_data):
        parity = (~(sum(list(raw_data)) % 256) + 1) % 256
        return parity

    def _send_cmd(self, cmd, parity=False, read_len=9):
        if parity:
            parity = self.parity(cmd[1:])
            parity = ustruct.pack(">H", parity)
            cmd += parity
        print("send:", cmd)
        sent_len = self.uart.write(cmd)
        if sent_len != len(cmd):
            raise Exception("uart write fail")
        time.sleep_ms(10)
        ack = self.uart.read(read_len)
        return ack

    def set_data_mode(self, active):
        if active:
            cmd = b'\xFF\x01\x78\x40\x00\x00\x00\x00\x47'
        else:
            cmd = b'\xFF\x01\x78\x41\x00\x00\x00\x00\x46'
        ack = self._send_cmd(cmd)
        print("ack:", ack)
        self.data_mode_active = active
    
    def _decode_active(self, raw_data, ):
        unpack_fmt = ">BBBBHHB",
        keys = self.active_keys
        parity_idx = 6
        return self._decode(raw_data, unpack_fmt, keys, parity_idx)
    
    def _decode_passive(self, raw_data):
        unpack_fmt = ">BBHHHB"
        keys = self.passive_keys
        parity_idx = 5
        return self._decode(raw_data, unpack_fmt, keys, parity_idx)
    
    def _decode(self, raw_data, unpack_fmt, keys, parity_idx):
        data = None
        print("raw data:", raw_data)
        try:
            data = ustruct.unpack(unpack_fmt,raw_data)
        except Exception:
            return None
        if data[0] == 0xFF:
            parity = self.parity(raw_data[1:-1])
            if parity != data[parity_idx]:
                print("check parity error: {}--{}".format(parity, data[parity_idx]))
                return None
            print("decode data:", data)
            data = data[1:-1]
            data = dict(zip(keys, data))
        return data

if __name__ == "__main__":
    import lcd, image

    lcd.init()

    fm.register(33, fm.fpioa.UART1_TX, force=True)
    fm.register(34, fm.fpioa.UART1_RX, force=True)
    uart = UART(UART.UART1, 9600, 8, 0, 0, timeout=1000, read_buf_len=1024)

    def on_data(data):
        print(data)
        img = image.Image(size=(320, 240))
        img.draw_string(6, 110, "CH2O:{}ppb,{}ug/m3".format(data["value_ppb"], data["value_ug_m3"]), scale=2, color=(255, 255, 255))
        lcd.display(img)

    ws_h3 = WS_H3(uart, on_data)
    # ws_h3.set_power_mode(low_power = False)
    ws_h3.set_data_mode(active = False)
    cmd = b'\xFF\x01\x78\x40\x00\x00\x00\x00\x47'
    ws_h3.parity(cmd[1:-1])
    while 1:
        ws_h3.run()

