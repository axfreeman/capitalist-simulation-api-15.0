from models.models import Industry_stock, Simulation, Industry, SocialClass, Commodity
from .demand import report
from sqlalchemy.orm import Session

def invest(simulation:Simulation,db:Session):
    match simulation.investment_algorithm:
        case "Standard":
            standard_invest(simulation,db)
            
        case "Expanded":
            expanded_reproduction_invest(simulation, db)

        case _:
            report(1,simulation.id,"UNKNOWN INVESTMENT ALGORITHM",db)

def expanded_reproduction_invest(simulation:Simulation,db:Session):
    """
    The algorithm for expanded reproduction - see the spreadsheet in 'supplementary'

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
    report(1,simulation.id,"APPLYING THE EXPANDED REPRODUCTION INVESTMENT ALGORITHM",db)
    mp_industry=means_of_production_industry(simulation,db)
    if mp_industry==None:
        report(1,simulation.id,"INDUSTRY PRODUCING MEANS OF PRODUCTION WAS NOT FOUND: GIVING UP ON INVESTMENT",db)
        return
    output_stock:Industry_stock=mp_industry.sales_stock(db)
    report(2,simulation.id,f"Means of Production in Department I is {output_stock.value}",db)

    
    return

def standard_invest(simulation:Simulation,db:Session):
    report(1,simulation.id,"APPLYING THE STANDARD INVESTMENT ALGORITHM",db)
    industries=db.query(Industry).where(Industry.simulation_id==simulation.id)
    for industry in industries:
        report(3,simulation.id,"Transferring profit to the capitalists as revenue",db)
        capitalists=db.query(SocialClass).where(SocialClass.simulation_id==simulation.id).first() # for now suppose just one propertied class
        private_capitalist_consumption = capitalists.consumption_ratio*industry.profit

        report(3,simulation.id,f"Industry {industry.name} will transfer {private_capitalist_consumption} of its profit to its owners",db)
        cms =capitalists.money_stock(db)
        ims=industry.money_stock(db)

        print("Capitalist money stock",cms.id, cms.name)
        print("Industry money stock",ims.id,ims.name)

        db.add(cms)
        db.add(ims)
        cms.change_size(private_capitalist_consumption,db)
        ims.change_size(-private_capitalist_consumption,db)
        db.commit()

        report(3,simulation.id,f"Capitalists now have a money stock of {capitalists.money_stock(db).size}",db)
        report(3,simulation.id,f"Industry {industry.name} now has a money stock of {industry.money_stock(db).size}",db)
        report(2,simulation.id,"Estimating the output scale which can be financed",db)

        cost=industry.unit_cost(db)*industry.output_scale
        report(3,simulation.id,f"Industry {industry.name} has unit cost {industry.unit_cost(db)} so needs to spend {cost} to produce at the same scale.",db)

        spare=industry.money_stock(db).size-cost
        report(3,simulation.id,f"It has {industry.money_stock(db).size} to spend and so can invest {spare}",db)

        possible_increase=spare/industry.unit_cost(db)
        monetarily_potential_growth=possible_increase/cost
        if monetarily_potential_growth>industry.output_growth_rate:
            attempted_new_scale=industry.output_scale*(1+industry.output_growth_rate)
        else:
            attempted_new_scale=industry.output_scale*(1+monetarily_potential_growth)
        report(3,simulation.id,f"Setting output scale, which was {industry.output_scale}, to {attempted_new_scale}",db)
        industry.output_scale=attempted_new_scale
    simulation.state = "DEMAND"
    db.commit()

def means_of_production_industry(simulation:Simulation,db:Session)->Industry:
    """
    Find the industry in this simulation that produces Means of Production
    NOTE if there is more than one such, this will fail
    TODO extend to multiple such industries
    """
    industries=db.query(Industry).where(Industry.simulation_id==simulation.id)
    report(2,simulation.id,"Remaining unconsumed Means of Production in the Sales stock of Department I",db)
    for industry in industries:
        output_commodity:Commodity=industry.output_commodity(db)
        report(3,simulation.id,f"Inspecting Industry {industry.name} which produces {output_commodity.name} with usage {output_commodity.usage}",db)
        if output_commodity.usage=="PRODUCTIVE":
            return industry
    return None        
