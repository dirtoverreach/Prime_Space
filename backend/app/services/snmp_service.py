from pysnmp.hlapi import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, getCmd, nextCmd,
)
from app.security.credentials import get_device_credentials

# OIDs
OID_CPU = "1.3.6.1.2.1.25.3.3.1.2"          # HOST-RESOURCES-MIB hrProcessorLoad
OID_MEM_STORAGE_TYPE = "1.3.6.1.2.1.25.2.3.1.2"  # hrStorageType
OID_MEM_USED = "1.3.6.1.2.1.25.2.3.1.6"      # hrStorageUsed
OID_MEM_SIZE = "1.3.6.1.2.1.25.2.3.1.5"      # hrStorageSize
OID_SYSUPTIME = "1.3.6.1.2.1.1.3.0"          # sysUpTime
OID_IF_DESCR = "1.3.6.1.2.1.2.2.1.2"
OID_IF_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"
OID_IF_OUT_OCTETS = "1.3.6.1.2.1.2.2.1.16"
OID_IF_IN_ERRORS = "1.3.6.1.2.1.2.2.1.14"
OID_IF_OUT_ERRORS = "1.3.6.1.2.1.2.2.1.20"
OID_IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"


def _community(device) -> CommunityData:
    creds = get_device_credentials(device)
    return CommunityData(creds["snmp_community"], mpModel=0 if device.snmp_version == "v2c" else 1)


def _transport(device) -> UdpTransportTarget:
    return UdpTransportTarget((device.ip_address, 161), timeout=5, retries=1)


def _walk(device, oid: str) -> dict:
    results = {}
    for (err_ind, err_stat, err_idx, var_binds) in nextCmd(
        SnmpEngine(), _community(device), _transport(device), ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False,
    ):
        if err_ind or err_stat:
            break
        for var_bind in var_binds:
            results[str(var_bind[0])] = var_bind[1].prettyPrint()
    return results


def _get(device, oid: str) -> str | None:
    for (err_ind, err_stat, _, var_binds) in getCmd(
        SnmpEngine(), _community(device), _transport(device), ContextData(),
        ObjectType(ObjectIdentity(oid)),
    ):
        if err_ind or err_stat:
            return None
        return var_binds[0][1].prettyPrint()
    return None


def poll_device(device) -> dict:
    cpu_values = list(_walk(device, OID_CPU).values())
    cpu_percent = sum(float(v) for v in cpu_values) / len(cpu_values) if cpu_values else None

    mem_used_map = _walk(device, OID_MEM_USED)
    mem_size_map = _walk(device, OID_MEM_SIZE)
    mem_used_percent = None
    if mem_used_map and mem_size_map:
        used = sum(float(v) for v in mem_used_map.values())
        size = sum(float(v) for v in mem_size_map.values())
        mem_used_percent = (used / size * 100) if size else None

    uptime_raw = _get(device, OID_SYSUPTIME)
    uptime_seconds = float(uptime_raw) / 100 if uptime_raw else None

    return {
        "cpu_percent": cpu_percent,
        "mem_used_percent": mem_used_percent,
        "uptime_seconds": uptime_seconds,
    }


def poll_interfaces(device) -> list[dict]:
    descr = _walk(device, OID_IF_DESCR)
    in_octets = _walk(device, OID_IF_IN_OCTETS)
    out_octets = _walk(device, OID_IF_OUT_OCTETS)
    in_errors = _walk(device, OID_IF_IN_ERRORS)
    out_errors = _walk(device, OID_IF_OUT_ERRORS)
    oper_status = _walk(device, OID_IF_OPER_STATUS)

    interfaces = []
    for oid_key, name in descr.items():
        idx = oid_key.split(".")[-1]
        interfaces.append({
            "index": idx,
            "name": name,
            "in_octets": in_octets.get(f"{OID_IF_IN_OCTETS}.{idx}", 0),
            "out_octets": out_octets.get(f"{OID_IF_OUT_OCTETS}.{idx}", 0),
            "in_errors": in_errors.get(f"{OID_IF_IN_ERRORS}.{idx}", 0),
            "out_errors": out_errors.get(f"{OID_IF_OUT_ERRORS}.{idx}", 0),
            "oper_status": "up" if oper_status.get(f"{OID_IF_OPER_STATUS}.{idx}") == "1" else "down",
        })
    return interfaces
