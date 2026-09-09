"""Offline sanity check for --exit-after-subscribed's wait_all_subscribed()
helper: no sockets, no networking, so it runs anywhere (including sandboxes
with no IPv6 support at all). Exits non-zero on any assertion failure.

Doesn't (and can't, without real sockets) verify the no-StopOffer/os._exit
behavior itself -- that needs a live run, see ci.yml's
"exit-after-subscribed" step, which checks it against real pysomeip
Offer/Subscribe/Ack traffic over --peer-addr unicast SD.
"""

import asyncio
import logging

from someip_sd_demo.common import MEASUREMENTS, STATUS
from someip_sd_demo.server import SensorEventgroupListener, wait_all_subscribed

log = logging.getLogger("exit_after_subscribed_check")


async def main() -> None:
    l1 = SensorEventgroupListener(MEASUREMENTS, log)
    l2 = SensorEventgroupListener(STATUS, log)
    listeners = {MEASUREMENTS.service_id: l1, STATUS.service_id: l2}

    try:
        await wait_all_subscribed(listeners, timeout=0.2, log=log)
        raise AssertionError("expected TimeoutError when nobody has subscribed")
    except TimeoutError as exc:
        assert "Measurements" in str(exc) and "Status" in str(exc), exc
        print(f"OK: times out naming every still-unsubscribed service: {exc}")

    l1.active = 1
    try:
        await wait_all_subscribed(listeners, timeout=0.2, log=log)
        raise AssertionError("expected TimeoutError while Status has no subscriber yet")
    except TimeoutError as exc:
        assert "Measurements" not in str(exc) and "Status" in str(exc), exc
        print(f"OK: times out naming only the still-unsubscribed service: {exc}")

    async def subscribe_status_shortly():
        await asyncio.sleep(0.05)
        l2.active = 1

    asyncio.create_task(subscribe_status_shortly())
    await wait_all_subscribed(listeners, timeout=2.0, log=log)
    print("OK: returns once every service has a subscriber")

    print("\nALL EXIT-AFTER-SUBSCRIBED OFFLINE CHECKS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
