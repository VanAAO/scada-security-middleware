from pyModbusTCP.client import ModbusClient
import socket
import struct
import time

def authenticate_to_bridge(username, password):
    """Authenticate with the bridge"""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 5020))   #connect to bridge
    
    auth_message = f"{username}:{password}"   #send credentials
    client.send(auth_message.encode('utf-8'))
    
    response = client.recv(1024).decode('utf-8')
    print(f"Auth response: {response}")
    
    if response == "AUTH_OK":
        return client
    else:
        client.close()
        return None

def send_modbus_write_command(client_socket, register, value):
    """Send a Modbus write single register command (FC 06)"""
    # Build Modbus TCP packet
    transaction_id = 1 #because just testing security
    protocol_id = 0 #modbus standard, it should be 0
    length = 6 #[bytes that come after length so]1 (unit_id) + 1 (FC) + 2 (register) + 2 (value) = 6
    unit_id = 1 #modbuspal slave id is 1
    function_code = 6 #write single register command
    
    packet = struct.pack('>HHHBBHH',         #convert numbers into binary bytes H=2bytes, B=1bytes total 12
                         transaction_id,
                         protocol_id,
                         length,
                         unit_id,
                         function_code,
                         register,
                         value)
    
    client_socket.send(packet)
    time.sleep(0.2)

# ===== TEST CASES =====
print("=" * 60)
print("VALIDATION TEST SUITE")
print("=" * 60)

# TEST 1: Valid command (should pass)
print("\n[TEST 1] Valid command - Temperature = 20°C")
bridge = authenticate_to_bridge("operator1", "pass123")
if bridge:
    send_modbus_write_command(bridge, register=0, value=20)
    time.sleep(1)
    bridge.close()

# TEST 2: Out of range - Too high (should block)
print("\n[TEST 2] Invalid - Temperature = 50°C (too high)")
bridge = authenticate_to_bridge("operator1", "pass123")
if bridge:
    send_modbus_write_command(bridge, register=1, value=50)
    time.sleep(1)
    bridge.close()

# TEST 3: Out of range - Too low (should block)
print("\n[TEST 3] Invalid - Temperature = 5°C (too low)")
bridge = authenticate_to_bridge("operator1", "pass123")
if bridge:
    send_modbus_write_command(bridge, register=0, value=5)
    time.sleep(1)
    bridge.close()

# TEST 4: Valid humidity command
print("\n[TEST 4] Valid command - Humidity = 50%")
bridge = authenticate_to_bridge("operator1", "pass123")
if bridge:
    send_modbus_write_command(bridge, register=1, value=50)
    time.sleep(1)
    bridge.close()

# TEST 5: Rate limiting test
print("\n[TEST 5] Rate limiting - Send 12 commands rapidly")
bridge = authenticate_to_bridge("operator1", "pass123")
if bridge:
    for i in range(12):
        send_modbus_write_command(bridge, register=0, value=20)
        time.sleep(0.1)
    bridge.close()

print("\n" + "=" * 60)
print("TESTS COMPLETE - Check bridge terminal and logs!")
print("=" * 60)