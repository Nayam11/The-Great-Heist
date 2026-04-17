import urllib.request
import json
import threading

# ⚠️ INSTRUCTION FOR USER:
# You must create a completely FREE Firebase Realtime Database at https://firebase.google.com/
# Once created, copy-paste your Database URL right here! Ensure it has no trailing slash.
FIREBASE_URL = "https://the-great-heist-27acb-default-rtdb.asia-southeast1.firebasedatabase.app"

# Global flags tracked by Pygame's active looping thread
login_status = "idle" # 'idle', 'loading', 'success', 'error', 'wrong_password'
cached_unlocked_levels = 1

def _bg_fetch_levels(username, password):
    global login_status, cached_unlocked_levels
    login_status = "loading"
    url = f"{FIREBASE_URL}/users/{username}.json"
    
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data:
                # Account Exists! Verify strict password requirements.
                if data.get('password') == password:
                    cached_unlocked_levels = data.get('unlocked_levels', 1)
                    login_status = "success"
                else:
                    login_status = "wrong_password"
            else:
                # Ghost Account detected - Generating a new profile automatically with the assigned password!
                cached_unlocked_levels = 1
                _bg_generate_account(username, password, 1)
                login_status = "success"

    except Exception as e:
        print(f"[NETWORKING]: Firebase Auth Sync Error -> {e}")
        # Failsafe Protocol: Let the player continue in "Offline Local Mode"
        cached_unlocked_levels = 1
        login_status = "error"

def login_async(username, password):
    """
    Spools up an independent invisible compute thread to manage the HTTP request.
    This prevents Pygame's main graphical rendering loop from 'crashing' while waiting for internet latency.
    """
    global login_status
    if login_status == "loading": return # Prevent spam clicking!
    
    t = threading.Thread(target=_bg_fetch_levels, args=(username, password), daemon=True)
    t.start()

def _bg_generate_account(username, password, level):
    url = f"{FIREBASE_URL}/users/{username}.json"
    payload = json.dumps({"unlocked_levels": level, "password": password}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method="PATCH", headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            pass # Request synced directly into Cloud!
    except Exception as e:
        print(f"[NETWORKING]: Firebase Registration Error -> {e}")

def _bg_save_level(username, level):
    # Only PATCH unlocked_levels so we never accidentally overwrite/delete their password!
    url = f"{FIREBASE_URL}/users/{username}.json"
    payload = json.dumps({"unlocked_levels": level}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method="PATCH", headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            pass # Request synced directly into Cloud!
    except Exception as e:
        print(f"[NETWORKING]: Firebase Write Sync Error -> {e}")

def save_progress_async(username, level):
    """
    Silent fire-and-forget data patcher sent when finishing a level.
    """
    t = threading.Thread(target=_bg_save_level, args=(username, level), daemon=True)
    t.start()
