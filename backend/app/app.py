from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from backend.app.routers import experiment_router, run_router

# orjson.dumps() 4x Faster serialization of JSON
# at the global level compared to json.dumps()
app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(experiment_router.router)
app.include_router(run_router.router)


@app.get("/")
def index():
    return {"index": "NeuralRipper"}
