import time
import json
import ure
import image, lcd
from explorer import Explorer_AT:
from Maix import GPIO
from machine import UART
from fpioa_manager import fm


class App:
    def __init__(self, product_key, device_name, device_key):
        fm.register(8, fm.fpioa.GPIOHS1, force=True)
        fm.register(12, fm.fpioa.GPIOHS2, force=True)
        fm.register(16, fm.fpioa.GPIOHS3, force=True)
        fm.register(14, fm.fpioa.GPIOHS4, force=True)
        fm.register(7,fm.fpioa.UART2_TX)
        fm.register(6,fm.fpioa.UART2_RX)
        self.wifi_rst_btn=GPIO(GPIO.GPIOHS1, GPIO.OUT)
        self.led_g=GPIO(GPIO.GPIOHS2, GPIO.OUT)
        self.led_b=GPIO(GPIO.GPIOHS4, GPIO.OUT)
        self.button=GPIO(GPIO.GPIOHS3, GPIO.PULL_UP)
        self.uart = UART(UART.UART2,115200,timeout=1000, read_buf_len=4096)

        self.led_g.value(1)
        self.led_b.value(1)
        self.wifi_rst_btn.value(1)
        lcd.init()

        self.explorer = Explorer_AT(self.uart, self.on_control)
        self.smartconfiging = False
    
    def is_light_on():
        if self.led_g.value() == 0:
            return True
        return False
    
    def on_control(self, msg):
        for key in msg:
            print("control {}:{}".format(key, msg[key]))

    def main_loop(self):
        if button.value() == 0:
            time.sleep_ms(20)
            if button.value() == 0:
                if not self.smartconfiging:
                    self.smartconfiging = True
                    self.led_b.value(0)
                    explorer.smartconfig()
                    self.led_b.value(1)
                    self.smartconfiging = False

    def show_text(self, text, pos=(0, 115), color=(255, 255, 255), scale=2):
        img = image.Image(size=(320, 240))
        img.draw_string(pos[0], pos[1], text, color=color, scale=scale)
        lcd.display(img)

    def init(self):
        print("reset...")
        self.explorer.wifi_reset(self.wifi_rst_btn)
        print("reset ok")
        print("--config")
        explorer.config(product_key, device_name, device_key)
        print("--config ok")
        print("--connect")
        try:
            explorer.connect()
            print("--connect expoler ok")
        except Exception as e:
            print("--connect expoler fail: ", e)
            explorer.need_report = false

    def run(self):
        while 1:
            self.explorer.run()
            self.main_loop()






# print("--start smartconfig")
# explorer.smartconfig()

data = {
    "pm2_5": 0,
    "pm1_0": 0,
    "pm10": 0,
    "light": 0,
}


if __name__ == "__main__":
    app = App("1WAN4M5NPX", "device_01", "PHsWVCZkf9IaPnkhZkG4Rg==")
    while 1:
        try:
            app.init()
            app.run()
        except Exception as e:
            app.show_text(str(e), pos=(0,0), scale=1)

