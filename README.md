# Mouse Mover

防止屏幕锁定的小工具，每隔一段时间自动移动鼠标，支持 macOS 和 Windows。

## 下载

前往 [Releases](../../releases) 页面下载最新版本：

- `MouseMover-macOS.zip` — macOS 应用（解压后双击运行）
- `MouseMover.exe` — Windows 可执行文件（直接双击运行）

> 国内下载慢可以用加速链接，把地址中的 `github.com` 替换为 `ghfast.top/github.com`。

> macOS 首次运行若提示"无法验证开发者"，有两种方式绕过：
> 1. 右键点击 `.app` → 选"打开" → 弹窗里点"打开"
> 2. 或在终端执行：`xattr -dr com.apple.quarantine MouseMover.app`

## 功能

- 指定结束时间（如 18:00），到点自动停止
- 或指定运行分钟数
- 自定义鼠标移动间隔（默认 60 秒）
- 实时显示剩余时间
- 日志面板可展开/收起

## 本地运行

需要 Python 3.10+：

```bash
pip install customtkinter pyautogui
python app.py
```

## 本地打包

**macOS：**
```bash
pip install pyinstaller customtkinter pyautogui
pyinstaller --onedir --windowed --name "MouseMover" app.py
```

**Windows：**
```bash
pip install pyinstaller customtkinter pyautogui
pyinstaller --onefile --windowed --name "MouseMover" app.py
```

## License

MIT
