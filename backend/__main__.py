"""CLI entry point for running the DP1 FastAPI server."""
import uvicorn
from .config import API_HOST, API_PORT


def main():
    print(f"Starting DP1 API server on http://{API_HOST}:{API_PORT} ...")
    uvicorn.run("backend.app:app", host=API_HOST, port=API_PORT, reload=False)


if __name__ == "__main__":
    main()
