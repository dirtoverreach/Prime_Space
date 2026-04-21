from ncclient import manager
from app.services.driver_factory import get_ncclient_params, supports_netconf


def get_config_netconf(device, source: str = "running") -> str:
    if not supports_netconf(device):
        raise ValueError(f"Platform {device.platform} does not support NETCONF")
    params = get_ncclient_params(device)
    with manager.connect(**params) as m:
        result = m.get_config(source=source)
        return result.data_xml


def edit_config_netconf(device, config_xml: str, target: str = "candidate") -> None:
    if not supports_netconf(device):
        raise ValueError(f"Platform {device.platform} does not support NETCONF")
    params = get_ncclient_params(device)
    with manager.connect(**params) as m:
        m.edit_config(target=target, config=config_xml)
        if target == "candidate":
            m.commit()


def get_interfaces_netconf(device) -> list[dict]:
    params = get_ncclient_params(device)
    interfaces = []
    with manager.connect(**params) as m:
        if device.platform == "junos":
            result = m.get(filter=("subtree", "<interfaces xmlns='http://yang.juniper.net/junos-es/conf/interfaces'/>"))
        else:
            result = m.get(filter=("subtree", "<interfaces xmlns='urn:ietf:params:xml:ns:yang:ietf-interfaces'/>"))
        # Return raw XML — parsing is caller's responsibility
        interfaces.append({"raw_xml": result.data_xml})
    return interfaces
