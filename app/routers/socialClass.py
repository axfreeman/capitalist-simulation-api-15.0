"""Endpoints for the SocialClass object.
"""

from typing import List
from fastapi import Depends, APIRouter, HTTPException, Security
from sqlalchemy.orm import Session
from ..authorization.auth import get_api_key
from ..database import  get_session
from ..models import SocialClass,Simulation, User
from ..schemas import SocialClassBase

router=APIRouter(
    prefix="/classes",
    tags=['Class']
)

@router.get("/",response_model=List[SocialClassBase])
def get_socialClasses(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session)
    ):

    """Get all social classes in the current user simulation

    Return empty list if the user doesn't have a simulation yet.
    """

    simulation_id:Simulation=u.current_simulation_id
    if (simulation_id==0):
        return []
    socialClasses=session.query(SocialClass).where(SocialClass.simulation_id==simulation_id)
    return socialClasses

@router.get("/{id}")
def get_socialClass(
    id:str,
    u:User=Security(get_api_key),    
    session:Session = Depends(get_session)
    ):

    """Get one SocialClass defined by id.

    Calls get_api_key to authorize access but does not use it to locate the user
    or the simulation, because id is unique to the whole app.

      Returns the SocialClass if it exists.

      Raises 404 exception if it does not.
    """
    socialClass=session.query(SocialClass).filter(SocialClass.id==int(id)).first()
    if socialClass is None:
        raise HTTPException(status_code=404, detail=f'Social Class {id} does not exist')

    return socialClass

