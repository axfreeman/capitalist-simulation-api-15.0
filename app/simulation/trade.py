"""This module contains functions used in handling the trade action."""

from sqlalchemy.orm import Session
from ..models import Buyer, Class_stock, Industry_stock, Seller, Commodity, Simulation
from app.logging import report

def constrain_demand(session,simulation):
    """Constrain demand to supply.
    TODO mostly untested
    """
    report(1,simulation.id,"CONSTRAINING DEMAND TO SUPPLY",session)
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
                    report(4,simulation.id, f"constraining stock {stock.id} demand to {stock.demand}",session)

# Tell class stocks the bad news.
                stock_query=session.query(Class_stock).where(Class_stock.commodity_id==commodity.id)
                for stock in stock_query:
                    session.add(stock)
                    stock.demand=stock.demand*commodity.allocation_ratio
                    report(4,simulation.id, f"constraining stock {stock.id} demand to {stock.demand}",session)

def buy_and_sell(db:Session, simulation:Simulation):
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

    report(1, simulation.id, f"Starting trade with simulation {simulation.id}", db)
    for seller in db.query(Seller).where(Seller.simulation_id == simulation.id):
        sales_stock = seller.sales_stock(db)
        report(2,simulation.id,
            f"seller {seller.owner_name(db)} can sell {sales_stock.size} and is looking for buyers {sales_stock.name}",db,
        )

        for buyer in db.query(Buyer).where(
            Buyer.simulation_id == simulation.id,
            Buyer.commodity_id == seller.commodity_id,
        ):
            report(3,simulation.id,
                f"buyer {buyer.owner_name(db)} will be asked to buy {buyer.purchase_stock(db).demand}",db,
            )
            buy(buyer, seller, simulation, db)
    db.commit()

def buy(buyer:Buyer, seller:Seller, simulation:Simulation, db:Session):
    """Tell seller to sell whatever the buyer demands and collect the money."""
    report(4,simulation.id,
        f"buyer {buyer.owner_name(db)} is buying {buyer.purchase_stock(db).demand}",db,
    )
    buyer_purchase_stock:Industry_stock|Class_stock = buyer.purchase_stock(db)
    seller_sales_stock:Industry_stock|Class_stock = seller.sales_stock(db)
    buyer_money_stock:Industry_stock|Class_stock = buyer.money_stock(db)
    seller_money_stock:Industry_stock|Class_stock = seller.money_stock(db)
    commodity:Commodity = seller.commodity(db)  # does not change yet, so no need to add it to the session
    amount = buyer_purchase_stock.demand
    report(5,simulation.id,f"seller sales stock is {seller_sales_stock.name}",db)
    report(5,simulation.id,f"buyer purchase stock is {buyer_purchase_stock.name}",db)
    report(5,simulation.id,f"buyer money stock is {buyer_money_stock.name}",db)
    report(5,simulation.id,f"seller money stock is {seller_money_stock.name}",db)
    report(4,simulation.id,
        f"Buying {amount} at price {commodity.unit_price} and value {commodity.unit_value}",db,
    )

# Transfer the goods

    db.add(buyer_purchase_stock)
    db.add(seller_sales_stock)
    buyer_purchase_stock.change_size(amount,db)
    buyer_purchase_stock.demand -= amount
    seller_sales_stock.change_size(-amount,db)

# Pay for the goods
    report(4,simulation.id,"Now you must pay",db)

    if buyer_money_stock == seller_money_stock:  
        # Internal trade to the sector
        report(4,simulation.id,"Internal transfer: no net payment effected",db,)
    else:
        db.add(buyer_purchase_stock)
        db.add(seller_sales_stock)
        # TODO account for MELT. Money can have a value different from its price
        seller_money_stock.change_size(amount * commodity.unit_price,db)
        buyer_money_stock.change_size(-amount * commodity.unit_price,db)
    # db.commit() # TODO verify that this is achieved by the final commit.

