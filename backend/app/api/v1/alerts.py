from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.alert import Alert, AlertRule
from app.schemas.alert import AlertRead, AlertRuleCreate, AlertRuleUpdate, AlertRuleRead

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(
    severity: str | None = None,
    state: str | None = None,
    device_id: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Alert).order_by(Alert.triggered_at.desc())
    if severity:
        q = q.filter(Alert.severity == severity)
    if state:
        q = q.filter(Alert.state == state)
    if device_id:
        q = q.filter(Alert.device_id == device_id)
    return q.all()


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    a = db.query(Alert).get(alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    return a


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    a = db.query(Alert).get(alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    a.state = "acknowledged"
    db.commit()
    db.refresh(a)
    return a


@router.post("/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    from datetime import datetime
    a = db.query(Alert).get(alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    a.state = "resolved"
    a.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(a)
    return a


@router.get("/rules", response_model=list[AlertRuleRead])
def list_rules(db: Session = Depends(get_db)):
    return db.query(AlertRule).all()


@router.post("/rules", response_model=AlertRuleRead, status_code=201)
def create_rule(body: AlertRuleCreate, db: Session = Depends(get_db)):
    rule = AlertRule(**body.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleRead)
def update_rule(rule_id: str, body: AlertRuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(AlertRule).get(rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(AlertRule).get(rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    db.delete(rule)
    db.commit()
