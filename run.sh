#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

source ./.env

VENVPATH="./venv"

venv() {
    local _bin="${VENVPATH}/bin"
    if [ -d "${_bin}" ]; then
        echo "source ${VENVPATH}/bin/activate"
    else
        echo "source ${VENVPATH}/Scripts/activate"
    fi
}

make-venv() {
    python -m venv "${VENVPATH}"
}

reset-venv() {
    rm -rf "${VENVPATH}"
    make-venv
}

wrapped-python() {
    local _bin="${VENVPATH}/bin"
    if [ -d "${_bin}" ]; then
        "${VENVPATH}"/bin/python "$@"
    else
        "${VENVPATH}"/Scripts/python "$@"
    fi
}

wrapped-pip() {
    wrapped-python -m pip "$@"
}

python-deps() {
    wrapped-pip install --upgrade pip setuptools wheel

    local pip_extras="${1:-}"
    if [ -z "${pip_extras}" ]; then
        wrapped-pip install --upgrade -e .
    else
        wrapped-pip install --upgrade -e ".[${pip_extras}]"
    fi
}

install() {
    if [ -d "${VENVPATH}" ]; then
        python-deps "$@"
    else
        make-venv && python-deps "$@"
    fi
}

build() {
    wrapped-python -m build
}

get-wheel(){
    # return the .whl file in dist/
    local _files=(dist/*.whl)
    basename -- "${_files[0]}"
}

clean() {
    rm -rf dist/
    rm -rf .eggs/
    rm -rf build/
    find . -name '*.pyc' -exec rm -f {} +
    find . -name '*.pyo' -exec rm -f {} +
    find . -name '*~' -exec rm -f {} +
    find . -name '__pycache__' -exec rm -fr {} +
    find . -name '.mypy_cache' -exec rm -fr {} +
    find . -name '.pytest_cache' -exec rm -fr {} +
    find . -name '*.egg-info' -exec rm -fr {} +
}

tests() {
    wrapped-python -m pytest -rA tests
}

deploy-sensor() {
    scp config/* "${PI_USER}@${PI_SSH_HOST}:/home/${PI_USER}/.config/systemd/user/"
    scp src/garage/sensor.py "${PI_USER}@${PI_SSH_HOST}:/home/${PI_USER}"
    local commands=(
        "systemctl --user stop sensor.service;"
        "systemctl --user daemon-reload;"
        "systemctl --user enable --now sensor.service;"
        "sleep 1;"
        "systemctl --user status sensor.service;"
    )
    ssh "${PI_USER}@${PI_SSH_HOST}" "${commands[@]}"
}

deploy-server() {
    clean && build
    local _wheel
    _wheel=$(get-wheel)
    if [[ ! -f "${_wheel}" ]]; then
        echo "No wheel file! Cannot deploy-server"
        return 1
    fi
    scp config/* "${SERVER_USER}@${SERVER_SSH_HOST}:/home/${SERVER_USER}/.config/systemd/user/"
    scp dist/"${_wheel}" "${SERVER_SSH_HOST}:/tmp/"
    local commands=(
        "systemctl --user stop garage-server.service;"
        "rm -rf /home/${SERVER_USER}/venv;"
        "python -m venv venv;"
        "./venv/bin/python -m pip install --upgrade wheel setuptools /tmp/${_wheel};"
        "systemctl --user daemon-reload;"
        "systemctl --user enable --now garage-server.service;"
        "sleep 1;"
        "systemctl --user status garage-server.service;"
    )
    ssh "${SERVER_USER}@${SERVER_SSH_HOST}" "${commands[@]}"
}

fake-sensor() {
    wrapped-python -m garage.fake_sensor
}

prod-server() {
    GARAGE_API_KEY=testkey wrapped-python -m hypercorn garage.server:app --bind '0.0.0.0:8081' --debug
}

default() {
    GARAGE_API_KEY=testkey QUART_APP=garage.server:app \
        wrapped-python -m quart --debug \
            run --host 0.0.0.0 --port 8081 \
            --reload
}


TIMEFORMAT="Task completed in %3lR"
time "${@:-default}"
