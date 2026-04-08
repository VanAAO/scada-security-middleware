from pyModbusTCP.client import ModbusClient
import socket #listens and sends data over tcp
import struct #unpacks modbus binary data
import time
from datetime import datetime #for logs

# ===== AUTHENTICATION DATABASE =====
authorized_users = {
    "operator1": {"password": "pass123", "role": "operator"},
    "engineer1": {"password": "secure456", "role": "engineer"}
}

# ===== LOGGING FUNCTION =====
def log_event(action, user, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action} | User: {user} | {details}\n"
    print(log_entry.strip())
    
    with open("security_log.txt", "a") as f:
        f.write(log_entry)

# ===== AUTHENTICATION FUNCTION =====
def authenticate(username, password):
    if username in authorized_users:
        if authorized_users[username]["password"] == password:
            log_event("AUTH_SUCCESS", username, "Login successful")
            return True
    
    log_event("AUTH_FAILED", username or "Unknown", "Invalid credentials")
    return False

# ===== MODBUS PACKET PARSER =====
def parse_modbus_packet(data):
    if len(data) < 8:     #a modbus packet should be greater than 8, otherwise it is broken
        return None
    
    transaction_id = struct.unpack('>H', data[0:2])[0] #so once the packet surpases 8, let the the first 2[0,1] be converted to 1 number
    protocol_id = struct.unpack('>H', data[2:4])[0]
    length = struct.unpack('>H', data[4:6])[0]  #shows how many bytes follow
    unit_id = data[6] # the unit id is the id of the plc
    function_code = data[7]  # a function code is usually position 7
    
    return {
        'transaction_id': transaction_id,
        'function_code': function_code,
        'unit_id': unit_id,
        'raw_data': data
    }

# ===== MAIN BRIDGE =====
print("🔒 Security Bridge with Authentication Started")
print("📡 Listening on port 5020")
print("🎯 Forwarding to PLC on port 502\n")

# Create socket server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #use ipv4 and tcp to ensure connectivity
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # continue to use port 5020 such that even after stopping you can keep reusing 
server_socket.bind(("127.0.0.1", 5020))
server_socket.listen(5) #ready to accept connections , queue up to 5

print("⏳ Waiting for SCADA connection...\n")

try:
    while True:
        client_conn, client_addr = server_socket.accept()
        print(f"📞 Connection from {client_addr}")
        
        # SIMPLE AUTH: Expect username:password as first message
        auth_data = client_conn.recv(1024).decode('utf-8').strip() #how may packets to read at once, buffer size and decode bytes
        
        if ':' in auth_data:
            username, password = auth_data.split(':', 1) #checks if colon exists and splits the authorised user data into 2
            
            if authenticate(username, password):
                client_conn.send(b"AUTH_OK")
                print(f"✅ {username} authenticated\n")
                
                # Now handle Modbus commands
                plc = ModbusClient(host="127.0.0.1", port=502, unit_id=1)
                
                if plc.open():
                    print("🔗 Connected to PLC")
                    
                    while True:
                        data = client_conn.recv(1024)
                        if not data:
                            break
                        
                        packet = parse_modbus_packet(data)
                        if packet:
                            log_event("COMMAND", username, f"FC: {packet['function_code']}")
                            
                            # TODO: Add validation 
                            # For now, forward to PLC
                            
                        time.sleep(0.01)
                    
                    plc.close()
            else:
                client_conn.send(b"AUTH_FAILED")
                print("❌ Authentication failed\n")
        
        client_conn.close()
        
except KeyboardInterrupt:
    print("\n🛑 Bridge stopped")
    server_socket.close()