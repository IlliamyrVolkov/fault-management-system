import asyncio

from ping3 import ping
from sqlalchemy import select

from app.core.logger import logger
from app.domain.models import Device
from app.infra.database import db_helper
from app.services.analyzer_service import AnalyzerService

PROBE_INTERVAL_SECONDS = 10
PING_TIMEOUT_SECONDS = 1


async def ping_device(ip: str) -> float | None:
    return await asyncio.to_thread(ping, ip, timeout=PING_TIMEOUT_SECONDS)


async def run_icmp_probe() -> None:
    logger.info("ICMP-зонд запущено.")
    analyzer = AnalyzerService()
    while True:
        try:
            async with db_helper.session_factory() as session:
                devices = (await session.execute(select(Device))).scalars().all()

                for device in devices:
                    delay = await ping_device(str(device.ip_address))
                    is_alive = delay is not None
                    raw_data = (
                        f"Delay: {round(delay * 1000, 2)} ms"
                        if is_alive
                        else "Timeout (Packet Loss)"
                    )
                    logger.debug(
                        f"[ICMP] {device.hostname} ({device.ip_address}) "
                        f"-> {'UP' if is_alive else 'FAIL'} | {raw_data}"
                    )
                    await analyzer.process_probe_result(
                        session, device, is_alive, raw_data
                    )

                await session.commit()
        except asyncio.CancelledError:
            logger.info("ICMP-зонд зупинено.")
            raise
        except Exception:
            logger.exception("Помилка в ICMP-зонді")

        await asyncio.sleep(PROBE_INTERVAL_SECONDS)
