import os
import sys
import json
import base64
from cryptography.fernet import Fernet
from soc.bus.event_queue import EventBus

def test_bus_hardening():
    # 0. Cleanup
    soc_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "soc")
    bus_dir = os.path.join(soc_root, "bus", "hardening_test")
    if os.path.exists(bus_dir):
        import shutil
        shutil.rmtree(bus_dir)
    os.makedirs(bus_dir, exist_ok=True)

    # 1. Setup a test key
    test_key = Fernet.generate_key().decode()
    os.environ["SOC_BUS_KEY"] = test_key
    
    print(f"Testing with SOC_BUS_KEY: {test_key}")
    
    bus = EventBus("hardening_test")
    test_payload = {"secret_code": "ANTIGRAVITY-ALPHA", "priority": "CRITICAL"}
    
    # 2. PUSH
    filename = bus.push(test_payload)
    # The bus is in soc/bus/
    soc_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "soc")
    filepath = os.path.join(soc_root, "bus", "hardening_test", filename)
    
    # 3. VERIFY ENCRYPTION ON DISK
    with open(filepath, "r") as f:
        disk_data = json.load(f)
        
    print(f"Disk content: {json.dumps(disk_data, indent=2)}")
    
    if disk_data["secure"] is True and "ANTIGRAVITY-ALPHA" not in json.dumps(disk_data):
        print("[SUCCESS] Data is encrypted on disk.")
    else:
        print("[FAILURE] Data is NOT encrypted on disk!")
        sys.exit(1)
        
    # 4. POP
    received = bus.pop()
    print(f"Received payload: {received}")
    
    if received == test_payload:
        print("[SUCCESS] Round-trip decryption and verification successful.")
    else:
        print("[FAILURE] Retreived payload does not match!")
        sys.exit(1)

    # 5. TAMPER TEST
    # Push another one
    fn2 = bus.push({"msg": "tamper-me"})
    fp2 = os.path.join(soc_root, "bus", "hardening_test", fn2)
    
    # Tamper with the payload
    with open(fp2, "r") as f:
        tamper_data = json.load(f)
    
    tamper_data["payload"] = "TamperedUnsignedData" # Signature will now be invalid
    
    with open(fp2, "w") as f:
        json.dump(tamper_data, f)
        
    # Attempt to POP
    tampered_result = bus.pop()
    if tampered_result is None:
        print("[SUCCESS] Tampered message was REJECTED by POP.")
    else:
        print("[FAILURE] Tampered message was ACCEPTED!")
        sys.exit(1)

if __name__ == "__main__":
    test_bus_hardening()
