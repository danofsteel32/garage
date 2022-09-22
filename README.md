# Garage

Uses a [HC-SR04](https://www.sparkfun.com/products/15569) ultrasonic distance sensor hooked up to a [Raspberry Pi Zero WiFi](https://www.raspberrypi.com/products/raspberry-pi-zero-w/) to monitor whether my garage door is open.
I made this so I don't have to turn around after leaving my house to check if I remembered to close the garage.

Written in python using the [Quart](https://pgjones.gitlab.io/quart/index.html) framework.

- `X-Api-Key` header to prevent randos from posting fake data to my server
- SSE (server sent events) for live updates


### TODO
- Remove all assumptions from deployment
- Generate `./config/garage-env` based on `.env`
- Maybe send text message when opened
- Table of past open events
- Script for downloading new versions of [htmx](https://htmx.org/)


### Develop

- Install deps `./run.sh install`
- Run local server `./run.sh`
- Run simulated sensor `./run.sh fake-sensor`
- Run tests `./run.sh tests`
- Go to <http://localhost:8081/garage/status>


### Deploy

##### Assumptions

- `.env` exists and has the Env vars `PI_USER,PI_SSH_HOST,SERVER_USER,SERVER_SSH_HOST` set
- Raspi GPIO libs and python3-httpx are installed on the pi
- `SERVER_USER` exists on `SERVER_SSH_HOST`
- `loginctl enable-linger SERVER_USER`
- `./config/garage-env` exists and has the Env vars `GARAGE_API_KEY`


##### Sensor

`./run.sh deploy-sensor`

- Copy `sensor.py` and it's systemd service and environment files to the raspberry pi
- Stop and reload systemd service
- check status


##### Server

`./run.sh deploy-server` does the following:

- Build `.whl` file for the `garage` package
- Copy the `.whl` file and it's systemd service/env files to my VPS
- Stop `garage-server.service` systemd service
- Clean up any previous virtual environments
- Create fresh venv
- Install build deps (wheel, setuptools) and `.whl` package into venv
- Load new service files `systemctl daemon-reload`
- Start `garage-server.service`
- Check status of `garage-server`
