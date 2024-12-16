import json
import logging
from multiprocessing import get_logger
import os
import subprocess
import uuid
from fastapi import FastAPI, Request
from app.configuration.db import init_db
from .configuration.config import load_env
from fastapi.middleware.cors import CORSMiddleware

from app.configuration.logger import get_logger

# Load environment variables
load_env()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAPI configuration
openapi_info = {
    "title": "Role Management API",
    "description": "API for managing roles",
    "termsOfService": "http://swagger.io/terms/",
    "contact": {
        "email": "aravind@monkeeys.com"
    },
    "license": {
        "name": "Apache 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0.html"
    },
    "version": "1.0.11"

}

servers = [{"url": "http://localhost:8080/users"}]

# FastAPI app initialization with OpenAPI details
app = FastAPI(
    root_path="/roles",
    title=openapi_info["title"],
    description=openapi_info["description"],
    version=openapi_info["version"],
    terms_of_service=openapi_info["termsOfService"],
    contact=openapi_info["contact"],
    license_info=openapi_info["license"],
    servers=servers,
)


origins = [
    "http://localhost:4200",  # Angular local development server
    "http://192.168.1.52:4203",
    "http://122.165.225.9:4203",  # Your production Angular app URL
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers (Authorization, Content-Type, etc.)
)


@app.on_event("startup")
async def startup_event():
    try:
        await generate_routers()
        await init_db()
        logger.info("Application startup successful")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")

async def generate_routers():
    openapi_file = './app/open-api/openapi.yaml'
    output_dir = './app/generated_app'
    templates_dir='./app/open-api/custom-templates'
    generated_file = os.path.join(output_dir, '__init__.py')  # Check for a file in the output directory
    os.makedirs(output_dir, exist_ok=True)

    # Check if routers have already been generated
    if not os.path.exists(generated_file):
        if os.path.exists(openapi_file):
            logger.info("Generating routers...")
            # Generate FastAPI routers using fastapi-code-generator
            command = f"fastapi-codegen --input {openapi_file} --output {output_dir} --output-model-type pydantic_v2.BaseModel --generate-routers --template-dir {templates_dir}"
            result = subprocess.run(command, shell=True,capture_output=True, text=True)
            print(result.stdout)
            print(result.stderr)
            logger.info(f"Routers generated and saved to {output_dir}")

            try:
                # Import and register the routers dynamically
                from app.generated_app.routers.role import router as role_router

                app.include_router(role_router, tags=["Role"])



            except Exception as e:
                logger.error(f"Failed to import generated routers: {e}")
                raise e

        else:
            logger.error("OpenAPI specification file not found.")  
    else:
        logger.info("Routers already generated, skipping generation.")




@app.middleware("http")
async def logger_middleware(request: Request, call_next):
    # Generate or retrieve worker_id (could be from request headers or generated)
    worker_id = request.headers.get("X-Worker-ID", str(uuid.uuid4()))

    # Set up the logger with worker_id
    request.state.logger = get_logger(worker_id)

    # Log that the worker_id is set
    request.state.logger.info(f"Worker ID {worker_id} initialized for request {request.url.path}")

    # Call the next middleware or route handler
    response = await call_next(request)

    # Optionally, log after request is processed
    request.state.logger.info(f"Finished processing request for {request.url.path}")

    return response

        
if __name__ == "__main__":
    import uvicorn # type: ignore
    logger.info("Starting application...")
    uvicorn.run(app, host="0.0.0.0", port=5002)
