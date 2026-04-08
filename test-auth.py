import socket

def test_authentication(username, password):
    # Connect to bridge
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", 5020))
    
    # Send credentials
    auth_message = f"{username}:{password}"
    client.send(auth_message.encode('utf-8'))
    
    # Get response
    response = client.recv(1024).decode('utf-8')
    print(f"Response: {response}")
    
    client.close()

# TEST CASES
print("Testing valid credentials:")
test_authentication("operator1", "pass123")

print("\nTesting invalid credentials:")
test_authentication("hacker", "wrong")