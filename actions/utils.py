from models.models import Class_stock, Commodity,Industry, Industry_stock, Simulation
from report.report import report
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

  report(1,simulation.id,"Calculate the size, value and price of all commodities",session)
  commodities=session.query(Commodity).where(Commodity.simulation_id==simulation.id)
  for c in commodities:
      session.add(c)
      c.total_value=0
      c.total_price=0
      c.size=0

# Calculate the contribution of all stocks belonging to industries
      istocks=session.query(Industry_stock).where(Industry_stock.commodity_id==c.id)
      for si in istocks:
          report(2,simulation.id,f"Processing industrial stock of {c.name} called [{si.name}]",session)
          c.total_value+=si.value
          c.total_price+=si.price
          c.size+=si.size
          report(3,simulation.id,f"Adding {si.size} to the size of {c.name}",session)
          report(3,simulation.id,f"Adding {si.value} to the value of {c.name}",session)
          report(3,simulation.id,f"Adding {si.price} to the price of {c.name}",session)
          # report(2,simulation.id,f"Commodity {c.name} now has size {c.size}, value {c.total_value}, price {c.total_price}",session)

# Calculate the contribution of all stocks belonging to classes
      cstocks=session.query(Class_stock).where(Class_stock.commodity_id==c.id)
      for sc in cstocks:
          report(2,simulation.id,f"Processing class stock of {c.name} called [{sc.name}]",session)
          c.total_value+=sc.value
          c.total_price+=sc.price
          c.size+=sc.size
          report(3,simulation.id,f"Adding {sc.size} to the size of {c.name}",session)
          report(3,simulation.id,f"Adding {sc.value} to the value of {c.name}",session)
          report(3,simulation.id,f"Adding {sc.price} to the price of {c.name}",session)
          # report(2,simulation.id,f"Commodity {c.name} now has size {c.size}, value {c.total_value}, price {c.total_price}",session)
# Recalculate the unit vvalues and prices of all commodities from their size and totals
  for c in commodities:
      report(2,simulation.id,f"Resetting unit value and price of commodity {c.name} with size {c.size}, value {c.total_value}, price {c.total_price}",session)
      if c.size>0:
        report(3,simulation.id,f"Commodity {c.name} has size {c.size}, total value {c.total_value} and total price {c.total_price}",session)
        c.unit_value=c.total_value/c.size
        c.unit_price=c.total_price/c.size
        report(3,simulation.id,f"Setting unit value of {c.name} to {c.unit_value} and its unit price to {c.unit_price}",session)
      else:
        report(3,simulation.id,f"Commodity {c.name} has zero size; no action taken",session)
      report(2,simulation.id,f"Finished resetting unit value and price of commodity {c.name}",session)
  session.commit()
  report(1,simulation.id,"Finished calculating both total and unit value and price of all commodities",session)

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
  report(1,simulation.id,"Reset stock values and prices from the unit values and prices of their commodities",session)

# Industry stocks
  istocks=session.query(Industry_stock).where(Industry_stock.simulation_id==simulation.id)
  report(2,simulation.id,"Resetting industry stocks",session)
  for stock in istocks:
      commodity=session.query(Commodity).where(Commodity.id == stock.commodity_id).first()
      session.add(stock)
      stock.value=stock.size*commodity.unit_value
      stock.price=stock.size*commodity.unit_price
      report(3,simulation.id,f"Setting value {stock.value} and price {stock.price} for stock [{stock.name}]",session)
  session.commit()
  report(2,simulation.id,"Finished resetting industry stocks",session)

# Class stocks
  cstocks=session.query(Class_stock).where(Class_stock.simulation_id==simulation.id)
  report(2,simulation.id,"Resetting class stocks",session)
  for stock in cstocks:
      commodity=session.query(Commodity).where(Commodity.id == stock.commodity_id).first()
      session.add(stock)
      stock.value=stock.size*commodity.unit_value
      stock.price=stock.size*commodity.unit_price
      report(3,simulation.id,f"Setting value to {stock.value} and price to {stock.price} for stock called {stock.name} ",session)
  session.commit()
  report(2,simulation.id,"Finished resetting class stocks",session)

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
    result=0
    istocks=session.query(Industry_stock).where(Industry_stock.industry_id==industry.id)
    for stock in istocks:
        report(3,simulation.id,f"Adding {stock.price} to capital of {industry.name} for Industry stock [{stock.name}]",session)
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
    report(1,simulation.id,f"Calculate initial capital for simulation {simulation.id}",session)
    industries=session.query(Industry).where(Industry.simulation_id==simulation.id)
    for ind in industries:
      session.add(ind)
      report(2,simulation.id,f"Calculating the initial capital of {ind.name}",session)
      ind.initial_capital=capital(session,simulation,ind)
      report(2,simulation.id,f"Initial capital of {ind.name} is {ind.initial_capital}",session)
    # report(1,simulation.id,f"Finished calculating initial capital",session)

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
    report(1,simulation.id,f"Calculating current capital for simulation {simulation.id}",session)
    industries=session.query(Industry).where(Industry.simulation_id==simulation.id)
    for ind in industries:
      report(2,simulation.id,f"Calculating the current capital of {ind.name}",session)
      session.add(ind)
      ind.current_capital=capital(session,simulation,ind)
      ind.profit=ind.current_capital-ind.initial_capital
      ind.profit_rate=ind.profit/ind.initial_capital
      report(2,simulation.id,f"Current capital of {ind.name} is {ind.current_capital}, profit is {ind.profit} and profit rate is {ind.profit_rate}",session)
    session.commit()
    # report(1,simulation.id,f"Finished calculating current capital",session)

def validate(object:any, name:str)->bool:
   """
   if object is empty, report a meaningful message and return false
   """
   if object is None:
      print(f"The object called {name} does not exist")
      return False
   return True
      
