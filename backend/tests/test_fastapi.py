"""Smoke test: verifies that FastAPI and uvicorn are installed and can serve a minimal HTTP endpoint on port 8888."""
from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888)
