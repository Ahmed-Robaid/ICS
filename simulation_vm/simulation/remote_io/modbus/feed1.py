"""
MODIFIED Pymodbus Server With Updating Thread
--------------------------------------------------------------------------
This is an example of having a background thread updating the
context in an SQLite4 database while the server is operating.

This scrit generates a random address range (within 0 - 65000) and a random
value and stores it in a database. It then reads the same address to verify
that the processworks as expected

This can also be done with a python thread::
    from threading import Thread
    thread = Thread(target=updating_writer, args=(context,))
    thread.start()
"""
# TODO maybe cut down on calls to simulation by combining all remote io into one file?
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
# define your callback process
# --------------------------------------------------------------------------- #
# import logging
# logging.basicConfig()
# log = logging.getLogger()
# log.setLevel(logging.INFO)

last_command = -1
async def updating_writer(context, sock):
    global last_command
    print('updating FEED 1')

    slave_id = 0x01 # slave address
    count = 50

    #Write multiple analog output registers(0x10)

    current_command = context[slave_id].getValues(16, 1, 1)[0] / 65535.0 *100.0
    sock.sendall(('{"request":"write","data":{"inputs":{"f1_valve_sp":' + repr(current_command) + '}}}\n').encode())

    data = json.loads(sock.recv(1500).decode())
    valve_pos = int(data["state"]["f1_valve_pos"]/100.0*65535)
    flow = int(data["outputs"]["f1_flow"]/500.0*65535)
    print(data)

    valve_pos = max(0, min(valve_pos, 65535))  # Clamp value between 0 and 65535
    flow = max(0, min(flow, 65535))  # Clamp value between 0 and 65535

    context[slave_id].setValues(4, 1, [valve_pos,flow])


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
        ir=ModbusSequentialDataBlock(0, range(301, 401))
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
    identity.MajorMinorRevision = version #'1.0'

    # connect to simulation
    HOST = '127.0.0.1'
    PORT = 55555
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    asyncio.create_task(run_updating_task(context, sock))

    # ----------------------------------------------------------------------- #
    # run the server
    # ----------------------------------------------------------------------- #
    await StartAsyncTcpServer(context, identity=identity, address=("192.168.95.10", 502))


if __name__ == "__main__":
    asyncio.run(run_update_server())
