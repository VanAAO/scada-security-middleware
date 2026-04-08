from pyModbusTCP.client import ModbusClient
import socket
import struct
import time

def authenticate_to_bridge(username, password):
    """Connect and authenticate to bridge"""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 5020))
    
    auth_message = f"{username}:{password}"
    client.send(auth_message.encode('utf-8'))
    
    response = client.recv(1024).decode('utf-8')
    if response == "AUTH_OK":
        print(f"✅ Authenticated as {username}\n")
        return client
    else:
        print(f"❌ Authentication failed\n")
        return None

def send_write_command(bridge_socket, register, value):
    """Send write command through bridge"""
    packet = struct.pack('>HHHBBHH', 1, 0, 6, 1, 6, register, value)
    bridge_socket.send(packet)
    time.sleep(0.5)

def read_from_plc_directly(register):
    """Read current value from ModbusPal (direct connection)"""
    plc = ModbusClient(host="127.0.0.1", port=502, unit_id=1)
    if plc.open():
        result = plc.read_holding_registers(register, 1)
        plc.close()
        return result[0] if result else None
    return None

# ===== DEMONSTRATION =====
print("="*70)
print("COMPLETE FLOW DEMONSTRATION")
print("="*70)
print("\n👀 WATCH BOTH:")
print("  1. This terminal (shows bridge decisions)")
print("  2. ModbusPal window (shows actual PLC values changing)")
print("\n" + "="*70 + "\n")

# Read initial state
print("📖 Initial PLC State:")
temp_initial = read_from_plc_directly(0)
humid_initial = read_from_plc_directly(1)
print(f"  Register 0 (Temperature): {temp_initial}")
print(f"  Register 1 (Humidity): {humid_initial}\n")

input("Press Enter to start sending commands...\n")

# Connect to bridge
bridge = authenticate_to_bridge("operator1", "pass123")

if bridge:
    # TEST 1: Valid temperature command
    print("="*70)
    print("[TEST 1] Sending VALID command: Set Temperature = 22°C")
    print("Expected: ✅ Bridge ALLOWS → ModbusPal changes to 22")
    print("="*70)
    send_write_command(bridge, register=0, value=22)
    
    new_temp = read_from_plc_directly(0)
    print(f"📖 PLC Register 0 now shows: {new_temp}")
    print(f"{'✅ SUCCESS' if new_temp == 22 else '❌ FAILED'}\n")
    
    input("Press Enter for next test...\n")
    
    # TEST 2: Invalid temperature (too high)
    print("="*70)
    print("[TEST 2] Sending INVALID command: Set Temperature = 50°C")
    print("Expected: ❌ Bridge BLOCKS → ModbusPal stays at 22")
    print("="*70)
    send_write_command(bridge, register=0, value=50)
    
    blocked_temp = read_from_plc_directly(0)
    print(f"📖 PLC Register 0 now shows: {blocked_temp}")
    print(f"{'✅ CORRECTLY BLOCKED' if blocked_temp == 22 else '❌ SECURITY FAILED'}\n")
    
    input("Press Enter for next test...\n")
    
    # TEST 3: Valid humidity command
    print("="*70)
    print("[TEST 3] Sending VALID command: Set Humidity = 45%")
    print("Expected: ✅ Bridge ALLOWS → ModbusPal changes to 45")
    print("="*70)
    send_write_command(bridge, register=1, value=45)
    
    new_humid = read_from_plc_directly(1)
    print(f"📖 PLC Register 1 now shows: {new_humid}")
    print(f"{'✅ SUCCESS' if new_humid == 45 else '❌ FAILED'}\n")
    
    input("Press Enter for next test...\n")
    
    # TEST 4: Invalid humidity (too low)
    print("="*70)
    print("[TEST 4] Sending INVALID command: Set Humidity = 10%")
    print("Expected: ❌ Bridge BLOCKS → ModbusPal stays at 45")
    print("="*70)
    send_write_command(bridge, register=1, value=10)
    
    blocked_humid = read_from_plc_directly(1)
    print(f"📖 PLC Register 1 now shows: {blocked_humid}")
    print(f"{'✅ CORRECTLY BLOCKED' if blocked_humid == 45 else '❌ SECURITY FAILED'}\n")
    
    bridge.close()
    
    # Final summary
    print("="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\n✅ What you just saw:")
    print("  1. Valid commands go THROUGH bridge → PLC values change")
    print("  2. Invalid commands BLOCKED by bridge → PLC stays protected")
    print("  3. Bridge logs everything in security_log.txt")
    print("\n👉 Check security_log.txt to see all logged events!")
    print("="*70)