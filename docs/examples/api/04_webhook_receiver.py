"""
Simple webhook receiver for NixClaw task completion callbacks.

1. Start this webhook server:
    python docs/examples/api/04_webhook_receiver.py

2. Start the NixClaw API:
    nixclaw --serve

3. Submit a task with callback_url:
    curl -X POST http://localhost:8000/api/v1/tasks \
        -H "Content-Type: application/json" \
        -d '{"task": "List files", "callback_url": "http://localhost:9000/webhook"}'

4. When the task completes, NixClaw POSTs the result to your webhook.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
            print(f"\n{'='*50}")
            print(f"Webhook received!")
            print(f"Task ID: {payload.get('task_id')}")
            print(f"Status:  {payload.get('status')}")
            if payload.get("result"):
                print(f"Result:  {payload['result'][:500]}")
            print(f"{'='*50}\n")
        except json.JSONDecodeError:
            print(f"Invalid JSON: {body}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"received": True}).encode())

    def log_message(self, format, *args):
        pass  # Suppress default logging


def main():
    port = 9000
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"Webhook receiver listening on http://localhost:{port}/webhook")
    print("Submit tasks with callback_url='http://localhost:9000/webhook'")
    print("Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
