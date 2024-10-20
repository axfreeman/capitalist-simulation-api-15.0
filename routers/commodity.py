from fastapi import Depends, APIRouter, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List
from authorization.auth import get_api_key
from database.database import get_session
from models.models import Commodity, Simulation, User
from models.schemas import CommodityBase, PostedPrice, PricePostMessage
from report.report import report
from simulation.price import calculate_melt
 
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

@router.post("/setprice", status_code=201,response_model=CommodityBase)
def setPrice(
    # form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_data:PostedPrice,
    session: Session = Depends(get_session),
    u:User=Security(get_api_key)
)->str:
    """Accept a form that sets the unit price of a commodity, externally to the simulation.
    Validates the commodity exists and belongs to the simulation in the post request
        
        form_data: commodityId, SimulationId, unitPrice.

        Return status: 201 if the post succeeds.
        Return status: 401 if access not authorised (supplied by fastapi)
        Return status: 404 if the commodity does not exist
        Return status: 422 if the input has the wrong format (supplied by fastapi)
        Return status: 422 if the commodity exists but not in the specified simulation
    """
    report(1,0,f"The user {u.username} wants to set the price of a commodity",session)

    # Contents of user_data are:
        # user_data.commodityId
        # user_data.simulationId
        # user_data.unitPrice

    commodity:Commodity=session.query(Commodity).where(
        Commodity.id == user_data.commodityId
        ).first()
    
    if commodity is None:
        raise HTTPException(status_code=404, detail=f'Commodity {user_data.commodityId} does not exist')

    if commodity.simulation_id!=user_data.simulationId:
        raise HTTPException(status_code=422, detail=f'Commodity {Commodity.id} does not belong to simulation {user_data.simulationID}')

    # TODO reset what needs to be reset.
    # TODO log an appropriate trace message (tricky: what Level to use?)

    calculate_melt(session,user_data.simulationId)
    return commodity

