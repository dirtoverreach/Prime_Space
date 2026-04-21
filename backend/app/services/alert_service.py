import operator as op
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertRule
from app.models.device import Device

OPERATORS = {
    "gt": op.gt,
    "lt": op.lt,
    "gte": op.ge,
    "lte": op.le,
}


def evaluate_rules(device: Device, metrics: dict, db: Session) -> list[Alert]:
    rules = db.query(AlertRule).filter(
        AlertRule.enabled == True,
        (AlertRule.device_id == None) | (AlertRule.device_id == device.id),
    ).all()

    new_alerts = []
    for rule in rules:
        value = metrics.get(rule.metric)
        if value is None:
            continue
        comparator = OPERATORS.get(rule.operator)
        if comparator and comparator(float(value), rule.threshold):
            existing = db.query(Alert).filter_by(
                rule_id=rule.id,
                device_id=device.id,
                state="open",
            ).first()
            if not existing:
                alert = Alert(
                    rule_id=rule.id,
                    device_id=device.id,
                    metric=rule.metric,
                    value=float(value),
                    message=f"{rule.metric} is {value} ({rule.operator} {rule.threshold})",
                    severity=rule.severity,
                )
                db.add(alert)
                new_alerts.append(alert)
    db.commit()
    return new_alerts
