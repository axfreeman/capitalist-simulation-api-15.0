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

def process_price_reset(session: Session,simulation:Simulation):
    """
    Apply the effects of a change in money prices. 
    This change can arise either through the algorithm itself (for example through the equalization process) 
    or by the user setting new prices directly. Thus can happen for any reason, not just when prices of production are formed.

    Steps are
        1. for each commodity propagate the change in unit prices to the price of its stocks TODO we could directly reset total price
        2. do NOT resize, because a price change should not affect sizes TODO maybe test for this
        3. calculate MELT as sum of all commodity prices divided by sum of all commodity values
        4. modify all unit values by dividing by the MELT
        5. for each commodity, propagate the change in unit values to the value of its stocks.
        6. TEST that the total value of all stocks has not changed?
        7. TEST that total surplus value has not changed/is equal to profit in value terms?
    """
    report(1,simulation.id,f"Resetting and adding up prices. Economy-wide price is {simulation.total_price}, E-W value is {simulation.total_value} and melt is {simulation.melt}",session)
   
#   Steps 1-3
    total_price=0
    total_value=0
    # TODO FOR DEMONSTRATION PURPOSES HERE WE ONLY INCLUDE PRODUCED COMMODITIES. FULL VERSION SHOULD LET USER CHOOSE
    commodities=session.query(Commodity).where(Commodity.simulation_id==simulation.id).where(Commodity.origin=="INDUSTRIAL")
    c:Commodity
    for c in commodities:
        session.add(c)
        report(2,simulation.id,f"Commodity {c.name} before processing: total price is {c.total_price}",session)
        extra_price=c.unit_price*c.size
        extra_value=c.unit_value*c.size
        c.total_price=extra_price
        total_price+=extra_price
        total_value+=extra_value 
        # NOTE total value of c should be invariant; this calculation is ONLY used to set the simulation.total_value and hence calculate the MELT.
        # NOTE extra_value should not be used to reset c.total_value. Instead, we test they are equal and report a warning if they are not.

        # report(2,simulation.id,f"Calculated value of {c.name} is {extra_value} bringing economy-wide total to {total_value}",session)
        # report(2,simulation.id,f"Total price has reached {simulation.total_price}",session)

        report(2,simulation.id,f"Price of {c.name} is {extra_price} bringing economy-wide total to {total_price}",session)
        report(2,simulation.id,f"Value of {c.name} is {extra_value} bringing calculated economy-wide total to {total_value}",session)
        if c.total_value!=extra_value:
            report(2,simulation.id,f"WARNING: value of {c.name} was {c.total_value} and the calculated value is {extra_value}. These should be the same but are not")

    # TODO simulation.total_value should be set separately from this. But since it isn't as yet, we set it here
    simulation.total_value=total_value
    simulation.total_price=total_price
    simulation.melt=simulation.total_price/simulation.total_value
    report(1,simulation.id,f"Finished resetting and adding up prices. E-W price is now {simulation.total_price}, E-W value is {simulation.total_value} and MELT is {simulation.melt}",session)

#   Steps 4-5
    report(1,simulation.id,f"Applying MELT to unit values and then to stocks",session)
    for c in commodities:
        new_unit_value=c.unit_price/simulation.melt
        report(2,simulation.id,f"Unit price of {c.name} was {c.unit_price} so unit value was reset to {new_unit_value}",session)
        c.unit_value=new_unit_value
        c.revalue_stocks(session,simulation)
    report(1,simulation.id,f"Finished applying MELT",session)

#   TODO tests (steps 6-7)

    session.commit()
