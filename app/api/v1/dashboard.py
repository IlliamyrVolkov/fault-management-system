from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ROOT_DIR, settings
from app.domain.models import Alert, Device, Event
from app.infra.database import db_helper


router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory=str(ROOT_DIR / "app" / "templates"))

RECENT_ALERTS_LIMIT = 10
TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"


@router.get("/", response_class=HTMLResponse)
async def get_dashboard_page(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    last_check_subq = (
        select(
            Event.device_id,
            func.max(Event.timestamp).label("last_check"),
        )
        .group_by(Event.device_id)
        .subquery()
    )

    devices_stmt = (
        select(Device, last_check_subq.c.last_check)
        .outerjoin(last_check_subq, Device.id == last_check_subq.c.device_id)
        .order_by(Device.hostname)
    )
    devices_result = await session.execute(devices_stmt)
    devices = [
        {
            "device": device,
            "last_check": last_check.strftime(TIMESTAMP_FMT) if last_check else None,
        }
        for device, last_check in devices_result.all()
    ]

    alerts_stmt = (
        select(Alert, Event, Device)
        .join(Event, Alert.event_id == Event.id)
        .join(Device, Event.device_id == Device.id)
        .order_by(Event.timestamp.desc())
        .limit(RECENT_ALERTS_LIMIT)
    )
    alerts_result = await session.execute(alerts_stmt)
    alerts = [
        {
            "timestamp": event.timestamp.strftime(TIMESTAMP_FMT),
            "hostname": device.hostname,
            "ip_address": str(device.ip_address),
            "severity": alert.severity,
            "message": event.raw_data,
        }
        for alert, event, device in alerts_result.all()
    ]

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "project_name": settings.project_name,
            "devices": devices,
            "alerts": alerts,
        },
    )
