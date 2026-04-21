from netmiko import ConnectHandler
from app.services.driver_factory import get_netmiko_params

RUNNING_CONFIG_COMMANDS = {
    "junos": "show configuration | display set",
    "cisco_ios": "show running-config",
    "cisco_xe": "show running-config",
}


def run_command(device, command: str) -> str:
    params = get_netmiko_params(device)
    with ConnectHandler(**params) as conn:
        if device.platform in ("cisco_ios", "cisco_xe"):
            conn.enable()
        return conn.send_command(command, read_timeout=60)


def run_commands(device, commands: list[str]) -> list[str]:
    params = get_netmiko_params(device)
    results = []
    with ConnectHandler(**params) as conn:
        if device.platform in ("cisco_ios", "cisco_xe"):
            conn.enable()
        for cmd in commands:
            results.append(conn.send_command(cmd, read_timeout=60))
    return results


def get_running_config(device) -> str:
    cmd = RUNNING_CONFIG_COMMANDS.get(device.platform, "show running-config")
    return run_command(device, cmd)


def send_config_set(device, config_lines: list[str]) -> str:
    params = get_netmiko_params(device)
    with ConnectHandler(**params) as conn:
        if device.platform in ("cisco_ios", "cisco_xe"):
            conn.enable()
        output = conn.send_config_set(config_lines, read_timeout=120)
        if device.platform in ("cisco_ios", "cisco_xe"):
            conn.save_config()
        return output


def check_reachability(device) -> bool:
    try:
        params = get_netmiko_params(device)
        params["timeout"] = 10
        with ConnectHandler(**params):
            return True
    except Exception:
        return False
