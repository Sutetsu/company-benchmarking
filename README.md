# Setup
For a test run, the Proxy should be started first.  
Next should be the Server for the keys (and the analyst for the algorithm, if needed).  
After that, Clients can start to communicate with their datasets.  
Lastly, the Server can pull the aggregated KPI.

For Arguments for each File see below.


# Main Files
## Client3.py  
#### Usage: python3  
Reads values from the ClientData.txt and gets KPI in a dialogue with Proxy.  
Arguments: Column of input data-1 and 'fhe' or 'phe' (unimplemented) for Fully or Partially Homomorphic Encryption respectively.  
Input Data excel sheet should have the EIDs in the leftmost column, and the global path variable in Client.py will need to be adjusted if a different table is used.

## Proxy3.py  
#### Usage: python3
Main part of the setup.  
Arguments: 'fhe' or 'phe' (unimplemented) for Fully or Partially Homomorphic Encryption respectively. Cleartext is default

## Analyst3.py
#### Usage: python3
Provides/Updates algorithm for Proxy  
Arguments: None

## Server3.py
#### Usage: python3
Generates Keys, and decrypt KPIs at the end.  
Arguments: 'keys' for providing Server keys at startup, and 'kpi' to pull aggregated kpi from the proxy


# Other files

## analyst/Graph.py  
#### Usage: python  
Arguments are 'all' or 'all2' to graph all connections, 'Count' to count functions and variables, or an EID which build the dependency graph for that EID, potentially followed by 'up', to instead graph everything depending on this EID, 'nolables' to turn off lables for the nodes (increases visibility for big graphs), or 'reverse' to colour the "easy" functions instead of the "harder" ones.  
Default colours are red for exponents, blue for minimum/maximum, yellow for abs, with mixtures following colour theory if the function includes multiple of those. Any function using division which is not already included will be grey.   

## analyst/Parser.py  
#### Usage: python  
Parses Kennkunstoff.xlsm. Outputs to parsed.txt  
Minor issues have to be solved by hand

## analyst/Depth.py
#### Usage: python
Returns the multiplication depth (level) of atomic functions, disregarding functions being sent back to the client.  
Which document it takes is hardcoded.

## analyst/GraphStats.py
#### Usage: python
Returns various stats about the algorithm.  
It has parsed2 and ClientData hardcoded as sources.

## analyst/MissingEID.py
#### Usage: python
Returns which EID are missing in the Client Inputs.  
parsed2 and ClientData are hardcoded.

## CorrectResults.txt
List of expected Results for the first SmallTest.xlsx

## Various tests in /tests
#### Usage: python3
Default Python Seal tests and additional testbeds made during programming
