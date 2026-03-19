"""
Quick test to verify password hashing fixes work correctly
"""
import sys
sys.path.insert(0, '.')

from app.core.security import get_password_hash, verify_password

def test_password_hashing():
    print("Testing password hashing fixes...")
    
    # Test 1: Normal password
    print("\n1. Testing normal password (12 chars)...")
    password1 = "MyPassword123"
    hash1 = get_password_hash(password1)
    assert verify_password(password1, hash1), "Normal password failed!"
    print("   ✓ Normal password works")
    
    # Test 2: Long password (80 chars - exceeds 72 byte limit)
    print("\n2. Testing long password (80 chars)...")
    password2 = "A" * 80
    hash2 = get_password_hash(password2)
    assert verify_password(password2, hash2), "Long password failed!"
    print("   ✓ Long password works (auto-truncated)")
    
    # Test 3: Unicode password
    print("\n3. Testing unicode password...")
    password3 = "Пароль123密码"
    hash3 = get_password_hash(password3)
    assert verify_password(password3, hash3), "Unicode password failed!"
    print("   ✓ Unicode password works")
    
    # Test 4: Very long unicode (exceeds 72 bytes)
    print("\n4. Testing very long unicode password...")
    password4 = "密码" * 20  # Each character is 3 bytes in UTF-8
    hash4 = get_password_hash(password4)
    assert verify_password(password4, hash4), "Long unicode password failed!"
    print("   ✓ Long unicode password works (auto-truncated)")
    
    # Test 5: Edge case - exactly 72 bytes
    print("\n5. Testing exactly 72 byte password...")
    password5 = "A" * 72
    hash5 = get_password_hash(password5)
    assert verify_password(password5, hash5), "72-byte password failed!"
    print("   ✓ 72-byte password works")
    
    print("\n" + "="*50)
    print("✅ All password hashing tests passed!")
    print("="*50)

if __name__ == "__main__":
    try:
        test_password_hashing()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
