"""This module contains models, and their methods, for the objects of
the system, except for the User model which is in authorization.py.
"""

import typing
from fastapi import Depends, HTTPException
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship, Session
from .database import Base


Industry_stock = typing.NewType("Industry_stock", None)
Class_stock = typing.NewType("Class_stock", None)

class Simulation(Base):
    """
    Simulation is the primary model of the project. Each entry in the
    Simulation database defines the state of the simulation at a
    single point in (virtual) time defined by time_stamp.

    A User can run a number of simulations concurrently and switch
    between them. Using the user-dashboard, users can also create,
    delete and switch between Simulations, but must choose from
    one of a number of predefined Templates. Future versions of the
    project will permit users to define and edit Templates but this
    requires a lot of validation logic.

    Every object of the simulation (Commodity, Industry, Stock, etc)
    belongs to one simulation and has a foreign key that links to it
    """

    __tablename__ = "simulations"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    time_stamp = Column(Integer)
    username = Column(String, nullable=True)  # Foreign key to the User model
    state = Column(String)  # what stage the simulation has reached
    periods_per_year = Column(Float)
    population_growth_rate = Column(Float)
    investment_ratio = Column(Float)
    labour_supply_response = Column(String)
    price_response_type = Column(String)
    melt_response_type = Column(String)
    currency_symbol = Column(String)
    quantity_symbol = Column(String)
    melt = Column(Float)

    def set_state(self,state:str,session:Session):
        """Helper function sets the state of a simulation. Does not test 
        for error, so the caller should do that.
         
           state is the desired state ("DEMAND", "SUPPLY", ...)
         """

        session.add(self)
        self.state = state
        session.commit()

class User(Base):
    """
    The user object contains everything needed to describe a user.
    
    Simulations are uniquely mapped to users. 
        
    Every Simulation contains a foreign key pointing to the User.username field.
    Every Object in the simulation (Commodity, Industry, etc) contains a foreign 
    key pointing to a Simulation object.
    """
    __tablename__ = "users"

    username = Column(String, nullable=False, primary_key=True)
    password =  Column(String)
    current_simulation_id = Column(Integer, nullable=False, default=0)
    api_key = Column (String)
    is_locked = Column(Boolean)
    role=Column(String)

    def current_simulation(self,session:Session)->Simulation:
        """Return this user's current simulation.
            Raise 404 exception if it does not exist
        """
        simulation= session.query(Simulation).where (Simulation.id==self.current_simulation_id).first()
        if simulation is None:
            raise HTTPException(status_code=404,detail=f"User {self.username} has no current simulation")
        return simulation

class Commodity(Base):
    """
    The commodity object refers to a type of tradeable good, for example
    Means of Production, Means of Consumption, Labour Power. In Marx's
    terms it is a 'use value'. Each commodity has a one-many relation
    to the stocks in the simulation, so if an industry owns a stock of
    Means of Production, the stock object will have a foreign key to
    the Means of Production Commodity.

    The simulation keeps track of aggregate magnitudes associated with
    each Commodity, such as its total price, total value, total quantity
    and so on.

    It also keeps track of the total supply of, and the total demand for
    that Commodity.
    """

    __tablename__ = "commodities"
    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    username = Column(String, nullable=True)
    name = Column(String)
    origin = Column(String)
    usage = Column(String)
    size = Column(Float)
    total_value = Column(Float)
    total_price = Column(Float)
    unit_value = Column(Float)
    unit_price = Column(Float)
    turnover_time = Column(Float)
    demand = Column(Float)
    supply = Column(Float)
    allocation_ratio = Column(Float)
    display_order = Column(Integer)
    image_name = Column(String)
    tooltip = Column(String)
    monetarily_effective_demand = Column(Float)
    investment_proportion = Column(Float)
    successor_id = Column(Integer, nullable=True)  # Helper column to use when cloning

    simulation_name = relationship("Simulation")

