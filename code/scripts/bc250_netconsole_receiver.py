#!/usr/bin/env python3
"""Keep BC250 kernel netconsole packets off the board across its freezes."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import socket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--port', type=int, default=6666)
    parser.add_argument('--log', required=True)
    args = parser.parse_args()
    path = Path(args.log)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('bc250-netconsole')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(path, maxBytes=10 * 1024 * 1024, backupCount=3)
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((args.bind, args.port))
        logger.info('LISTEN bind=%s:%s source=%s', args.bind, args.port, args.source)
        while True:
            data, source = sock.recvfrom(65535)
            if source[0] == args.source:
                logger.info('%s', data.decode('utf-8', errors='replace').rstrip())


if __name__ == '__main__':
    main()
