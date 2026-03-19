import hashlib, base64, bcrypt, sys

# Confirm version
with open("_verify_out.txt", "w") as f:
    f.write(f"bcrypt version: {bcrypt.__version__}\n")

    # Test the exact logic used in security.py
    def prepare(pw):
        return base64.b64encode(hashlib.sha256(pw.encode("utf-8")).digest())

    def hash_pw(pw):
        return bcrypt.hashpw(prepare(pw), bcrypt.gensalt(rounds=12)).decode("utf-8")

    def verify_pw(pw, hashed):
        try:
            return bcrypt.checkpw(prepare(pw), hashed.encode("utf-8"))
        except Exception as e:
            return f"ERROR: {e}"

    # Test 1: short password (like the user's "Sample@12345")
    h1 = hash_pw("Sample@12345")
    r1 = verify_pw("Sample@12345", h1)
    f.write(f"Test1 short pw hash: {'OK' if h1.startswith('$2b$') else 'FAIL'}\n")
    f.write(f"Test1 verify correct: {r1}\n")
    f.write(f"Test1 verify wrong:   {verify_pw('wrong', h1)}\n")

    # Test 2: very long password (200 chars - would break old bcrypt directly)
    long_pw = "A" * 200
    h2 = hash_pw(long_pw)
    r2 = verify_pw(long_pw, h2)
    f.write(f"Test2 long pw (200 chars): {'OK' if h2.startswith('$2b$') else 'FAIL'}\n")
    f.write(f"Test2 verify correct: {r2}\n")

    # Test 3: unicode password
    uni_pw = "密码@2024"
    h3 = hash_pw(uni_pw)
    r3 = verify_pw(uni_pw, h3)
    f.write(f"Test3 unicode pw: {'OK' if h3.startswith('$2b$') else 'FAIL'}\n")
    f.write(f"Test3 verify correct: {r3}\n")

    f.write("ALL TESTS DONE\n")