class Industry(Base):
    """Each Industry is a basic productive unit.

    It owns:
     several Productive Stocks;
     a SalesStock;
     a MoneyStock;

    These Stocks have a foreign key uniquely stating which Industry they
    belong to.

    During the 'produce' action, Industries are asked to produce output
    on a scale given by output_scale.

    To this end, they use up the Productive Stocks.

    The amount of each such Stock which is consumed in this way depends on
    Industry.output_scale, Stock.requirement, and Commodity.turnover_time
    where Commodity is referenced by Stock.commodity_id.

    During the 'trade' action, Industries buy the Stocks they need, and
    sell their SalesStock. They may or may not manage to get all the
    productive Stocks they need. If they fail, output_scale is reduced.

    To facilitate the calculation, the app calculates the money cost of
    buying the productive Stocks needed for one unit of output in one
    period.

    This is provided by the method 'self.unit_cost'.
    """

    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    username = Column(String, nullable=True)
    name = Column(String)
    output = Column(String)
    output_scale = Column(Float)
    output_growth_rate = Column(Float)
    initial_capital = Column(Float)
    work_in_progress = Column(Float)
    current_capital = Column(Float)
    profit = Column(Float)
    profit_rate = Column(Float)
    successor_id = Column(Integer, nullable=True)  # Helper column to use when cloning

    def unit_cost(self, db: Session)->float:
        """Calculate the cost of producing a single unit of output."""
        cost = 0
        for stock in (
            db.query(Industry_stock)
            .where(Industry_stock.industry_id == self.id)
            .where(Industry_stock.usage_type == "Production")
        ):
            print(
                f"Stock called {stock.name} is adding {stock.unit_cost(db)} to its industry's unit cost"
            )
            cost += stock.unit_cost(db)
        return cost

    def simulation(self, db: Session)->Simulation:
        """
        Helper method yields the (unique) Simulation this industry belongs to.
        """
        return db.get_one(Simulation, self.simulation_id)

    def sales_stock(self, db: Session)->Industry_stock:
        """Helper method yields the Sales Stock of this industry."""
        result = get_industry_sales_stock(self, db)  # workaround because pydantic won't easily accept this query in a built-in function
        if result == None:
            raise Exception(
                f"INDUSTRY {self.name} with id {self.id} and simulation id {self.simulation_id} HAS NO SALES STOCK"
            )
        return result

    def money_stock(self, session)->Industry_stock:
        """Helper method yields the Money Stock of this industry."""
        return get_industry_money_stock(self, session)  # workaround because pydantic won't easily accept this query in a built-in function

class SocialClass(Base):
    __tablename__ = "social_classes"

    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)
    username = Column(String, nullable=True)
    population = Column(Float)
    participation_ratio = Column(Float)
    consumption_ratio = Column(Float)
    revenue = Column(Float)
    assets = Column(Float)
    successor_id = Column(Integer, nullable=True)  # Helper column to use when cloning

    def simulation(self, session)->Simulation:
        return session.get_one(Simulation, self.simulation_id)

    def sales_stock(self, session):
        """Helper method yields the Sales Class_stock of this class."""
        return get_class_sales_stock(self, session)

    def money_stock(self, session):
        """Helper method yields the Money Class_stock of this class."""
        return get_class_money_stock(self, session)

