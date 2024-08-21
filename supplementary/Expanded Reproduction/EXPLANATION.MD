## Background information
The spreadsheets with the following names are taken from a presentation to Moscow Plekhanov University in 2019:  
*  `spreadsheet illustrations (for Moscow Plekhanov)`  
*  `Expanded Reproduction Only.xlsx`  

The explanation of these is given here:  
*  `2019ba Expanded Reproduction in Marx and Luxemburg.pptx`  

The remaining spreadsheet (s) is a scratch calculation pad to set up the simulation. It is not complete.  

## How to incorporate Expanded Reproduction into the model

1. Create an 'investment algorithm' field. This should be a function
2. Steps in the ER function
   a. How much is left after consumption? This will be the excess unconsumed MP
   b. Set an attempted output scale for D1 based on desired growth rate parameter
   c. Calculate all demand (might as well)
   d. Subtract the demand for Means of Production from the surplus (a)
   e. Set an attempted output scale for DII based on the surplus that is left over
   f. Recalculate all demand
   g. Increase the population of the working class to meet the demand for labour power
   h. Recalculate all demand
   i. Somehow we have to restrict the consumer demand of the capitalists. 
     i. The issue is that they have to release sufficient funds to pay for the MP
* We could either override the 'requirement' OR reset it.