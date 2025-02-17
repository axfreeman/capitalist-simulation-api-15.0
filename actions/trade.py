"""This module contains functions used in handling the trade action."""

from sqlalchemy.orm import Session
from models.models import Buyer, Class_stock, Industry_stock, Seller, Commodity, Simulation
from report.report import report

def process_trade(session,simulation):
    """
    Conduct the trade action. First, constrain traded quantities to demand.
    Then identify buyers and sellers. Then Trade.

    # TODO I don't think it's necessary to revalue, but check this.
    # This is because trade only involves a change of ownership.
    """
    constrain_demand(session, simulation)
    buy_and_sell(session, simulation)

def constrain_demand(session,simulation):
    """Constrain demand to supply.
    TODO mostly untested
    """
    report(1,simulation.id,"Constraining demand to supply",session)
    query=session.query(Commodity).where(Commodity.simulation_id==simulation.id)
    for commodity in query:
        session.add(commodity)
        if (commodity.usage=="PRODUCTIVE".strip()) or (commodity.usage=="CONSUMPTION".strip()):
            report(2,simulation.id,f'Demand for {commodity.name} is {commodity.demand} and supply is {commodity.supply}',session)
            if commodity.supply==0:
                report(3,simulation.id,f"Zero Supply of {commodity.name}",session)
                commodity.allocation_ratio=0
            elif commodity.demand<=commodity.supply:
                report(3,simulation.id,f'Supply exceeds or equals demand; no constraint applied',session)
                commodity.allocation_ratio=1
            else:
                report(3,simulation.id,f'Supply is less than demand; demand will be constrained',session)
                commodity.allocation_ratio=commodity.supply/commodity.demand
                commodity.demand*=commodity.allocation_ratio
                report(3,simulation.id,f'Demand for {commodity.name} has been constrained by supply to {commodity.demand}',session)
                report(3,simulation.id,f'Constraining stocks of {commodity.name} by a factor of {commodity.allocation_ratio}',session)

# Tell industry stocks the bad news.
                stock_query=session.query(Industry_stock).where(Industry_stock.commodity_id==commodity.id)
                for stock in stock_query:
                    session.add(stock)
                    stock.demand=stock.demand*commodity.allocation_ratio
                    report(3,simulation.id, f"constraining demand in industry stock {stock.id} called {stock.name} to {stock.demand}",session)

# Tell class stocks the bad news.
                stock_query=session.query(Class_stock).where(Class_stock.commodity_id==commodity.id)
                for stock in stock_query:
                    session.add(stock)
                    stock.demand=stock.demand*commodity.allocation_ratio
                    report(3,simulation.id, f"constraining demand in class stock {stock.id} called {stock.name} {stock.demand}",session)
            report(2,simulation.id,f'Finished constraining demand',session)

def buy_and_sell(session:Session, simulation:Simulation):
    """Implements buying and selling.

    Uses two helper classes 'Buyer' and 'Seller' which are created when the
    simulation is initialized. 
    
    An instantiation of each of these classes is stored in the database, but
    is not exported in the API

    It does not change once initialised.

    It contains the id fields of the underlying objects, on which this 
    function operates.

    TODO if demand is actually less than supply then we need some mechanism
    to oblige sellers to sell less. This can probably done within this 
    function - as indeed may be possible for the allocation of demand itself.
    """

    for seller in session.query(Seller).where(Seller.simulation_id == simulation.id):
        sales_stock = seller.sales_stock(session)
        try:
            report(2,simulation.id,f"seller {seller.owner_name(session)} can sell {sales_stock.size} and is looking for buyers {sales_stock.name}",session,)

            for buyer in session.query(Buyer).where(
                Buyer.simulation_id == simulation.id,
                Buyer.commodity_id == seller.commodity_id,
            ):
                report(3,simulation.id,f"buyer {buyer.owner_name(session)} will buy {buyer.purchase_stock(session).demand}",session,)
                buy(buyer, seller, simulation, session)
            report(2,simulation.id,"Finished selling",session,)
        except Exception as e:
            print(f"Error {e} looking for buyers")
    session.commit()

def buy(buyer:Buyer, seller:Seller, simulation:Simulation, session:Session):
    """Tell seller to sell whatever the buyer demands and collect the money."""
    report(3,simulation.id,f"buyer {buyer.owner_name(session)} is buying {buyer.purchase_stock(session).demand}",session,)
    buyer_purchase_stock:Industry_stock|Class_stock = buyer.purchase_stock(session)
    seller_sales_stock:Industry_stock|Class_stock = seller.sales_stock(session)
    buyer_money_stock:Industry_stock|Class_stock = buyer.money_stock(session)
    seller_money_stock:Industry_stock|Class_stock = seller.money_stock(session)
    commodity:Commodity = seller.commodity(session)  # does not change yet, so no need to add it to the session
    amount = buyer_purchase_stock.demand
    # report(4,simulation.id,f"seller sales stock is {seller_sales_stock.name}",session)
    # report(4,simulation.id,f"buyer purchase stock is {buyer_purchase_stock.name}",session)
    # report(4,simulation.id,f"buyer money stock is {buyer_money_stock.name}",session)
    # report(4,simulation.id,f"seller money stock is {seller_money_stock.name}",session)
    report(3,simulation.id,
        f"{buyer.owner_name(session)} is buying {amount} at price {commodity.unit_price} and value {commodity.unit_value}",session,
    )

# Transfer the goods

    session.add(buyer_purchase_stock)
    session.add(seller_sales_stock)
    buyer_purchase_stock.change_size(amount,session)
    buyer_purchase_stock.demand -= amount
    seller_sales_stock.change_size(-amount,session)

# Pay for the goods
    report(3,simulation.id,"Paying",session)

    if buyer_money_stock == seller_money_stock:  
        # Internal trade to the sector
        report(4,simulation.id,"Internal transfer: no net payment effected",session,)
    else:
        session.add(buyer_purchase_stock)
        session.add(seller_sales_stock)
        # TODO account for MELT. Money can have a value different from its price
        seller_money_stock.change_size(amount * commodity.unit_price,session)
        buyer_money_stock.change_size(-amount * commodity.unit_price,session)
    # db.commit() # TODO verify that this is achieved by the final commit.
    report(3,simulation.id,"Finished Paying",session,)
    
