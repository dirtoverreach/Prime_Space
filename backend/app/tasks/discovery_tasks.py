import ipaddress
from datetime import datetime
from app.tasks.celery_app import celery
from app.database import SessionLocal
from app.models.device import Device
from app.security.credentials import encrypt


@celery.task(bind=True, name="app.tasks.discovery_tasks.discover_network")
def discover_network(self, cidr: str, username: str, password: str,
                     enable_secret: str = "", snmp_community: str = "public",
                     snmp_version: str = "v2c"):
    db = SessionLocal()
    discovered = []
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        for ip in network.hosts():
            ip_str = str(ip)
            try:
                _probe_and_upsert(db, ip_str, username, password, enable_secret, snmp_community, snmp_version)
                discovered.append(ip_str)
            except Exception:
                pass
    finally:
        db.close()
    return {"discovered": discovered, "count": len(discovered)}


def _probe_and_upsert(db, ip: str, username: str, password: str,
                      enable_secret: str, snmp_community: str, snmp_version: str):
    import napalm
    from app.services.driver_factory import PLATFORM_TO_NAPALM

    # Try NAPALM-supported platforms first
    for platform, driver_name in PLATFORM_TO_NAPALM.items():
        try:
            driver_cls = napalm.get_network_driver(driver_name)
            optional_args = {"secret": enable_secret} if enable_secret else {}
            with driver_cls(hostname=ip, username=username, password=password,
                            optional_args=optional_args) as conn:
                facts = conn.get_facts()
                hostname = facts.get("hostname") or ip
                existing = db.query(Device).filter_by(hostname=hostname).first()
                if not existing:
                    existing = db.query(Device).filter_by(ip_address=ip).first()
                if not existing:
                    existing = Device(ip_address=ip)
                    db.add(existing)

                existing.hostname = hostname
                existing.system_hostname = facts.get("hostname") or facts.get("fqdn")
                existing.ip_address = ip
                existing.platform = platform
                existing.username = username
                existing.password_encrypted = encrypt(password)
                existing.enable_secret_encrypted = encrypt(enable_secret) if enable_secret else None
                existing.snmp_community_encrypted = encrypt(snmp_community)
                existing.snmp_version = snmp_version
                existing.serial_number = facts.get("serial_number")
                existing.model = facts.get("model")
                existing.os_version = facts.get("os_version")
                existing.status = "reachable"
                existing.last_seen = datetime.utcnow()
                db.commit()
                return
        except Exception:
            continue

    # Fallback: try OpenWrt via SSH
    _probe_openwrt(db, ip, username, password, snmp_community, snmp_version)


def _probe_openwrt(db, ip: str, username: str, password: str,
                   snmp_community: str, snmp_version: str):
    import re
    from netmiko import ConnectHandler
    params = {
        "device_type": "linux",
        "host": ip,
        "username": username,
        "password": password,
        "timeout": 15,
    }
    with ConnectHandler(**params) as conn:
        hostname_raw = conn.send_command("uname -n").strip().splitlines()[-1].strip()
        release_raw = conn.send_command("cat /etc/openwrt_release")

    if not hostname_raw:
        return

    os_version, model = None, None
    for line in release_raw.splitlines():
        if line.startswith("DISTRIB_RELEASE"):
            os_version = line.split("=", 1)[-1].strip().strip('"')
        elif line.startswith("DISTRIB_TARGET"):
            model = line.split("=", 1)[-1].strip().strip('"')

    existing = db.query(Device).filter_by(ip_address=ip).first()
    if not existing:
        existing = Device(ip_address=ip)
        db.add(existing)

    existing.hostname = hostname_raw
    existing.system_hostname = hostname_raw
    existing.ip_address = ip
    existing.platform = "openwrt"
    existing.username = username
    existing.password_encrypted = encrypt(password)
    existing.snmp_community_encrypted = encrypt(snmp_community)
    existing.snmp_version = snmp_version
    existing.os_version = os_version
    existing.model = model
    existing.status = "reachable"
    existing.last_seen = datetime.utcnow()
    db.commit()


@celery.task(bind=True, name="app.tasks.discovery_tasks.sync_device_facts")
def sync_device_facts(self, device_id: str):
    db = SessionLocal()
    device = None
    try:
        device = db.query(Device).get(device_id)
        if not device:
            return {"error": "device not found"}

        from app.services.driver_factory import NAPALM_UNSUPPORTED
        if device.platform in NAPALM_UNSUPPORTED:
            _sync_openwrt(device, db)
        else:
            _sync_napalm(device, db)

        db.commit()
        return {"status": "synced", "hostname": device.hostname}
    except Exception as e:
        if device:
            device.status = "unreachable"
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()


def _sync_napalm(device, db):
    import napalm
    from app.services.driver_factory import get_napalm_driver_name, get_napalm_optional_args
    from app.security.credentials import get_device_credentials
    from app.models.device import Interface

    creds = get_device_credentials(device)
    driver_cls = napalm.get_network_driver(get_napalm_driver_name(device))
    with driver_cls(hostname=device.ip_address, username=creds["username"],
                    password=creds["password"],
                    optional_args=get_napalm_optional_args(device)) as conn:
        facts = conn.get_facts()
        interfaces = conn.get_interfaces()

    device.system_hostname = facts.get("hostname") or facts.get("fqdn")
    device.serial_number = facts.get("serial_number")
    device.model = facts.get("model")
    device.os_version = facts.get("os_version")
    device.status = "reachable"
    device.last_seen = datetime.utcnow()

    for iface_name, iface_data in interfaces.items():
        iface = db.query(Interface).filter_by(device_id=device.id, name=iface_name).first()
        if not iface:
            iface = Interface(device_id=device.id, name=iface_name)
            db.add(iface)
        iface.description = iface_data.get("description", "")
        iface.admin_status = "up" if iface_data.get("is_enabled") else "down"
        iface.oper_status = "up" if iface_data.get("is_up") else "down"
        speed = iface_data.get("speed", 0)
        iface.speed_mbps = int(speed) if speed else None
        iface.mac_address = iface_data.get("mac_address", "")


def _sync_openwrt(device, db):
    import re
    from app.services.ssh_service import run_commands
    from app.models.device import Interface

    outputs = run_commands(device, [
        "uname -n",
        "cat /etc/openwrt_release",
        "ip -o link show",
    ])
    hostname_raw, release_raw, links_raw = outputs

    device.system_hostname = hostname_raw.strip().splitlines()[-1].strip()
    device.status = "reachable"
    device.last_seen = datetime.utcnow()

    for line in release_raw.splitlines():
        if line.startswith("DISTRIB_RELEASE"):
            device.os_version = line.split("=", 1)[-1].strip().strip('"')
        elif line.startswith("DISTRIB_TARGET"):
            device.model = line.split("=", 1)[-1].strip().strip('"')

    for line in links_raw.splitlines():
        m = re.match(r"\d+:\s+(\S+)@?\S*:\s+<([^>]+)>.*\s+link/\S+\s+(\S+)", line)
        if not m:
            continue
        name, flags, mac = m.group(1), m.group(2), m.group(3)
        iface = db.query(Interface).filter_by(device_id=device.id, name=name).first()
        if not iface:
            iface = Interface(device_id=device.id, name=name)
            db.add(iface)
        iface.admin_status = "up" if "UP" in flags else "down"
        iface.oper_status = "up" if "LOWER_UP" in flags else "down"
        iface.mac_address = mac if mac != "00:00:00:00:00:00" else ""
    finally:
        db.close()
