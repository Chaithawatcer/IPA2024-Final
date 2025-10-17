# ipa2024_final.py
import os
import sys
import json
import requests
from dotenv import load_dotenv

from restconf_final import RestconfClient
from netconf_final import NetconfClient
from netmiko_final import get_gigabit_status_string
from ansible_final import run_ansible_showrun_and_get_path

load_dotenv()

WEBEX_TOKEN = os.getenv("WEBEX_TOKEN")
WEBEX_ROOM_ID = os.getenv("WEBEX_ROOM_ID")
STUDENT_ID = os.getenv("STUDENT_ID")
USE_RESTCONF = os.getenv("USE_RESTCONF", "true").lower() == "true"

ROUTER_IP = os.getenv("ROUTER_IP")
ROUTER_USERNAME = os.getenv("ROUTER_USERNAME", "admin")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD", "cisco")

def send_webex_message(text: str):
    url = "https://webexapis.com/v1/messages"
    headers = {"Authorization": f"Bearer {WEBEX_TOKEN}"}
    data = {"roomId": WEBEX_ROOM_ID, "markdown": text}
    r = requests.post(url, headers=headers, data=data, timeout=15)
    r.raise_for_status()

def send_webex_file(filepath: str, caption: str):
    url = "https://webexapis.com/v1/messages"
    headers = {"Authorization": f"Bearer {WEBEX_TOKEN}"}
    files = {"files": open(filepath, "rb")}
    data = {"roomId": WEBEX_ROOM_ID, "text": caption}
    r = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    r.raise_for_status()

def last3_digits(sid: str):
    last3 = sid[-3:].zfill(3)
    x = int(last3[0])
    y = int(last3[1:])
    return x, y

def loopback_name(sid: str):
    return f"Loopback{sid}"

def loopback_ip_cidr(sid: str):
    x, y = last3_digits(sid)
    return f"172.{x}.{y}.1/24"

def get_driver():
    if USE_RESTCONF:
        return RestconfClient(ROUTER_IP, ROUTER_USERNAME, ROUTER_PASSWORD)
    else:
        return NetconfClient(ROUTER_IP, ROUTER_USERNAME, ROUTER_PASSWORD)

def handle_l1_commands(student_id: str, command: str):
    """
    Part 1: create / delete / enable / disable / status
    """
    if student_id != STUDENT_ID:
        return  # ignore other student IDs

    drv = get_driver()
    lname = loopback_name(student_id)

    if command == "create":
        if not drv.interface_exists(lname):
            ip_cidr = loopback_ip_cidr(student_id)
            ok = drv.create_loopback(lname, ip_cidr)
            if ok:
                send_webex_message(f"Interface {lname} is created successfully")
            else:
                send_webex_message(f"Cannot create: Interface {lname}")
        else:
            send_webex_message(f"Cannot create: Interface {lname}")

    elif command == "delete":
        if drv.interface_exists(lname):
            ok = drv.delete_loopback(lname)
            if ok:
                send_webex_message(f"Interface {lname} is deleted successfully")
            else:
                send_webex_message(f"Cannot delete: Interface {lname}")
        else:
            send_webex_message(f"Cannot delete: Interface {lname}")

    elif command == "enable":
        if drv.interface_exists(lname):
            ok = drv.set_enabled(lname, True)
            if ok:
                send_webex_message(f"Interface {lname} is enabled successfully")
            else:
                send_webex_message(f"Cannot enable: Interface {lname}")
        else:
            send_webex_message(f"Cannot enable: Interface {lname}")

    elif command == "disable":
        if drv.interface_exists(lname):
            ok = drv.set_enabled(lname, False)
            if ok:
                send_webex_message(f"Interface {lname} is shutdowned successfully")
            else:
                send_webex_message(f"Cannot shutdown: Interface {lname}")
        else:
            send_webex_message(f"Cannot shutdown: Interface {lname}")

    elif command == "status":
        if drv.interface_exists(lname):
            admin, oper = drv.get_admin_oper_status(lname)
            if admin == "up" and oper == "up":
                send_webex_message(f"Interface {lname} is enabled")
            elif admin == "down" and oper == "down":
                send_webex_message(f"Interface {lname} is disabled")
            else:
                # สถานะไม่ตรง spec เป๊ะ ๆ แสดงดิบ ๆ ไว้ช่วย debug
                send_webex_message(f"Interface {lname}: admin={admin}, oper={oper}")
        else:
            send_webex_message(f"No Interface {lname}")

def handle_l2_commands(student_id: str, command: str):
    """
    Part 2: gigabit_status / showrun
    """
    if student_id != STUDENT_ID:
        return

    if command == "gigabit_status":
        # Netmiko + TextFSM
        s = get_gigabit_status_string(
            host=ROUTER_IP, username=ROUTER_USERNAME, password=ROUTER_PASSWORD
        )
        send_webex_message(s)

    elif command == "showrun":
        # เรียก ansible playbook แล้วส่งไฟล์
        path, ok = run_ansible_showrun_and_get_path()
        if ok and path and os.path.exists(path):
            try:
                send_webex_file(path, "show running-config")
            except Exception:
                send_webex_message("Error: Ansible (upload)")
        else:
            send_webex_message("Error: Ansible")

def parse_message(msg: str):
    # รูปแบบข้อความ: "/<studentID> <command>"
    msg = msg.strip()
    if not msg.startswith("/"):
        return None, None
    parts = msg[1:].split()
    if len(parts) != 2:
        return None, None
    return parts[0], parts[1].lower()

def main():
    """
    ใช้ได้ 2 แบบ:
    1) ยัดข้อความผ่าน argv เช่น:
       python ipa2024_final.py "/66070046 create"
    2) อ่านจาก STDIN (เช่น webhook ต่อเข้ามา)
    """
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        raw = sys.stdin.read()

    sid, cmd = parse_message(raw)
    if not sid or not cmd:
        print("Bad command format. Use: /<studentID> <command>")
        return

    if cmd in {"create","delete","enable","disable","status"}:
        handle_l1_commands(sid, cmd)
    elif cmd in {"gigabit_status","showrun"}:
        handle_l2_commands(sid, cmd)
    else:
        send_webex_message(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
