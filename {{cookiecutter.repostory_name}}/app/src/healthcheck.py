#!/usr/bin/env python3

import argparse
import socket
import sys


def healthcheck(socket_path: str, url: str):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        s.connect(socket_path)
        req = f"GET {url} HTTP/1.1\r\n\r\n"
        s.sendall(req.encode())
        response = s.recv(64)
        assert response, "No response received"

        status_code = int(response.decode().split()[1])
        assert status_code == 200, f"Unexpected status code: {status_code}"

        sys.stdout.write("OK\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("socket_path", type=str, help="Path to the socket file")
    parser.add_argument("--url", type=str, required=False, default="/admin/login/", help="URL to check")
    args = parser.parse_args()

    try:
        healthcheck(args.socket_path, args.url)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
