import time,ure


def test():
    a = 'AT+CIFSR\r\n+CIFSR:STAIP,"0.0.0.0"\r\n+CIFSR:STAMAC,"18:fe:34:de:a6:00"\r\n\r\nOK\r\n'
    mat = ure.match('.*CIFSR:STAIP\,"(.*)".*CIFSR.*', a)
    print(mat)
    if mat:
        ip = mat.group(1)
        print(ip)
    print("test end")

if __name__ == "__main__":
    test()
    from Maix import GPIO
    from machine import UART
    from fpioa_manager import fm

    fm.register(0, fm.fpioa.GPIOHS1, force=True)
    wifi_io0_en=GPIO(GPIO.GPIOHS1, GPIO.OUT)
    wifi_io0_en.value(0)

    fm.register(7,fm.fpioa.UART2_TX)
    fm.register(6,fm.fpioa.UART2_RX)

    uart = UART(UART.UART2,115200,timeout=1000, read_buf_len=4096)
    time.sleep_ms(5000)
    uart.write("AT\r\n")
    print(uart.read())
    print("-----")


    uart.write("AT+CIFSR\r\n")
    while 1:
        read = uart.read()
        if read:
            print(read)


