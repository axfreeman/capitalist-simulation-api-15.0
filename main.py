from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.database import Base, engine

from app.routers import (
    actions,
    commodity,
    simulation,
    user,
    admin,
    industry,
    socialClass,
    stocks,
    trace,
    templates
)

app=FastAPI()

users = []

Base.metadata.create_all(bind=engine)

@app.get("/")
def reroute():
    return RedirectResponse(url="/docs", status_code=303) 

app.include_router(actions.router)
app.include_router(admin.router)
app.include_router(socialClass.router)
app.include_router(user.router)
app.include_router(commodity.router)
app.include_router(industry.router)
app.include_router(simulation.router)
app.include_router(stocks.router)
app.include_router(templates.router)
app.include_router(trace.router)

# app.include_router(tests.router)


