DONE
Commodity table at the top
Add consumption to class table

BUGS
Bug: Player logs out and logs in as same: gets disallowed as 'not locked at server'
Bug: VerifyPlayer says no valid cookie
Note: client can correctly note locked player names, but sometimes gets it wrong, or so it seems.

IMPROVEMENTS
Add header to index page saying who is playing and which simulation (or maybe put this in the menu, or in a bar underneath)

Add option to 'has no simulations' to choose a player.
'has no simulations' should be white, not blue

(1) CSV dump of the simulation
(2) Trail of any selected row?


icons for the names of industries and classes

NOTE
Run api on gerg-create:
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >logofasort.txt


