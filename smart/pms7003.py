from fpioa_manager import fm
from board import board_info
from machine import UART
import ustruct
import time

class PMS7003:
    def __init__(self, uart_obj, on_data):
        self.uart = uart_obj
        self.on_data = on_data
        self.data_mode_active = None
        self.keys = [
            # μg/m3 CF=1, Standard particles
            "pm1.0",
            "pm2.5",
            "pm10" ,
            # μg/m3 Atmospheric 
            "pm1.0_atm",
            "pm2.5_atm",
            "pm10_atm",
            # Number of particles with a diameter of `x` um or more in 0.1 liter of air
            "num0.3um",
            "num0.5um",
            "num1.0um",
            "num2.5um",
            "num5.0um",
            "num10um",
            "version",
            "err_code"]


    def run(self):
        read_data = None
        if self.data_mode_active is None:
            self.set_data_mode(active = True)
            self.data_mode_active = True
        elif self.data_mode_active:
            if self.uart.any():
                read_data = self.uart.read()

        else:
            read_data = self.read_passive()
        if read_data:
            data = self._decode(read_data)
            if data and self.on_data:
                self.on_data(data)

    def read_passive(self):
        cmd = b'\x42\x4d\xe2\x00\x00'
        ack = self._send_cmd(cmd)
        print("read_passive ack:", ack)
        return ack
        # if ack:
        #     return self._decode(ack)
        # return None
    
    def _send_cmd(self, cmd):
        parity = sum(list(cmd)) % 0xffff
        parity = ustruct.pack(">H", parity)
        cmd += parity
        print("send:", cmd)
        sent_len = self.uart.write(cmd)
        if sent_len != len(cmd):
            raise Exception("uart write fail")
        time.sleep_ms(10)
        ack = self.uart.read(32)
        return ack

    def set_data_mode(self, active):
        if active:
            cmd = b'\x42\x4d\xe1\x00\x01'
        else:
            cmd = b'\x42\x4d\xe1\x00\x00'
        ack = self._send_cmd(cmd)
        print("ack:", ack)
        self.data_mode_active = active
    
    def set_power_mode(self, low_power):
        if low_power:
            cmd = b'\x42\x4d\xe4\x00\x00'
        else:
            cmd = b'\x42\x4d\xe4\x00\x01'
        ack = self._send_cmd(cmd)
        print("ack:", ack)

    def _decode(self, raw_data):
        data = None
        data = ustruct.unpack(">HHHHHHHHHHHHHHBBH",raw_data)
        if data[0] == 0x424d:
            parity = sum(list(raw_data)[:-2]) % 0xffff
            if parity != data[16]:
                print("check parity error: {}--{}".format(parity, data[15]))
                return None
            print(data)
            data = data[2:-1]
            data = dict(zip(self.keys, data))
        return data

if __name__ == "__main__":
    fm.register(24, fm.fpioa.UART1_TX, force=True)
    fm.register(25, fm.fpioa.UART1_RX, force=True)
    uart = UART(UART.UART1, 9600, 8, 0, 0, timeout=1000, read_buf_len=1024)

    def on_data(data):
        print(data)

    pms7003 = PMS7003(uart, on_data)
    pms7003.set_power_mode(low_power = False)
    pms7003.set_data_mode(active = True)
    while 1:
        pms7003.run()

