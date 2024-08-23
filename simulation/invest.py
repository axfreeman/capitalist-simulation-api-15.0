from models.models import Industry_stock, Simulation, Industry, SocialClass, Commodity
from report.report import report
from simulation.supply import calculate_supply
from .demand import calculate_demand
from sqlalchemy.orm import Session

def invest(simulation:Simulation,session:Session):
    match simulation.investment_algorithm:
        case "Standard":
            standard_invest(simulation,session)
            
        case "Expanded":
            expanded_reproduction_invest(simulation, session)

        case _:
            report(1,simulation.id,"UNKNOWN INVESTMENT ALGORITHM",session)

def expanded_reproduction_invest(simulation:Simulation,session:Session):
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
    report(1,simulation.id,"APPLYING THE EXPANDED REPRODUCTION INVESTMENT ALGORITHM",session)
    mp:Commodity=session.query(Commodity).where(
        Commodity.simulation_id==simulation.id,
        Commodity.usage=="PRODUCTIVE",
        Commodity.origin=="INDUSTRIAL").first()
    mp_industry:Industry=means_of_production_industry(simulation,session)
    calculate_supply(session,simulation)
    calculate_demand(session,simulation)
    excess_supply=mp.total_value-mp.demand*mp.unit_value
    report(2,simulation.id,f"Demand for MP is {mp.demand*mp.unit_value}, supply is {mp.supply} and excess is {excess_supply},",session)

    mp_industry.output_scale*=(1+mp_industry.output_growth_rate)
    calculate_demand(session,simulation)
    excess_supply=mp.total_value-mp.demand*mp.unit_value
    report(2,simulation.id,f"After increasing MP growth rate, demand for MP is {mp.demand*mp.unit_value}, supply is {mp.supply} and excess is {excess_supply},",session)

    # TBA incomplete so far

    return

def standard_invest(simulation:Simulation,session:Session):
    report(1,simulation.id,"APPLYING THE STANDARD INVESTMENT ALGORITHM",session)
    industries=session.query(Industry).where(Industry.simulation_id==simulation.id)
    for industry in industries:
        report(3,simulation.id,"Transferring profit to the capitalists as revenue",session)
        capitalists=session.query(SocialClass).where(SocialClass.simulation_id==simulation.id).first() # for now suppose just one propertied class
        private_capitalist_consumption = capitalists.consumption_ratio*industry.profit

        report(3,simulation.id,f"Industry {industry.name} will transfer {private_capitalist_consumption} of its profit to its owners",session)
        cms =capitalists.money_stock(session)
        ims=industry.money_stock(session)

        print("Capitalist money stock",cms.id, cms.name)
        print("Industry money stock",ims.id,ims.name)

        session.add(cms)
        session.add(ims)
        cms.change_size(private_capitalist_consumption,session)
        ims.change_size(-private_capitalist_consumption,session)
        session.commit()

        report(3,simulation.id,f"Capitalists now have a money stock of {capitalists.money_stock(session).size}",session)
        report(3,simulation.id,f"Industry {industry.name} now has a money stock of {industry.money_stock(session).size}",session)
        report(2,simulation.id,"Estimating the output scale which can be financed",session)

        cost=industry.unit_cost(session)*industry.output_scale
        report(3,simulation.id,f"Industry {industry.name} has unit cost {industry.unit_cost(session)} so needs to spend {cost} to produce at the same scale.",session)

        spare=industry.money_stock(session).size-cost
        report(3,simulation.id,f"It has {industry.money_stock(session).size} to spend and so can invest {spare}",session)

        possible_increase=spare/industry.unit_cost(session)
        monetarily_potential_growth=possible_increase/cost
        if monetarily_potential_growth>industry.output_growth_rate:
            attempted_new_scale=industry.output_scale*(1+industry.output_growth_rate)
        else:
            attempted_new_scale=industry.output_scale*(1+monetarily_potential_growth)
        report(3,simulation.id,f"Setting output scale, which was {industry.output_scale}, to {attempted_new_scale}",session)
        industry.output_scale=attempted_new_scale
    simulation.state = "DEMAND"
    session.commit()

def means_of_production_industry(simulation:Simulation,session:Session)->Industry:
    """
    Find the industry in this simulation that produces Means of Production
    Legacy, deprecated
    """
    industries=session.query(Industry).where(Industry.simulation_id==simulation.id)
    report(2,simulation.id,"Remaining unconsumed Means of Production in the Sales stock of Department I",session)
    for industry in industries:
        output_commodity:Commodity=industry.output_commodity(session)
        report(3,simulation.id,f"Inspecting Industry {industry.name} which produces {output_commodity.name} with usage {output_commodity.usage}",session)
        if output_commodity.usage=="PRODUCTIVE":
            return industry
    return None        
