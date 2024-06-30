from fastapi import Depends, APIRouter, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List
from ..authorization.auth import get_api_key
from ..database import get_session
from ..models import Commodity, Simulation, User
from ..schemas import CommodityBase
 
router = APIRouter(prefix="/commodity", tags=["Commodity"])

@router.get("/", response_model=List[CommodityBase])
def get_commodities(
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session),
):
    """Get all commodities in the simulation of the logged-in user.
       
        Return a list of all commodities in the simulation of the user 
        making this request.     
    
        Return empty list if the user doesn't have a simulation yet.
    """

    simulation_id:Simulation=u.current_simulation_id

    if simulation_id == 0:
        return []
    commodities = session.query(Commodity).where(Commodity.simulation_id == simulation_id)
    return commodities

@router.get("/{id}",response_model=CommodityBase)
def get_commodity(
    id: str, 
    u:User=Security(get_api_key),    
    session: Session = Depends(get_session)):

    """Get the commodity defined by id.
    Calls get_api_key to authorize access but does not use it to locate the user
    or the simulation, because id is unique to the whole app.

      Returns the commodity if it exists.

      Raise HttpException if it does not exist.
    """

    commodity = session.query(Commodity).filter(Commodity.id == int(id)).first()
    if commodity is None:
        raise HTTPException(status_code=404, detail=f'Commodity {id} does not exist')
    return commodity
