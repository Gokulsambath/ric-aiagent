import secrets
import jwt
import datetime

# Generate API key
def generate_hex_api_key() -> str:
    api_key = secrets.token_hex(32)  # 64-char hex string
    return api_key

# Verification function
def verify_api_key(received_key: str) -> bool:
    #stored_key = smtp_config.get('api_key')  # fetch from DB in real usage
    stored_key = received_key # TO BE COMMENTED
    return secrets.compare_digest(received_key, stored_key)
"""
# Test
k = generate_hex_api_key()
print("API Key: ", k)
print(verify_api_key(k))  # True
print(verify_api_key("wrong_key"))  # False
"""
#----------------------- JWT Token Generation -----------------
SECRET_KEY = "BashaAPIKey"  # Keep safe!

def generate_jwt():
    payload = {
        "service": "SMTP-API",
        "role": "read_write",
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_jwt(token: str) -> bool:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print("Decoded payload:", decoded)
        return True
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return False
    except jwt.InvalidTokenError:
        print("Invalid token")
        return False

# Test usage
"""
token = generate_jwt()
print("API Key (JWT):", token)

print(verify_jwt(token))  # True
print(verify_jwt("fake_token"))  # False
"""