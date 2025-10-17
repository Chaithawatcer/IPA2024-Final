# restconf_final.py
import requests
from requests.auth import HTTPBasicAuth

class RestconfClient:
    def __init__(self, host, username, password):
        self.base = f"https://{host}/restconf/data"
        self.state = f"https://{host}/restconf/data"
        self.auth = HTTPBasicAuth(username, password)
        self.verify = False  # lab มักใช้ self-signed cert
        self.headers = {
            "Content-Type": "application/yang-data+json",
            "Accept": "application/yang-data+json"
        }

    def _if_path(self, ifname):
        # ietf-interfaces:interfaces/interface={name}
        return f"{self.base}/ietf-interfaces:interfaces/interface={ifname}"

    def interface_exists(self, ifname):
        r = requests.get(self._if_path(ifname), auth=self.auth, headers=self.headers, verify=self.verify, timeout=10)
        return r.status_code == 200

    def create_loopback(self, ifname, ip_cidr):
        # ip_cidr: "172.x.y.1/24"
        ip, prefix = ip_cidr.split("/")
        body = {
            "ietf-interfaces:interface": {
                "name": ifname,
                "type": "iana-if-type:softwareLoopback",
                "enabled": True,
                "ietf-ip:ipv4": {
                    "address": [
                        {"ip": ip, "netmask": self._prefix_to_netmask(int(prefix))}
                    ]
                }
            }
        }
        r = requests.put(self._if_path(ifname), json=body, auth=self.auth,
                         headers=self.headers, verify=self.verify, timeout=15)
        return r.status_code in (200,201,204)

    def delete_loopback(self, ifname):
        r = requests.delete(self._if_path(ifname), auth=self.auth, headers=self.headers, verify=self.verify, timeout=10)
        return r.status_code in (200,204)

    def set_enabled(self, ifname, enabled: bool):
        body = {"ietf-interfaces:interface": {"enabled": enabled}}
        r = requests.patch(self._if_path(ifname), json=body, auth=self.auth,
                           headers=self.headers, verify=self.verify, timeout=10)
        return r.status_code in (200,204)

    def get_admin_oper_status(self, ifname):
        # interfaces-state
        url = f"{self.state}/ietf-interfaces:interfaces-state/interface={ifname}"
        r = requests.get(url, auth=self.auth, headers=self.headers, verify=self.verify, timeout=10)
        if r.status_code != 200:
            # ถ้า state path ไม่เจอ ลอง fallback อ่าน config enabled
            # แล้ววัด oper จาก presence (simple heuristic)
            cfg = requests.get(self._if_path(ifname), auth=self.auth, headers=self.headers, verify=self.verify, timeout=10)
            if cfg.ok:
                enabled = cfg.json().get("ietf-interfaces:interface", {}).get("enabled", False)
                return ("up" if enabled else "down", "down")
            return "down","down"
        data = r.json().get("ietf-interfaces:interface", {})
        admin = data.get("admin-status", "down")
        oper  = data.get("oper-status", "down")
        return admin, oper

    @staticmethod
    def _prefix_to_netmask(p):
        v = (0xffffffff << (32 - p)) & 0xffffffff
        return ".".join(str((v >> i) & 0xff) for i in [24,16,8,0])
