#!/usr/bin/env python3
"""简易 TCP 端口扫描器（标准库实现，学习用）

用法:
    python3 portscan.py 192.168.1.1 --ports 1-1024 --workers 200
"""
import argparse
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_ports(spec: str):
    ports = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            ports.update(range(int(a), int(b) + 1))
        elif part:
            ports.add(int(part))
    return sorted(ports)


def scan_one(host: str, port: int, timeout: float):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        if s.connect_ex((host, port)) == 0:
            try:
                s.settimeout(1.0)
                s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                banner = s.recv(128).split(b"\r\n")[0].decode(errors="ignore")
            except Exception:
                banner = ""
            return port, banner
    return None


def main():
    ap = argparse.ArgumentParser(description="简易 TCP 端口扫描")
    ap.add_argument("host")
    ap.add_argument("--ports", default="1-1024")
    ap.add_argument("--workers", type=int, default=200)
    ap.add_argument("--timeout", type=float, default=0.6)
    args = ap.parse_args()

    try:
        ip = socket.gethostbyname(args.host)
    except socket.gaierror:
        print(f"解析失败: {args.host}", file=sys.stderr)
        return 1

    ports = parse_ports(args.ports)
    print(f"目标 {args.host} ({ip})  扫描 {len(ports)} 个端口")

    open_ports = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(scan_one, ip, p, args.timeout): p for p in ports}
        for fut in as_completed(futs):
            r = fut.result()
            if r:
                open_ports.append(r)

    for port, banner in sorted(open_ports):
        print(f"  {port:>5} open  {banner}")
    print(f"完成，开放 {len(open_ports)} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
