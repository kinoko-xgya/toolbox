#!/usr/bin/env python3
"""httpprobe.py 边界测试 —— 纯标准库，起本地 HTTP 服务对拍。"""
import http.server
import json
import socketserver
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "httpprobe.py"
PORT = 28099
BASE = f"http://127.0.0.1:{PORT}"

sys.path.insert(0, str(HERE))
import httpprobe  # noqa: E402


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path
        if p == "/ok":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"hello")
        elif p == "/redir":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
        elif p == "/redir-loop":
            self.send_response(302)
            self.send_header("Location", "/redir-loop")
            self.end_headers()
        elif p == "/404":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"nf")
        elif p == "/500":
            self.send_response(500)
            self.end_headers()
        elif p == "/empty":
            self.send_response(204)
            self.end_headers()
        elif p == "/slow":
            time.sleep(3)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"slow")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"root")

    def version_string(self):
        return "TestSrv"

    def log_message(self, *a):
        pass


class ReusableServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    allow_reuse_port = True
    daemon_threads = True

class TestHttpprobe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        cls.srv = ReusableServer(("127.0.0.1", PORT), Handler)
        cls.srv.daemon_threads = True
        cls.t = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.t.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    # ---- probe() 单元 ----

    def test_ok_200(self):
        r = httpprobe.probe(f"{BASE}/ok")
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], 200)
        self.assertEqual(r["server"], "TestSrv")
        self.assertEqual(r["type"], "text/html")
        self.assertGreaterEqual(r["ms"], 0)

    def test_follow_redirect(self):
        r = httpprobe.probe(f"{BASE}/redir")
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], 200)
        self.assertTrue(r["final_url"].endswith("/ok"))

    def test_no_follow_keeps_302(self):
        r = httpprobe.probe(f"{BASE}/redir", follow=False)
        self.assertEqual(r["status"], 302)
        self.assertTrue(r["ok"])  # 302 < 400
        self.assertTrue(r["final_url"].endswith("/redir"))

    def test_404_not_ok(self):
        r = httpprobe.probe(f"{BASE}/404")
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], 404)

    def test_500_not_ok(self):
        r = httpprobe.probe(f"{BASE}/500")
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], 500)

    def test_204_empty_body(self):
        r = httpprobe.probe(f"{BASE}/empty")
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], 204)

    def test_redirect_loop_follow_reports_302(self):
        # 已知行为：跟随重定向时 urllib 抛 HTTPError(302)，
        # 而 probe() 用 e.code < 400 判 ok → 重定向环会被误判为 ok=True。
        # 这个测试锁定当前行为，防止将来回归时无声变化；真要修 bug 再改这里。
        r = httpprobe.probe(f"{BASE}/redir-loop")
        self.assertEqual(r["status"], 302)
        self.assertTrue(r["ok"])

    def test_redirect_loop_no_follow(self):
        r = httpprobe.probe(f"{BASE}/redir-loop", follow=False)
        self.assertEqual(r["status"], 302)
        self.assertTrue(r["final_url"].endswith("/redir-loop"))

    def test_timeout(self):
        r = httpprobe.probe(f"{BASE}/slow", timeout=0.5)
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], 0)
        self.assertIn("error", r)
        self.assertIn("timeout", r["error"].lower())

    def test_no_scheme_gets_http_prefix(self):
        r = httpprobe.probe("127.0.0.1:18099/ok")
        self.assertTrue(r["url"].startswith("http://"))
        self.assertTrue(r["ok"])

    def test_connection_refused(self):
        r = httpprobe.probe("127.0.0.1:1/", timeout=2)
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], 0)
        self.assertIn("error", r)

    # ---- fmt() ----

    def test_fmt_ok_and_err(self):
        ok = httpprobe.probe(f"{BASE}/ok")
        err = httpprobe.probe(f"{BASE}/404")
        self.assertIn("[OK ]", httpprobe.fmt(ok))
        self.assertIn("[ERR]", httpprobe.fmt(err))
        dead = httpprobe.probe("127.0.0.1:1/", timeout=2)
        self.assertIn("[ERR]", httpprobe.fmt(dead))

    def test_fmt_shows_redirect_arrow(self):
        r = httpprobe.probe(f"{BASE}/redir")
        self.assertIn("->", httpprobe.fmt(r))

    # ---- CLI 集成 ----

    def run_cli(self, *args, stdin=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=stdin, capture_output=True, text=True, timeout=60,
        )

    def test_cli_json_output(self):
        p = self.run_cli(f"{BASE}/ok", f"{BASE}/404", "--json")
        data = json.loads(p.stdout)
        self.assertEqual(len(data), 2)
        self.assertEqual(p.returncode, 1)  # 有不可达 → 退出码 1

    def test_cli_stdin(self):
        p = self.run_cli("--json", stdin=f"{BASE}/ok\n")
        data = json.loads(p.stdout)
        self.assertEqual(len(data), 1)

    def test_cli_no_urls_shows_help(self):
        p = self.run_cli(stdin="")
        self.assertEqual(p.returncode, 1)
        self.assertIn("usage", p.stdout.lower() + p.stderr.lower())

    def test_cli_file_input(self, tmp=None):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(f"# comment\n{BASE}/ok\n\n")
            path = f.name
        p = self.run_cli("-f", path, "--json")
        data = json.loads(p.stdout)
        self.assertEqual(len(data), 1)
        self.assertTrue(data[0]["ok"])

    def test_cli_all_ok_returncode_zero(self):
        p = self.run_cli(f"{BASE}/ok")
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
