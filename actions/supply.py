"""Functions used by the 'Supply' action.

Their purpose is to calculate the total supply for each commodity, in
preparation for Trade.

Quite simple: supply is simply the size of the Sales Stock.
"""
from models.models import Class_stock, Commodity,Industry, Industry_stock,SocialClass, Simulation
from report.report import report
from sqlalchemy.orm import Session

def process_supply(session:Session, simulation:Simulation):
    """
    Calculate the supply of all commodities from their sales stocks
    and save the results in the commodity objects
    """
    initialise_supply(session, simulation)
    report(1,simulation.id, "Calculating supply from industries",session)
    industry_supply(session, simulation)  # tell industries to register their supply
    report(1,simulation.id, "Calculating supply from social classes",session)
    class_supply(session, simulation)  # tell classes to register their supply 

def initialise_supply(session,simulation):
    """Set supply of every commodity to zero to prepare for the calculation."""
    cquery = session.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for c in cquery:
        session.add(c)
        c.supply=0
    session.commit()

# Ask each industry to tell its sale commodity how much it has to sell
def industry_supply(session,simulation):
    """Calculate supply from every industries for each commodity it produces."""

    query=session.query(Industry).where(Industry.simulation_id==simulation.id)
    for industry in query:
        sales_stock:Industry_stock=industry.sales_stock(session)
        commodity:Commodity=sales_stock.commodity(session)
        # print(f"Debugging supply by industry {industry.name} and id {industry.id}")
        # print(f"Processing sales stock with name {sales_stock.name} and id {sales_stock.id}")
        # print(f"The commodity of this stock is {commodity.name} and its ID is {commodity.id}")
        session.add(commodity) # session.add(sales_stock) # not needed because we are not changing the stock
        ns=sales_stock.size 
        report(2,simulation.id,f'{industry.name} adds {ns:.0f} to the supply of {commodity.name}, which was previously {commodity.supply:.0f}',session)
        commodity.supply+=ns
    session.commit()

# Ask each class to tell its sale commodity how much it has to sell
def class_supply(session,simulation):
    """Calculate supply from every class for each commodity it produces."""

    query=session.query(SocialClass).where(SocialClass.simulation_id==simulation.id)
    for socialClass in query:
        sales_stock:Class_stock=socialClass.sales_stock(session)
        commodity:Commodity=sales_stock.commodity(session) # commodity that this owner supplies
        session.add(commodity)
        ns=sales_stock.size 
        report(2,simulation.id,f'{socialClass.name} adds {ns:.0f} to the supply of {commodity.name}, which was previously {commodity.supply:.0f}',session)  
        commodity.supply+=ns
    session.commit()

