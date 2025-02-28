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
import socket
import json
import asyncio
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.server import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
#from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
import random
from pymodbus import __version__ as version

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


async def updating_writer(context, sock):
    print('updating ANALYZER')
    readfunction = 0x03 # read holding registers
    writefunction = 0x10
    slave_id = 0x01 # slave address
    count = 50

    sock.sendall(b'{"request":"read"}')
    #data = s.recv(1500).decode('utf-8')
    data = json.loads(sock.recv(1500).decode())

    print(data)

    a_in_purge = int(data["outputs"]["A_in_purge"] * 65535)
    b_in_purge = int(data["outputs"]["B_in_purge"] * 65535)
    c_in_purge = int(data["outputs"]["C_in_purge"] * 65535)

    # import pdb; pdb.set_trace()
    context[slave_id].setValues(4, 1, [a_in_purge, b_in_purge, c_in_purge])
    values = context[slave_id].getValues(readfunction, 0, 2)
    log.debug("Values from datastore: " + str(values))

async def run_updating_task(context, sock):
    while True:
        await updating_writer(context, sock)
        await asyncio.sleep(1)  # 1-second delay


async def run_update_server():
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #


    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, range(1, 101)),
        co=ModbusSequentialDataBlock(0, range(101, 201)),
        hr=ModbusSequentialDataBlock(0, range(201, 301)),
        ir=ModbusSequentialDataBlock(0, range(301, 401)))
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
    identity.MajorMinorRevision = version

    # connect to simulation
    HOST = '127.0.0.1'
    PORT = 55555
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    asyncio.create_task(run_updating_task(context, sock))

    # ----------------------------------------------------------------------- #
    # run the server
    # ----------------------------------------------------------------------- #
    await StartAsyncTcpServer(context, identity=identity, address=("192.168.95.15", 502))


if __name__ == "__main__":
    asyncio.run(run_update_server())
