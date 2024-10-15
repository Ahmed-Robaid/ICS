"""
MODIFIED Pymodbus Server With Updating Thread
--------------------------------------------------------------------------
This is an example of having a background thread updating the
context in an SQLite4 database while the server is operating.

This scrit generates a random address range (within 0 - 65000) and a random
value and stores it in a database. It then reads the same address to verify
that the process works as expected

This can also be done with a python thread::
    from threading import Thread
    thread = Thread(target=updating_writer, args=(context,))
    thread.start()
"""
# TODO maybe cut down on calls to simulation by combining all remote io into one file?
import socket
import json
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
import random
from pymodbus.version import version

# --------------------------------------------------------------------------- #
# import the twisted libraries we need
# --------------------------------------------------------------------------- #
from twisted.internet.task import LoopingCall

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def updating_writer(a):
    print('updating')
    context  = a[0]
    readfunction = 0x03 # read holding registers
    writefunction = 0x10
    slave_id = 0x01 # slave address
    count = 50
    s = a[1]
    # import pdb; pdb.set_trace()
    s.sendall(b'{"request":"read"}')
    jdata = s.recv(1500).decode('utf-8')
    try:
        data = json.loads(jdata)
        print(data)
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return
    #data = json.loads(s.recv(1500).decode('utf-8'))
    pressure = int(data["outputs"]["pressure"]/3200.0*65535)
    level = int(data["outputs"]["liquid_level"]/100.0*65535)
    if pressure > 65535:
        pressure = 65535
    if level > 65535:
        level = 65535
    print(data)

    # import pdb; pdb.set_trace()
    context[slave_id].setValues(4, 1, [pressure,level])
    values = context[slave_id].getValues(readfunction, 0, 2)
    log.debug("Values from datastore: " + str(values))


def run_update_server():
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #


    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, list(range(1, 101))),
        co=ModbusSequentialDataBlock(0, list(range(101, 201))),
        hr=ModbusSequentialDataBlock(0, list(range(201, 301))),
        ir=ModbusSequentialDataBlock(0, list(range(301, 401)))
    )
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/bashwork/pymodbus/'
    identity.ProductName = 'pymodbus Server'
    identity.ModelName = 'pymodbus Server'
    identity.MajorMinorRevision = '1.0'

    # connect to simulation
    HOST = '127.0.0.1'
    PORT = 55555
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        log.info(f"Connected to simulation at {HOST}:{PORT}")
    except socket.error as e:
        log.error(f"Failed to connect to simulation: {e}")
        return    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    time = 1  # 5 seconds delay
    loop = LoopingCall(f=updating_writer, a=(context,sock))
    loop.start(time, now=False)  # initially delay by time
    StartTcpServer(context, identity=identity, address=("192.168.95.14", 502))


if __name__ == "__main__":
    run_update_server()
