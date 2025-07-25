from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.routers import experiment_router, run_router
from app.routers import infer_router
from app.routers.infer_router import lifespan

# orjson.dumps() 4x Faster serialization of JSON
# at the global level compared to json.dumps()
app = FastAPI(default_response_class=ORJSONResponse, lifespan=lifespan)
app.include_router(experiment_router.router)
app.include_router(run_router.router)
app.include_router(infer_router.router)

# Mind, different port is also different origin
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return {"index": "NeuralRipper"}
