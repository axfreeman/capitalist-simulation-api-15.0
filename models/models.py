"""This module contains models, and their methods, for the objects of
the system, except for the User model which is in authorization.py and the Trace
model which is in report.report.py
"""

import typing
from fastapi import HTTPException
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship, Session
from database.database import Base
from report.report import report


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
    setPriceMode= Column(String) # "Locked", "User", "Equalise","Dsynamic": Whether prices are fixed, set by the user, equlised, or dynamically generated
    total_value= Column(Float)
    total_price= Column (Float)
    melt = Column(Float)
    currency_symbol = Column(String)
    quantity_symbol = Column(String)
    investment_algorithm = Column(String)

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

    def revalue_stocks(self,session:Session,simulation:Simulation):
        """
        Reset the value of every stock of this commodity from the unit value of that commodity. 
        Commit the changes
        """
        report(1,simulation.id,f"Resetting the value of all stocks of the commodity {self.name}",session)
        session.add(self)
        
        # Reset the values of all industry stocks
        istocks=session.query(Industry_stock).where(Industry_stock.commodity_id==self.id)
        for si in istocks:
            report(2,simulation.id,f"Reset value (currently {si.value}) with size {si.size} of industrial stock {si.name}",session)
            session.add(si)
            si.value=si.size*self.unit_value
            report(2,simulation.id,f"Its value is now {si.value}",session)

        # Reset the values of all class stocks
        cstocks=session.query(Class_stock).where(Class_stock.commodity_id==self.id)
        for sc in cstocks:
            report(2,simulation.id,f"Reset value (currently {si.value}) with size {sc.size} of class stock {sc.name}",session)
            session.add(sc)
            sc.value=si.size*self.unit_value
            report(2,simulation.id,f"Its value is now {sc.value}",session)
        session.commit()

    def reprice_stocks(self,session:Session,simulation:Simulation):
        """
        Reset the price of every stock of this commodity from the unit price of that commodity. 
        Commit the changes.
        """
        report(1,simulation.id,f"Resetting the price of all stocks of the commodity {self.name}",session)
        session.add(self)
        # Calculate the prices of all industry stocks
        istocks=session.query(Industry_stock).where(Industry_stock.commodity_id==id)
        for si in istocks:
            report(2,simulation.id,f"Reset price (currently {si.price}) with size {si.size} of industrial stock {si.name}",session)
            session.add(si)
            si.price=si.size*self.unit_price
            report(2,simulation.id,f"Its price is now {si.value}",session)

        # Calculate the contribution of all class stocks
        cstocks=session.query(Class_stock).where(Class_stock.commodity_id==id)
        for sc in cstocks:
            report(2,simulation.id,f"Reset price (currently {si.value}) with size {sc.size} of class stock {sc.name}",session)
            session.add(sc)
            sc.price=si.size*self.unit_price
            report(2,simulation.id,f"Its price is now {sc.value}",session)
        session.commit()

    def resize(self,session:Session,simulation:Simulation):
        """
        Reset the total size of this commodity.
        Should be called before reset_value_from_stocks() or reset_price_from_stocks()
        """
        session.add(self)
        report(1,simulation.id,f"Recalculating the size of the commodity {self.name} which is currently {self.size}",session)
        self.size=0

        # Add the sizes of all industry stocks of this commodity
        istocks=session.query(Industry_stock).where(Industry_stock.commodity_id==id)
        for si in istocks:
            self.size+=si.size
            report(2,simulation.id,f"Adding {si.size} to total {self.size}, from industrial stock {si.name}",session)

        # Add the sizes of all class stocks of this commodity
        cstocks=session.query(Class_stock).where(Class_stock.commodity_id==id)
        for sc in cstocks:
            self.size+=si.size
            report(2,simulation.id,f"Adding {sc.size} to make new total {self.size}, from class stock {sc.name}",session)
        session.commit()

    def revalue(self, session:Session,simulation:Simulation):
        """
        Reset the total value and unit value of this commodity.
        Expects that resize() has been called or that in some way, the total size of the commodity is correct
        """
        report(1,simulation.id,f"Recalculating the value of the commodity {self.name} which is currently {self.total_value}",session)
        total_value:float=0

        # Add the values of all industry stocks of this commodity
        istocks=session.query(Industry_stock).where(Industry_stock.commodity_id==self.id)
        
        for si in istocks:
            total_value+=si.value
            report(2,simulation.id,f"Adding {si.value} to total value {total_value}, from industrial stock {si.name}",session)

        # Add the values of all class stocks of this commodity
        cstocks=session.query(Class_stock).where(Class_stock.commodity_id==self.id)
        for sc in cstocks:
            total_value+=sc.value
            report(2,simulation.id,f"Adding {sc.value} to total value {total_value}, from class stock {sc.name}",session)

        # reset total value if relevant
        if (total_value)!=self.total_value:
            report(2,simulation.id,f"Total value has changed from {self.total_value} to {total_value}",session)
            self.total_value=total_value

        if self.size==0:
            report(2,simulation.id,f"WARNING: SIZE OF {self.name} IS ZERO",session)
        else:
            new_unit_value=total_value/self.size
            if self.unit_value!=new_unit_value:
                report(2,simulation.id,f"Unit value has changed from {self.unit_value} to {new_unit_value}",session)
                self.unit_value=new_unit_value
        session.commit()

    def reprice(self,session:Session,simulation:Simulation):
        """
        Reset the total price and unit price of this commodity.
        Should be called after reset_size_from_stocks()
        """
        session.add(self)
        report(1,simulation.id,f"Recalculating the price of the commodity {self.name} which is currently {self.total_price}",session)
        total_price=0

        # Add the prices of all industry stocks of this commodity
        istocks=session.query(Industry_stock).where(Industry_stock.commodity_id==id)
        for si in istocks:
            total_price+=si.price
            report(2,simulation.id,f"Adding {si.price} to total {total_price}, from industrial stock {si.name}",session)

        # Add the sizes of all class stocks of this commodity
        cstocks=session.query(Class_stock).where(Class_stock.commodity_id==id)
        for sc in cstocks:
            self.total_price+=si.price
            report(2,simulation.id,f"Adding {sc.value} to make new total {total_price}, from class stock {sc.name}",session)

        if (total_price)!=self.total_value:
            report(2,simulation.id,f"Total value has changed from {self.total_value} to {total_price}",session)
            self.total_value=total_price

        new_unit_price=total_price/self.size
        if self.unit_price!=new_unit_price:
            report(2,simulation.id,f"Unit Price will be changed from {self.unit_price} to {new_unit_price}",session)
            self.unit_price=new_unit_price

        session.commit()

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

    def unit_cost(self, session: Session)->float:
        """Calculate the cost of producing a single unit of output."""
        cost = 0
        for stock in (
            session.query(Industry_stock)
            .where(Industry_stock.industry_id == self.id)
            .where(Industry_stock.usage_type == "Production")
        ):
            # TODO resolve circular import problem with 'report'
            # report(3,self.simulation_id(),
            #     f"Stock called [{stock.name}] is adding {stock.unit_cost(session)} to its industry's unit cost",session
            # )
            cost += stock.unit_cost(session)
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

    def money_stock(self, db)->Industry_stock:
        """Helper method yields the Money Stock of this industry."""
        return get_industry_money_stock(self, db)  # workaround because pydantic won't easily accept this query in a built-in function

    def get_capitalist_help(self, shortfall, session:Session)->float:
        """ ask for help if funds are insufficient to maintain production.
        There are three options:
        1) Create money and give it to me
        2) Give me money out of state funds
        3) Buy my excess stock
        """
        print("HELP IS ON THE WAY!!!!! Money requested was ", shortfall)
        # (Initial test) just give money, to see if it works
        money_stock:Industry_stock=self.money_stock(session)
        print("Money stock is", money_stock.name, money_stock.size)
        session.add(money_stock)
        money_stock.change_size(shortfall,session)
        print ("Money was donated")
        session.commit()
        return shortfall

    def output_commodity(self, db)->Commodity:
        sales_stock:Industry_stock=self.sales_stock(db)
        sales_commodity:Commodity =sales_stock.commodity(db)
        return sales_commodity
    
    def mp_stock(self,session:Session)->Session.query:
        """
        Returns all stocks of this industry which form inputs to production, including Labour Power
        This will fail if there is more than one means of input
        """
        stocks=session.query(Industry_stock).where(
            Industry_stock.industry_id==self.id,
            Industry_stock.usage_type=="Production"
        )
        for stock in stocks:
            input_commodity:Commodity=stock.commodity(session)
            if input_commodity.origin=="INDUSTRIAL":
                return stock
        return None

    def labour_power_stock(self,session:Session)->Session.query:
        stocks=session.query(Industry_stock).where(
            Industry_stock.industry_id==self.id,
            Industry_stock.usage_type=="Productive"
        )
        for stock in stocks:
            input_commodity:Commodity=stock.commodity(session).first()
            if input_commodity.origin=="SOCIAL":
                return stock
        return None

