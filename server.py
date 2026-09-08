"""Launch the SOC with AI server.

    python server.py           → starts on http://localhost:8000
    python server.py --port 9000
"""

import argparse
import uvicorn

from src.api.routes import app


def main():
    parser = argparse.ArgumentParser(description="SOC with AI")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    print(f"\n  SOC with AI")
    print(f"   Dashboard: http://{args.host}:{args.port}/")
    print(f"   API docs:  http://{args.host}:{args.port}/docs\n")

    uvicorn.run(
        "src.api.routes:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
