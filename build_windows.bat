@echo off
echo 📦 安装依赖...
pip install -r requirements.txt

echo 🔨 打包中...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "鼠标自动移动工具" ^
  app.py

echo ✅ 打包完成！应用在 dist\ 目录下
explorer dist\
pause
