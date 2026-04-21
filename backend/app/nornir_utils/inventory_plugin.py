from nornir.core.inventory import Inventory, Host, Hosts, Group, Groups, ConnectionOptions
from app.security.credentials import get_device_credentials
from app.services.driver_factory import PLATFORM_TO_NETMIKO


class DBInventory:
    """Nornir inventory plugin that builds host list from a list of Device ORM objects."""

    def __init__(self, devices: list):
        self.devices = devices

    def load(self) -> Inventory:
        hosts = Hosts()
        groups = Groups()

        for device in self.devices:
            creds = get_device_credentials(device)
            device_type = PLATFORM_TO_NETMIKO.get(device.platform, "autodetect")

            hosts[device.hostname] = Host(
                name=device.hostname,
                hostname=device.ip_address,
                username=creds["username"],
                password=creds["password"],
                platform=device_type,
                data={
                    "device_id": device.id,
                    "platform": device.platform,
                    "enable_secret": creds["secret"],
                },
                connection_options={
                    "netmiko": ConnectionOptions(
                        extras={
                            "secret": creds["secret"],
                            "timeout": 30,
                        }
                    )
                },
            )

        return Inventory(hosts=hosts, groups=groups)
