from pyModbusTCP.client import ModbusClient 
from pyModbusTCP.server import ModbusServer #listen/receive for commands
import time

# Create server (listens for SCADA commands)
server = ModbusServer(host="127.0.0.1", port=5020, no_block=True)

# Create client (connects to real PLC)
plc = ModbusClient(host="127.0.0.1", port=502, unit_id=1)

print("🔒 Security Bridge Started")
print("📡 Listening on port 5020")
print("🎯 Forwarding to PLC on port 502")

server.start()

try:
    while True:                          #adding further checks here
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n🛑 Bridge stopped")
    server.stop()