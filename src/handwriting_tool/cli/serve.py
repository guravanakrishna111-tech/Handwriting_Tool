from __future__ import annotations

import argparse
import webbrowser

from handwriting_tool.web.server import run_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the local handwriting tool web interface.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--output-root", default="outputs/web")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = run_server(args.host, args.port, args.config, args.output_root)
    url = f"http://{args.host}:{args.port}"
    print(f"Serving handwriting UI at {url}")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