class Industry_stock(Base):
    """Stocks are produced, consumed, and traded in a market economy.

    There are two types of stock:
        Those that belong to Industries
        Those that belong to Classes

    An Industry_stock knows:
        which Simulation it belongs to;
        which Commodity it consists of (in Marx's terms, its Use Value);
        quantitative information notably its size, value and price;
        which Industry it belongs to.

    It has a usage_type which may be Consumption, Production or Money.
    Note that an industry can own any of these.
    This is because Consumption goods are produced by industries.

    Usage type is a substitute for subclassing.

    The field 'requirement' says how much of it will be used for its
    Industry to produce a unit of output.

    The helper method Stock.unit_cost says how much it will cost to do this.
    """

    __tablename__ = "industry_stocks"
    id = Column(Integer, primary_key=True, nullable=False)
    industry_id = Column(Integer, ForeignKey("industries.id"), nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    commodity_id = Column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)  # Owner.Name+Commodity.Name+usage_type
    username = Column(String, nullable=True)
    usage_type = Column(String)  # 'Consumption', 'Production' or 'Money'
    size = Column(Float)
    value = Column(Float)
    price = Column(Float)
    requirement = Column(Float)
    demand = Column(Float)

    def annual_flow_rate(self, db: Session) -> float:
        """The annual rate at which this Stock is consumed.
        Returns zero for Money and Sales Stocks.
        """
        if self.usage_type == "Production":
            industry = db.query(Industry).where(Industry.id == self.industry_id).first()
            return round(industry.output_scale * self.requirement,4)
        else:
            return 0.0

    def flow_per_period(self, db: Session) -> float:
        return round(self.annual_flow_rate(db) / self.simulation(db).periods_per_year,4)

    def standard_stock(self, db: Session) -> float:
        """The size of the normal stock which an industry must maintain in order to conduct
        production.

        Returns zero for non-productive Stocks.
        """
        if self.usage_type == "Production":
            commodity = db.query(Commodity).where(Commodity.id == self.commodity_id).first()
            return self.annual_flow_rate(db) * commodity.turnover_time
        else:
            return 0.0

    def industry(self, db: Session)->Industry:
        """Returns the  Industry to which this stock belongs."""
        return db.get_one(Industry, self.industry_id)

    def commodity(self, db: Session)->Commodity:
        return db.get_one(Commodity, self.commodity_id)

    def simulation(self, session)->Simulation:
        return session.get_one(Simulation, self.simulation_id)

    def unit_cost(self, db: Session)->float:
        """Money price of using this Stock to make one unit of output
        in a period.

        Returns zero if Stock is not productive, which is harmless -
        nevertheless, caller should invoke this method only on productive
        Stocks.
        """
        return self.requirement * self.commodity(db).unit_price

    def owner(self, db:Session)->Industry: 
        """Really just for diagnostic purposes """
        return db.get_one(Industry, self.industry_id)
    
    def change_size(self,amount:float,db:Session)->bool:
        """Change the size of this Industry_stock by 'amount'.
        
        Change the value and price using the unit_value and unit_price 
        of this Industry_stock's Commodity.
        
        Return false if the result is negative, true otherwise.

        ONLY for use in Trade.

        Do NOT use this in production or consumption, which can change
        unit values and prices.
        """
        self.size += amount
        self.price=self.size*self.commodity(db).unit_value
        self.value=self.size*self.commodity(db).unit_price

