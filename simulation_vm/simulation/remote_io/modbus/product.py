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
import asyncio
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.server import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
from pymodbus import __version__ as pymodbus_version
import random
# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


last_command = -1
async def updating_writer(context, sock):
    global last_command
    print('updating')

    slave_id = 0x01  # slave address
    count = 50

    current_command = context[slave_id].getValues(16, 1, 1)[0] / 65535.0 * 100.0
    sock.sendall(b'{"request":"write","data":{"inputs":{"product_valve_sp":' + repr(current_command).encode() + b'}}}\n')
    data = json.loads(sock.recv(1500))
    valve_pos = int(data["state"]["product_valve_pos"]/100.0*65535)
    flow = int(data["outputs"]["product_flow"]/500.0*65535)
    print(data)
    if valve_pos > 65535:
        valve_pos = 65535
    elif valve_pos < 0:
        valve_pos = 0
    if flow > 65535:
        flow = 65535
    elif flow < 0:
        flow = 0
    # import pdb; pdb.set_trace()
    context[slave_id].setValues(4, 1, [valve_pos,flow])
    await asyncio.sleep(1)  # 1 second delay



async def run_update_server():
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #


    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0,range(1,101)),
        co=ModbusSequentialDataBlock(0,range(101,201)),
        hr=ModbusSequentialDataBlock(0,range(201,301)),
        ir=ModbusSequentialDataBlock(0,range(301,401)))

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
    identity.MajorMinorRevision = pymodbus_version

    # connect to simulation
    HOST = '127.0.0.1'
    PORT = 55555
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    asyncio.create_task(updating_writer(context, sock))
    await StartAsyncTcpServer(context=context, identity=identity, address=("192.168.95.13", 502))


if __name__ == "__main__":
    asyncio.run(run_update_server())
