#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys

def main():
    print("--- Kairos Codex CLI Proof of Concept ---")
    
    # 1. Detect Codex installation
    codex_path = shutil.which("codex")
    if not codex_path:
        print("[FAIL] Codex CLI not found in PATH.")
        sys.exit(1)
    print(f"[OK] Codex installed at: {codex_path}")
    
    # 2. Detect authenticated session & 3. Show connection state
    try:
        doctor_proc = subprocess.run(
            ["codex", "doctor", "--json"], 
            capture_output=True, text=True, check=True
        )
        doctor_data = json.loads(doctor_proc.stdout)
    except Exception as e:
        print(f"[FAIL] Could not execute codex doctor: {e}")
        sys.exit(1)
        
    auth_state = doctor_data.get("checks", {}).get("auth.credentials", {})
    if auth_state.get("status") == "ok":
        print(f"[OK] Authenticated session detected: {auth_state.get('summary')}")
        details = auth_state.get("details", {})
        print(f"     Mode: {details.get('auth mode', details.get('stored auth mode'))}")
        print(f"     File: {details.get('auth file')}")
    else:
        print(f"[FAIL] Authenticated session not found or unhealthy.")
        sys.exit(1)
        
    # Check websocket connection state just for more info
    ws_state = doctor_data.get("checks", {}).get("network.websocket_reachability", {})
    if ws_state.get("status") == "ok":
        print(f"[OK] Connection State: {ws_state.get('summary')}")
    else:
        print(f"[WARN] Connection State: Unreachable or not OK.")

    # 4. Send one simple prompt through the official Codex SDK/CLI
    prompt = "say hello in one word"
    print(f"\nSending prompt to Codex: '{prompt}'")
    try:
        # Use stdin=subprocess.DEVNULL to prevent blocking if it waits for input
        exec_proc = subprocess.run(
            ["codex", "exec", prompt],
            stdin=subprocess.DEVNULL,
            capture_output=True, text=True, check=True
        )
        
        # 5. Return the response
        # The response includes headers, we just print the raw stdout for the PoC
        print("\n--- Codex Response ---")
        print(exec_proc.stdout.strip())
        print("----------------------")
        print("[SUCCESS] Proof of Concept completed successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Codex exec failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
