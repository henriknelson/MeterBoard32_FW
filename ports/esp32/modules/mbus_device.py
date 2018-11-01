from mbus_record import MBusValueRecord
import ubinascii
import random
import time

class MBusDevice:

    def __init__(self, primary_address, secondary_address, manufacturer, meter_type):
        self._primary_address = primary_address
        self._secondary_address = secondary_address
        self._manufacturer = manufacturer
        self._type = meter_type
	self._access_number = random.randint(0,255)
	self._records = []
        self._rsp_ud2 = []
        self._selected = False
    
    def get_time(self):
        return "%04u-%02u-%02u %02u:%02u:%02u" % time.localtime()[0:6]

    def log(self, message):
        print("[{}][debug] - {}".format(self.get_time(),message))

    def update(self):
        for record in self._records:
  	    record.update()
        self.log("Device with ID {} has updated its data".format(self._secondary_address))
        self.seal()

    def add_record(self,record):
	self._records.append(record)

    def seal(self):
        self._rsp_ud2 = self.get_rsp_ud2()

    def get_primary_address(self):
        return self._primary_address

    def get_secondary_address(self):
        return self._secondary_address

    def get_manufacturer_id(self):
        return self._manufacturer

    def get_type(self):
        return self._type

    def get_address_bytes(self):
        resp_bytes = []
        resp_bytes.append(self._secondary_address[6])
        resp_bytes.append(self._secondary_address[7])
        resp_bytes.append(self._secondary_address[4])
        resp_bytes.append(self._secondary_address[5])
        resp_bytes.append(self._secondary_address[2])
        resp_bytes.append(self._secondary_address[3])
        resp_bytes.append(self._secondary_address[0])
        resp_bytes.append(self._secondary_address[1])
        resp_str = []
        resp_str.append(resp_bytes[0] + resp_bytes[1])
        resp_str.append(resp_bytes[2] + resp_bytes[3])
        resp_str.append(resp_bytes[4] + resp_bytes[5])
        resp_str.append(resp_bytes[6] + resp_bytes[7])
        ret = [x for x in resp_str]
        return ret

    def get_manufacturer_bytes(self):
        manufacturer = self._manufacturer.upper()
        id = ((ord(manufacturer[0]) - 64) * 32 * 32 +
            (ord(manufacturer[1]) - 64) * 32 +
            (ord(manufacturer[2]) - 64))
        if 0x0421 <= id <= 0x6b5a:
            return self.manufacturer_encode(id, 2)
        return False

    def manufacturer_encode(self, value, size):
        if value is None or value == False:
            return None
        data = []
        for i in range(0, size):
            data.append((value >> (i * 8)) & 0xFF)
        return data

    def calculate_checksum(self, message):
        return sum([int(x, 16) if type(x) == str else x for x in message]) & 0xFF

    def get_latest_values(self):
        return self._rsp_ud2

    def get_rsp_ud2(self):
        resp_bytes = []
        resp_bytes.append(0x68)  # start
        resp_bytes.append(0xFF)  # length
        resp_bytes.append(0xFF)  # length
        resp_bytes.append(0x68)  # start
        resp_bytes.append(0x08)  # C
        resp_bytes.append(self._primary_address)  # A
        resp_bytes.append(0x72) # CI
        resp_bytes.extend(self.get_address_bytes())
        resp_bytes.extend(self.get_manufacturer_bytes())
        resp_bytes.append(0x01)  # version
        resp_bytes.append(self._type)  # medium (heat)
        resp_bytes.append(self._access_number)  # access no
        resp_bytes.append(0x00)  # status
        resp_bytes.append(0x00)  # configuration 1
        resp_bytes.append(0x00)  # configuration 2
	for record in self._records:
		resp_bytes.extend(record.get_bytes())
        resp_bytes.append(self.calculate_checksum(resp_bytes[4:]))
        resp_bytes.append(0x16)  # stop
        length = len(resp_bytes) - 9 + 3
        resp_bytes[1] = length
        resp_bytes[2] = length
        ret = ["{:>2}".format(hex(x)[2:]).replace(' ', '0') if type(x) == int else x for x in resp_bytes]
	if self._access_number < 255:
		self._access_number = self._access_number + 1
	else:
		self._access_number = 1
        return ''.join(ret).upper()
