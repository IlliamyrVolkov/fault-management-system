import asyncio
from ping3 import ping
from sqlalchemy import select
from app.infra.database import db_helper
from app.domain.models import Device, Event


async def ping_device(ip: str):
    return await asyncio.to_thread(ping, ip, timeout=1)


async def run_icmp_probe():
    while True:
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(select(Device))
                devices = result.scalars().all()

                for device in devices:
                    delay = await ping_device(str(device.ip_address))
                    status = "UP" if delay is not None else "DOWN"

                    raw_data = f"Delay: {round(delay * 1000, 2)} ms" if status == "UP" else "Timeout (Packet Loss)"
                    print(f"[ICMP] {device.hostname} ({device.ip_address}) -> {status} | {raw_data}")

                    event = Event(
                        device_id=device.id,
                        event_source="ICMP",
                        raw_data=raw_data
                    )
                    session.add(event)

                    device.status = status

                await session.commit()
            except Exception as e:
                print(f"Помилка в ICMP зонді: {e}")

        await asyncio.sleep(5)