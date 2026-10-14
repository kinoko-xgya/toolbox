# toolbox

平时顺手写的小工具集合，能用就行。

## 脚本

| 文件 | 用途 |
|---|---|
| `portscan.py` | 简易 TCP 端口扫描（学习用，无依赖） |
| `kaoyan_countdown.py` | 考研倒计时，默认 12-19，可自定义日期 |

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

## 说明

纯标准库，不装依赖。portscan 仅供自己网络排查和学习，请勿用于未授权目标。
