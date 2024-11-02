import socket
import json
from pymodbus.server.async_io import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from twisted.internet.task import LoopingCall
import logging

from pymodbus import __version__ as version


# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

last_command = -1
def updating_writer(a):
    global last_command
    print('updating')
    context  = a[0]

    slave_id = 0x01 # slave address
    count = 50
    s = a[1]


    current_command = context[slave_id].getValues(16, 1, 1)[0] / 65535.0 *100.0

    s.sendall(('{"request":"write","data":{"inputs":{"f1_valve_sp":' + repr(current_command) + '}}}\n').encode())

    # import pdb; pdb.set_trace()
    #s.send('{"request":"read"}')
    data = json.loads(s.recv(1500).decode())
    valve_pos = int(data["state"]["f1_valve_pos"]/100.0*65535)
    flow = int(data["outputs"]["f1_flow"]/500.0*65535)
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
    identity.MajorMinorRevision = version.short()

    # connect to simulation
    HOST = '127.0.0.1'
    PORT = 55555
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    # Start updating the Modbus context periodically
    time_interval = 1  # Time interval (in seconds) between updates
    loop = LoopingCall(f=updating_writer, a=(context, sock))
    loop.start(time_interval, now=False)  # Delay the first call


    # Start the Modbus TCP server
    StartTcpServer(context=context, identity=identity, address=("192.168.95.10", 502))

if __name__ == "__main__":
    run_update_server()
