import re
from sqlalchemy.orm import Session
from app.models.device import Device, Interface

_IFACE_PREFIXES = [
    ("GigabitEthernet",      re.compile(r"^GigabitEthernet\s*", re.I)),
    ("GigabitEthernet",      re.compile(r"^GigE\s*", re.I)),
    ("GigabitEthernet",      re.compile(r"^Gig\s*", re.I)),
    ("GigabitEthernet",      re.compile(r"^Gi\s*", re.I)),
    ("TenGigabitEthernet",   re.compile(r"^TenGigabitEthernet\s*", re.I)),
    ("TenGigabitEthernet",   re.compile(r"^TenGigE\s*", re.I)),
    ("TenGigabitEthernet",   re.compile(r"^TenGig\s*", re.I)),
    ("TenGigabitEthernet",   re.compile(r"^Ten\s*", re.I)),
    ("TenGigabitEthernet",   re.compile(r"^Te\s*", re.I)),
    ("FastEthernet",         re.compile(r"^FastEthernet\s*", re.I)),
    ("FastEthernet",         re.compile(r"^FastE\s*", re.I)),
    ("FastEthernet",         re.compile(r"^Fa\s*", re.I)),
    ("HundredGigE",          re.compile(r"^HundredGigE\s*", re.I)),
    ("HundredGigE",          re.compile(r"^HundredGig\s*", re.I)),
    ("HundredGigE",          re.compile(r"^Hu\s*", re.I)),
    ("FortyGigabitEthernet", re.compile(r"^FortyGigabitEthernet\s*", re.I)),
    ("FortyGigabitEthernet", re.compile(r"^FortyGig\s*", re.I)),
    ("FortyGigabitEthernet", re.compile(r"^Fo\s*", re.I)),
    ("TwentyFiveGigE",       re.compile(r"^TwentyFiveGigE\s*", re.I)),
    ("TwentyFiveGigE",       re.compile(r"^TwentyFiveGig\s*", re.I)),
    ("TwentyFiveGigE",       re.compile(r"^Twe\s*", re.I)),
    ("Ethernet",             re.compile(r"^Ethernet\s*", re.I)),
    ("Ethernet",             re.compile(r"^Eth\s*", re.I)),
    ("Ethernet",             re.compile(r"^Et\s*", re.I)),
    ("Loopback",             re.compile(r"^Loopback\s*", re.I)),
    ("Loopback",             re.compile(r"^Lo\s*", re.I)),
    ("Vlan",                 re.compile(r"^Vlan\s*", re.I)),
    ("Vlan",                 re.compile(r"^Vl\s*", re.I)),
    ("Serial",               re.compile(r"^Serial\s*", re.I)),
    ("Serial",               re.compile(r"^Se\s*", re.I)),
    ("Tunnel",               re.compile(r"^Tunnel\s*", re.I)),
    ("Tunnel",               re.compile(r"^Tu\s*", re.I)),
    ("Port-channel",         re.compile(r"^Port-channel\s*", re.I)),
    ("Port-channel",         re.compile(r"^Po\s*", re.I)),
    ("mgmt",                 re.compile(r"^management\s*", re.I)),
    ("mgmt",                 re.compile(r"^mgmt\s*", re.I)),
]


def _normalize_iface(name: str) -> str:
    """Expand CDP-abbreviated interface names to NAPALM full form."""
    name = name.strip()
    for full, pattern in _IFACE_PREFIXES:
        m = pattern.match(name)
        if m:
            return full + name[m.end():]
    return name


LLDP_COMMANDS = {
    "junos": "show lldp neighbors",
    "cisco_ios": "show lldp neighbors detail",
    "cisco_xe": "show lldp neighbors detail",
}

CDP_COMMAND = "show cdp neighbors detail"


def _parse_lldp_junos(output: str) -> list[dict]:
    neighbors = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 4 and not line.startswith("Local"):
            neighbors.append({
                "local_interface": parts[0],
                "neighbor_hostname": parts[2],
                "neighbor_interface": parts[3] if len(parts) > 3 else "",
            })
    return neighbors


def _parse_lldp_cisco(output: str) -> list[dict]:
    neighbors = []
    blocks = re.split(r"(?=^-+$)", output, flags=re.MULTILINE)
    for block in blocks:
        local_if = re.search(r"Local Intf:\s+(\S+)", block)
        sys_name = re.search(r"System Name:\s+(\S+)", block)
        port_id = re.search(r"Port id:\s+(\S+)", block)
        if local_if and sys_name:
            neighbors.append({
                "local_interface": local_if.group(1),
                "neighbor_hostname": sys_name.group(1),
                "neighbor_interface": port_id.group(1) if port_id else "",
            })
    return neighbors


