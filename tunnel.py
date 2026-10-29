"""Expose the local Streamlit app through an ngrok public URL."""

from pyngrok import ngrok

import keys


PORT = 8501

ngrok.set_auth_token(keys.require("NGROK_AUTH_TOKEN", keys.NGROK_AUTH_TOKEN))
tunnel = ngrok.connect(PORT)
print(f"\nPublic URL: {tunnel.public_url}\n")

try:
    input("Press Enter to stop the tunnel...")
finally:
    ngrok.disconnect(tunnel.public_url)
    ngrok.kill()