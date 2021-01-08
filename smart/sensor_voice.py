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
        self.wifi_ip = False
        self.server_conn = False
        self.show_text = ""
    
    def update_show_info(self, text=None, wifi_ip=None, server_conn=None)
        if not text is None:
            self.show_text = text
        if not wifi_ip is None:
            self.wifi_ip = wifi_ip
        if not server_conn is None:
            self.server_conn = server_conn
        self.show()

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
                    try:
                        explorer.smartconfig()
                        self.wifi_ip = self.explorer.get_ip()
                        self.update_show_info(server_conn=True)
                    except Exception:
                        print("--[ERROR] smartconfig fail")
                        self.update_show_info(wifi_ip="null", server_conn=False)
                    self.led_b.value(1)
                    self.smartconfiging = False

    def get_pannel(self):
        img = image.Image(size=(320, 240))
        img.draw_string(0,0, "WiFi:{}".format(self.wifi_ip), color=(255, 255, 255))
        img.draw_string(190,0, "Server:", color=(255, 255, 255))
        if self.server_conn:
            color = (0, 255, 0)
        else:
            color = (255, 0, 0)
        img.draw_circle(220, 15, 12, color=color, fill=True)
        return img

    def show(self):
        pos = (0, 40)
        color = (255, 255, 255)
        scale = 1
        img = self.get_pannel()
        img.draw_string(pos[0], pos[1], self.show_text, color=color, scale=scale)
        lcd.display(img)
        del img

    def init(self):
        print("reset...")
        text = "reset...\n"
        self.update_show_info(text=text)
        self.explorer.wifi_reset(self.wifi_rst_btn)
        print("reset ok")
        print("--config")
        text += "config...\n"
        self.update_show_info(text=text)
        explorer.config(product_key, device_name, device_key)
        print("--config ok")
        print("--connect")
        text += "connect server...\n"
        self.update_show_info(text=text)
        try:
            explorer.connect()
            self.update_show_info( server_conn=True)
            print("--connect expoler ok")
        except Exception as e:
            explorer.server_conn = False
            print("--connect expoler fail: ", e)
            explorer.need_report = False

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

