import time
import json
import ure



class Explorer_AT:
    def __init__(self, uart, on_msg):
        self.uart = uart
        self.on_msg = on_msg
        self.msg = b""
        self.product_key = None
        self.device_name = None
        self.device_key = None
        self.send_id = 0
        self.data = {}
        self.data_changed_keys = []  # [ [], []]

    def config(self, product_key, device_name, device_key, product_secret=None):
        if not product_secret:
            cmd = 'AT+TCDEVINFOSET=1,"{}","{}","{}"'.format(
                product_key, device_name, device_key
            )
            ack = self._cmd(cmd, ["+TCDEVINFOSET:OK"], timeout=3)
        else: # auto register
            cmd = 'AT+TCPRDINFOSET=1,"{}","{}","{}"'.format(
                product_key, product_secret, device_name
            )
            cmd2 = 'AT+TCDEVREG'
            ack = self._cmd(cmd, ["+TCPRDINFOSET:OK"], timeout=3)
            ack = self._cmd(cmd2, ["+TCDEVREG:OK", "+TCDEVREG:FAIL,1021"], ["+TCDEVREG:FAIL"], timeout=15) # 1021 already registerd
        self.product_key = product_key
        self.device_name = device_name
        self.device_key = device_key
        self.product_secret = product_secret
            
    def restore_config(self):
        cmd = 'AT+TCRESTORE'
        ack = self._cmd(cmd, ["OK"], timeout=3)

    def smartconfig(self, timeout=120):
        cmd_stop = "AT+TCSTOPSMART"
        cmd_start = "AT+TCSTARTSMART"
        # print("--now stop smartconfig")
        # ack = self._cmd(cmd_stop, "OK", timeout=3) # this will cause reboot
        print("--now start smartconfig")
        ack = self._cmd(cmd_start, ["+TCSTARTSMART:WIFI_CONNECT_SUCCESS"], timeout=timeout)
        print("--now smartconfig end")

    def connect(self):
        cmd = "AT+TCMQTTCONN=1,5000,240,1,1"
        cmd_sub = 'AT+TCMQTTSUB="$thing/down/property/{}/{}",0'.format(self.product_key, self.device_name)
        ack = self._cmd(cmd, ["+TCMQTTCONN:OK"], ["+TCMQTTCONN:FAIL"], timeout=10)
        ack = self._cmd(cmd_sub, ["+TCMQTTSUB:OK"], ["+TCMQTTSUB:FAIL", "ERROR"], timeout=10)


    def report_(self, data):
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

    def wifi_reset(self, rest_button):
        rest_button.value(0)
        time.sleep_ms(200)
        rest_button.value(1)
        read = b""
        t = time.ticks_ms()
        while 1:
            time.sleep_ms(100)
            msg = self.uart.read()
            if msg:
                read += msg
                if b"ready\r\n" in read:
                    break
            if time.ticks_ms() - t > 5000:
                raise Exception("reset timeout")
        time.sleep_ms(200)
        read = self.uart.read()
    
    def get_ip(self):
        cmd = "AT+CIFSR"
        try:
            ack = self._cmd(cmd, ["OK"], ["ERROR"], timeout=2)
        except Exception as e:
            print("--[ERROR] AT ack erro:", e)
            return ""
        # 'AT+CIFSR\r\n+CIFSR:STAIP,"0.0.0.0"\r\n+CIFSR:STAMAC,"18:fe:34:de:a6:00"\r\n\r\nOK\r\n'
        mat = ure.match('.*CIFSR:STAIP\,"(.*)".*CIFSR.*', ack)
        if mat:
            ip = mat.group(1)
            if "0.0.0.0" in ip:
                return ""
            return ip
        return ""
    
    def get_mac(self):
        cmd = "AT+CIFSR"
        ack = self._cmd(cmd, ["OK"], ["ERROR"], timeout=2)
        print(ack)
        # 'AT+CIFSR\r\n+CIFSR:STAIP,"0.0.0.0"\r\n+CIFSR:STAMAC,"18:fe:34:de:a6:00"\r\n\r\nOK\r\n'
        mat = ure.match('.*CIFSR:STAMAC\,"(.*)"\r\n.*', ack)
        if mat:
            mac = mat.group(1)
            return mac
        return ""
        


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

    def notify_report(self, keys):
        if not self.data_changed_keys:
            self.data_changed_keys = list(keys)
        else:
            for item in keys:
                self.data_changed_keys.append(item)
    
    def report(self, keys):
        data = {}
        for key in keys:
            data[key] = self.data[key]
        print("--report:", data)
        self.report_(data)
        print("--report success")

    def run(self):
        if len(self.data_changed_keys) > 0:
            data = {}
            for key in self.data_changed_keys:
                if type(key) == list:
                    data0 = {}
                    for key0 in key:
                        data0[key0] = self.data[key0]
                    if data0:
                        print("--report:", data0)
                        self.report_(data0)
                        print("--report success")
                else:
                    data[key] = self.data[key]
            if data:
                print("--report:", data)
                self.report_(data)
                print("--report success")
            self.data_changed_keys = []
        msg = self.uart.read()
        if msg:
            self.msg += msg
            idx = self.msg.find(b"+TCMQTTRCVPUB:")
            if idx >= 0:
                self.msg = self.msg[idx:]
                print("--msg:", self.msg)
                idx = self.msg.find(b'}"\r\n') + 2
                if idx >= 0:
                    pub_msg = self.msg
                    try:
                        mat = ure.match('.*"{(.*)}".*', pub_msg.decode())
                        if mat:
                            pub_msg = '{'+mat.group(1)+'}'
                            pub_msg = json.loads(pub_msg)
                    except Exception as e:
                        print(e)
                        print("--[error] pub msg decode error:{}".format(pub_msg))
                        pub_msg = None
                    if pub_msg:
                        self.on_msg(pub_msg)
                    self.msg = self.msg[idx+2:] # remove "+TCMQTTRCVPUB:...\r\n"


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

    def on_msg(msg):
        for key in msg:
            print("control {}:{}".format(key, msg[key]))

    explorer = Explorer_AT(uart, on_msg)
    print("--config")
    explorer.config("1WAN4M5NPX", "device_01", "PHsWVCZkf9IaPnkhZkG4Rg==")
    print("--start smartconfig")
    explorer.smartconfig()
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



