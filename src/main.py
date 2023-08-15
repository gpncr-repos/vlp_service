import uvicorn
from fastapi import FastAPI
from routes.vlp import router as vlp_router

app = FastAPI()

app.include_router(vlp_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
