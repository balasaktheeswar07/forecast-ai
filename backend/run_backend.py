import uvicorn
import sys
import os

if __name__ == "__main__":
    # Ensure current folder is in Python path so app package is importable
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    print("Starting AI Forecasting Assistant backend on http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
