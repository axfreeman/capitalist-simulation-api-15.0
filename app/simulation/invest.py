from ..models import Simulation, Industry, SocialClass
from .demand import report
from sqlalchemy.orm import Session

def invest(simulation:Simulation,db:Session):
    industries=db.query(Industry).where(Industry.simulation_id==simulation.id)
    for industry in industries:
        report(3,simulation.id,"Transferring profit to the capitalists as revenue",db)
        # TODO calculate private consumption
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
