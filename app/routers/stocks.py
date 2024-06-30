from fastapi import Depends, APIRouter, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List
from ..authorization.auth import get_api_key
from ..database import get_session
from ..models import Class_stock, Industry_stock, Simulation, User
from ..schemas import Class_stock_base, Industry_stock_base

router = APIRouter(prefix="/stocks", tags=["Stocks"])

@router.get("/industry", response_model=List[Industry_stock_base])
def find_industry_stocks(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session)
  ):
    """Get all industry stocks in one simulation.
    Return empty list if simulation is None."""

    simulation_id:int=u.current_simulation_id

    if simulation_id ==0:
        return []
    return session.query(Industry_stock).filter(Industry_stock.simulation_id == simulation_id)

@router.get("/industry/{id}")
def get_stock(
    id: str, 
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session),
    ):

    """Get one industry stock with the given id.
    Calls get_api_key to authorize access but does not use it to locate
    the user or the simulation, because id is unique to the whole app.

      Returns the industry stock if it exists.

      Raises 404 Exception if it does not exist.
    """
    
    stock:Industry_stock=session.query(Industry_stock).filter(Industry_stock.id == int(id)).first()
    if stock is None:
        raise HTTPException(status_code=404, detail=f'Industry Stock {id} does not exist')
    return stock

@router.get("/class", response_model=List[Class_stock_base])
def find_class_stocks(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session)
    ):

    """Get all class stocks in one simulation.
    Returns empty list if simulation is None.
    """
    
    simulation_id:Simulation=u.current_simulation_id

    if simulation_id == 0:
        return []
    return session.query(Class_stock).filter(Class_stock.simulation_id == simulation_id)

@router.get("/class/{id}")
def get_stock(id: str, session: Session = Depends(get_session)):

    """Get one class stock with the given id.
    Calls get_api_key to authorize access but does not use it to locate
    the user or the simulation, because id is unique to the whole app.

      Returns the class stock if it exists.

      Raises 404 exception if it does not exist.
    """
    stock= session.query(Class_stock).filter(Class_stock.id == int(id)).first()
    if stock is None:
        raise HTTPException(status_code=404, detail=f'Industry Stock {id} does not exist')
    return stock

