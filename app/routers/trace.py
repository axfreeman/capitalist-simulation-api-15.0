from fastapi import  Depends, APIRouter, Security
from sqlalchemy.orm import Session
from typing import List
from ..authorization.auth import get_api_key
from ..database import  get_session
from ..models import Simulation,Trace,User
from ..schemas import TraceOut

router=APIRouter(
    prefix="/trace",
    tags=['Trace']
)

@router.get("/",response_model=List[TraceOut])
def get_trace(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session)
    ):
    """Get the trace records in the current simulation of the user.

        Return empty list if the user doesn't have a simulation yet.
    """
    simulation_id:Simulation=u.current_simulation_id
    if (simulation_id==0):
        return []
    trace=session.query(Trace).where(Trace.simulation_id==simulation_id)
    return trace
