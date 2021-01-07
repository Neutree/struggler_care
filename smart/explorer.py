import time



class Explorer_AT:
    def __init__(self, uart, on_control):
        self.uart = uart
        self.on_control = on_control
        self.msg = ""

    def connect(self):
        pass

    def report(self):
        pass

    def run(self):
        msg = self.uart.read()
        if msg:
            self.msg += msg.decode()
            print(self.msg)
    

if __name__ == "__main__":
    from Maix import GPIO
    from machine import UART
    from fpioa_manager import fm

    fm.register(0, fm.fpioa.GPIOHS1, force=True)
    wifi_io0_en=GPIO(GPIO.GPIOHS1, GPIO.OUT)
    wifi_io0_en.value(0)

    fm.register(7,fm.fpioa.UART2_TX)
    fm.register(6,fm.fpioa.UART2_RX)


    uart = UART(UART.UART2,115200,timeout=1000, read_buf_len=4096)

    print("wait 3s...")
    time.sleep_ms(3000)
    read = uart.read()
    print("ok")
    
    def on_control(msg):
        for key in msg:
            print("control {}:{}".format(key, msg[key]))

    explorer = Explorer_AT(uart, on_control)

    while 1:
        explorer.run()

