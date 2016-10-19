from www.app import create_server
import asyncio
loop = asyncio.get_event_loop()
loop.run_until_complete(create_server(loop,"config"))
loop.run_forever()