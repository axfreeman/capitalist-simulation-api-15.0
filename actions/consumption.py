from sqlalchemy.orm import Session
from actions.utils import calculate_current_capitals, revalue_commodities,revalue_stocks
from models.models import Commodity, SocialClass, Simulation, Class_stock
from report.report import report

"""This module contains functions needed to implement the consumption action.
"""

def process_consume(session,simulation):
    consume(session, simulation)
    # Recalculate the price and value of every stock, then calculate capital
    revalue_commodities(session,simulation)
    revalue_stocks(session, simulation)
    calculate_current_capitals(session,simulation)


def consume(session:Session, simulation:Simulation)->str:
    """Tell all classes to consume and reproduce their product if they have one.
    TODO currently there are no population dynamics
    """
    squery = session.query(SocialClass).where(
        SocialClass.simulation_id == simulation.id
    )

    for social_class in squery:
        report(1,simulation.id,f"Social Class {social_class.name} is reproducing",session)
        class_consume(social_class, session, simulation)
        report(1, simulation.id, f"Social Class {social_class.name} has finished consuming", session)

    return "Consumption complete"

def class_consume(
        social_class:SocialClass, 
        session:Session, 
        simulation:Simulation):
    """Tell one social class to consume and reproduce its product if it has one.
    No population dynamics at present - just consumption.

        social_class(SocialClass):
            the class which is being processed

        session(Session):
            the sqlAlchemy session which will store the data

        simulation(Simulation):
            the Simulation currently under way
    """
    sales_stock = social_class.sales_stock(session)
    sales_commodity:Commodity=sales_stock.commodity(session)
    session.add(sales_stock)
    report(2,simulation.id,f"Sales stock size before consumption is {sales_stock.size} with value {sales_stock.value}",session)

    consumption_stocks_query = session.query(Class_stock).where(
        Class_stock.simulation_id == simulation.id,
        Class_stock.class_id == social_class.id,
        Class_stock.usage_type == "Consumption",
    )

    for stock in consumption_stocks_query:
        session.add(stock)
        commodity=stock.commodity(session)
        report(2,simulation.id,f"Consuming size  {stock.size} and value {stock.value} by stock [{stock.name}]",session)
        stock.size -=stock.flow_per_period(session)  # eat according to defined consumption standards
        stock.price-=stock.flow_per_period(session)*commodity.unit_price
        stock.value-=stock.flow_per_period(session)*commodity.unit_value
        report(2,simulation.id,f"Consumption stock size {stock.size}, value {stock.value} and price {stock.price} for [{stock.name}] ",session)
    
    # Currently no population dynamics and no differential labour intensity
    # Capitalists are assumed here (as per Cheng et al.) to supply services
    # in proportion to their number. But in neoclassical theory they would
    # have to supply in proportion to their capital. Others who believe this
    # nonsense will have to construct algorithms instantiating it if they
    # wish to test it logically.
    #
    # TODO We also do not calculate the unit value of factors, but we should
    report(2,simulation.id,f"Replenishing the sales stock {sales_stock.name} of {social_class.name} whose population is {social_class.population}",session)
    report(2,simulation.id,f"Its size before replenishment is {sales_stock.size} with value {sales_stock.value} and price {sales_stock.price}",session)
    sales_stock.size += (social_class.population/simulation.periods_per_year)
    sales_stock.value += (social_class.population/simulation.periods_per_year)*sales_commodity.unit_value
    sales_stock.price += (social_class.population/simulation.periods_per_year)*sales_commodity.unit_price
    report(2,simulation.id,f"Its size is now {sales_stock.size}, value {sales_stock.value} and price {sales_stock.price}",session)
    session.commit()
