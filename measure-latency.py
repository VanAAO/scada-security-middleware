from pyModbusTCP.client import ModbusClient
import time
import statistics

def measure_direct_to_plc(num_tests=100):
    """Measure latency connecting directly to PLC"""
    print("📊 Measuring DIRECT connection to PLC...")
    
    client = ModbusClient(host="127.0.0.1", port=502, unit_id=1)
    latencies = []
    
    if client.open():
        for i in range(num_tests):
            start = time.time()
            result = client.write_single_register(0, 20)
            end = time.time()
            
            if result:
                latency_ms = (end - start) * 1000
                latencies.append(latency_ms)
            
            time.sleep(0.01)
        
        client.close()
    
    return latencies

def measure_simple_overhead():
    """Measure just validation processing time"""
    print("\n📊 Measuring validation overhead...")
    
    REGISTER_RULES = {
        0: {"name": "Temperature", "min": 15, "max": 30},
        1: {"name": "Humidity", "min": 35, "max": 65}
    }
    
    def validate_register_value(register, value):
        if register in REGISTER_RULES:
            rule = REGISTER_RULES[register]
            if rule["min"] <= value <= rule["max"]:
                return True, "Value in range"
            return False, "Out of range"
        return True, "No rule"
    
    times = []
    for i in range(1000):
        start = time.time()
        validate_register_value(0, 20)
        end = time.time()
        times.append((end - start) * 1000)
    
    avg_processing = statistics.mean(times)
    print(f"  Average: {avg_processing:.4f} ms")
    
    return avg_processing

# ===== RUN TEST =====
print("🚀 Latency Measurement\n")

direct = measure_direct_to_plc(100)

if direct:
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    avg_direct = statistics.mean(direct)
    print(f"\n📌 Direct to PLC: {avg_direct:.2f} ms average")
    
    processing = measure_simple_overhead()
    estimated_with_bridge = avg_direct + processing
    
    print(f"\n🔒 ESTIMATED WITH BRIDGE:")
    print(f"  Direct PLC: {avg_direct:.2f} ms")
    print(f"  + Security: {processing:.4f} ms")
    print(f"  = Total:    {estimated_with_bridge:.2f} ms")
    
    print("\n✅ THRESHOLD CHECK:")
    threshold = 50
    if estimated_with_bridge < threshold:
        print(f"  ✅ PASS: {estimated_with_bridge:.2f} ms < {threshold} ms")
    else:
        print(f"  ❌ FAIL: {estimated_with_bridge:.2f} ms > {threshold} ms")
    
    print("\n" + "="*70)
    
    with open("latency_results.txt", "w") as f:
        f.write("LATENCY MEASUREMENT RESULTS\n")
        f.write("="*70 + "\n\n")
        f.write(f"Direct Connection: {avg_direct:.2f} ms\n")
        f.write(f"Security Processing: {processing:.4f} ms\n")
        f.write(f"Estimated Total: {estimated_with_bridge:.2f} ms\n")
        f.write(f"Threshold (50ms): {'MET' if estimated_with_bridge < threshold else 'EXCEEDED'}\n")
    
    print("📁 Saved to: latency_results.txt")