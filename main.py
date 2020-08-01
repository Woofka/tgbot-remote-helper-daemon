import subprocess
import re
import socket
import logging

from protocol import Protocol


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='error.log',
    level=logging.INFO
)


RU = {
    'encoding': 'cp866',
    'startup_time': 'Время загрузки системы',
    'mac': r'.{0,}Физический адрес.{0,}',
    'ip': r'.{0,}IPv4-адрес.{0,}'
}


PROTO_PORT_SERVER = 10788
PROTO_PORT_CLIENT = 10789


def system_startup_time():
    """ return startup time in iso format """
    cmd_res = subprocess.run(['systeminfo'], stdout=subprocess.PIPE)
    cmd_res = cmd_res.stdout.decode(RU['encoding'])
    f = RU['startup_time']
    i = cmd_res.find(f)
    j = cmd_res.find('\n', i)
    dt = re.findall(r'\d{2}', cmd_res[i + len(f):j])
    return f'{dt[2]}{dt[3]}-{dt[1]}-{dt[0]}T{dt[4]}:{dt[5]}:{dt[6]}'


def handle(data):
    packet = Protocol.decode(data)
    if packet is None:
        return None

    if packet.code == Protocol.CODE_IFALIVE:
        return Protocol(Protocol.CODE_IFALIVE, packet.uid).encode()
    elif packet.code == Protocol.CODE_ASKSTARTTIME:
        return Protocol(Protocol.CODE_STARTTIME, packet.uid, system_startup_time()).encode()
    else:
        return None


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.bind(('', PROTO_PORT_SERVER))

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            answ = handle(data)
            if answ is not None:
                sock.sendto(answ, (addr[0], PROTO_PORT_CLIENT))
        except KeyboardInterrupt:
            break
        except Exception as err:
            logging.error(err)


if __name__ == '__main__':
    main()