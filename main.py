import subprocess
import re
import socket
import logging
import os
import datetime

from logger import setup_logger
from protocol import Protocol


setup_logger()
log = logging.getLogger('logger')


RU = {
    'encoding': 'cp866',
    'startup_time': 'Время загрузки системы',
    'mac': r'.{0,}Физический адрес.{0,}',
    'ip': r'.{0,}IPv4-адрес.{0,}'
}

STARTUP_FILE_NAME = 'startup.info'

PROTO_PORT_SERVER = 10788
PROTO_PORT_CLIENT = 10789


def system_startup_time():
    if os.path.exists(STARTUP_FILE_NAME):
        with open(STARTUP_FILE_NAME, 'r') as f:
            return f.read()
    else:
        return update_startup_time()


def update_startup_time():
    with open(STARTUP_FILE_NAME, 'w') as f:
        time = datetime.datetime.now().isoformat()
        f.write(time)
        return time


def handle(data):
    packet = Protocol.decode(data)
    if packet.code == Protocol.CODE_IFALIVE:
        return Protocol(Protocol.CODE_IFALIVE, packet.uid, packet.cid).encode()
    elif packet.code == Protocol.CODE_ASKSTARTTIME:
        return Protocol(Protocol.CODE_STARTTIME, packet.uid, packet.cid, system_startup_time()).encode()
    else:
        return None


def main():
    log.info('Starting daemon')

    log.info('Updating startup time')
    update_startup_time()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.bind(('', PROTO_PORT_SERVER))

    while True:
        data, addr = sock.recvfrom(1024)
        log.debug(f'From {addr[0]}:{addr[1]} {data}')
        try:
            answ = handle(data)
            log.debug(f'Response: {answ}')
            if answ is not None:
                sock.sendto(answ, (addr[0], PROTO_PORT_CLIENT))
        except KeyboardInterrupt:
            break
        except Exception as err:
            log.error(f'Packet: {data}. Error msg: {err}')


if __name__ == '__main__':
    main()
