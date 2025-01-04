"""Helper functions used by the 'price' action.

These functions are uncharacteristic, in that they do not represent a distinct
Stage of the simulation. Prices can change at any time, and when they do, values
are transformed as a result.

"""

from actions.utils import revalue_stocks
from models import models
from models.models import Class_stock, Commodity,Industry, Industry_stock,SocialClass, Simulation
from report.report import report
from sqlalchemy.orm import Session

def process_price_reset(session,simulation):

    # Reset the prices of all stocks. Also resets their values though this should have no effect
    revalue_stocks(session, simulation) #TODO separate revaluation of prices from revaluation of values

    # Calculate total price and total value of all commodities; then calculate the MELT
    calculate_melt(session,simulation)

    # Now revalue stocks again
    revalue_stocks(session, simulation) #TODO separate revaluation of prices from revaluation of values

def calculate_melt(session:Session,simulation:Simulation)->float:
    """
    Calculate total value, total price, the melt, and normalized prices.
    Invoked when the user changes prices, or when prices change as a result
    of the simulation itself.

    TODO under development. At present only revalue produced commodities. We should include all commodities 
    but at present, we are testing the simple transformation of produced stock values into normalised market prices
    """
    
    # Calculate the total value and total price of all produced commodities
    commodities = session.query(Commodity).where(Commodity.simulation_id == simulation.id,Commodity.origin=='INDUSTRIAL')
    session.add(simulation)
    simulation.total_value=0
    simulation.total_price=0
    commodity:Commodity # This is just a type hint - pylance doesn't allow it in the for loop

    for commodity in commodities:
        session.add(commodity)
        report(1,simulation.id,f"Processing prices for commodity {commodity.name} with value {commodity.total_value} and price {commodity.total_price}",session)
        simulation.total_value+=commodity.total_value
        simulation.total_price+=commodity.total_price
    simulation.melt=simulation.total_price/simulation.total_value
    report(1,simulation.id,f"Total price is {simulation.total_price} total value is {simulation.total_value} and melt is {simulation.melt}",session)

    # Recalculate unit values on this basis
    for commodity in commodities:
        report(2,simulation.id,f"Recalculating unit value of commodity {commodity.name}, currently {commodity.unit_value}",session)
        commodity.unit_value/=simulation.melt
        report(2,simulation.id,f"Unit value of commodity {commodity.name} is now {commodity.unit_value}",session)
    report(1,simulation.id,f"Finished recalculating unit values",session)
    session.commit()
    return simulation.melt

