"""Production entry point. Binds to 127.0.0.1 only -- this process must
never listen on a public interface; the Cloudflare Tunnel is the only path
in. See ../../.cloudflared/barcodeportal.yml and the systemd --user units."""
from waitress import serve

from app import app

if __name__ == "__main__":
    serve(app, host="127.0.0.1", port=5001, ident=None)
