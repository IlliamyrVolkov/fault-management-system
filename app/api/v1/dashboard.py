from ipaddress import IPv4Address

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ROOT_DIR, settings
from app.domain.models import Alert, Device, Event
from app.infra.database import db_helper

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory=str(ROOT_DIR / "app" / "templates"))

RECENT_ALERTS_LIMIT = 10
TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"

DEVICES_URL = (
    f"{settings.api.api_prefix}{settings.api.v1.prefix}"
    f"{settings.api.v1.dashboard}/devices"
)


class DeviceCreate(BaseModel):
    hostname: str = Field(min_length=1, max_length=100)
    ip_address: str = Field(min_length=1, max_length=15)
    device_type: str | None = Field(default=None, max_length=50)


def _serialize_device(device: Device, last_check=None) -> dict:
    return {
        "id": device.id,
        "hostname": device.hostname,
        "ip_address": str(device.ip_address),
        "device_type": device.device_type,
        "status": device.status,
        "last_check": last_check.strftime(TIMESTAMP_FMT) if last_check else None,
    }


async def _fetch_devices(session: AsyncSession) -> list[dict]:
    last_check_subq = (
        select(
            Event.device_id,
            func.max(Event.timestamp).label("last_check"),
        )
        .group_by(Event.device_id)
        .subquery()
    )

    stmt = (
        select(Device, last_check_subq.c.last_check)
        .outerjoin(last_check_subq, Device.id == last_check_subq.c.device_id)
        .order_by(Device.hostname)
    )
    result = await session.execute(stmt)
    return [_serialize_device(device, last_check) for device, last_check in result.all()]


async def _fetch_alerts(session: AsyncSession) -> list[dict]:
    stmt = (
        select(Alert, Event, Device)
        .join(Event, Alert.event_id == Event.id)
        .join(Device, Event.device_id == Device.id)
        .order_by(Event.timestamp.desc())
        .limit(RECENT_ALERTS_LIMIT)
    )
    result = await session.execute(stmt)
    return [
        {
            "timestamp": event.timestamp.strftime(TIMESTAMP_FMT),
            "hostname": device.hostname,
            "ip_address": str(device.ip_address),
            "severity": alert.severity,
            "message": event.raw_data,
        }
        for alert, event, device in result.all()
    ]


@router.get("/", response_class=HTMLResponse)
async def get_dashboard_page(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "project_name": settings.project_name,
            "devices": await _fetch_devices(session),
            "alerts": await _fetch_alerts(session),
            "devices_url": DEVICES_URL,
        },
    )


@router.get("/devices")
async def list_devices(
    session: AsyncSession = Depends(db_helper.session_getter),
):
    return {"devices": await _fetch_devices(session)}


@router.post("/devices", status_code=status.HTTP_201_CREATED)
async def create_device(
    payload: DeviceCreate,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    try:
        ip = IPv4Address(payload.ip_address.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат IP-адреса",
        )

    device = Device(
        hostname=payload.hostname,
        ip_address=str(ip),
        device_type=payload.device_type,
    )
    session.add(device)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пристрій з такою IP-адресою вже існує.",
        )
    await session.refresh(device)
    return _serialize_device(device)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    session: AsyncSession = Depends(db_helper.session_getter),
):
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пристрій не знайдено.",
        )

    await session.execute(
        delete(Alert).where(
            Alert.event_id.in_(
                select(Event.id).where(Event.device_id == device_id)
            )
        )
    )
    await session.execute(delete(Event).where(Event.device_id == device_id))
    await session.delete(device)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
