import time
import json
import ure
import image, lcd
from explorer import Explorer_AT
from Maix import GPIO
from machine import UART
from fpioa_manager import fm


class App:
    def __init__(self, product_key, device_name, device_key, product_secret=None):
        self.product_key = product_key
        self.device_name = device_name
        self.device_key = device_key
        self.product_secret = product_secret

        fm.register(8, fm.fpioa.GPIOHS1, force=True)
        fm.register(12, fm.fpioa.GPIOHS2, force=True)
        fm.register(16, fm.fpioa.GPIOHS3, force=True)
        fm.register(14, fm.fpioa.GPIOHS6, force=True)
        fm.register(7,fm.fpioa.UART2_TX)
        fm.register(6,fm.fpioa.UART2_RX)
        self.wifi_rst_btn=GPIO(GPIO.GPIOHS1, GPIO.OUT)
        self.led_g=GPIO(GPIO.GPIOHS2, GPIO.OUT)
        self.led_b=GPIO(GPIO.GPIOHS6, GPIO.OUT)
        self.button=GPIO(GPIO.GPIOHS3, GPIO.PULL_UP)
        self.uart = UART(UART.UART2,115200,timeout=1000, read_buf_len=4096)

        self.led_g.value(1)
        self.led_b.value(1)
        self.wifi_rst_btn.value(1)
        lcd.init()

        self.explorer = Explorer_AT(self.uart, self.on_control)
        self.smartconfiging = False
        self.wifi_ip = ""
        self.server_conn = False
        self.show_text = ""
        self.button_down_t = -1

    def show(self, text=None, wifi_ip=None, server_conn=None, append=False, print_text=True):
        if not text is None:
            if append:
                self.show_text += text
            else:
                self.show_text = text
            if print_text:
                print(text)
        if not wifi_ip is None:
            self.wifi_ip = wifi_ip
        if not server_conn is None:
            self.server_conn = server_conn
        self.show_update()

    def is_light_on(self):
        if self.led_g.value() == 0:
            return True
        return False
    
    def set_light(self, on):
        self.led_g.value(0 if on else 1)
    
    def set_hint_led(self, on):
        self.led_b.value(0 if on else 1)

    def on_control(self, msg):
        for key in msg:
            print("control {}:{}".format(key, msg[key]))

    def try_connect(self):
        ip = self.explorer.get_ip()
        self.show(wifi_ip=ip)
        print("IP:", ip)
        if ip:
            text = "config...\n"
            self.show(text=text, print_text=True)
            self.explorer.config(self.product_key, self.device_name, self.device_key, self.product_secret)
            text ="--config ok"
            self.show(text=text, append=True, print_text=True)
            text = "connect to server...\n"
            self.show(text=text, append=True, print_text=True)
            try:
                self.explorer.connect()
                self.show(text="connect to server ok", server_conn=True, append=True, print_text=True)
                self.explorer.need_report = True
            except Exception as e:
                self.explorer.server_conn = False
                print("--connect expoler fail: ", e)
                self.show(text="connect server fail", server_conn=False, append=True, print_text=True)
        else:
            print("no IP, wait or long push func button to start config WiFi")
            text = "Wait or long push button to config WiFi\n"
            self.show(text=text)

    def main_loop(self):
        if not self.wifi_ip:
            time.sleep_ms(500)
            self.try_connect()

        if self.button.value() == 0:
            time.sleep_ms(20)
            if self.button.value() == 0:
                if self.button_down_t < 0:
                    self.button_down_t = time.ticks_ms()
                else:
                    if time.ticks_ms() - self.button_down_t > 5000:
                        if not self.smartconfiging:
                            self.smartconfiging = True
                            self.set_hint_led(True)
                            text = "start smartconfig, use mobilephone to config"
                            print(text)
                            self.show(text=text)
                            try:
                                self.explorer.smartconfig()
                                wifi_ip = self.explorer.get_ip()
                                print("-- smartconfig success, ip:", wifi_ip)
                                self.show(wifi_ip=wifi_ip, server_conn=True)
                            except Exception:
                                print("--[ERROR] smartconfig fail")
                                self.show(wifi_ip="null", server_conn=False)
                            self.set_hint_led(False)
                            self.smartconfiging = False
        else:
            self.button_down_t = -1

    def get_pannel(self):
        img = image.Image(size=(320, 240))
        img.draw_string(0,0, "IP:{}".format(self.wifi_ip), color=(255, 255, 255))
        img.draw_string(110,0, "[{}]".format(self.device_name), color=(255, 255, 255))
        img.draw_string(250,0, "Server:", color=(255, 255, 255))
        if self.server_conn:
            color = (0, 255, 0)
        else:
            color = (255, 0, 0)
        img.draw_circle(300, 7, 6, color=color, fill=True)
        return img

    def show_update(self):
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
        self.show(text=text)
        self.explorer.wifi_reset(self.wifi_rst_btn)
        print("reset ok")
        if not self.device_name:
            mac = self.explorer.get_mac()
            if not mac:
                raise Exception("can not get MAC address")
            self.device_name = mac.replace(":", "_")
        print("device name:", self.device_name)

        # print("reset config")
        # self.explorer.restore_config()
        # print("reset config ok")

    def run(self):
        while 1:
            self.explorer.run()
            self.main_loop()


if __name__ == "__main__":
    # app = App("1WAN4M5NPX", None, None, "5aSx6oJozEh2rT9CtAIlzVeI")
    # app = App("1WAN4M5NPX", "device_01", "JvTXVmtGJQXVBboVCFRTDQ==")
    app = App("1WAN4M5NPX", "device_02", "vQsu7B6unW+p4fxSZWUBRg==")
    app.data = {
        "pm2_5": 0,
        "pm1_0": 0,
        "pm10": 0,
        "light": 0,
    }
    while 1:
        try:
            app.init()
            app.run()
        except Exception as e:
            import uio
            import sys
            err_str = uio.StringIO()
            sys.print_exception(e, err_str)
            err_str = err_str.getvalue()
            print(err_str)
            app.show( text=str(err_str))
            time.sleep(5)
            while 1:
                pass

