"""Start the Terra-GEN website:  python server.py   then open http://localhost:5000"""
import os

from app.web import create_app

web = create_app()

if __name__ == "__main__":
    web.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), debug=False)
