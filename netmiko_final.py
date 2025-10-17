# netmiko_final.py
from netmiko import ConnectHandler

def get_gigabit_status_string(host, username, password):
    device = {
        "device_type": "cisco_xe",
        "host": host,
        "username": username,
        "password": password,
    }
    with ConnectHandler(**device) as conn:
        # ใช้ show ip interface brief เพื่อดูสถานะ
        out = conn.send_command("show ip interface brief", use_textfsm=True)
        # out เป็น list ของ dict (ถ้า textfsm ใช้ได้)
        # ตรงตาม lab: สนใจเฉพาะ GigabitEthernet1-4
        status_map = {}   # name -> ("up"/"down"/"administratively down")
        for row in out:
            name = row.get("intf")
            if not name or not name.startswith("GigabitEthernet"):
                continue
            # columns ที่ TextFSM template ให้มา:
            # 'status' (protocol), 'proto' (line protocol) ต่าง template อาจต่างกัน
            # แต่ IOS XE มักมี 'status' เป็น 'up'/'down'/'administratively down'
            status = row.get("status", "").lower()
            if status == "up":
                status_map[name] = "up"
            elif "admin" in status:
                status_map[name] = "administratively down"
            else:
                status_map[name] = "down"

        # ร้อยเรียงข้อความตามรูปแบบโจทย์
        parts = []
        up_cnt = down_cnt = admin_cnt = 0
        for i in range(1,5):
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
