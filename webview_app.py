import threading
import webview
from app import app  # Replace with your Flask app's Python file name

def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Open the app in a native window
    webview.create_window("To-Do Task Manager", "http://127.0.0.1:5000", width=1000, height=700)
    webview.start()
# for local webview app 