from colorama import Fore 
import logging
from sqlalchemy.orm import Session

from sqlalchemy import Column, Integer, String
from database.database import Base

FORMAT = "%(levelname)s:%(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger("capsim-logger")
logger.info("Started Logging")


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


# Logs both to the console and
# As the simulation proceeds, create entries in the 'Trace' file which can be accesed via an endpoint

def report(level: int, simulation_id: int, message: str, session: Session):
    """
    Prints a message on the terminal (comment out for less verbose logging).  
    
    Exports it to the Trace database.
    If the Level of this entry is more than one level higher than the previous entry, fill the gap
    This allows clients to display the result as a foldable accordion
    TODO at present only compensates for gaps of one level.
    TODO however if the reporting is done correctly there should be no gaps.
    TODO thus this is more of a fault-catcher than a stable workaround

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
    logging.debug(log_message)

    # Get the last trace record that was added
    lastRecord: Trace =session.query(Trace).where(Trace.simulation_id==simulation_id).order_by(Trace.id.desc()).first()
    if lastRecord is not None:
    # print(f"The id of the last Trace record was {lastRecord.id} and its level was {lastRecord.level}")
        if lastRecord.level - level >1:
            logging.warning(f"A subitem was not closed. Last record had level {lastRecord.level} and this trace entry has level {level}")
            logging.warning(f"The last record said {lastRecord.message}")

            gapentry = Trace(
                simulation_id=simulation_id,
                level=lastRecord.level-1,
                time_stamp=1,
                message=f"CORRECTION to Minor API error. Previous level was {lastRecord.level} and this entry was {level}. Please tell the developer",
            )
            session.add(gapentry)

    # TODO check that gapentry and entry are added to the database in the order we add them to the session!
    entry = Trace(
        simulation_id=simulation_id,
        level=level,
        time_stamp=1,
        message=user_message,
    )
    session.add(entry)
    session.commit() # TODO ideally we should not commit every time a new report is made...
