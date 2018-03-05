# =============================================================================
# This script is designed to be run as a background service using Systemd. The
# purpose of this script is to receive information (rx) and send information
# (tx) to the sensors via a communication link.
# =============================================================================

# import asyncio
# from commlink import RFM69
# from config import settings
# from random import randint
# from utils import get_InfluxDB

# ifdb = get_InfluxDB()
# comm = RFM69(ifdb)

# async def rx(number, n):
#     while n > 0:
#         print('T-minus', n, '({})'.format(number))
#         await asyncio.sleep(1)
#         n -= 1

# loop = asyncio.get_event_loop()
# try:
#     tasks = [
#         asyncio.ensure_future(rx("A", 2)),
#         asyncio.ensure_future(rx("B", 3))
#     ]
#     loop.run_forever(asyncio.wait(tasks)

# except Exception as e:
#     loop.close()




    