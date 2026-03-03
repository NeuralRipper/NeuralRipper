from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.connection import start_engine




@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function for all initialization startups, instances stored in app.state, disposes at shutdown
    """
    engine = start_engine()     # create engine instance
    app.state.engine = engine   # save to app.state
    yield                       # FastAPI runs and serves requests
    await engine.dispose()      # remove from state
    

app = FastAPI(lifespan=lifespan)    # lifespan registered to app


@app.get("/health")
async def health():
    return {
        "Health": "OK"
    }


    
    


# uv run uvicorn main:app --host 0.0.0.0