"""Helper functions used by the 'demand' action.

They are all called by 'demandHandler' but are available for use 
elsewhere.

"""

from models import models
from models.models import Class_stock, Commodity,Industry, Industry_stock,SocialClass, Simulation
from report.report import report
from sqlalchemy.orm import Session

def calculate_demand(session:Session, simulation:Simulation):
        
    """Set demand for all stocks and commodities in one simulation.

        First, initialise demand to zero.
    
        Then ask every industry to calculate demand for its productive 
        stocks, and every social class to calculate consumer demand.
    
        Finally, tell every commodity to add up demand from stocks of it."""

    initialise_demand(session, simulation)
    industry_demand(session, simulation) # tell industries to register their demand with their stocks.
    class_demand(session, simulation)  # tell classes to register their demand with their stocks.
    commodity_demand(session, simulation)  # tell the commodities to tot up the demand from all stocks of them.

def initialise_demand(session: Session,simulation: Simulation):
    """Set demand to zero for all commodities and stocks, prior to recalculating total demand."""

    report(1,simulation.id, "INITIALISING DEMAND FOR COMMODITIES AND STOCKS",session)
    cquery = session.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for c in cquery:
        session.add(c)
        c.demand=0
    squery = session.query(Industry_stock).where(Industry_stock.simulation_id==simulation.id)
    for s in squery:
        session.add(s)
        s.demand=0
    squery = session.query(Class_stock).where(Class_stock.simulation_id==simulation.id)
    for s in squery:
        session.add(s)
        s.demand=0
    session.commit()

def industry_demand(session:Session,simulation:Simulation):
    """Tell each industry to set demand for each of its productive stocks."""
    query=session.query(Industry).where(Industry.simulation_id==simulation.id)
    report(1,simulation.id, "CALCULATING DEMAND FROM INDUSTRIES",session)
    industry:Industry
    for industry in query:
        report(2, simulation.id,f"Industry {industry.name} will set demand for all its productive stocks",session)
        session.add(industry)
        cost:float =0
        money_stock:Industry_stock=industry.money_stock(session)
        money=money_stock.size
        query=session.query(Industry_stock).filter(Industry_stock.industry_id==industry.id,Industry_stock.usage_type=="Production")
        for stock in query:
            session.add(stock)
            commodity: Commodity=stock.commodity(session)
            demand=round(stock.flow_per_period(session),4)
            stock.demand+=demand
            cost+=demand*commodity.unit_price
            report(3,simulation.id,f'Demand for {commodity.name} has grown by {demand} to {stock.demand}, from [{stock.name}]',session)
        report(2, simulation.id,f"Industry {industry.name} has {money} to finance costs of {cost}",session)
        if money<cost:
            report(2, simulation.id,f"Insufficient money to maintain production: CALL FOR HELP!",session)
            finance_ratio=industry.get_capitalist_help(cost-money,session)
            report(2, simulation.id,f"After getting help, industry has {money_stock.size}",session)
            # TODO adjust demand depending on finance? I think this is done in Trade
    session.commit()

def class_demand(session:Session,simulation:Simulation):
    """Tell each class to set demand for each of its consumption stocks."""
    report(1,simulation.id, "CALCULATING DEMAND FROM SOCIAL CLASSES",session)
    query=session.query(SocialClass).where(SocialClass.simulation_id==simulation.id)
    for socialClass in query:
        report(2, simulation.id,f"Asking class {socialClass.name} to set demand for all its consumption stocks",session)
        session.add(socialClass)
        query=session.query(Class_stock).filter(Class_stock.class_id==socialClass.id,Class_stock.usage_type=="Consumption")
        for stock in query:
            session.add(stock)
            commodity=stock.commodity(session)
            demand=round(stock.flow_per_period(session),4) 
            stock.demand+=demand
            report(3,simulation.id,f'Demand for {commodity.name} has grown by {demand} to {stock.demand}, from [{stock.name}]',session)
        report(2, simulation.id,f"Class {socialClass.name} has finished setting demand",session)
    session.commit()

def commodity_demand(session:Session,simulation:Simulation):
    """For each commodity, add up the total demand by asking all its stocks what they need.
    Do this separately from the stocks as a kind of check - could be done at the same time.
    """
    report(1,simulation.id,"ADDING UP DEMAND FOR COMMODITIES",session)
    query=session.query(models.Commodity).where(Commodity.simulation_id==simulation.id)
    for commodity in query:
       
# Demand from Industry Stocks

        session.add(commodity)
        # report(2,simulation.id, f'Calculating total demand for {commodity.name} from Industries',session)
        squery=session.query(Industry_stock).filter(Industry_stock.commodity_id==commodity.id,Industry_stock.usage_type=="Production")
        for stock in squery:
            industry:Industry=stock.industry(session)
            report(3,simulation.id,f'Demand for {commodity.name} with owner ({industry.name}) is {stock.demand}, from [{stock.name}] ',session)
            commodity.demand+=stock.demand
        report (2,simulation.id, f'Total demand from industries for {commodity.name} is {commodity.demand}',session)

# Demand from Class Stocks

        # report(2,simulation.id, f'Calculating total demand for {commodity.name} from Classes',session)
        squery=session.query(Class_stock).filter(Class_stock.commodity_id==commodity.id)
        for stock in squery:
            social_class:SocialClass=stock.social_class(session)
            report(3,simulation.id,f'Demand for {commodity.name}  with owner ({social_class.name}) is {stock.demand} from [{stock.name}]',session)
            commodity.demand+=stock.demand
        report (2,simulation.id, f'Total demand from classes for {commodity.name} is now {commodity.demand}',session)

    session.commit()

