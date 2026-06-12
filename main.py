from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(
    title="Blitz Movie API",
    description=(
        "An unofficial REST API for MovieBox — search, discover, and get download links "
        "for movies, TV series, anime, music, and educational content.\n\n"
        "**Created by Blitz** | Powered by [moviebox-api](https://github.com/Simatwa/moviebox-api)"
    ),
    version="1.0.0",
    contact={"name": "Blitz", "url": "https://github.com/heroblitz"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["General"])
async def root():
    return {
        "name": "Blitz Movie API",
        "version": "1.0.0",
        "created_by": "Blitz",
        "description": "Unofficial MovieBox REST API — movies, series, anime, music & education",
        "docs": "/docs",
        "status": "online",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
