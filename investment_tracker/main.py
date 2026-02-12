import webview
import threading
import subprocess
import time
import sys

def run_streamlit():
    # 使用你剛才成功的路徑來啟動 Streamlit
    # --server.headless=true 代表不要自動彈出瀏覽器
    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "portfolio.py", 
        "--server.headless", "true", 
        "--server.port", "8501"
    ])

if __name__ == "__main__":
    # 1. 在背景偷偷啟動 Streamlit
    t = threading.Thread(target=run_streamlit)
    t.daemon = True
    t.start()

    # 2. 等待 3 秒讓伺服器啟動
    time.sleep(3)

    # 3. 彈出桌面小視窗
    print("正在啟動桌面應用程式...")
    webview.create_window("我的投資顧問", "http://localhost:8501", width=1000, height=800)
    webview.start()
