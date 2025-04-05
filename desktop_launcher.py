import webview

# Change this to your Render deployment URLpython desktop_launcher.py
print("Launching desktop wrapper...")  # Hack to fix disassembler bug
url = "https://task-app-hpe3.onrender.com/"

# Create the app window
webview.create_window("To-Do Manager", url, width=1000, height=700, resizable=True)
webview.start()
# for deployed apps view on app