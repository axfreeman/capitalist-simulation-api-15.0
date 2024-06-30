# Simulation-api, version 15.0

This supersedes all earlier versions, some of which are still public for reference but are no longer maintained. 

## This is an api provider for the simulation of a capitalist economy 
* You can see the results in a browser using Swagger.  
    
* Or you can view more meaningful representations using a front end.  
* This version contains a primitive Excel frontend, in the 'Excel-frontend' folder.
    
* Or you can use the front end at www.github.com/axfreeman/capitalism-simulation-client-15.0. This is recommended.  
  
* That said, the whole point of having an API is that you can make your own frontend. So you can use the API without accepting my front end.  

## The general idea
* Everything that explains this project is in the DOCS folder. Some of this is out of date. 

## Installation and use, brief suggestions  

To install, create virtual environment (assuming you want one) and pip install from ``requirements.txt``  

Runs with ``uvicorn app:main `` but could be adapted to any other server.  

To see the endpoints enter http://localhost:8000/docs (or use whichever port you created).  

This invokes the Swagger interface which tells you most of what you need to know.  



