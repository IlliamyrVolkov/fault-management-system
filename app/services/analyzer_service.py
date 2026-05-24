import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.domain.models import Alert, Device, Event
from app.infra.telegram_client import send_telegram_alert

FAILURE_THRESHOLD = 3


class AnalyzerService:
    def __init__(self, failure_threshold: int = FAILURE_THRESHOLD) -> None:
        self._failure_threshold = failure_threshold
        self._failure_counts: dict[int, int] = {}

    async def process_probe_result(
        self,
        session: AsyncSession,
        device: Device,
        is_alive: bool,
        raw_data: str,
    ) -> None:
        if is_alive:
            await self._handle_success(session, device, raw_data)
        else:
            await self._handle_failure(session, device, raw_data)

    async def _handle_success(
        self,
        session: AsyncSession,
        device: Device,
        raw_data: str,
    ) -> None:
        self._failure_counts.pop(device.id, None)

        if device.status == "DOWN":
            device.status = "UP"
            session.add(
                Event(
                    device_id=device.id,
                    event_source="ICMP",
                    raw_data=f"Відновлено зв'язок. {raw_data}",
                )
            )
            logger.success(
                f"[ANALYZER] {device.hostname} ({device.ip_address}) ВІДНОВЛЕНО -> UP"
            )

    async def _handle_failure(
        self,
        session: AsyncSession,
        device: Device,
        raw_data: str,
    ) -> None:
        count = self._failure_counts.get(device.id, 0) + 1
        self._failure_counts[device.id] = count
        logger.warning(
            f"[ANALYZER] {device.hostname} ({device.ip_address}) "
            f"невдала перевірка {count}/{self._failure_threshold}"
        )

        if count < self._failure_threshold or device.status == "DOWN":
            return

        device.status = "DOWN"
        event = Event(device_id=device.id, event_source="ICMP", raw_data=raw_data)
        session.add(event)
        await session.flush()

        alert = Alert(event_id=event.id, severity="CRITICAL", telegram_sent=False)
        session.add(alert)

        alert.telegram_sent = await asyncio.to_thread(
            send_telegram_alert,
            device.hostname,
            str(device.ip_address),
            "CRITICAL",
            raw_data,
        )
        logger.error(
            f"[ANALYZER] {device.hostname} ({device.ip_address}) НЕДОСТУПНИЙ -> DOWN"
        )