class Class_stock(Base):
    """Stocks are produced, consumed, and traded in a
    market economy.

    There are two types of stock:
        Those that belong to Industries
        Those that belong to Classes

    A Class_stock knows:
        which Simulation it belongs to;
        which Commodity it consists of (in Marx's terms, its Use Value);
        quantitative information notably its size, value and price;
        which Social Class it belongs to.

    It has a usage_type which may be Consumption, Production or Money.
    Note that classes can own any type of stock.
    This is because Labour Power is a stock of type Production.

    Usage_type is a substitute for subclassing, since these are all types of Stock.
    """

    __tablename__ = "class_stocks"
    id = Column(Integer, primary_key=True, nullable=False)
    class_id = Column(Integer, ForeignKey("social_classes.id"), nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    commodity_id = Column(
        Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)  # Owner.Name+Commodity.Name+usage_type
    username = Column(String, nullable=True)
    usage_type = Column(String)  # 'Consumption', Production' or 'Money'
    size = Column(Float)
    value = Column(Float)
    price = Column(Float)
    demand = Column(Float)

    def social_class(self, db: Session)->SocialClass:
        """Returns the Class which owns this Class_stock."""
        return db.get_one(SocialClass, self.class_id)

    def commodity(self, db: Session)->Commodity:
        """Returns the Commodity that this Class_stock consists of."""
        return db.get_one(Commodity, self.commodity_id)

    def simulation(self, session)->Simulation:
        """Return the Simulation that this Class_stock is part of"""
        return session.get_one(Simulation, self.simulation_id)
    
    def annual_flow_rate(self, db: Session) -> float:
        """The annual rate at which this Class_stock is consumed.
        Returns zero for Money and Sales Stocks.
        """
        if self.usage_type == "Consumption":
            social_class:SocialClass = db.query(SocialClass).where(SocialClass.id == self.class_id).first()
            return social_class.population * social_class.consumption_ratio
        else:
            return 0.0

    def flow_per_period(self, session: Session) -> float:
        print(f"annual flow rate of {self.name} is {self.annual_flow_rate(session)} and periods per year is {self.simulation(session).periods_per_year}")
        return self.annual_flow_rate(session) / self.simulation(session).periods_per_year

    def standard_stock(self, session: Session) -> float:
        """The size of the normal stock which a class must maintain in order to 
        exist at its current population level.

        Returns zero for Class_stocks other than Consumption stocks

        TODO money stock requires a non-zero standard, but it is not so 
        easy to calculate. Leave this for now. Too much money is not a 
        problem at present since we do not have any monetary algorithms,
        whilst too little money has results which we wish to investigate.
        """
        if self.usage_type == "Consumption":
            return self.annual_flow_rate(session) * self.commodity().turnover_time
        else:
            return 0.0

    def owner(self, session)->SocialClass: 
        """Really just for diagnostic purposes """
        return session.get_one(SocialClass, self.class_id)

    def change_size(self,amount:float,db:Session)->bool:
        """Change the size of this Class_stock by 'amount'.
        
        Change the value and price using the unit_value and unit_price 
        of this Industry_stock's Commodity.
        
        Return false if the result is negative, true otherwise.

        ONLY for use in Trade.

        Do NOT use this in production or consumption, which can change
        unit values and prices.
        """
        self.size += amount
        self.price=self.size*self.commodity(db).unit_value
        self.value=self.size*self.commodity(db).unit_price

class Trace(Base):
    """
    Trace reports the progress of the simulation in a format meaningful
    for the user. It works in combination with logging.report(). A call
    to report() creates a single trace entry in the database and prints
    it on the console
    """

    __tablename__ = "trace"
    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(Integer)
    time_stamp = Column(Integer)
    username = Column(String, nullable=True)
    level = Column(Integer)
    message = Column(String)

class Buyer(Base):
    """The Buyer class is initialized when a simulation is created,
    that is, when a user clones a template.

    It contains a list of the id fields of all objects relevant to purchasing:
        The type of the owner (the owner itself is not relevant);
        The simulation;
        The commodity that is being traded;
        The stock that will receive goods through trade;
        The money stock that will pay for the goods.

    """
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, nullable=False)
    owner_type = Column(String)  # `Industry` or `Class`
    simulation_id = Column(Integer)
    purchase_stock_id = Column(Integer)
    money_stock_id = Column(Integer)
    commodity_id = Column(Integer)

    def simulation(self, session)->Simulation:
        """Returns the simulation to which this buyer belongs"""
        return session.get_one(Simulation, self.simulation_id)

    def purchase_stock(self, session)->Industry_stock|Class_stock:
        """The stock that must receive the goods.
        This may be either an Industry_stock OR a Class_stock, as indicated by the
        type annotation of the method result.
        Trade assumes that both classes implement methods which allow them to receive goods.
        """
        if self.owner_type=="Industry":
            return session.get_one(Industry_stock, self.purchase_stock_id)
        else:
            return session.get_one(Class_stock, self.purchase_stock_id)

    def money_stock(self, session)->Industry_stock|Class_stock:
        """The stock that pays for the goods.
        This may be either an Industry_stock OR a Class_stock, as indicated by the
        type annotation of the method result.
        Trade assumes that both classes implement methods which allow them to pay for goods.
        """
        if self.owner_type=="Industry":
            return session.get_one(Industry_stock, self.money_stock_id)
        else:
            return session.get_one(Class_stock, self.money_stock_id)

    def commodity(self, session)->Commodity:
        """Returns the Commodity which this buyer wants to get for this stock."""
        return session.get_one(Commodity, self.commodity_id)

    def owner_name(self, session):  # Really just for diagnostic convenience
        if self.owner_type == "Industry":
            return session.get_one(Industry, self.purchase_stock(session).industry_id).name
        else:
            return session.get_one(SocialClass, self.purchase_stock(session).class_id).name

