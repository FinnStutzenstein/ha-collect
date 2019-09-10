import argparse
import asyncio
import base64
import logging
import os.path
from datetime import datetime
from pathlib import Path

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


class Main:
    statsfile = "stats.csv"
    lockfile = ".lock"

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    async def run(self):
        if os.path.isfile(self.lockfile):
            logging.warn("another collecter is running...")
            return
        Path(self.lockfile).touch()

        try:
            await self.add_content()
            logging.info("Done!")
        except Exception as e:
            logging.critical(f"Exception: {e}")
        finally:
            os.remove(self.lockfile)
        logging.info("bye\n")

    async def add_content(self):
        url = "http://" + self.host + "/;csv"
        basic_auth = self.user + ":" + self.password
        basic_auth = base64.b64encode(basic_auth.encode()).decode("utf-8")
        headers = {"Authorization": "Basic " + basic_auth}
        logging.info("connecting...")
        async with aiohttp.ClientSession(headers=headers) as session:
            response = await session.get(url)
            text = await response.text()
            if not text.startswith("# "):
                logging.critical(f"Error: {text}")
                return
        logging.info("got response...")
        lines = text.split("\n")
        csv_header = lines[0][2:]  # removing '# '
        csv_content = lines[1:]

        write_header = not os.path.isfile(self.statsfile)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.statsfile, "a+") as f:
            if write_header:
                f.write("time,")
                f.write(csv_header + "\n")
            for content_line in csv_content:
                if content_line:
                    f.write(timestamp + ",")
                    f.write(content_line + "\n")
        logging.info("written to file...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WS-Receiver")
    parser.add_argument("-i", help="HAProxy", default="localhost:8404")
    parser.add_argument("-u", help="User", default="admin")
    parser.add_argument("-p", help="Password", default="admin")
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    main = Main(args.i, args.u, args.p)
    loop.run_until_complete(main.run())
