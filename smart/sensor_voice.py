import time
import json
import ure



class Explorer_AT:
    def __init__(self, uart, on_control):
        self.uart = uart
        self.on_control = on_control
        self.msg = b""
        self.product_key = None
        self.device_name = None
        self.device_key = None
        self.send_id = 0
        self.need_report = True
    
    def config(self, product_key, device_name, device_key):
        cmd = 'AT+TCDEVINFOSET=1,"{}","{}","{}"'.format(
            product_key, device_name, device_key
        )
        self.product_key = product_key
        self.device_name = device_name
        self.device_key = device_key
        ack = self._cmd(cmd, ["+TCDEVINFOSET:OK"], timeout=3)

    def smartconfig(self):
        cmd_stop = "AT+TCSTOPSMART"
        cmd_start = "AT+TCSTARTSMART"
        # print("--now stop smartconfig")
        # ack = self._cmd(cmd_stop, "OK", timeout=3) # this will cause reboot
        print("--now start smartconfig")
        ack = self._cmd(cmd_start, ["+TCSTARTSMART:WIFI_CONNECT_SUCCESS"], timeout=60)
        print("--now smartconfig end")

    def connect(self):
        cmd = "AT+TCMQTTCONN=1,5000,240,1,1"
        cmd_sub = 'AT+TCMQTTSUB="$thing/down/property/{}/{}",0'.format(self.product_key, self.device_name)
        ack = self._cmd(cmd, ["+TCMQTTCONN:OK"], timeout=10)
        ack = self._cmd(cmd_sub, ["+TCMQTTSUB:OK"], ["+TCMQTTSUB:FAIL", "ERROR"], timeout=10)


    def report(self, data):
        data = json.dumps(data)
        cmd = '{}"clientToken": "msgpub-token-{}", "method": "report", "params": {}{}'.format(
             "{", "{:012d}".format(self.send_id),
            data, "}"
        )
        cmd = cmd.replace('"', '\\"')
        cmd = cmd.replace(',', '\\,')
        cmd = 'AT+TCMQTTPUB="$thing/up/property/{}/{}",1,"{}"'.format(self.product_key, self.device_name, cmd)
        self.send_id += 1
        ack = self._cmd(cmd, ["+TCMQTTPUB:OK"], timeout=10)

    def _cmd(self, cmd, expected=[], fail_ack=["ERROR"], timeout=6):
        cmd += "\r\n"
        self.uart.read()
        self.uart.write(cmd.encode())
        ack = ""
        t = time.ticks_ms()
        while 1:
            read = self.uart.read()
            if read:
                try:
                    read = read.decode()
                    ack += read
                except Exception as e:
                    print("decode error: {}".format(read))
                for msg in expected:
                    if msg in ack:
                        return ack
                for msg in fail_ack:
                    if msg in ack:
                        break
            if time.ticks_ms() - t > timeout * 1000:
                break
        raise Exception("cmd ack error: {}, ack: {}".format(cmd, ack))

    def run(self):
        if self.need_report:
            print("--report:", data)
            data['pm10'] += 1
            explorer.report(data)
            print("--report success")
            self.need_report = False
        msg = self.uart.read()
        if msg:
            self.msg += msg
            idx = self.msg.find(b"+TCMQTTRCVPUB:")
            if idx >= 0:
                self.msg = self.msg[idx:]
                print("--", self.msg)
                idx = self.msg.find(b'}"\r\n') + 2
                if idx >= 0:
                    pub_msg = self.msg[:idx]
                    try:
                        pub_msg = pub_msg.decode()
                        mat = ure.match('.*"params":(.*)}".*', pub_msg)
                        if mat:
                            pub_msg = mat.group(1)
                        else:
                            raise Exception("find json data fail")
                        pub_msg = json.loads(pub_msg)
                    except Exception as e:
                        print(e)
                        print("--[error] pub msg decode error:{}".format(pub_msg))
                        pub_msg = None
                    if pub_msg:
                        self.on_control(pub_msg)
                    self.msg = self.msg[idx+2:] # remove "+TCMQTTRCVPUB:...\r\n"

def main_loop():
    pass

if __name__ == "__main__":
    from Maix import GPIO
    from machine import UART
    from fpioa_manager import fm

    fm.register(8, fm.fpioa.GPIOHS1, force=True)
    fm.register(12, fm.fpioa.GPIOHS2, force=True)
    wifi_rst=GPIO(GPIO.GPIOHS1, GPIO.OUT)
    led_g=GPIO(GPIO.GPIOHS2, GPIO.OUT)
    led_g.value(1)
    wifi_rst.value(0)
    t = time.ticks_ms()
    def wifi_reset(uart):
        wifi_rst.value(0)
        time.sleep_ms(200)
        wifi_rst.value(1)
        read = b""
        while 1:
            time.sleep_ms(100)
            msg = uart.read()
            if msg:
                read += msg
                if b"ready\r\n" in read:
                    break
            if time.ticks_ms() - t > 5000:
                raise Exception("reset timeout")

    def is_light_on():
        if led_g.value() == 0:
            return True
        return False

    fm.register(7,fm.fpioa.UART2_TX)
    fm.register(6,fm.fpioa.UART2_RX)


    uart = UART(UART.UART2,115200,timeout=1000, read_buf_len=4096)

    print("reset...")
    wifi_reset(uart)
    read = uart.read()
    print("reset ok")
    
    def on_control(msg):
        for key in msg:
            print("control {}:{}".format(key, msg[key]))

    explorer = Explorer_AT(uart, on_control)
    print("--config")
    explorer.config("1WAN4M5NPX", "device_01", "PHsWVCZkf9IaPnkhZkG4Rg==")
    # print("--start smartconfig")
    # explorer.smartconfig()
    print("--connect")
    explorer.connect()
    data = {
        "pm2_5": 0,
        "pm1_0": 0,
        "pm10": 0,
        "light": is_light_on(),
    }
    print("--connect ok")

    while 1:
        explorer.run()
        main_loop()



