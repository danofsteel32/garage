import itertools
import time

import httpx


def run():
    client = httpx.Client()

    distances = itertools.cycle([float(n) for n in range(50, 110)])
    while True:
        try:
            dist = next(distances)
            r = client.post(
                "http://localhost:8081/garage/status",
                json={"message": dist},
                headers={"X-Api-Key": "testkey"},
            )
            print(r.json())
            time.sleep(2)
        except KeyboardInterrupt:
            client.close()
            break

    client.close()


if __name__ == "__main__":
    run()
