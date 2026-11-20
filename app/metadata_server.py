"""Fake GCP metadata server. Nothing here is real.

Which flag the token endpoint returns depends on which defense layers are on, so a flag
proves you beat the lab in that exact configuration.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import BIND, METADATA_PORT, load_state

PREFIX = "/computeMetadata/v1"
TOKEN_FLAGS = {
    frozenset(): "FLAG{metadata_is_not_a_secret_store}",
    frozenset({"filter"}): "FLAG{filters_are_speed_bumps}",
    frozenset({"egress"}): "FLAG{allowlists_must_check_redirects}",
}


def token_flag():
    on = frozenset(k for k, v in load_state().items() if v)
    return TOKEN_FLAGS.get(on, "FLAG{no_flag_in_this_configuration}")


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
        if self.path == PREFIX + "/instance/service-accounts/default/token":
            return self._send(200, json.dumps({
                "access_token": "ya29.FAKE-not-a-real-token",
                "expires_in": 3599,
                "token_type": "Bearer",
                "flag": token_flag(),
            }))
        if self.path == PREFIX + "/instance/service-accounts/default/identity":
            return self._send(200, json.dumps({
                "identity_token": "eyJFAKE.not.a.real.jwt",
                "flag": "FLAG{poisoned_tools_ride_along}",
            }))
        if self.path == PREFIX + "/project/project-id":
            return self._send(200, json.dumps({
                "project_id": "fake-project-123",
                "flag": "FLAG{pages_can_give_orders}",
            }))
        if self.path == PREFIX + "/instance/service-accounts/default/email":
            return self._send(200, "shopbot-sa@fake-project.iam.gserviceaccount.com", "text/plain")
        self._send(404, "not found", "text/plain")


if __name__ == "__main__":
    ThreadingHTTPServer((BIND, METADATA_PORT), Handler).serve_forever()
