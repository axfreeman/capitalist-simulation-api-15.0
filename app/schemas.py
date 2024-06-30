import http
from pydantic import BaseModel

# Return message for a remote registration
# Returns with confirmation of the name and an apikey
class UserRegistrationMessage(BaseModel):
    username: str
    apikey:str

class ServerMessage(BaseModel):
    message:str
    statusCode:http.HTTPStatus

class CloneMessage(BaseModel):
    message:str
    statusCode:http.HTTPStatus
    simulation_id:int

class UserBase(BaseModel):
    username: str
    current_simulation_id: int
    is_locked:bool
    api_key:str

class UserCreate(BaseModel):
    username: str
        
class SimulationBase(BaseModel):
    id:int
    name: str
    time_stamp: int
    username: str
    state: str
    periods_per_year: float
    population_growth_rate: float
    investment_ratio: float
    currency_symbol: str
    quantity_symbol: str
    melt: float

class CommodityBase(BaseModel):
    id: int
    simulation_id: int
    name: str
    username: str
    origin: str
    usage: str
    size: float
    total_value: float
    total_price: float
    unit_value: float
    unit_price: float
    turnover_time: float
    demand: float
    supply: float
    allocation_ratio: float
    display_order: int
    image_name: str
    tooltip: str
    monetarily_effective_demand: float
    investment_proportion: float

class IndustryBase(BaseModel):
    id: int
    name: str
    simulation_id: int
    username: str
    output: str
    output_scale: float
    output_growth_rate: float
    initial_capital: float
    work_in_progress: float
    current_capital: float
    profit: float
    profit_rate: float

class TraceOut(BaseModel):
    id: int
    simulation_id: int
    time_stamp: int
    level :int
    message: str

class SocialClassBase(BaseModel):
    id: int
    simulation_id: int
    name: str
    username: str
    population: float
    participation_ratio: float
    consumption_ratio: float
    revenue: float
    assets: float

class Industry_stock_base(BaseModel):
    __tablename__="industry_stocks"

    id: int
    simulation_id:int
    industry_id: int
    commodity_id:int
    username:str
    name:str
    usage_type: str
    size: float
    value: float
    price: float
    requirement: float
    demand: float

class Class_stock_base(BaseModel):
    __tablename__="class_stocks"

    id: int
    simulation_id:int
    class_id: int
    commodity_id:int
    name:str
    username:str
    usage_type: str
    size: float
    value: float
    price: float
    demand: float

class BuyerBase(BaseModel):
    __tablename__ = "buyers"

    id: int
    simulation_id: int 
    owner_type: str
    purchase_stock_id: int
    money_stock_id: int
    commodity_id: int

class SellerBase(BaseModel):
    __tablename__ = "sellers"

    id: int
    simulation_id: int 
    owner_type: str
    sales_stock_id: int
    money_stock_id: int
    commodity_id: int

