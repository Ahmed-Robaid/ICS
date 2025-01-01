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
from pymodbus.server.async_io import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
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
    while True:
        print('updating ANALYZER')
        readfunction = 0x03 # read holding registers
        writefunction = 0x10
        slave_id = 0x01 # slave address
        # import pdb; pdb.set_trace()
        sock.send(b'{"request":"read"}')
        try:
            data = json.loads(sock.recv(1500).decode())
        except json.JSONDecodeError:
            print("Received data is not in JSON format.")
            await asyncio.sleep(1)
            return
        a_in_purge = int(data["outputs"]["A_in_purge"]*65535)
        b_in_purge = int(data["outputs"]["B_in_purge"]*65535)
        c_in_purge = int(data["outputs"]["C_in_purge"]*65535)
        print(data)

        # import pdb; pdb.set_trace()
        context[slave_id].setValues(4, 1, [a_in_purge,b_in_purge,c_in_purge])
        values = context[slave_id].getValues(readfunction, 0, 2)
        log.debug("Values from datastore: " + str(values))


        await asyncio.sleep(1)


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
    identity.MajorMinorRevision = version  # '1.0'

    # connect to simulation
    HOST = '127.0.0.1'
    PORT = 55555
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    # ----------------------------------------------------------------------- #
    # run the updating task
    # ----------------------------------------------------------------------- #
    asyncio.create_task(updating_writer(context, sock))

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    await StartAsyncTcpServer(context=context, identity=identity, address=("192.168.168.15", 502))


if __name__ == "__main__":
    asyncio.run(run_update_server())
