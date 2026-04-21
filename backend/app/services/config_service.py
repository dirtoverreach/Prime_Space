import hashlib
import difflib
from datetime import datetime
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

from app.models.config_backup import ConfigBackup, ConfigTemplate
from app.models.device import Device
from app.services import ssh_service
from app.services.driver_factory import supports_netconf


def pull_config(device: Device, db: Session, source: str = "manual", label: str | None = None, created_by: str = "system") -> ConfigBackup:
    content = ssh_service.get_running_config(device)
    checksum = hashlib.sha256(content.encode()).hexdigest()

    existing = db.query(ConfigBackup).filter_by(device_id=device.id, checksum=checksum).first()
    if existing:
        return existing

    backup = ConfigBackup(
        device_id=device.id,
        content=content,
        checksum=checksum,
        source=source,
        label=label,
        created_by=created_by,
    )
    db.add(backup)
    device.last_backup = datetime.utcnow()
    db.commit()
    db.refresh(backup)
    return backup


def push_config(device: Device, config_snippet: str) -> str:
    lines = [line for line in config_snippet.splitlines() if line.strip()]
    if supports_netconf(device) and device.platform == "junos":
        from app.services import netconf_service
        junos_xml = f"<config><configuration>{config_snippet}</configuration></config>"
        netconf_service.edit_config_netconf(device, junos_xml)
        return "Pushed via NETCONF"
    return ssh_service.send_config_set(device, lines)


def diff_configs(backup_a: ConfigBackup, backup_b: ConfigBackup) -> dict:
    lines_a = backup_a.content.splitlines(keepends=True)
    lines_b = backup_b.content.splitlines(keepends=True)
    diff_lines = list(difflib.unified_diff(
        lines_a, lines_b,
        fromfile=f"backup/{backup_a.id[:8]} ({backup_a.created_at.date()})",
        tofile=f"backup/{backup_b.id[:8]} ({backup_b.created_at.date()})",
    ))
    unified = "".join(diff_lines)
    added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    return {"unified_diff": unified, "lines_added": added, "lines_removed": removed}


def diff_live(device: Device, backup: ConfigBackup) -> dict:
    live_content = ssh_service.get_running_config(device)
    live_backup = ConfigBackup(
        id="live",
        device_id=device.id,
        content=live_content,
        checksum="",
        source="manual",
        created_by="system",
        created_at=datetime.utcnow(),
    )
    return diff_configs(backup, live_backup)


def render_template(template: ConfigTemplate, variables: dict) -> str:
    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(template.body)
    return tmpl.render(**variables)
