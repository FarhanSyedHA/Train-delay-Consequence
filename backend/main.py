from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import DatabaseConnection
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    DatabaseConnection.get_driver()
    yield

    DatabaseConnection.close()


app = FastAPI(
    title="Train Delay Cascades & Passenger Connection API",
    description="Graph-backed simulation engine for railway knock-on delay propagation and transfer feasibility.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration (React, Vite, Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)