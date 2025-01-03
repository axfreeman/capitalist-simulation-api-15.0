"""Helper functions used by the 'price' action.

These functions are uncharacteristic, in that they do not represent a distinct
Stage of the simulation. Prices can change at any time, and when they do, values
are transformed as a result.

"""

from models import models
from models.models import Class_stock, Commodity,Industry, Industry_stock,SocialClass, Simulation
from report.report import report
from sqlalchemy.orm import Session

def calculate_melt(session:Session,simulation:Simulation)->float:
    """
    Calculate total value, total price, the melt, and normalized prices.
    Invoked when the user changes prices, or when prices change as a result
    of the simulation itself.
    """
# TODO under development. At present only revalue productive commodities
# TODO actually we should include all commodities but at present, we are
# TODO testing the simple transformation of productive stock values into normalised market prices
# Calculate the total value and total price of all productive commodities

    commodities = session.query(Commodity).where(Commodity.simulation_id == simulation.id,Commodity.usage=='PRODUCTIVE')
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

