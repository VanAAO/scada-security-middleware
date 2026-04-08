from pyModbusTCP.client import ModbusClient
import socket
import struct
import time

def authenticate_to_bridge():
    """Interactive authentication"""
    print("\n" + "="*70)
    print("🔐 AUTHENTICATION REQUIRED")
    print("="*70)
    
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 5020))
    
    auth_message = f"{username}:{password}"
    client.send(auth_message.encode('utf-8'))
    
    response = client.recv(1024).decode('utf-8')
    print(f"\n{response}")
    
    if response == "AUTH_OK":
       print(f"✅ Welcome, {username}!\n")
       return client, username
    elif response.startswith("LOCKED"):
        remaining = response.split(":")[1]
        print(f"🔒 Account locked. Try again in {remaining} seconds.\n")
        client.close()
        return None, None
    else:
        print(f"❌ Access denied\n")
        client.close()
        return None, None

def send_write_command(bridge_socket, register, value):
    """Send write command through bridge"""
    packet = struct.pack('>HHHBBHH', 1, 0, 6, 1, 6, register, value)
    bridge_socket.send(packet)
    time.sleep(0.3)

def read_plc_value(register):
    """Read current PLC value"""
    plc = ModbusClient(host="127.0.0.1", port=502, unit_id=1)
    if plc.open():
        result = plc.read_holding_registers(register, 1)
        plc.close()
        return result[0] if result else None
    return None

# ===== INTERACTIVE DEMO =====
print("="*70)
print("🏭 DATA CENTER HVAC CONTROL SYSTEM")
print("="*70)
print("\n📋 SYSTEM INFORMATION:")
print("  Register 1: Temperature (Safe range: 15-30°C)")
print("  Register 2: Humidity (Safe range: 35-65%)")
print("  Rate Limit: 10 commands per minute")

while True:
    print("\n" + "="*70)
    
    # Authenticate
    bridge, username = authenticate_to_bridge()
    
    if not bridge:
        retry = input("Try again? (y/n): ")
        if retry.lower() != 'y':
            break
        continue
    
    # Show current PLC state
    print("="*70)
    print("📊 CURRENT PLC STATE:")
    print("="*70)
    temp = read_plc_value(0)
    humid = read_plc_value(1)
    print(f"  Temperature (Reg 0): {temp}°C")
    print(f"  Humidity (Reg 1): {humid}%\n")
    
    # Get command from user
    print("="*70)
    print("⚙️  SEND COMMAND")
    print("="*70)
    
    try:
        register = int(input("Which register? (0=Temp, 1=Humid): "))
        if register not in [0, 1]:
            print("❌ Invalid register. Only 0 (Temperature) and 1 (Humidity) are available.")
            bridge.close()
            continue
        value = int(input("Enter value: "))
        
        print(f"\n📤 Sending command to bridge...")
        print(f"   Register: {register}")
        print(f"   Value: {value}")
        print(f"\n⏳ Waiting for bridge validation...\n")
        
        send_write_command(bridge, register, value)
        
        # Read back to verify
        time.sleep(0.5)
        new_value = read_plc_value(register)
        
        print("="*70)
        print("📊 RESULT:")
        print("="*70)
        
        if new_value == value:
            print(f"✅ COMMAND ALLOWED")
            print(f"   Register {register} changed: {temp if register == 0 else humid} → {new_value}")
        else:
            print(f"❌ COMMAND BLOCKED BY SECURITY BRIDGE")
            print(f"   Register {register} unchanged: {new_value}")
            print(f"   Check bridge terminal for reason")
        
    except ValueError:
        print("❌ Invalid input!")
    
    bridge.close()
    
    # Continue?
    print("\n" + "="*70)
    another = input("Send another command? (y/n): ")
    if another.lower() != 'y':
        break

print("\n👋 Session ended. Check security_logs.txt for audit trail!")
print("="*70)