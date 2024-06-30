import http
from fastapi import  HTTPException, Security, status, Depends, APIRouter,status
from sqlalchemy.orm import Session
from typing import List

from app.logging import report
from ..reporting.caplog import logger
from ..database import  get_session
from ..models import Simulation, User
from ..schemas import  ServerMessage, SimulationBase
from ..authorization.auth import get_api_key

"""Endpoints to retrieve data about Simulations.
At present these are all public.
This is because there is no privacy consideration.
Any user can see what any other is doing.
But each user can only *change* what that user is doing.
"""

router=APIRouter(
    prefix="/simulations",
    tags=['Simulation']
)

def delete_simulation(id:int,session:Session)->bool:    
    """Delete the simulation with this id and all dependent objects.  

        id: the id of the simulation to delete
        session: a valid sqlalchemy session.  
    
        If there is no such simulation, do nothing and return False
        If this simulation does exist, delete it and return True.
        Relies on cascading dependent objects.
    """

    report(1,1,f"Trying to delete simulation {id}",session)
    query = session.query(Simulation).where(Simulation.id==id)
    if (query is None):
        return False
    query.delete(synchronize_session=False)
    session.commit()
    return True


@router.get("/",response_model=List[SimulationBase])
def get_simulations(
    session: Session = Depends (get_session), 
    u:User=Security(get_api_key),    
    ):    
    """Get all simulations belonging to one user.

        Return all simulations belonging to the user 'u'
        If there are none, return an empty list.
    """        
    simulations = session.query(Simulation).where(Simulation.username == u.username)
    return simulations

@router.get("/by_id/{id}",response_model=SimulationBase)
def get_simulation(
    id:str,
    u:User=Security(get_api_key),    
    session: Session=Depends(get_session)):    
    
    """Get one simulation.
        
        id is the actual simulation number.
        
        Raise httpException if there is no such simulation
    """
    simulation=session.query(Simulation).filter(Simulation.id==int(id)).first()
    if simulation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='This simulation does not exist')
    return simulation

@router.get("/current",response_model=List[SimulationBase])
def get_current_user_simulation(
    session: Session = Depends (get_session), 
    u:User=Security(get_api_key),    
    ):

    """Get the current simulation of the api_key user
    
        Return the user's current simulation if there is one.

        Raise httpException otherwise
    """
    report(1,0,f"User {u.username} requested simulation {u.current_simulation_id}",session)
    simulations:Simulation=session.query(Simulation).where(Simulation.id==u.current_simulation_id)
    if simulations is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='This user has no simulations')
    return simulations


@router.get("/delete/{id}",response_model=ServerMessage)
def delete_one_simulation(
    id:str,
    session: Session=Depends(get_session),
    u:User=Security(get_api_key))->str:    
    """
    Delete the simulation with this id and all dependent objects.

        If there is no such simulation, do nothing.
        If this simulation does exist, delete and return confirmation.
        Relies on cascading of dependent objects
        Uses the separate 'delete_simulation' function which can be 
        used independently (eg to delete all simulations of a given user)
    """
    print(f"{u.username} wants to delete simulation {id}")
    result=delete_simulation(id, session)
    if (result==False):
        userMessage:str={"message":f"Simulation {id} does not exist","statusCode":status.HTTP_200_OK}
    userMessage:str={"message":f"Simulation {id} deleted","statusCode":status.HTTP_200_OK}
    return userMessage

@router.get("/current-delete/", response_model=ServerMessage)
def delete_user_simulation(
    u: User = Security(get_api_key),
    session:Session =Depends(get_session)
    ):
    """
    Delete the current simulation of the user who sent this request.  

        u: name of the current user
        session: a valid sqlAlchemy session

    """
    report(1,1,f"Deleting Simulations for user {u.username}",session)

    query:Simulation=session.query(Simulation).where(Simulation.id==u.current_simulation_id)

    # TODO some error trapping
    for simulation in query:
        delete_simulation(query.id)

    return {"message":f"Deleted current simulation of user {u.username}","statusCode":status.HTTP_200_OK}
    
@router.get("/user-delete/", response_model=ServerMessage)
def delete_user_simulation(
    u: User = Security(get_api_key),
    session:Session =Depends(get_session)
    ):
    """Delete all the simulations of the user who sent this request.  

        u: name of the current user
        session: a valid sqlAlchemy session

    """
    report(1,1,f"Deleting Simulations for user {u.username}",session)
    query:Simulation=session.query(Simulation).where(Simulation.username == u.username)
    for simulation in query:
        delete_simulation(simulation.id)
    return {"message":f"Deleted all simulations of user {u.username}","statusCode":status.HTTP_200_OK}
        