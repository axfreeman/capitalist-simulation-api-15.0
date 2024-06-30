from typing import List
from fastapi import HTTPException, Security, Depends, APIRouter, Security
from sqlalchemy.orm import Session

from app.authorization.auth import get_api_key
from ..database import get_session
from ..models import Simulation, Industry, User
from ..schemas import IndustryBase

router = APIRouter(prefix="/industry", tags=["Industry"])

@router.get("/", response_model=List[IndustryBase])
def get_Industries(
    u:User = Security(get_api_key),
    session: Session = Depends(get_session),
    ):
    
    """Get all industries in the simulation of the logged-in user
    Return empty list if the user doesn't have a simulation yet.
    """
    
    simulation_id:Simulation=u.current_simulation_id
    if simulation_id == 0:
        return []
    Industries = session.query(Industry).where(Industry.simulation_id == simulation_id)
    return Industries

@router.get("/{id}", response_model=IndustryBase)
def get_Industry(
    id: str, 
    u:User = Security(get_api_key),
    session: Session = Depends(get_session),
    ):

    """Get one industry defined by id.
    get_api_key authorizes access but does not use it to locate
    the user or the simulation, because id is unique to the whole app.

      Returns the industry if it exists.

      Raises 404 exception if it does not exist.
    """
    
    industry = session.query(Industry).filter(Industry.id == int(id)).first()
    if industry is None:
        raise HTTPException(status_code=404, detail=f'Industry {id} does not exist')
    return industry
