import smbus
import time
import sqlite3
from datetime import datetime

bus = smbus.SMBus(1)
address = 0x5d


REF_P_XL = 0x8   #Reference pressure (LSB data)
REF_P_L  = 0x9   #Reference pressure (middle part)
REF_P_H  = 0xa   #Reference pressure (MSB data)
WHO_AM_I = 0xf   #Dummy register, 0xbb
RES_CONF = 0x10  #Pressure resolution mode

CTRL_REG1 = 0x20
CTRL_REG2 = 0x21
CTRL_REG3 = 0x22
INT_CFG_REG = 0x23
INT_SOURCE_REG = 0x24
THS_P_LOW_REG = 0x25
THS_P_HIGH_REG = 0x26
STATUS_REG = 0x27
PRESS_POUT_XL_REH = 0x28 #Pressure data (LSB)
PRESS_OUT_L       = 0x29 #Pressure data middle
PRESS_OUT_H       = 0x2a # Pressure data (MSB)
TEMP_OUT_L = 0x2b
TEMP_OUT_H = 0x2c


def id():
    return bus.read_byte_data(address, 0x8F)

def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if( (val&(1<<(bits-1))) != 0 ):
        val = val - (1<<bits)
    return val        

def temp():
        temp1 = bus.read_byte_data(address, TEMP_OUT_H)
        temp2 = bus.read_byte_data(address, TEMP_OUT_L)
        temp = (temp1 << 8) + temp2
        temp = 42.5 + twos_comp(temp,16) / float(480)
        return temp

def pressure():
        pressLSB = bus.read_byte_data(address, PRESS_POUT_XL_REH)
        pressM = bus.read_byte_data(address, PRESS_OUT_L)
        pressMSB = bus.read_byte_data(address, PRESS_OUT_H)
        press = (pressMSB << 16) + (pressM << 8) + pressLSB
        press = press / float(4096)
        return press

bus.write_byte_data(address, CTRL_REG1,0x00) #power down
bus.write_byte_data(address, RES_CONF,0x7a) #pressure sensor to higher-precision
bus.write_byte_data(address, CTRL_REG1,0x84) #pressure analog on, single shot
bus.write_byte_data(address, CTRL_REG2, 0x01) #run one shot measurement

cntrl = bus.read_byte_data(address, CTRL_REG2)
while cntrl != 0 :
        cntrl = bus.read_byte_data(address, CTRL_REG2)

temperature_ = temp()
pressure_ = pressure()
now = datetime.now()
print now
print temperature_
print pressure_

conn = sqlite3.connect("/home/pi/readings.db", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS logging (datetime TIMESTAMP, temp FLOAT, pressure FLOAT)')
c.execute('INSERT INTO logging VALUES(?, ?, ?)', (now, temperature_, pressure_))
conn.commit()
