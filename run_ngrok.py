from pyngrok import ngrok
import time
import sys

# Start ngrok tunnel on port 5050
print("Starting ngrok tunnel...")
try:
    public_url = ngrok.connect(5050).public_url
    print("\n" + "="*50)
    print("🎉 SUCCESS! Your public link is ready: ")
    print(f"👉 {public_url}")
    print("="*50 + "\n")
    print("Share this link with your friends!")
    print("Keep this terminal open. Press CTRL+C to close the link.")
    
    # Keep the tunnel alive
    while True:
        time.sleep(1)
except Exception as e:
    print(f"Error starting ngrok: {e}")
    sys.exit(1)
