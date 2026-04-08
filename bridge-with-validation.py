from pyModbusTCP.client import ModbusClient
import socket
import struct
import time
from datetime import datetime

# ===== AUTHENTICATION DATABASE =====
authorized_users = {
    "operator1": {"password": "pass123", "role": "operator"},
    "engineer1": {"password": "secure456", "role": "engineer"}
}

# ===== VALIDATION RULES =====
ALLOWED_FUNCTION_CODES = {
    "operator": [3, 6],      # Read (03), Write Single (06)
    "engineer": [3, 6, 16]   # Read (03), Write Single (06), Write Multiple (16)
}

REGISTER_RULES = {
    0: {"name": "Temperature", "min": 15, "max": 30},  # 15-30°C safe range
    1: {"name": "Humidity", "min": 35, "max": 65}      # 35-65% safe range
}

failed_attempts = {}
LOCKOUT_THRESHOLD = 3
LOCKOUT_DURATION = 300  # 5 minutes in seconds

# ===== RATE LIMITING =====
command_count = {}
RATE_LIMIT = 10  # Max 10 commands per minute

# ===== LOGGING FUNCTION =====
def log_event(action, user, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action} | User: {user} | {details}\n"
    print(log_entry.strip())
    
    with open("security_logs.txt", "a") as f:
        f.write(log_entry)

# ===== AUTHENTICATION =====
def authenticate(username, password):
    current_time = time.time()
    
    # Check if account is locked
    if username in failed_attempts:
        attempts, lock_time = failed_attempts[username]["count"], failed_attempts[username].get("locked_at", 0)
        if lock_time and current_time - lock_time < LOCKOUT_DURATION:
            remaining = int(LOCKOUT_DURATION - (current_time - lock_time))
            log_event("LOCKED", username, f"Account locked. Try again in {remaining} seconds")
            return False, None
        elif lock_time and current_time - lock_time >= LOCKOUT_DURATION:
            failed_attempts[username] = {"count": 0}
    
    # Normal authentication
    if username in authorized_users:
        if authorized_users[username]["password"] == password:
            if username in failed_attempts:
                failed_attempts[username] = {"count": 0}
            log_event("AUTH_SUCCESS", username, "Login successful")
            return True, authorized_users[username]["role"]
    
    # Track failed attempt
    if username not in failed_attempts:
        failed_attempts[username] = {"count": 0}
    failed_attempts[username]["count"] += 1
    count = failed_attempts[username]["count"]
    
    if count >= LOCKOUT_THRESHOLD:
        failed_attempts[username]["locked_at"] = current_time
        log_event("LOCKED", username, f"Account locked after {LOCKOUT_THRESHOLD} failed attempts")
    else:
        log_event("AUTH_FAILED", username or "Unknown", f"Invalid credentials (attempt {count}/{LOCKOUT_THRESHOLD})")
    
    return False, None

# ===== VALIDATION FUNCTIONS =====
def validate_function_code(fc, role):
    if fc in ALLOWED_FUNCTION_CODES.get(role, []):
        return True, "Allowed"
    return False, f"Function code {fc} not permitted for role {role}"

def validate_register_value(register, value):
    if register in REGISTER_RULES:
        rule = REGISTER_RULES[register]
        if rule["min"] <= value <= rule["max"]: #checks if value is within range
            return True, "Value in range"
        return False, f"{rule['name']} value {value} outside safe range ({rule['min']}-{rule['max']})"
    return False, "No rule defined - register not permitted"
    
def check_rate_limit(username):
    current_time = time.time()
    
    if username not in command_count:
        command_count[username] = []
    
    # Remove commands older than 1 minute
    command_count[username] = [t for t in command_count[username] if current_time - t < 60]
    
    if len(command_count[username]) >= RATE_LIMIT:
        return False, "Rate limit exceeded (max 10/min)"
    
    command_count[username].append(current_time)
    return True, "Rate OK"

# ===== MODBUS PACKET PARSER =====
def parse_modbus_write(data):
    if len(data) < 12: #it is 12 because it consists of 8 (header[needed for basic check:transid, protoid, len, unitid, fc]) + 2 (register address) + 2 (value)
        return None
    
    function_code = data[7]
    register_address = struct.unpack('>H', data[8:10])[0]
    value = struct.unpack('>H', data[10:12])[0]
    
    return {
        'function_code': function_code,
        'register': register_address,
        'value': value,
        'raw_data': data
    }

value_history = {}

def check_oscillation(register, value, username):
    current_time = time.time()
    
    if register not in value_history:
        value_history[register] = []
    
    value_history[register].append({"value": value, "time": current_time})
    
    # Keep only last 60 seconds
    value_history[register] = [v for v in value_history[register] if current_time - v["time"] < 60]
    
    # Check for direction changes
    values = [v["value"] for v in value_history[register]]
    if len(values) >= 3:
        direction_changes = 0
        for i in range(2, len(values)):
            if (values[i] > values[i-1]) != (values[i-1] > values[i-2]):
                direction_changes += 1
        
        if direction_changes >= 2:
            return False, "Suspicious oscillation pattern detected"
    
    return True, "Pattern OK"