def _parse_cdp_cisco(output: str) -> list[dict]:
    neighbors = []
    blocks = re.split(r"-{3,}", output)
    for block in blocks:
        device_id = re.search(r"Device ID:\s+(\S+)", block)
        local_if = re.search(r"Interface:\s+(\S+),", block)
        port_id = re.search(r"Port ID \(outgoing port\):\s+(\S+)", block)
        neighbor_ip = re.search(r"IP address:\s+(\S+)", block)
        if device_id and local_if:
            neighbors.append({
                "local_interface": local_if.group(1),
                "neighbor_hostname": device_id.group(1).split(".")[0],
                "neighbor_interface": port_id.group(1) if port_id else "",
                "neighbor_ip": neighbor_ip.group(1) if neighbor_ip else "",
            })
    return neighbors


def _parse_lldp_openwrt(output: str) -> list[dict]:
    """Parse `lldpcli show neighbors detail` output."""
    neighbors = []
    blocks = re.split(r"(?=^---------------)", output, flags=re.MULTILINE)
    for block in blocks:
        local_if = re.search(r"Interface:\s+(\S+),", block)
        sys_name = re.search(r"SysName:\s+(\S+)", block)
        port_id = re.search(r"PortID:\s+ifname\s+(\S+)", block) or re.search(r"PortDescr:\s+(\S+)", block)
        neighbor_ip = re.search(r"IP:\s+(\d+\.\d+\.\d+\.\d+)", block)
        if local_if and sys_name:
            neighbors.append({
                "local_interface": local_if.group(1),
                "neighbor_hostname": sys_name.group(1).split(".")[0],
                "neighbor_interface": port_id.group(1) if port_id else "",
                "neighbor_ip": neighbor_ip.group(1) if neighbor_ip else "",
            })
    return neighbors


def discover_neighbors(device) -> list[dict]:
    from app.services import ssh_service
    neighbors = []

    if device.platform == "openwrt":
        try:
            output = ssh_service.run_command(device, "lldpcli show neighbors detail")
            neighbors = _parse_lldp_openwrt(output)
        except Exception:
            pass
        return neighbors

    if device.platform == "junos":
        try:
            output = ssh_service.run_command(device, "show lldp neighbors")
            neighbors = _parse_lldp_junos(output)
        except Exception:
            pass
    else:
        # Cisco: CDP first (always enabled), LLDP as fallback
        try:
            output = ssh_service.run_command(device, CDP_COMMAND)
            neighbors = _parse_cdp_cisco(output)
        except Exception:
            pass

        if not neighbors:
            try:
                cmd = LLDP_COMMANDS.get(device.platform, "show lldp neighbors detail")
                output = ssh_service.run_command(device, cmd)
                neighbors = _parse_lldp_cisco(output)
            except Exception:
                pass

    return neighbors


def build_topology_graph(db: Session) -> dict:
    devices = db.query(Device).all()
    device_map = {d.hostname: d for d in devices}
    device_map_by_id = {d.id: d for d in devices}

    nodes = [
        {
            "id": d.id,
            "hostname": d.hostname,
            "ip_address": d.ip_address,
            "platform": d.platform,
            "status": d.status,
            "model": d.model,
            "site": d.site,
        }
        for d in devices
    ]

    edges = []
    seen_edges: set[frozenset] = set()
    for iface in db.query(Interface).filter(Interface.neighbor_device_id.isnot(None)).all():
        edge_key = frozenset([iface.device_id, iface.neighbor_device_id])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            edges.append({
                "source": iface.device_id,
                "target": iface.neighbor_device_id,
                "source_interface": iface.name,
                "target_interface": iface.neighbor_interface,
            })

    return {"nodes": nodes, "edges": edges}


def update_interface_neighbors(device, neighbors: list[dict], db: Session) -> None:
    all_devices = db.query(Device).all()
    device_by_hostname: dict[str, Device] = {}
    for d in all_devices:
        device_by_hostname[d.hostname] = d
        if d.system_hostname:
            device_by_hostname[d.system_hostname] = d
            device_by_hostname[d.system_hostname.split(".")[0]] = d
    device_by_ip = {d.ip_address: d for d in all_devices}

    for neighbor in neighbors:
        local_iface_norm = _normalize_iface(neighbor["local_interface"])

        iface = (
            db.query(Interface).filter_by(device_id=device.id, name=local_iface_norm).first()
            or db.query(Interface).filter_by(device_id=device.id, name=neighbor["local_interface"]).first()
        )
        if not iface:
            iface = Interface(device_id=device.id, name=local_iface_norm)
            db.add(iface)

        neighbor_device = (
            device_by_hostname.get(neighbor["neighbor_hostname"])
            or device_by_ip.get(neighbor.get("neighbor_ip", ""))
        )
        if neighbor_device:
            iface.neighbor_device_id = neighbor_device.id
            iface.neighbor_interface = _normalize_iface(neighbor["neighbor_interface"])
    db.commit()
