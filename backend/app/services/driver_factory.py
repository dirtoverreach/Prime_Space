from app.security.credentials import get_device_credentials

PLATFORM_TO_NETMIKO = {
    "junos": "juniper_junos",
    "cisco_ios": "cisco_ios",
    "cisco_xe": "cisco_xe",
}

PLATFORM_TO_NAPALM = {
    "junos": "junos",
    "cisco_ios": "ios",
    "cisco_xe": "iosxe",
}

PLATFORM_TO_NCCLIENT = {
    "junos": {"name": "junos"},
    "cisco_xe": {"name": "iosxe"},
}


def get_netmiko_params(device) -> dict:
    creds = get_device_credentials(device)
    device_type = PLATFORM_TO_NETMIKO.get(device.platform, "autodetect")
    params = {
        "device_type": device_type,
        "host": device.ip_address,
        "username": creds["username"],
        "password": creds["password"],
        "timeout": 30,
        "session_timeout": 60,
    }
    if creds["secret"]:
        params["secret"] = creds["secret"]
    return params


def get_napalm_driver_name(device) -> str:
    return PLATFORM_TO_NAPALM.get(device.platform, "ios")


def get_napalm_optional_args(device) -> dict:
    creds = get_device_credentials(device)
    args = {}
    if creds["secret"]:
        args["secret"] = creds["secret"]
    return args


def get_ncclient_params(device) -> dict:
    creds = get_device_credentials(device)
    device_params = PLATFORM_TO_NCCLIENT.get(device.platform)
    if not device_params:
        raise ValueError(f"Platform {device.platform} does not support NETCONF")
    return {
        "host": device.ip_address,
        "port": 830,
        "username": creds["username"],
        "password": creds["password"],
        "device_params": device_params,
        "hostkey_verify": False,
        "timeout": 30,
    }


def supports_netconf(device) -> bool:
    return device.platform in PLATFORM_TO_NCCLIENT
