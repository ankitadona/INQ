import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    default_host = "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
    host = os.getenv("HOST", default_host)
    uvicorn.run("app.main:app", host=host, port=port)
