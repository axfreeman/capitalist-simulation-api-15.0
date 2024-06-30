"""Functions used by the 'Supply' action.

Their purpose is to calculate the total supply for each commodity, in
preparation for Trade.

Quite simple: supply is simply the size of the Sales Stock.
"""
from ..models import Class_stock, Commodity,Industry, Industry_stock,SocialClass
from app.logging import report

def initialise_supply(session,simulation):
    """Set supply of every commodity to zero to prepare for the calculation."""
    cquery = session.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for c in cquery:
        report(1,simulation.id,f"Initialising commodity {c.name}",session)
        session.add(c)
        c.supply=0
    session.commit()

# Ask each industry to tell its sale commodity how much it has to sell
def industry_supply(session,simulation):
    """Calculate supply from every industries for each commodity it produces."""

    report(1,simulation.id, "CALCULATING SUPPLY FOR INDUSTRIES",session)
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

    report(1,simulation.id, "CALCULATING SUPPLY FROM SOCIAL CLASSES",session)
    query=session.query(SocialClass).where(SocialClass.simulation_id==simulation.id)
    for socialClass in query:
        sales_stock:Class_stock=socialClass.sales_stock(session)
        commodity:Commodity=sales_stock.commodity(session) # commodity that this owner supplies
        session.add(commodity)
        ns=sales_stock.size 
        report(2,simulation.id,f'{socialClass.name} adds {ns:.0f} to the supply of {commodity.name}, which was previously {commodity.supply:.0f}',session)  
        commodity.supply+=ns
    session.commit()
