from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.routers import experiment_router, run_router

# orjson.dumps() 4x Faster serialization of JSON
# at the global level compared to json.dumps()
app = FastAPI(default_response_class=ORJSONResponse)

# Add CORS middleware FIRST, before including routers
app.add_middleware(
    CORSMiddleware,
    # ["*""] won't allow request with credentials, need to specify
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(experiment_router.router)
app.include_router(run_router.router)


@app.get("/")
def index():
    return {"index": "NeuralRipper"}
