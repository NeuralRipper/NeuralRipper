from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.routers import experiment_router, run_router
# from app.routers import infer_router
# from app.routers.infer_router import lifespan

# orjson.dumps() 4x Faster serialization of JSON
# at the global level compared to json.dumps()
# app = FastAPI(default_response_class=ORJSONResponse, lifespan=lifespan)
app = FastAPI(default_response_class=ORJSONResponse)

# Add CORS middleware FIRST, before including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow all sources
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(experiment_router.router)
app.include_router(run_router.router)
# app.include_router(infer_router.router)


@app.get("/")
def index():
    return {"index": "NeuralRipper"}
