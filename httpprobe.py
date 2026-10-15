#!/usr/bin/env python3
"""httpprobe.py - 批量探测一串 URL 的 HTTP 状态、跳转和响应时间。

纯标准库，无依赖。常用于：服务探活、批量检查域名、排查跳转链路。
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "httpprobe/1.0 (+https://github.com/kinoko-xgya/toolbox)"


def probe(url, timeout=10.0, follow=True):
    """探测单个 URL，返回结果字典。"""
    if "://" not in url:
        url = "http://" + url
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA})
    opener = urllib.request.build_opener()
    if not follow:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **kw):
                return None
        opener = urllib.request.build_opener(NoRedirect)

    start = time.perf_counter()
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read(64)
            return {
                "url": url,
                "ok": True,
                "status": resp.status,
                "final_url": resp.geturl(),
                "server": resp.headers.get("Server", ""),
                "type": resp.headers.get("Content-Type", "").split(";")[0],
                "length": resp.headers.get("Content-Length", ""),
                "ms": round((time.perf_counter() - start) * 1000),
            }
    except urllib.error.HTTPError as e:
        return {
            "url": url,
            "ok": e.code < 400,
            "status": e.code,
            "final_url": url,
            "server": e.headers.get("Server", "") if e.headers else "",
            "type": "",
            "length": "",
            "ms": round((time.perf_counter() - start) * 1000),
        }
    except Exception as e:
        return {
            "url": url,
            "ok": False,
            "status": 0,
            "error": f"{type(e).__name__}: {e}",
            "ms": round((time.perf_counter() - start) * 1000),
        }


def fmt(r):
    if r["status"]:
        mark = "OK " if r["ok"] else "ERR"
        extra = f" -> {r['final_url']}" if r["final_url"].rstrip("/") != r["url"].rstrip("/") else ""
        return f"[{mark}] {r['status']:>3}  {r['ms']:>5}ms  {r['url']}{extra}"
    return f"[ERR]  ---  {r['ms']:>5}ms  {r['url']}  ({r.get('error', '')})"


def main():
    ap = argparse.ArgumentParser(
        description="批量探测 URL 的 HTTP 状态与响应时间",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python3 httpprobe.py github.com baidu.com\n"
               "  python3 httpprobe.py -f urls.txt -t 8 --no-follow\n"
               "  cat urls.txt | python3 httpprobe.py --json",
    )
    ap.add_argument("urls", nargs="*", help="要探测的 URL（可多个）")
    ap.add_argument("-f", "--file", help="从文件读取 URL，每行一个")
    ap.add_argument("-t", "--timeout", type=float, default=10.0, help="单次超时秒数（默认 10）")
    ap.add_argument("-j", "--jobs", type=int, default=8, help="并发数（默认 8）")
    ap.add_argument("--no-follow", action="store_true", help="不跟随 3xx 跳转")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    urls = list(args.urls)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            urls += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    if not urls and not sys.stdin.isatty():
        urls += [ln.strip() for ln in sys.stdin if ln.strip()]

    if not urls:
        ap.print_help()
        return 1

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(
            lambda u: probe(u, timeout=args.timeout, follow=not args.no_follow), urls))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(fmt(r))
        ok = sum(1 for r in results if r["ok"])
        print(f"\n{ok}/{len(results)} 可达")

    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
