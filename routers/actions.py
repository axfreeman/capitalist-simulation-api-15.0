from fastapi import Depends, APIRouter, Security, status
from sqlalchemy.orm import Session
from database.database import get_session
from models.schemas import ServerMessage
from simulation.consumption import consume
from authorization.auth import get_api_key
from report.report import report
from simulation.reload import clear_table, load_table
from simulation.demand import calculate_demand
from simulation.supply import calculate_supply, initialise_supply, industry_supply, class_supply
from simulation.trade import buy_and_sell, constrain_demand
from simulation.production import produce
from simulation.invest import invest
from models.models import (
    Class_stock,
    Industry_stock,
    Simulation,
    SocialClass,
    Industry,
    Commodity,
    Trace,
    User,
)
from simulation.utils import calculate_current_capitals, revalue_stocks, revalue_commodities

router = APIRouter(prefix="/action", tags=["Actions"])

@router.get("/demand",response_model=ServerMessage)
def demandHandler(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session),

)->str:
    """Handles calls to the 'Demand' action. Sets demand, then resets 
    the simulation state to the next in the circuit.

        u: User (supplied by Oath middleware)
        session: a valid session which stores the results
        returns: None if there is no current simulation
        returns: success message if there is a simulation
    """
    try:
        simulation:Simulation=u.current_simulation(session)
        calculate_demand(session,simulation)
        simulation.set_state("SUPPLY",session) # set the next state in the circuit, obliging the user to do this next.
    except Exception as e:
        return{"message":f"Error {e} processing demand for user {u.username}: no action taken","statusCode":status.HTTP_200_OK}

    return {"message":f"Demand initialised for user {u.username}","statusCode":status.HTTP_200_OK}

@router.get("/supply",response_model=ServerMessage)
def supplyHandler(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session),
)->str:
    """Handles calls to the 'Supply' action. Sets supply, then resets 
    simulation state to the next in the circuit.

        u: User (supplied by Oath middleware)
        session: a valid session which stores the results
        returns: None if there is no current simulation
        returns: success message if there is a simulation
    """
    try:
        simulation:Simulation=u.current_simulation(session)
        calculate_supply(session, simulation)        
        simulation.set_state("TRADE",session) # set the next state in the circuit, obliging the user to do this next.

    except Exception as e:
        return{"message":f"Error {e} processing supply for user {u.username}: no action taken","statusCode":status.HTTP_200_OK}
    return {"message":f"Supply initialised for user {u.username}","statusCode":status.HTTP_200_OK}

@router.get("/trade",response_model=ServerMessage)
def tradeHandler(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session),
)->str:
    """
    Handles calls to the 'Trade' action. Allocates supply, conducts 
    trade, and resets simulation state to the next in the circuit.

        If there is no current simulation, returns None
        Otherwise, return success message
    """
    simulation:Simulation=u.current_simulation(session)
    report(1, simulation.id, f"TRADE", session)
    constrain_demand(session, simulation)
    buy_and_sell(session, simulation)
    simulation.set_state("PRODUCE",session) # set the next state in the circuit, obliging the user to do this next.

    report(1,1,"TRADE IS COMPLETE",session)
    # TODO I don't think it's necessary to revalue, but check this.
    # This is because trade only involves a change of ownership.
    # revalue_stocks(session,simulation) 

    return {"message":f"Trade conducted for user {u.username}","statusCode":status.HTTP_200_OK}

@router.get("/produce",response_model=ServerMessage)
def produceHandler(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session),
)->str:
    """
    Handles calls to the 'Produce' action then resets simulation state
    to the next in the circuit.

        If there is no current simulation, returns None
        Otherwise, return success message
    """

    try:
        simulation:Simulation=u.current_simulation(session)
        produce(session, simulation)
        simulation.set_state("CONSUME",session) # set the next state in the circuit, obliging the user to do this next.
    except Exception as e:
        return{"message":f"Error {e} processing trade for user {u.username}: no action taken","statusCode":status.HTTP_200_OK}

    # Don't revalue yet, because consumption (social reproduction) has to
    # be complete before all the facts are in. 
    calculate_current_capitals(session,simulation)
    return {"message":f"Production conducted for user {u.username}","statusCode":status.HTTP_200_OK}

@router.get("/consume",response_model=ServerMessage)
def consumeHandler(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session),
)->str:
    """
    Handles calls to the 'Consume' action then resets simulation state
    to the next in the circuit.

    Instructs every social class to consume and reproduce anything it sells.

        If there is no current simulation, returns None
        Otherwise, return success message
    """

    try:
        simulation:Simulation=u.current_simulation(session)
        consume(session, simulation)
        simulation.set_state("INVEST",session) # set the next state in the circuit, obliging the user to do this next.

        # Now recalculate the price and value of every stock

        revalue_commodities(session,simulation)
        revalue_stocks(session, simulation)

        calculate_current_capitals(session,simulation)
    except Exception as e:
        return{"message":f"Error {e} processing social consumption for user {u.username}: no action taken","statusCode":status.HTTP_200_OK}
    return {"message":f"Social Consumption conducted for user {u.username}","statusCode":status.HTTP_200_OK}

@router.get("/invest",response_model=ServerMessage)
def investHandler(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session),
)->str:
    """Handles calls to the 'Invest' action then resets simulation state
    to restart the next circuit.

        Instructs every industry to assess whether it has a money surplus above
        what would be needed to produce at the same level as it has been doing.

        If so, attempt to raise the output_scale by the minimum of what this 
        money will pay for, and the growth rate.

        Note that if the means are not available to make this possible, in the 
        demand stage of the next circuit, output will be scaled down.

        This is only one of a number of possible algorithms.
    
        returns(str):
            If there is no current simulation, None
            Otherwise success message
    """
    try:
        simulation:Simulation=u.current_simulation(session)
        invest(simulation,session)
        simulation.set_state("DEMAND",session) # set the next state in the circuit, obliging the user to do this next.
    except Exception as e:
        return{"message":f"Error {e} processing investment for user {u.username}: no action taken","statusCode":status.HTTP_200_OK}
    return {"message":f"Investment conducted for user {u.username}","statusCode":status.HTTP_200_OK}

@router.get("/reset")
def get_json(session: Session = Depends(get_session)):
    """
    Reloads all tables in the simulation from json fixtures.

        Logs out all users and sets their current simulation to 0.  
        Should only be available to admin since it reinitialises everything.  
        If 'reload' is false in the call to reload_table, does not re-initialise
    """
    report(1,1,"RESETTING ENTIRE DATABASE",session)
    clear_table(session, Simulation, 1)
    clear_table(session, SocialClass, 1)
    clear_table(session, Commodity, 1)
    clear_table(session, Industry, 1)
    clear_table(session, Industry_stock, 1)
    clear_table(session, Class_stock, 1)
    clear_table(session, User, 1)
    clear_table(session, Trace, 1)

    for i in range(1,6):
        load_table(session, Simulation, f"static/{i}/simulations.json", True, 1)
        load_table(session, SocialClass, f"static/{i}/classes.json", True, 1)
        load_table(session, Commodity, f"static/{i}/commodities.json", True, 1)
        load_table(session, Industry, f"static/{i}/industries.json", True, 1)
        load_table(session, Class_stock, f"static/{i}/class_stocks.json", True, 1)
        load_table(session, Industry_stock, f"static/{i}/industry_stocks.json", True, 1)

    load_table(session, User,"static/users.json", True, 1)

    return "Database reloaded"


