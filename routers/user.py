"""This module provides the endpoint for a user to clone a model."""

from fastapi import APIRouter, Depends, HTTPException, Security, status, Response
from database.database import get_session
from report.report import report
from models.schemas import CloneMessage, ServerMessage
from actions.reload import initialise_buyers_and_sellers
from actions.utils import calculate_current_capitals, calculate_initial_capitals, revalue_commodities, revalue_stocks
from authorization.auth import get_api_key
from models.models import Class_stock, Commodity, Industry, Industry_stock, SocialClass, Simulation, User

from sqlalchemy.orm import Session

router = APIRouter(prefix="/clone", tags=["Clone"])

def clone_model(model, session: Session, **kwargs):
    """Clone an arbitrary sqlalchemy model object without its 
    primary key values. These primary keys are then added by the caller.  

        Returns the clone unless the call is illegal (eg null model).

        Returns None if it can't be done
    """
    try:
        table = model.__table__
        non_pk_columns = [
            k for k in table.columns.keys() if k not in table.primary_key.columns.keys()
        ]
        data = {c: getattr(model, c) for c in non_pk_columns}
        data.update(kwargs)
        clone = model.__class__(**data)
        session.add(clone)
        session.commit()
        return clone
    except:
        return None

@router.get("/{id}",status_code=200, response_model=CloneMessage)
def create_simulation_from_template(
    id: str,
    response: Response,     
    u: User = Security(get_api_key),
    session: Session = Depends(get_session),
)->str:
    """Create a complete cloned simulation of the template defined by 'id'.  
    
    Parameters:  
    
        id: id of the template to clone.  
        api_key: api_key issued to the user of the cloned simulation.  
        session: an sqlAlchemy session.  

        return:  a message, httpStatus, id of the new simulation if successful.
    """
    try:
        id_as_number = int(id)
    except ValueError:
        response.status_code=status.HTTP_406_NOT_ACCEPTABLE
        return {
            "message":"invalid simulation id",
            "statusCode":status.HTTP_406_NOT_ACCEPTABLE, 
            "simulation_id":0
        }

    template = session.query(Simulation).filter(Simulation.id == int(id)).first()
    new_simulation = clone_model(template, session)
    if new_simulation is None:
        print("Failed call to clone. Quitting without doing anything")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clone Failed: Server error (Requested Simulation is 'None')",
        )
    report(0,new_simulation.id,f"CLONE SIMULATION FOR USER {u.username} FROM TEMPLATE {template.name} WITH ID {new_simulation.id}",session)
    session.add(new_simulation)  # commit twice, because we want to get the autogenerated id. There's probably a better way
    new_simulation.username = u.username
    session.add(new_simulation)
    session.add(u)
    new_simulation.state = "DEMAND"  # The simulation starts at this point
    u.current_simulation_id = new_simulation.id  # this is (initially) the current simulation
    session.commit()  # TODO reduce number of commits?

    # Clone all commodities in this simulation
    commodities = session.query(Commodity).filter(Commodity.simulation_id == template.id)
    report(1,new_simulation.id,f"Cloning Commodities",session)
    for commodity in commodities:
        report(2,new_simulation.id,f"Cloning commodity {commodity.name}",session,)
        new_commodity = clone_model(commodity, session)
        session.add(new_commodity)  # commit twice, because we want to get the autogenerated id. There's probably a better way
        session.add(commodity)  # seems to be transient after it is committed, which is a bit weird. So bring it out again, because we will modify it by adding successor_id
        new_commodity.simulation_id = new_simulation.id
        new_commodity.username = u.username
        commodity.successor_id = new_commodity.id
        session.commit()

    # Clone all industries in this simulation
    industries = session.query(Industry).filter(Industry.simulation_id == template.id)
    report(1,new_simulation.id,f"Cloning Industries",session)
    for industry in industries:
        report(2,new_simulation.id,f"Cloning industry {industry.name}",session)
        new_industry = clone_model(industry, session)
        session.add(new_industry)  # commit twice, because we want to get the autogenerated id. There's probably a better way
        session.add(industry)   # seems to be transient after we committed it, which is a bit weird - so bring it out again, because we're going to modify it
        new_industry.simulation_id = new_simulation.id
        new_industry.username = u.username
        industry.successor_id = new_industry.id
        session.commit()

    # Clone all classes in this simulation
    classes = session.query(SocialClass).filter(SocialClass.simulation_id == template.id)
    report(1,new_simulation.id,f"Cloning Classes",session)
    for socialClass in classes:
        report(2,new_simulation.id,f"Cloning class {socialClass.name}",session,)
        new_class = clone_model(socialClass, session)
        session.add(new_class)  # we commit twice, because we want to get the autogenerated id. There's probably a better way
        session.add(socialClass) # seems to be transient after we committed it, which is a bit weird - so bring it out again, because we're going to modify it
        new_class.simulation_id = new_simulation.id
        new_class.username = u.username
        socialClass.successor_id = new_class.id
        session.commit()

    # Clone all industry stocks in this simulation
    stocks = session.query(Industry_stock).filter(Industry_stock.simulation_id == template.id)
    report(1,new_simulation.id,f"Cloning Industry Stocks",session)
    for stock in stocks:
        report(2,new_simulation.id,
            f"Cloning industry stock [{stock.name}] with id {stock.id}, industry id {stock.industry(session).id} , and commodity  {stock.commodity(session).name} [id {stock.commodity(session).id}]",
            session,
        )
        old_industry = stock.industry(session)
        old_commodity = stock.commodity(session)
        successor_commodity_id = old_commodity.successor_id
        successor_id = old_industry.successor_id
        new_stock = clone_model(stock, session)
        session.add(new_stock)  # we commit twice, because we want to get the autogenerated id. There's probably a better way
        new_stock.simulation_id = new_simulation.id
        # This stock now has to be connected with its owner and commodity objects in the new simulation
        new_stock.industry_id = successor_id
        new_stock.username = u.username
        new_stock.commodity_id = successor_commodity_id
        new_stock.name = (
            new_stock.industry(session).name+ "."
            + new_stock.commodity(session).name+ "."
            + new_stock.usage_type+ "."
            + str(new_stock.simulation_id)
        )
        session.commit()

    # Clone all class stocks in this simulation
    stocks = session.query(Class_stock).filter(Class_stock.simulation_id == template.id)
    report(1,new_simulation.id,f"Cloning Class Stocks",session)

    for stock in stocks:
        report(2,new_simulation.id,
            f"Cloning class stock [{stock.name}] with id {stock.id}, class id {stock.social_class(session).id} , and commodity  {stock.commodity(session).name} [id {stock.commodity(session).id}]",
            session,
        )
        old_class = stock.social_class(session) #TODO deal with No result (ie error in the static file) - also throughout
        old_commodity = stock.commodity(session)
        successor_commodity_id = old_commodity.successor_id
        successor_id = old_class.successor_id
        new_stock = clone_model(stock, session)
        session.add(new_stock)  # we commit twice, because we want to get the autogenerated id. There's probably a better way
        new_stock.simulation_id = new_simulation.id
        # This stock now has to be connected with its owner and commodity objects in the new simulation
        new_stock.class_id = successor_id
        new_stock.username = u.username
        new_stock.commodity_id = successor_commodity_id
        new_stock.name = (
            new_stock.social_class(session).name+ "."
            + new_stock.commodity(session).name+ "."
            + new_stock.usage_type+ "."
            + str(new_stock.simulation_id)
        )
        session.commit()

    initialise_buyers_and_sellers(session, new_simulation.id)

    # TODO eliminate old revalue code
    revalue_commodities(session,new_simulation)
    revalue_stocks(session,new_simulation)
    calculate_initial_capitals(session,new_simulation)
    calculate_current_capitals(session,new_simulation)
    message=f"Cloned Template with id {id} into simulation with id {new_simulation.id}"
    report(1,new_simulation.id,message,session)
    session.commit()
    return {
        "message":message,
        "statusCode":status.HTTP_200_OK, 
        "simulation_id":new_simulation.id
        }