class Seller(Base):
    """The Seller class is initialized when a simulation is created,
    that is, when a user clones a template.

    It contains a list of the id fields of all objects relevant to purchasing:
        The type of the owner (the owner itself is not relevant);
        The simulation;
        The commodity that is being traded;
        The stock that will sell goods through trade;
        The money stock that will receive payment.
    """
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, nullable=False)
    owner_type = Column(String)  # `Industry` or `Class`
    simulation_id = Column(Integer)
    sales_stock_id = Column(Integer)
    money_stock_id = Column(Integer)
    commodity_id = Column(Integer)

    def simulation(self, session)->Simulation:
        """Returns the simulation to which this buyer belongs"""
        return session.get_one(Simulation, self.simulation_id)

    def sales_stock(self, session)->Industry_stock|Class_stock:
        """The stock that must receive the goods.
        This may be either an Industry_stock OR a Class_stock, as indicated by the
        type annotation of the method result.
        Trade assumes that both classes implement methods which allow them to receive goods.
        """
        if self.owner_type=="Industry":
            return session.get_one(Industry_stock, self.sales_stock_id)
        else:
            return session.get_one(Class_stock, self.sales_stock_id)

    def money_stock(self, session):
        """The stock that pays for the goods.
        This may be either an Industry_stock OR a Class_stock, as indicated by the
        type annotation of the method result.
        Trade assumes that both classes implement methods which allow them to pay for goods.
        """
        if self.owner_type=="Industry":
            return session.get_one(Industry_stock, self.money_stock_id)
        else:
            return session.get_one(Class_stock, self.money_stock_id)

    def commodity(self, session):
        """Returns the Commodity which this seller is offering."""
        return session.get_one(Commodity, self.commodity_id)

    def owner_name(self, session):  # Really just for diagnostic convenience
        if self.owner_type == "Industry":
            return session.get_one(Industry, self.sales_stock(session).industry_id).name
        else:
            return session.get_one(SocialClass, self.sales_stock(session).class_id).name

    def owner_id(self, session):  # also just for diagnostic purposes
        if self.owner_type == "Industry":
            return session.get_one(Industry, self.sales_stock(session).industry_id).id
        else:
            return session.get_one(SocialClass, self.sales_stock(session).class_id).id

"""Helper functions which serve as workarounds for dealing with pydantic limitations."""

def get_industry_sales_stock(industry, session)->Industry_stock:
    """Workaround because pydantic won't accept this query in a built-in function."""
    return (
        session.query(Industry_stock)
        .filter(
            Industry_stock.industry_id == industry.id,
            Industry_stock.usage_type == "Sales",
            Industry_stock.simulation_id == industry.simulation_id,
        )
        .first()
    )

def get_industry_money_stock(industry, session)->Industry_stock:
    """workaround because pydantic won't accept this query in a built-in function."""
    return (
        session.query(Industry_stock)
        .filter(
            Industry_stock.industry_id == industry.id,
            Industry_stock.usage_type == "Money",
            Industry_stock.simulation_id == industry.simulation_id,
        )
        .first()
    )

def get_class_sales_stock(social_class, session)->Class_stock:
    """Workaround because pydantic won't accept this query in a built-in function."""
    return (
        session.query(Class_stock)
        .filter(
            Class_stock.class_id == social_class.id,
            Class_stock.usage_type == "Sales",
            Class_stock.simulation_id == social_class.simulation_id,
        )
        .first()
    )

def get_class_money_stock(social_class, session)->Class_stock:
    """Workaround because pydantic won't accept this query in a built-in function."""    
    return (
        session.query(Class_stock)
        .filter(
            Class_stock.class_id == social_class.id,
            Class_stock.usage_type == "Money",
            Class_stock.simulation_id == social_class.simulation_id,
        )
        .first()
    )
