# netmiko_final.py
import os
from netmiko import ConnectHandler

def gigabit_status():
    host = os.getenv("ROUTER_IP")
    username = os.getenv("ROUTER_USERNAME", "admin")
    password = os.getenv("ROUTER_PASSWORD", "cisco")

    if not host:
        return "Error: ROUTER_IP is not set"

    device = {
        "device_type": "cisco_xe",   # ใช้ SSH; จะไม่ยุ่งกับ telnetlib
        "host": host,
        "username": username,
        "password": password,
        "port": 22,
        "fast_cli": True,
        "conn_timeout": 15,
        "banner_timeout": 20,
        "auth_timeout": 20,
        "timeout": 30,
        # "session_log": "netmiko_session.log",  # เปิดคอมเมนต์ถ้าอยากเก็บล็อกดีบัก
    }

    with ConnectHandler(**device) as conn:
        out = conn.send_command("show ip interface brief", use_textfsm=True)
        if not out or isinstance(out, str):
            # กรณีไม่มี template textfsm ให้พาร์สเองคร่าว ๆ
            raw = conn.send_command("show ip interface brief")
            lines = [l for l in raw.splitlines() if l.strip() and not l.lower().startswith("interface")]
            status_map = {}
            for l in lines:
                parts = l.split()
                if len(parts) >= 6:
                    name, _, _, _, _, status = parts[:6]
                    if name.startswith("GigabitEthernet"):
                        s = status.lower()
                        if "admin" in s:
                            status_map[name] = "administratively down"
                        elif s == "up":
                            status_map[name] = "up"
                        else:
                            status_map[name] = "down"
        else:
            # มี textfsm -> out เป็น list[dict]
            status_map = {}
            for row in out:
                name = row.get("intf")
                if not name or not name.startswith("GigabitEthernet"):
                    continue
                s = row.get("status", "").lower()
                if s == "up":
                    status_map[name] = "up"
                elif "admin" in s:
                    status_map[name] = "administratively down"
                else:
                    status_map[name] = "down"

        parts = []
        up_cnt = down_cnt = admin_cnt = 0
        for i in range(1, 5):
            key = f"GigabitEthernet{i}"
            st = status_map.get(key, "down")
            parts.append(f"{key} {st}")
            if st == "up":
                up_cnt += 1
            elif st == "administratively down":
                admin_cnt += 1
            else:
                down_cnt += 1

        return f"{', '.join(parts)} -> {up_cnt} up, {down_cnt} down, {admin_cnt} administratively down"