# ===== SESSION TIMEOUT
TIMEOUT = 300 # 5 minutes
last_activity = time.time()

# ===== MAIN BRIDGE =====
print("🔒 Security Bridge with Validation Started")
print("📡 Listening on port 5020")
print("🎯 Forwarding to PLC on port 502")
print("\n📋 VALIDATION RULES:")
print(f"  Temperature (Reg 1): 15-30°C")
print(f"  Humidity (Reg 2): 35-65%")
print(f"  Rate Limit: {RATE_LIMIT} commands/minute\n")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("127.0.0.1", 5020))
server_socket.listen(5)

print("⏳ Waiting for SCADA connection...\n")

try:
    while True:
        client_conn, client_addr = server_socket.accept()  #accept connection
        print(f"📞 Connection from {client_addr}")
        
        # Authentication
        auth_data = client_conn.recv(1024).decode('utf-8').strip()
        
        if ':' in auth_data:
            username, password = auth_data.split(':', 1)    #get credentials
            auth_success, role = authenticate(username, password)
            
            if auth_success:
                client_conn.send(b"AUTH_OK")
                print(f"✅ {username} ({role}) authenticated\n")    #check authentication
                
                plc = ModbusClient(host="127.0.0.1", port=502, unit_id=1)   #connect to plc
                
                if plc.open():
                    print("🔗 Connected to PLC\n")
                    
                    while True:
                        data = client_conn.recv(1024)
                        if not data:
                            break
                                                                #Get command → Check session time → Parse it → Extract details
                        if time.time() - last_activity > 300:
                            log_event("TIMEOUT", username, "Session expired due to inactivity")
                            client_conn.send(b"SESSION_EXPIRED")
                            break
        
                        last_activity = time.time()   

                        packet = parse_modbus_write(data)
                        if packet:
                            fc = packet['function_code']
                            reg = packet['register']
                            val = packet['value']
                            
                            # VALIDATION CHECKS
                            print(f"🔍 Validating: FC={fc}, Reg={reg}, Val={val}")
                            
                            # Check 1: Rate limit
                            rate_ok, rate_msg = check_rate_limit(username)
                            if not rate_ok:
                                log_event("BLOCKED", username, f"FC:{fc} Reg:{reg} - {rate_msg}")
                                print(f"❌ BLOCKED: {rate_msg}\n")
                                continue
                            
                            # Check 2: Function code allowed?
                            fc_ok, fc_msg = validate_function_code(fc, role)
                            if not fc_ok:
                                log_event("BLOCKED", username, f"FC:{fc} Reg:{reg} - {fc_msg}")
                                print(f"❌ BLOCKED: {fc_msg}\n")
                                continue
                            
                            # Check 3: Value in range?
                            if fc == 6:  # Write Single Register
                                val_ok, val_msg = validate_register_value(reg, val)
                                if not val_ok:
                                    log_event("BLOCKED", username, f"FC:{fc} Reg:{reg} Val:{val} - {val_msg}")
                                    print(f"❌ BLOCKED: {val_msg}\n")
                                    continue

                                # Check 4: Oscillation detection
                                osc_ok, osc_msg = check_oscillation(reg, val, username)
                                if not osc_ok:
                                    log_event("BLOCKED", username, f"FC:{fc} Reg:{reg} Val:{val} - {osc_msg}")
                                    print(f"❌ BLOCKED: {osc_msg}\n")
                                    continue

                            # ALL CHECKS PASSED - FORWARD TO PLC
                            log_event("ALLOWED", username, f"FC:{fc} Reg:{reg} Val:{val}")
                            print(f"✅ ALLOWED: Forwarding to PLC\n")
                            
                            # Actually write to PLC
                            if fc == 6:
                                plc.write_single_register(reg, val)
                        
                        time.sleep(0.01)
                    
                    plc.close()
            else:
                    if username in failed_attempts and failed_attempts.get(username, {}).get("locked_at", 0):
                        remaining = int(LOCKOUT_DURATION - (time.time() - failed_attempts[username]["locked_at"]))
                        if remaining > 0:
                           client_conn.send(f"LOCKED:{remaining}".encode('utf-8'))
                           print(f"🔒 Account locked ({remaining}s remaining)\n")
                        else:
                           client_conn.send(b"AUTH_FAILED")
                           print("❌ Authentication failed\n")
                    else:
                         client_conn.send(b"AUTH_FAILED")
                         print("❌ Authentication failed\n")
        
        client_conn.close()
        
except KeyboardInterrupt:
    print("\n🛑 Bridge stopped")
    server_socket.close()