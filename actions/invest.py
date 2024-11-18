from fastapi import HTTPException
from models.models import (
    Class_stock,
    Industry_stock,
    Simulation,
    Industry,
    SocialClass,
    Commodity,
    capitalists,
    labour_power,
    necessities_commodity,
    workers,
)
from report.report import report
from actions.supply import calculate_supply
from actions.utils import validate
from .demand import calculate_demand
from sqlalchemy.orm import Session

def invest(simulation: Simulation, session: Session):
    match simulation.investment_algorithm:
        case "Standard":
            standard_invest(simulation, session)

        case "Expanded":
            expanded_reproduction_invest(simulation, session)

        case _:
            report(1, simulation.id, "UNKNOWN INVESTMENT ALGORITHM", session)

def expanded_reproduction_invest(simulation: Simulation, session: Session):
    """
    The algorithm for expanded reproduction - see the spreadsheet in 'supplementary'
    ONLY applies if there is a single Means of Production

        Steps:
                a. How much MP is left after consumption? This will be the unconsumed MP in the Sales field of D1
                b. Set an attempted output scale for D1 based on desired growth rate parameter
                c. Calculate all demand (might as well)
                d. Subtract the demand for Means of Production from the surplus (a)
                e. Set an attempted output scale for DII based on the surplus that is left over
                f. Recalculate all demand
                g. Increase the population of the working class to meet the demand for labour power
                h. Recalculate all demand
                i. Somehow we have to restrict the consumer demand of the capitalists.
                        i. The issue is that they have to release sufficient funds to pay for the MP
                        ii. We could either override the 'requirement' OR reset it.
    """
    report(1,simulation.id,"Applying the expanded reproduction algorithm for investment",session)
    mp_commodity: Commodity = production_commodity(simulation,session)
    mc_commodity: Commodity = necessities_commodity(simulation, session)
    DI_industry: Industry = D1_industry(simulation, session)
    DII_industry: Industry = D2_industry(simulation, session) # See comments against the definition to explain this quirky choice of name

    report(2,simulation.id,f"*** Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)

    # DII_industry(simulation, session)
    if not (validate(mp_commodity,"mp commodity")and validate(mc_commodity, "mc commodity")and validate(DI_industry, "mp industry")and validate(DII_industry, "mc industry")):
        report(1, simulation, "One or more industries or commodities is missing", session)
        return
    cc: SocialClass = capitalists(simulation, session)
    wc: SocialClass = workers(simulation, session)
    if not (validate(cc, "capitalists")and validate(wc, "workers")):
        report(2, simulation, "One or more classes is missing", session)
        return
    cc_consumption_stock: Class_stock = cc.consumption_stocks(session).first()
    wc_consumption_stock: Class_stock = wc.consumption_stocks(session).first()
    DI_mp_stock: Industry_stock = DI_industry.mp_stock(session)
    DII_mp_stock: Industry_stock = DII_industry.mp_stock(session)
    lp_commodity: Commodity = labour_power(simulation, session)
    lp_sales_stock: Class_stock = wc.sales_stock(session)
    if not(
        validate(cc_consumption_stock, "capitalists consumption stock")
        and validate(wc_consumption_stock, "workers consumption stock")
        and validate(DI_mp_stock, "Means of production used by DI")
        and validate(DII_mp_stock, "Means of production used by DII")
        and validate(lp_sales_stock, "Labour Power Sales Stock")
    ):
        report(2, simulation, "One or more stocks is missing", session)
        return

    session.add(mp_commodity)
    session.add(mc_commodity)
    session.add(DI_industry)
    session.add(DII_industry)
    session.add(cc)
    session.add(wc)
    session.add(cc_consumption_stock)
    session.add(wc_consumption_stock)
    session.add(DI_mp_stock)
    session.add(cc_consumption_stock)
    session.add(wc_consumption_stock)
    session.add(lp_sales_stock)

    calculate_supply(session, simulation)
    calculate_demand(session, simulation)

    excess_supply = mp_commodity.total_value - mp_commodity.demand * mp_commodity.unit_value

    report(2,simulation.id,f"Demand for MP is {mp_commodity.demand*mp_commodity.unit_value}, supply is {mp_commodity.supply} and excess is {excess_supply}",session)
    report(2,simulation.id,f"Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)
    report(2,simulation.id,f"Demand for MP is {mp_commodity.demand*mp_commodity.unit_value}, supply is {mp_commodity.supply} and excess is {excess_supply}",session)
    report(2,simulation.id,f"Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)
    
    DI_industry.output_scale *= 1 + DI_industry.output_growth_rate

    report(2,simulation.id,f"DI Output Scale increased by {DI_industry.output_growth_rate} to {DI_industry.output_scale}",session,)
    report(2,simulation.id,f"Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)

    # Recalculate demand at the new output scale
    calculate_demand(session, simulation)

    excess_supply = mp_commodity.total_value - mp_commodity.demand * mp_commodity.unit_value
    report(2,simulation.id,f"*** Raised MP growth rate. MP demand is {mp_commodity.demand*mp_commodity.unit_value}, supply {mp_commodity.supply} and excess capital {excess_supply}",session)
    report(2,simulation.id,f"*** Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)

    # Allocate the remaining means of production to DII
    constant_capital = DII_mp_stock.flow_per_period(session) * mp_commodity.unit_value

    report(2,simulation.id,f"DII Constant Capital Requirement is {constant_capital}",session,)
    report(2,simulation.id,f"Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)

    expansion_ratio = excess_supply / constant_capital

    report(2,simulation.id,f"DII expand output scale by {expansion_ratio}",session )
    report(2,simulation.id,f"Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)

    DII_industry.output_scale *= 1 + expansion_ratio

    report(2,simulation.id,f"DI scale is now {DI_industry.output_scale} and DII scale is {DII_industry.output_scale}.",session)
    report(2,simulation.id,f"Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)

    # Now we don't have enough workers, so we have to increase the labour supply
    calculate_demand(session, simulation)
    lp_commodity: Commodity = labour_power(simulation, session)

    report(2,simulation.id,f"*** Demand for labour power is {lp_commodity.demand}. There are {wc.population} workers. Call up the reserve army!!!",session)
    report(2,simulation.id,f"*** Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)
    
    wc.population = lp_commodity.demand
    print(0)
    report(3,simulation.id,f"Raise sales stock of labour power from {lp_sales_stock.size} to {lp_commodity.demand}",session)
    lp_sales_stock.change_size(lp_commodity.demand-lp_sales_stock.size,session)
    print(1)
    print(2)
    report(3,simulation.id,f"Check: sales stock of labour poweris now {lp_sales_stock.size}",session)
    print(3)
    calculate_supply(session, simulation)  
    necessity_supply = mc_commodity.supply
    wc_consumption=wc_consumption_stock.demand
    cc_consumption=cc_consumption_stock.demand

    # This will tell us the workers' demand for necessities in the next circuit
    report(2,simulation.id,f"The supply of necessities is {necessity_supply} ",session)
    report(2,simulation.id,f"Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)
    report(2,simulation.id,f"Workers demand for necessities is {wc_consumption} and capitalist demand is {cc_consumption}",session)
    report(2,simulation.id,f"Capitalist demand for necessities will be reduced to {necessity_supply-wc_consumption}",session)
    report(2,simulation.id,f"Size of MP is {mp_commodity.size}, value is {mp_commodity.total_value}",session)

    cc_requirement=(necessity_supply-wc_consumption)/cc.population
    cc_consumption_stock.requirement=cc_requirement

    report(2,simulation.id,f"capitalist requirement per head for necessities has been reduced to {cc_requirement}",session)

    # session.rollback()
    session.commit()
    return

def standard_invest(simulation: Simulation, session: Session):

    """ The standard investment algorithm. 
    
    Other algorithms will be developed as the project proceeds. 
    
    In time, we aim to rationalise the system of algorithms. 
    For now this is a kind of test bed for development
    """
    
    report(1, simulation.id, "Applying the standard investment algorithm", session)
    industries = session.query(Industry).where(Industry.simulation_id == simulation.id)
    for industry in industries:
        session.add(industry)
        transfer_profits(industry,simulation,session)
        industry.output_scale=estimateIndustryScale(industry, simulation,session)  
    simulation.state = "DEMAND"
    session.commit()

def transfer_profits(industry:Industry, simulation: Simulation, session: Session):

    """Transfer profits to the capitalist class. The class is assumed to have
    a propensity to consume profits equal to 'consumption ratio' between 1 and 0.
    This if this is 0, they will invest all retained profits. If it is 1, they
    will either consume these profits or hold on to them as money. """

    report(2,simulation.id,"Transferring profit to the capitalists as revenue",session,)

    # for now suppose just one propertied class
    capitalists = (session.query(SocialClass).where(SocialClass.simulation_id == simulation.id).first()) 
    private_capitalist_consumption = capitalists.consumption_ratio * industry.profit

    report(2,simulation.id,f"Industry {industry.name} will transfer {private_capitalist_consumption} profits to its owners",session)
    cms = capitalists.money_stock(session)
    ims = industry.money_stock(session)

    report(3,simulation.id,f"Capitalist money stock is {cms.name}({cms.id})", session)
    report(3,simulation.id,f"Industry money stock is {ims.name}({ims.id})", session)

    session.add(cms)
    session.add(ims)
    cms.change_size(private_capitalist_consumption, session)
    ims.change_size(-private_capitalist_consumption, session)
    session.commit()

    report(3,simulation.id,f"Capitalists now have a money stock of {capitalists.money_stock(session).size}",session,)
    report(3,simulation.id,f"Industry {industry.name} now has a money stock of {industry.money_stock(session).size}",session )
    report(2,simulation.id,"Estimating the output scale which can be financed",session,)

def estimateIndustryScale(industry: Industry, simulation: Simulation, session:Session):

    """Set an attempted output scale based on the profits retained in the industry after
    transferring part thereof to the capitalist class. This algorithm takes no account
    of whether the industry has the money to pay for the attempted output. The Demand
    stage deals with monetary shortages.
    """

    cost = industry.unit_cost(session) * industry.output_scale
    report(3,simulation.id,f"Industry {industry.name} has unit cost {industry.unit_cost(session)} so needs to spend {cost} to produce at the same scale.",session,)

    # spare = industry.money_stock(session).size - cost
    # report(3,simulation.id,f"It has {industry.money_stock(session).size} to spend and so can invest {spare}",session,)
    retained_profit=industry.profit

    possible_increase = retained_profit / industry.unit_cost(session)
    potential_growth = possible_increase / cost
    if potential_growth > industry.output_growth_rate:
        attempted_new_scale = industry.output_scale * (1 + industry.output_growth_rate)
    else:
        attempted_new_scale = industry.output_scale * (1 + potential_growth)
    report(3,simulation.id,f"Setting output scale, which was {industry.output_scale}, to {attempted_new_scale}",session,)
    return attempted_new_scale
   

def D1_industry(simulation: Simulation, session: Session) -> Industry:
    """
    Find the industry in this simulation that produces Means of Production
    Short-term fix for the ER algorithm only.
    NOTE this will fail if there is more than one such industry
    """
    industries = session.query(Industry).where(Industry.simulation_id == simulation.id)
    for industry in industries:
        output_commodity: Commodity = industry.output_commodity(session)
        if output_commodity.usage == "PRODUCTIVE":
            return industry
    return None

def D2_industry(simulation: Simulation, session: Session) -> Industry:
    """
    Find the industry in this simulation that produces Means of Consumption
    Short-term fix for the ER algorithm only.
    NOTE this will fail if there is more than one such industry
    """
    industries = session.query(Industry).where(Industry.simulation_id == simulation.id)
    for industry in industries:
        output_commodity: Commodity = industry.output_commodity(session)
        if output_commodity.usage == "CONSUMPTION":
            return industry
    report(1,simulation.id,"Consumption industry not found",session)
    return None

def consumption_commodity(simulation: Simulation, session: Session) -> Commodity:
    """Fetch the necessities commodity"""
    return session.query(Commodity).where(
        Commodity.simulation_id==simulation.id,
        Commodity.name=="Necessities"
    ).first()

def production_commodity(simulation: Simulation, session: Session) -> Commodity:
    """Fetch the means of production commodity"""
    return session.query(Commodity).where(
        Commodity.simulation_id==simulation.id,
        Commodity.origin=="INDUSTRIAL",
        Commodity.usage=="PRODUCTIVE"
    ).first()

def capitalist_consumption_stock(simulation: Simulation, session: Session) -> Class_stock:
    """Fetch the stock of necessities of the capitalists"""
    result=session.query(Class_stock).where(

    )