class SocialClass(Base):
    __tablename__ = "social_classes"

    id = Column(Integer, primary_key=True, nullable=False)
    simulation_id = Column(
        Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String)
    output= Column(String)
    username = Column(String, nullable=True)
    population = Column(Float)
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
    
    def consumption_stocks(self,session):
        return get_class_consumption_stocks(self,session)

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
    origin = Column(String) # 'INDUSTRIAL','SOCIAL', 'MONEY' 
    size = Column(Float)
    value = Column(Float)
    price = Column(Float)
    requirement = Column(Float)
    demand = Column(Float)

    def annual_flow_rate(self, session: Session) -> float:
        """The annual rate at which this Stock is consumed.
        Returns zero for Money and Sales Stocks.
        """
        if self.usage_type == "Production":
            industry = session.query(Industry).where(Industry.id == self.industry_id).first()
            return round(industry.output_scale * self.requirement,4)
        else:
            return 0.0

    def flow_per_period(self, session: Session) -> float:
        return round(self.annual_flow_rate(session) / self.simulation(session).periods_per_year,4)

    def standard_stock(self, session: Session) -> float:
        """The size of the normal stock which an industry must maintain in order to conduct
        production.

        Returns zero for non-productive Stocks.
        """
        if self.usage_type == "Production":
            commodity = session.query(Commodity).where(Commodity.id == self.commodity_id).first()
            return self.annual_flow_rate(session) * commodity.turnover_time
        else:
            return 0.0

    def industry(self, session: Session)->Industry:
        """Returns the  Industry to which this stock belongs."""
        return session.get_one(Industry, self.industry_id)

    def commodity(self, session: Session)->Commodity:
        return session.get_one(Commodity, self.commodity_id)

    def simulation(self, session)->Simulation:
        return session.get_one(Simulation, self.simulation_id)

    def unit_cost(self, session: Session)->float:
        """Money price of using this Stock to make one unit of output
        in a period.

        Returns zero if Stock is not productive, which is harmless -
        nevertheless, caller should invoke this method only on productive
        Stocks.
        """
        return self.requirement * self.commodity(session).unit_price

    def owner(self, db:Session)->Industry: 
        """Really just for diagnostic purposes """
        return db.get_one(Industry, self.industry_id)
    
    def change_size(self,amount:float,session:Session)->bool:
        """Change the size of this Industry_stock by 'amount'.
        
        Change the value and price using the unit_value and unit_price 
        of this Industry_stock's Commodity.
        
        Return false if the result is negative, true otherwise.

        ONLY for use in Trade.

        Do NOT use this in production or consumption, which can change
        unit values and prices.
        """
        self.size += amount
        self.price=self.size*self.commodity(session).unit_value
        self.value=self.size*self.commodity(session).unit_price

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
    requirement = Column(Float)
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
            return self.requirement*social_class.population
        else:
            return 0.0

    def flow_per_period(self, session: Session) -> float:
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

