from app.api.v1.poe_endpoint import router as responses_router
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.utils import ImageManager


import uvicorn
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_instance(app: FastAPI):
    logger.info("Initializing singleton instances...")
    image_manager_instance = ImageManager()
    app.state.image_manager = image_manager_instance
    logger.info("Singleton instances are all created and loaded")

    yield


app = FastAPI(lifespan=create_instance)
app.include_router(responses_router)


@app.get("/")
@app.head("/")
async def root():
    return {"message": "API is running", "endpoint": "/"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2026)