# ansible_final.py
import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

def run_ansible_showrun_and_get_path():
    cwd = os.path.join(os.path.dirname(__file__), "ansible")
    env = os.environ.copy()
    try:
        p = subprocess.run(
            ["ansible-playbook", "playbook_showrun.yml"],
            cwd=cwd, env=env, capture_output=True, text=True, timeout=180
        )
        if p.returncode != 0:
            return None, False
        # หาไฟล์ผลลัพธ์ตามตัวแปร
        sid = env.get("ANSIBLE_STUDENT_ID", "unknown")
        rname = env.get("ANSIBLE_ROUTER_NAME", "CSR1KV")
        path = os.path.join(cwd, f"show_run_{sid}_{rname}.txt")
        return path, os.path.exists(path)
    except Exception:
        return None, False
