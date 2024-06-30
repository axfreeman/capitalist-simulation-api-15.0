"""Helper functions used by the 'demand' action.

They are all called by 'demandHandler' but are available for use 
elsewhere.

The end result is to set demand for all stocks and commodities in one 
simulation.

The sequence is:

    First, initialise demand to zero.
    
    Then ask every industry to calculate demand for its productive 
    stocks, and every social class to calculate consumer demand.
    
    Finally, tell every commodity to add up demand from stocks of it.
"""

from .. import models
from ..models import Class_stock, Commodity,Industry, Industry_stock,SocialClass, Simulation
from app.logging import report
from sqlalchemy.orm import Session

def initialise_demand(session: Session,simulation: Simulation):
    """Set demand to zero for all commodities and stocks, prior to
    recalculating total demand."""

    report(1,simulation.id, "INITIALISING DEMAND FOR COMMODITIES AND STOCKS",session)
    cquery = session.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for c in cquery:
        report(2,simulation.id,f"Initialising demand for commodity {c.name}",session)
        session.add(c)
        c.demand=0
    squery = session.query(Industry_stock).where(Industry_stock.simulation_id==simulation.id)
    for s in squery:
        report(2,simulation.id,f"Initialising demand for industry stock {s.name}",session)
        session.add(s)
        s.demand=0
    squery = session.query(Class_stock).where(Class_stock.simulation_id==simulation.id)
    for s in squery:
        report(2,simulation.id,f"Initialising demand for class stock {s.name}",session)
        session.add(s)
        s.demand=0
    session.commit()

def industry_demand(db:Session,simulation:Simulation):
    """Tell each industry to set demand for each of its productive stocks."""
    query=db.query(Industry).where(Industry.simulation_id==simulation.id)
    report(1,simulation.id, "CALCULATING DEMAND FROM INDUSTRIES",db)
    for industry in query:
        report(2, simulation.id,f"Industry {industry.name} will set demand for all its productive stocks",db)
        db.add(industry)
        query=db.query(Industry_stock).filter(Industry_stock.industry_id==industry.id,Industry_stock.usage_type=="Production")
        for stock in query:
            db.add(stock)
            commodity=stock.commodity(db)
            demand=round(stock.flow_per_period(db),4)
            stock.demand+=demand
            report(3,simulation.id,f'Demand for {stock.name} of {commodity.name} has been increased by {demand} to {stock.demand}',db)
    db.commit()

def class_demand(db:Session,simulation:Simulation):
    """Tell each class to set demand for each of its consumption stocks."""

    report(1,simulation.id, "CALCULATING DEMAND FROM SOCIAL CLASSES",db)
    query=db.query(SocialClass).where(SocialClass.simulation_id==simulation.id)
    for socialClass in query:
        report(2, simulation.id,f"Asking class {socialClass.name} to set demand for all its consumption stocks",db)
        db.add(socialClass)
        query=db.query(Class_stock).filter(Class_stock.class_id==socialClass.id,Class_stock.usage_type=="Consumption")
        for stock in query:
            db.add(stock)
            commodity=stock.commodity(db)
            demand=round(stock.flow_per_period(db),4) # TODO consider using fraction types
            stock.demand+=demand
            report(3,simulation.id,f'Demand for {stock.name} of {commodity.name} has been increased by {demand} to {stock.demand}',db)
    db.commit()

def commodity_demand(db:Session,simulation:Simulation):
    """For each commodity, add up the total demand by asking all its stocks what they need.
    Do this separately from the stocks as a kind of check - could be done at the same time.
    """
    report(1,simulation.id,"ADDING UP DEMAND FOR COMMODITIES",db)
    query=db.query(models.Commodity).where(Commodity.simulation_id==simulation.id)
    for commodity in query:
       
# Demand from Industry Stocks

        db.add(commodity)
        report(2,simulation.id, f'Calculating total demand for {commodity.name} from Industries',db)
        squery=db.query(Industry_stock).filter(Industry_stock.commodity_id==commodity.id,Industry_stock.usage_type=="Production")
        for stock in squery:
            industry:Industry=stock.industry(db)
            report(3,simulation.id,f'Demand for {commodity.name} from {stock.name} with owner ({industry.name}) is {stock.demand}',db)
            commodity.demand+=stock.demand
        report (2,simulation.id, f'Total demand for {commodity.name} is now {commodity.demand}',db)

# Demand from Class Stocks

        report(2,simulation.id, f'Calculating total demand for {commodity.name} from Classes',db)
        squery=db.query(Class_stock).filter(Class_stock.commodity_id==commodity.id)
        for stock in squery:
            social_class:SocialClass=stock.social_class(db)
            report(3,simulation.id,f'Demand for {commodity.name} from {stock.name} with owner ({social_class.name}) is {stock.demand}',db)
            commodity.demand+=stock.demand
        report (2,simulation.id, f'Total demand for {commodity.name} is now {commodity.demand}',db)

    db.commit()

