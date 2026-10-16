# toolbox

平时顺手写的小工具集合，能用就行。

## 脚本

| 文件 | 用途 |
|---|---|
| `portscan.py` | 简易 TCP 端口扫描（学习用，无依赖） |
| `kaoyan_countdown.py` | 考研倒计时，默认 12-19，可自定义日期 |
| `httpprobe.py` | 批量探测 URL 的 HTTP 状态、跳转和响应时间 |
| `test_httpprobe.py` | httpprobe 的边界测试（本地起服务对拍，纯标准库） |

## 用法

### portscan.py

```bash
python3 portscan.py 192.168.1.1 --ports 1-1024
```

### kaoyan_countdown.py

```bash
# 默认 12 月 19 日开考
python3 kaoyan_countdown.py

# 自定义日期，可指定年份
python3 kaoyan_countdown.py 12-21
python3 kaoyan_countdown.py 12-21 2026

# 额外显示周数 / 纯数字输出
python3 kaoyan_countdown.py --weeks
python3 kaoyan_countdown.py --no-banner
```

### httpprobe.py

```bash
# 直接给 URL
python3 httpprobe.py example.com github.com

# 从文件读，8 并发，不跟随跳转
python3 httpprobe.py -f urls.txt -j 8 --no-follow

# 管道输入 + JSON 输出
cat urls.txt | python3 httpprobe.py --json
```


### 测试

```bash
python3 -m unittest test_httpprobe -v
# 或
python3 test_httpprobe.py
```

## 已知问题

- `httpprobe.py`：跟随重定向时若遇到**重定向环**，`urllib` 抛 `HTTPError(302)`，
  而 `ok` 用 `code < 400` 判断，会误报 `ok: true`。目前行为已由
  `test_redirect_loop_follow_reports_302` 锁定，待后续修（改判据为 `300 <= code < 400` 时单独标注）。

## 说明

纯标准库，不装依赖。portscan / httpprobe 仅供自己网络排查和学习，请勿用于未授权目标。
