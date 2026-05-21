import asyncio

from sqlalchemy import select

from app.core.logger import logger
from app.domain.models import Device
from app.infra.database import db_helper


SEED_DEVICES: list[dict] = [
    {"hostname": "Border_Router", "ip_address": "192.168.1.1", "device_type": "Router", "status": "UP"},
    {"hostname": "Core_Switch", "ip_address": "10.0.0.1", "device_type": "Switch", "status": "UP"},
    {"hostname": "Access_SW_1", "ip_address": "10.0.1.5", "device_type": "Switch", "status": "UP"},
    {"hostname": "Access_SW_2", "ip_address": "10.0.2.5", "device_type": "Switch", "status": "DOWN"},
    {"hostname": "Test_Server_Off", "ip_address": "192.168.99.99", "device_type": "Server", "status": "DOWN"},
]


async def seed_devices() -> None:
    async with db_helper.session_factory() as session:
        existing = await session.execute(select(Device.ip_address))
        existing_ips = {str(ip) for ip in existing.scalars().all()}

        added = 0
        for data in SEED_DEVICES:
            if data["ip_address"] in existing_ips:
                logger.info(f"Пристрій {data['hostname']} ({data['ip_address']}) вже існує, пропускаємо.")
                continue

            session.add(Device(**data))
            logger.info(f"Додано {data['hostname']} ({data['ip_address']}) -> {data['status']}")
            added += 1

        await session.commit()
        logger.success(f"Сідінг завершено. Додано нових пристроїв: {added}/{len(SEED_DEVICES)}.")


async def main() -> None:
    try:
        await seed_devices()
    finally:
        await db_helper.dispose()


if __name__ == "__main__":
    asyncio.run(main())
