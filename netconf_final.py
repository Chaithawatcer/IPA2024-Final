# netconf_final.py
from ncclient import manager
from lxml import etree

IF_FILTER = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>{IFNAME}</name>
    </interface>
  </interfaces>
</filter>
"""

STATE_FILTER = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>{IFNAME}</name>
    </interface>
  </interfaces-state>
</filter>
"""

class NetconfClient:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def _connect(self):
        return manager.connect(
            host=self.host, port=830, username=self.username, password=self.password,
            hostkey_verify=False, look_for_keys=False, allow_agent=False, timeout=15
        )

    def interface_exists(self, ifname):
        with self._connect() as m:
            f = IF_FILTER.format(IFNAME=ifname)
            r = m.get(f)
            return ifname in r.xml

    def create_loopback(self, ifname, ip_cidr):
        ip, prefix = ip_cidr.split("/")
        netmask = self._prefix_to_netmask(int(prefix))
        config = f"""
<config>
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>{ifname}</name>
      <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
      <enabled>true</enabled>
      <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
        <address>
          <ip>{ip}</ip>
          <netmask>{netmask}</netmask>
        </address>
      </ipv4>
    </interface>
  </interfaces>
</config>
"""
        with self._connect() as m:
            r = m.edit_config(target="running", config=config)
            return "<ok/>" in r.xml

    def delete_loopback(self, ifname):
        config = f"""
<config>
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface operation="delete">
      <name>{ifname}</name>
    </interface>
  </interfaces>
</config>
"""
        with self._connect() as m:
            r = m.edit_config(target="running", config=config)
            return "<ok/>" in r.xml

    def set_enabled(self, ifname, enabled: bool):
        val = "true" if enabled else "false"
        config = f"""
<config>
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>{ifname}</name>
      <enabled>{val}</enabled>
    </interface>
  </interfaces>
</config>
"""
        with self._connect() as m:
            r = m.edit_config(target="running", config=config)
            return "<ok/>" in r.xml

    def get_admin_oper_status(self, ifname):
        with self._connect() as m:
            f = STATE_FILTER.format(IFNAME=ifname)
            r = m.get(f)
            xml = etree.fromstring(r.xml.encode())
            ns = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}
            admin = xml.find(".//if:admin-status", ns)
            oper  = xml.find(".//if:oper-status", ns)
            a = admin.text if admin is not None else "down"
            o = oper.text if oper is not None else "down"
            return a, o

    @staticmethod
    def _prefix_to_netmask(p):
        v = (0xffffffff << (32 - p)) & 0xffffffff
        return ".".join(str((v >> i) & 0xff) for i in [24,16,8,0])
