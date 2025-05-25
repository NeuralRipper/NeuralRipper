from fastapi import FastAPI
from backend.app.routers import experiment_router, run_router
app = FastAPI()
app.include_router(experiment_router.router)
app.include_router(run_router.router)


@app.get("/")
def index():
    return {"index": "NeuralRipper"}

