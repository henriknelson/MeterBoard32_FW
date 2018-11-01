import uos
from flashbdev import bdev

def check_bootsec():
    buf = bytearray(bdev.SEC_SIZE)
    bdev.readblocks(0, buf)
    empty = True
    for b in buf:
        if b != 0xff:
            empty = False
            break
    if empty:
        return True
    fs_corrupted()

def fs_corrupted():
    import time
    while 1:
        print("""\
FAT filesystem appears to be corrupted. If you had important data there, you
may want to make a flash snapshot to try to recover it. Otherwise, perform
factory reprogramming of MicroPython firmware (completely erase flash, followed
by firmware programming).
""")
        time.sleep(3)

def setup():
    check_bootsec()
    print("Performing initial setup")
    uos.VfsFat.mkfs(bdev)
    vfs = uos.VfsFat(bdev)
    uos.mount(vfs, '/flash')
    uos.chdir('/flash')
    uos.mkdir('/flash/.config')
    uos.chdir('/flash/.config')
    with open("meter_config.json", "w") as f:
        f.write("""\
[
  {
    "DataRecords": [
      {
        "dib": "04",
        "vib": "863B",
        "data": "D2040000"
      }
    ],
    "MeterId": "14881488",
    "PrimaryAddress": 2,
    "MeterType": 4,
    "ManufacturerId": "HCN"
  }
]
""")
    uos.chdir('/flash')
    with open("webrepl_cfg.py", "w") as f2:
        f2.write("""\
PASS = 'henke2k3'
""")
    with open("boot.py", "w") as f3:
        f3.write("""\
# This file is executed on every boot (including wake-boot from deepsleep)
from network import WLAN
import esp
import time
import ntptime
import machine
esp.osdebug(None)
print("Welcome to MeterBoard32 console!")
print("---------------------")
wlan = WLAN()
wlan.active(True)
wlan.connect("Helan","Un0s245A!")
print("Connecting to WiFi..", end="")
while not wlan.isconnected():
    print(".",end="")
    time.sleep_ms(200)
print("")
print("Connected to WiFi:", wlan.ifconfig())
time.sleep(2)
ntptime.settime()
print("Current time set via NTP server to:", "%04u-%02u-%02u %02u:%02u:%02u" % time.localtime()[0:6])
import webrepl
webrepl.start()
""")
    with open("main.py", "w") as f4:
        f4.write("""\
# This file is executed after every boot)
from neo import Neo
from mbus_device import MBusDevice
from mbus_handler import MBusHandler
from mbus_record import MBusValueRecord

neo = Neo(13)
neo.set_color(0,255,0)
handler = MBusHandler(baudrate=2400,timeout=350,debug=True)
handler.start()
""")
    return vfs
