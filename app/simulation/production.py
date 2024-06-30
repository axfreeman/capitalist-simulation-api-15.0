from ..models import Simulation, Industry, Industry_stock
from app.logging import report
from sqlalchemy.orm import Session

def produce(session:Session, simulation:Simulation):
    """Tell all industries to produce."""
    report(1, simulation.id, "PRODUCTION", session)
    iquery = session.query(Industry).where(Industry.simulation_id == simulation.id)

    for ind in iquery:
        industry_produce(ind, session, simulation)

def industry_produce(
        industry:Industry, 
        session:Session, 
        simulation:Simulation)->str:
    """Tell 'industry' to produce.

    Increase the size of self.sales_stock by self.output_scale.
    
    Calculate the amount of each productive Stock that is used up and
    decrease its size by that amount.

    Calculate the value of each industrially-produced productive Stock that
    is used up and add this to the value of self.sales_stock.

    Add the used-up size of each socially-produced productive Stock to 
    the value of self.sales_stock.

    Once Production and Reproduction are both complete, recalculate
    unit values and prices and then revalue all Stocks from their sizes.

    This is a separate calculation and is not done inside production,
    because it can only calculated after Social Classes have restored
    their sale_stocks. This applies in particular to Labour - but a 
    value-creating function can be assigned to any Social Class to study 
    the consequences of a theory which asserts that it provides a 'factor 
    of production' whether ficitious or not.

        industry(Industry):
            the industry that is producing

        session(Session):
            the sqlAlchemy session that will store the results

        simulation(Simulation):
            the simulation currently under way
    """

    report(2, simulation.id, f"{industry.name} is producing", session)
    sales_stock = industry.sales_stock(session)
    session.add(sales_stock)
    sales_commodity = sales_stock.commodity(session)
    report(3,simulation.id,
        f"{sales_stock.name} of {sales_commodity.name} before production is {sales_stock.size} with value {sales_stock.value}",session,
    )

    productive_stocks_query = session.query(Industry_stock).filter(
        Industry_stock.simulation_id == simulation.id,
        Industry_stock.industry_id == industry.id,
        Industry_stock.usage_type == "Production",
    )
    for stock in productive_stocks_query:
        session.add(stock)
        commodity = stock.commodity(session)
        report(4,simulation.id,f"Processing productive input '{stock.name}' with size {stock.size} and value {stock.value}",session)

        # Evaluate the size and value contribution of this stock
        if commodity.name == "Labour Power":
            # Labour Power adds its magnitude, not its value
            value_contribution=stock.flow_per_period(session)
            stock.size -= value_contribution
            stock.value-=value_contribution*commodity.unit_value
            stock.price-= value_contribution*commodity.unit_price
            report(4, simulation.id, f"{stock.name} creates value {value_contribution}", session)
        else:
            value_contribution = stock.flow_per_period(session)* sales_commodity.unit_value
            # Other productive stocks transfer their value, not their magnitude
            stock.value -= value_contribution
            stock.size -=stock.flow_per_period(session)
            stock.price-= stock.flow_per_period(session)*commodity.unit_price
            report(4,simulation.id,f"{stock.name} transfers value {value_contribution} at unit value {commodity.unit_value} ",session)
        sales_stock.value += value_contribution
        report(3, simulation.id, f"Sales value after inputs from {stock.name} is {sales_stock.value}", session)
    # report(4, simulation.id, f"output scale is {industry.output_scale}", session) # Uncomment for more verbose diagnostics
    sales_stock.size += industry.output_scale/simulation.periods_per_year
    report(3, simulation.id, f"Sales value after production is {sales_stock.value} and size {sales_stock.size}", session)
    
    # TODO If MELT is not 1, we have to account below for the value of money
    sales_stock.price=sales_stock.value
    report(3, simulation.id, f"Sales price after production is {sales_stock.price}", session)
    session.commit()

