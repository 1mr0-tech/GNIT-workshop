"""Fake GCP metadata server. Nothing here is real."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FLAG = "FLAG{metadata_is_not_a_secret_store}"
TOKEN_PATH = "/computeMetadata/v1/instance/service-accounts/default/token"
EMAIL_PATH = "/computeMetadata/v1/instance/service-accounts/default/email"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("metadata:", self.address_string(), fmt % args, flush=True)

    def _send(self, code, body, ctype="application/json"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Metadata-Flavor", "Google")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        # Like the real server, require the Metadata-Flavor header.
        if self.headers.get("Metadata-Flavor") != "Google":
            return self._send(403, "Missing Metadata-Flavor:Google header.", "text/plain")
        if self.path == TOKEN_PATH:
            return self._send(200, json.dumps({
                "access_token": "ya29.FAKE-not-a-real-token",
                "expires_in": 3599,
                "token_type": "Bearer",
                "flag": FLAG,
            }))
        if self.path == EMAIL_PATH:
            return self._send(200, "shopbot-sa@fake-project.iam.gserviceaccount.com", "text/plain")
        self._send(404, "not found", "text/plain")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), Handler).serve_forever()
