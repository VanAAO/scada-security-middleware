from pyModbusTCP.client import ModbusClient #send modbus commands

# Connect to ModbusPal
client = ModbusClient(host="127.0.0.1", port=502, unit_id=1, timeout=5)

if client.open():
    print("✅ Connected to ModbusPal!")
    
    # Read register 1 (Temperature)
    result = client.read_holding_registers(1, 1)
    
    if result:
        print(f"Temperature value: {result[0]}")
    else:
        print("❌ Failed to read")
    
    client.close()
else:
    print("❌ Connection failed")
