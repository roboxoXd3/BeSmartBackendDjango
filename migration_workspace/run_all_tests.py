import os
import subprocess
import sys

def main():
    test_files = [
        "test_api.py",
        "migration_workspace/test_batch1.py",
        "migration_workspace/test_batch2.py",
        "migration_workspace/verify_batch6_auth.py",
        "migration_workspace/verify_batch7_sdk.py"
    ]
    
    passed = 0
    failed = 0
    
    for f in test_files:
        print(f"\n--- Running {f} ---")
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = os.getcwd()
            res = subprocess.run([sys.executable, f], capture_output=True, text=True, env=env)
            print(res.stdout)
            if res.stderr:
                print(res.stderr, file=sys.stderr)
            
            if res.returncode == 0:
                print(f"✅ {f} SUCCESS")
                passed += 1
            else:
                print(f"❌ {f} FAILED with exit code {res.returncode}")
                failed += 1
        except Exception as e:
            print(f"❌ {f} FAILED with exception: {e}")
            failed += 1

    print("\n--- Test Summary ---")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
