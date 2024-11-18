from models.models import Trace
from colorama import Fore 
import logging

FORMAT = "%(levelname)s:%(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
from sqlalchemy.orm import Session
logger = logging.getLogger("capsim-logger")
logger.info("Started Logging")



# Logs both to the console and
# As the simulation proceeds, create entries in the 'Trace' file which can be accesed via an endpoint

def report(level: int, simulation_id: int, message: str, session: Session):
    """
    Prints a message on the terminal (comment out for less verbose logging).  
    
    Exports it to the Trace database.  

        Level (int): 
            depth within the simulation.  
        Simulation_id(int):
            which simulation this refers to. 
        message(str):
            the message to be logged 
        session(Session):
            the sqlAlchemy database session to store the report

    Does not commit the change. Assumes this will be done by the caller.
    """
    match level:
        case 0:
            colour = Fore.WHITE
        case 1:
            colour = Fore.GREEN
        case 2:
            colour = Fore.RED
        case 3:
            colour = Fore.BLUE
        case 4:
            colour= Fore.LIGHTRED_EX
        case 5:
            colour=Fore.LIGHTMAGENTA_EX

    user_message = " " * level + f"{message}"
    log_message = " " * level+colour + message + Fore.WHITE
    logging.info(log_message)
    entry = Trace(
        simulation_id=simulation_id,
        level=level,
        time_stamp=1,
        message=user_message,
    )
    session.add(entry)
    # db.commit()
