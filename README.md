# InstitutionalCompetency

Competency_of_institutions.pdf is an exmplanation of the model

getVoteData.py is a python script that downloads House & Senate roll-call vote results from CSPAN

plotVoteData.py is a python sctipt that uses the CSPAN vote results to make the epistemic agreement plots for the House and Senate


to run:
make sure your python has access to numpy, pandas, matplotlib, dill, requests, BeautifulSoup, and selenium webdriver; create a project folder; within the project folder, create a "src" folder, a "data" folder, and an "output" folder; 
place the python scripts in the src folder; try to run getVoteData; fail, then fix the errors; repeat; run getVoteData for way too long, then when it finishes run plotVoteData
 
