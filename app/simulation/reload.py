from sqlalchemy.orm import Session
import json
from sqlalchemy import insert
from ..models import Buyer, Class_stock, Industry_stock, Seller
from app.logging import report

def reload_table(session: Session, baseModel, filename: str, reload: bool, simulation_id:int):

    """Initialise one table,specified by baseModel, from JSON fixture data specified by filename."""
    
    report(2,simulation_id,f"Initialising table {filename}", session)
    query = session.query(baseModel)
    query.delete(synchronize_session=False)
    if reload:
        try:
            file = open(filename)
            jason = json.load(file)
            for item in jason:
                new_object = baseModel(**item)
                session.add(new_object)
            session.commit()
        except Exception as e:
            print(f"could not load because of exception {e}")
            print (f"trying to load ",item)
def initialise_buyers_and_sellers(db, simulation_id):

    """
    Create a helper table of buyers and sellers.

    Used by 'Trade' action, to organise the allocation of demand to supply
    and to conduct the actual transfers of goods and money from one owner 
    to another.

    The objects in this table are the id fields of the objects in the
    underlying owner and stock tables.

    These references are created when a simulation is cloned.
    """

# Create seller list

    report(1, simulation_id, "Creating a list of sellers for simulation {simulation_id}", db)
    query = db.query(Seller)
    query.delete(synchronize_session=False)

# Add all Industry Sales stocks to seller list

    stock_query = db.query(Industry_stock).filter(
        Industry_stock.simulation_id == simulation_id, Industry_stock.usage_type == "Sales"
    )
    for stock in stock_query:
        owner = stock.owner(db)
        commodity = stock.commodity(db)
        money_stock_id = owner.money_stock(db).id
        sales_stock_id = stock.id
        commodity_id = commodity.id
        report(2,simulation_id,
            f"Adding seller {owner.name} selling {stock.name} ({commodity.name}) for money {money_stock_id}",db,
        )
        seller = {
            "simulation_id": simulation_id,
            "owner_type": "Industry",
            "sales_stock_id": sales_stock_id,
            "money_stock_id": money_stock_id,
            "commodity_id": commodity_id,
        }
        new_seller = Seller(**seller)
        db.add(new_seller)

# Add all Class Sales stocks to seller list

    stock_query = db.query(Class_stock).filter(
        Class_stock.simulation_id == simulation_id, Class_stock.usage_type == "Sales"
    )
    for stock in stock_query:
        owner = stock.owner(db)
        commodity = stock.commodity(db)
        money_stock_id = owner.money_stock(db).id
        sales_stock_id = stock.id
        commodity_id = commodity.id
        report(2,simulation_id,
            f"Adding seller {owner.name} selling {stock.name} ({commodity.name})for money {money_stock_id}",db,
        )
        seller = {
            "simulation_id": simulation_id,
            "owner_type": "Class",
            "sales_stock_id": sales_stock_id,
            "money_stock_id": money_stock_id,
            "commodity_id": commodity_id,
        }
        new_seller = Seller(**seller)
        db.add(new_seller)
    db.commit()

# Create buyer list

    report(1, simulation_id, "Creating a list of buyers for simulation {simulation_id}", db)
    query = db.query(Buyer)
    query.delete(synchronize_session=False)

# Add all productive Industry stocks to buyer list
    
    stock_query = db.query(Industry_stock).filter(
        Industry_stock.simulation_id == simulation_id,
        Industry_stock.usage_type != "Money",
        Industry_stock.usage_type != "Sales",
    )
    for stock in stock_query:
        owner = stock.owner(db)
        commodity = stock.commodity(db)
        money_stock_id = owner.money_stock(db).id
        purchase_stock_id = stock.id
        commodity_id = commodity.id
        report(2,simulation_id,
            f"Adding buyer {owner.name} buying {stock.name} ({commodity.name}) using money {money_stock_id}",db,
        )
        buyer = {
            "simulation_id": simulation_id,
            "owner_type": "Industry",
            "purchase_stock_id": purchase_stock_id,
            "money_stock_id": money_stock_id,
            "commodity_id": commodity_id,
        }
        new_buyer = Buyer(**buyer)
        db.add(new_buyer)

# Add all consumption Class stocks to buyer list
    
    stock_query = db.query(Class_stock).filter(
        Class_stock.simulation_id == simulation_id,
        Class_stock.usage_type != "Money",
        Class_stock.usage_type != "Sales",
    )
    for stock in stock_query:
        owner = stock.owner(db)
        commodity = stock.commodity(db)
        money_stock_id = owner.money_stock(db).id
        purchase_stock_id = stock.id
        commodity_id = commodity.id
        report(2,simulation_id,
            f"Adding buyer {owner.name} buying {stock.name} ({commodity.name}) using money {money_stock_id}",db,
        )
        buyer = {
            "simulation_id": simulation_id,
            "owner_type": "Class",
            "purchase_stock_id": purchase_stock_id,
            "money_stock_id": money_stock_id,
            "commodity_id": commodity_id,
        }
        new_buyer = Buyer(**buyer)
        db.add(new_buyer)
    db.commit()
