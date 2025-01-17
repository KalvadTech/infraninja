import json
import random
from datetime import datetime
from pathlib import Path

# Constants
HISTORY_FILE = Path.home() / ".infraninja" / "history.json"
MAX_HISTORY = 5

def save_access_history(hostname=None, group=None, project=None):
    """Save server access history."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    history = {
        "last_access": datetime.now().isoformat(),
        "hostname": hostname,
        "group": group,
        "project": project
    }
    
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    except Exception:
        pass  # Fail silently if we can't write history

def get_last_access():
    """Get the last access history."""
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def show_motd(hostname=None, group=None, project=None):
    """Display an enhanced Message of the Day when infraninja starts."""
    messages = [
        "Welcome to InfraNinja - Your Infrastructure at Your Command 🥷",
        "InfraNinja: Silently Managing Your Infrastructure 🌐",
        "Ninja Skills Activated - Ready to Deploy! 🚀",
        "The Art of Infrastructure - InfraNinja at Your Service 🛠️"
    ]
    
    current_time = datetime.now()
    border = "=" * 70
    
    # Save current access
    save_access_history(hostname, group, project)
    
    # Get last access info
    last_access = get_last_access()
    
    print(f"\n{border}")
    print(f"{random.choice(messages)}")
    print(f"{border}")
    print(f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if hostname:
        print(f"Target Host: {hostname}")
    if group:
        print(f"Group: {group}")
    if project:
        print(f"Project: {project}")
        
    if last_access and last_access['last_access'] != current_time.isoformat():
        last_time = datetime.fromisoformat(last_access['last_access'])
        print(f"\nLast Access: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if last_access.get('hostname'):
            print(f"Last Host: {last_access['hostname']}")
        if last_access.get('group'):
            print(f"Last Group: {last_access['group']}")
            
    print(f"{border}\n")