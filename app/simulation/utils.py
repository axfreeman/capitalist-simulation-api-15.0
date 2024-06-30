from ..models import Class_stock, Commodity,Industry, Industry_stock, Simulation
from app.logging import report
from sqlalchemy.orm import Session

"""Helper functions for use in all parts of the simulation."""

def revalue_commodities(
      session:Session, 
      simulation:Simulation):
  """Calculate the size, value and price of all commodities from their stocks
  Recalculate unit values and unit prices on this basis.

  Normally, 'revalue stocks' should be called after this, because a change
  in the unit value and/or price will affect all stocks of it.

      session(Session):
          The sqlAlchemy session which will commit the commodity to storage

      simulation(Simulation):
          The simulation to which this calculation refers
  """

  report(1,simulation.id,"CALCULATE THE SIZE, VALUE AND PRICE OF ALL COMMODITIES",session)
  commodities=session.query(Commodity).where(Commodity.simulation_id==simulation.id)
  for commodity in commodities:
      session.add(commodity)
      commodity.total_value=0
      commodity.total_price=0
      commodity.size=0

# Calculate the contribution of all stocks belonging to industries
      istocks=session.query(Industry_stock).where(Industry_stock.commodity_id==commodity.id)
      for stock in istocks:
          report(2,simulation.id,f"Processing the industrial stock called {stock.name}",session)
          commodity.total_value+=stock.value
          commodity.total_price+=stock.price
          commodity.size+=stock.size
          report(3,simulation.id,f"Adding {stock.size} to the size of {commodity.name} bringing it to {commodity.size}",session)
          report(3,simulation.id,f"Adding {stock.value} to the value of {commodity.name} bringing it to {commodity.total_value}",session)
          report(3,simulation.id,f"Adding {stock.price} to the price of {commodity.name} bringing it to {commodity.total_price}",session)

# Calculate the contribution of all stocks belonging to classes
      cstocks=session.query(Class_stock).where(Class_stock.commodity_id==commodity.id)
      for stock in cstocks:
          report(2,simulation.id,f"Processing the class stock called {stock.name}",session)
          commodity.total_value+=stock.value
          commodity.total_price+=stock.price
          commodity.size+=stock.size
          report(3,simulation.id,f"Adding {stock.size} to the size of {commodity.name} bringing it to {commodity.size}",session)
          report(3,simulation.id,f"Adding {stock.value} to the value of {commodity.name} bringing it to {commodity.total_value}",session)
          report(3,simulation.id,f"Adding {stock.price} to the price of {commodity.name} bringing it to {commodity.total_price}",session)
  session.commit()

  for commodity in commodities:
      if commodity.size>0:
        report(2,simulation.id,f"Commodity {commodity.name} has size {commodity.size}, total value {commodity.total_value} and total price {commodity.total_price}",session)
        commodity.unit_value=commodity.total_value/commodity.size
        commodity.unit_price=commodity.total_price/commodity.size
        report(3,simulation.id,f"Setting its unit value to {commodity.unit_value} and its unit price to {commodity.unit_price}",session)

def revalue_stocks(
      session:Session, 
      simulation:Simulation):
  """ Revalue all stocks.
  Set value from unit value and size of their commodity
  Set price from unit price and size of their commodity

      session(Session):
          the sqlAlchemy session that will store the revalued stocks

      simulation(Simulation):
          the simulation that is currently being processed    
  """
  report(1,simulation.id,"RESETTING PRICES AND VALUES",session)

# Industry stocks

  istocks=session.query(Industry_stock).where(Industry_stock.simulation_id==simulation.id)
  report(2,simulation.id,"Revaluing industry stocks",session)
  for stock in istocks:
      commodity=session.query(Commodity).where(Commodity.id == stock.commodity_id).first()
      session.add(stock)
      stock.value=stock.size*commodity.unit_value
      stock.price=stock.size*commodity.unit_price
      report(3,simulation.id,f"Setting the value of the stock [{stock.name}] to {stock.value} and its price to {stock.price}",session)
  session.commit()

# Class stocks

  cstocks=session.query(Class_stock).where(Class_stock.simulation_id==simulation.id)
  report(2,simulation.id,"Revaluing class stocks",session)
  for stock in cstocks:
      commodity=session.query(Commodity).where(Commodity.id == stock.commodity_id).first()
      session.add(stock)
      stock.value=stock.size*commodity.unit_value
      stock.price=stock.size*commodity.unit_price
      report(3,simulation.id,f"Setting the value of the stock [{stock.name}] to {stock.value} and its price to {stock.price}",session)
  session.commit()

# TODO this should be a method of the Industry object
def capital(
      session:Session, 
      simulation:Simulation,
      industry:Industry)->float:
    """Calculate the initial capital of the given industry
    This is equal to the sum of the prices of all its stocks
    Assumes that the price of all these stocks has been set

      session(Session):
          the sqlAlchemy session that will store the revalued stocks

      simulation(Simulation):
          the simulation that is currently being processed    

      industry(Industry):
          the industry whose capital is calculated

      returns(float):
          the capital of the industry concerned
    """
    report(2,simulation.id,f"Calculating the capital of {industry.name}",session)
    result=0
    istocks=session.query(Industry_stock).where(Industry_stock.industry_id==industry.id)
    for stock in istocks:
        report(3,simulation.id,f"Industry stock [{stock.name}] is adding {stock.price} to the capital of {industry.name}",session)
        result+=stock.price
    return result

def calculate_initial_capitals(
      session:Session, 
      simulation:Simulation):
    """
    Calculate the initial capital of the given industry and store it.
    This is equal to the sum of the prices of all its stocks
    Assumes that the price of all these stocks has been set correctly
      session(Session):
          the sqlAlchemy session that will store the revalued stocks

      simulation(Simulation):
          the simulation that is currently being processed    
    """
    report(1,simulation.id,f"CALCULATING INITIAL CAPITAL for simulation {simulation.id}",session)
    industries=session.query(Industry).where(Industry.simulation_id==simulation.id)
    for industry in industries:
      report(2,simulation.id,f"Asking for the capital of {industry.name}",session)      
      session.add(industry)
      industry.initial_capital=capital(session,simulation,industry)
    session.commit()

def calculate_current_capitals(
      session:Session, 
      simulation:Simulation):
    """
    Calculate the current capital of all industries in the simulation and store it.
    Set the profit and the profit rate of each industry.

    Assumes that the price of all stocks has been set correctly.

      session(Session):
          the sqlAlchemy session that will store the revalued stocks

      simulation(Simulation):
          the simulation that is currently being processed    

    """
    report(1,simulation.id,"CALCULATING CURRENT CAPITAL",session)
    industries=session.query(Industry).where(Industry.simulation_id==simulation.id)
    for industry in industries:
      session.add(industry)
      industry.current_capital=capital(session,simulation,industry)
      industry.profit=industry.current_capital-industry.initial_capital
      industry.profit_rate=industry.profit/industry.initial_capital
    session.commit()