"""Helper functions which serve as workarounds for dealing with pydantic limitations"""

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

def get_class_consumption_stocks(social_class,session):
    """Workaround because pydantic won't accept this query in a built-in function."""    
    return (
        session.query(Class_stock)
        .filter(
            Class_stock.class_id == social_class.id,
            Class_stock.usage_type == "Consumption",
            Class_stock.simulation_id == social_class.simulation_id,
        )
    )

"""Helper functions which just put boilerplate code in one place"""

def labour_power(simulation:Simulation, session:Session):
    """Fetch the labour power commodity"""
    return session.query(Commodity).where(
        Commodity.simulation_id==simulation.id,
        Commodity.name=="Labour Power" # bodge
    ).first()

def workers(simulation:Simulation, session:Session)->SocialClass:
    """Fetch the social class called Workers"""
    return session.query(SocialClass).where(
        SocialClass.simulation_id==simulation.id,
        SocialClass.name=="Workers"
    ).first()

def capitalists(simulation:Simulation, session:Session)->SocialClass:
    """Fetch the social class called Capitalists"""
    return session.query(SocialClass).where(
        SocialClass.simulation_id==simulation.id,
        SocialClass.name=="Capitalists"
    ).first()

def necessities_commodity(simulation:Simulation, session:Session)->Commodity:
    result= session.query(Commodity).where(
        Commodity.simulation_id==simulation.id,
        Commodity.usage=="CONSUMPTION" 
    ) # bodge will fail if there is more than one consumption commodity
    return result.first()

def means_of_production(simulation:Simulation, session:Session)->Commodity:
        result=session.query(Commodity).where(
            Commodity.simulation_id == simulation.id,
            Commodity.usage == "PRODUCTIVE",
            Commodity.origin == "INDUSTRIAL",
        )# bodge will fail if there is more than one means of production commodity
        return result.first()
