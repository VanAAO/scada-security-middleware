from pyModbusTCP.client import ModbusClient
import time

print("🔍 Verifying ModbusPal Connection\n")

# Direct connection to ModbusPal
plc = ModbusClient(host="127.0.0.1", port=502, unit_id=1)

if plc.open():
    print("✅ Connected to ModbusPal on port 502\n")
    
    # Read initial value
    initial = plc.read_holding_registers(0, 1)
    print(f"📖 Initial Register 0 value: {initial[0]}")
    
    # Write new value
    print("✍️  Writing value 25 to Register 0...")
    plc.write_single_register(0, 25)
    time.sleep(0.5)
    
    # Read back
    after = plc.read_holding_registers(0, 1)
    print(f"📖 After write, Register 0 value: {after[0]}")
    
    print("\n👀 CHECK MODBUSPAL WINDOW - Did Register 0 change to 25?")
    
    plc.close()
else:
    print("❌ Failed to connect to ModbusPal")