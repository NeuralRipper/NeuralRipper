from fastapi import FastAPI
from routers import experiment
app = FastAPI()
app.include_router(models.router)


@app.get("/")
def index():
    return {"index": "NeuralRipper"}

