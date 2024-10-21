"""Helper functions used by the 'price' action.

These functions are uncharacteristic, in that they do not represent a distinct
Stage of the simulation. Prices can change at any time, and when they do, values
are transformed as a result.

"""

from models import models
from models.models import Class_stock, Commodity,Industry, Industry_stock,SocialClass, Simulation
from report.report import report
from sqlalchemy.orm import Session

def calculate_melt(session:Session,simulation_id:int)->float:
    """
    Calculate total value, total price, the melt, and normalized prices.
    Invoked when the user changes prices, or when prices change as a result
    of the simulation itself.
    """
# TODO under development
    report(2,simulation_id,f"Changing prices for simulation {simulation_id}",session)
    commodities = session.query(Commodity).where(Commodity.simulation_id == simulation_id,Commodity.usage=='PRODUCTIVE')
    simulation=session.query(Simulation).where(Simulation.id==simulation_id).first()
    session.add(simulation)
    commodity:Commodity
    total_value=0
    total_price=0
    for commodity in commodities:
        session.add(commodity)
        report(3,simulation_id,f"Processing prices for commodity {commodity.name} with value {commodity.total_value} and price {commodity.total_price}",session)
        simulation.total_value+=commodity.total_value
        simulation.total_price+=commodity.total_price
    simulation.melt=simulation.total_price/simulation.total_value
    report(2,simulation_id,f"Total price is {simulation.total_price} total value is {simulation.total_value} and melt is {simulation.melt}",session)
    for commodity in commodities:
        report(3,simulation_id,f"Recalculating unit value of commodity {commodity.name}, currently {commodity.unit_value}",session)
        commodity.unit_value/=simulation.melt
        report(3,simulation_id,f"Unit value of commodity {commodity.name} is now {commodity.unit_value}",session)
    report(2,simulation_id,f"Finished recalculating unit values",session)
    session.commit()
    return simulation.melt

