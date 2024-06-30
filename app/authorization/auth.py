from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.models import User
from ..database import get_session
from ..reporting.caplog import logger
from fastapi import Security, status

"""In this version, all security is handled via api_keys. 
These are manually allocated on request.  
Each user is given a unique key.  
So the api_key used in the client request uniquely identifies the user.
"""
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def get_api_key(
    api_key_header: str = Security(api_key_header),
    session:Session=Depends(get_session)
) -> User:
    """Retrieve and validate an API key from the query parameters or HTTP header.

        api_key_header: The API key passed in the HTTP header.

        Returns the user who was allocated this key;
        Raises HTTPException if the API key is invalid.
    """
    # Uncomment for more detailed diagnostics
    # logger.info(f"Received request using api key {api_key_header}")
    u:User=session.query(User).where(User.api_key==api_key_header).first()
    if u is not None:
        # logger.info(f"the user associated with this key is {u.username}")
        return u
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )

