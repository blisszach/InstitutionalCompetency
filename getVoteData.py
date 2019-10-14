# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 21:06:44 2019

@author: zachb
"""
import os
import time
import dill
from selenium import webdriver
from bs4 import BeautifulSoup as soup


os.chdir(os.path.dirname(__file__))

home_dir = os.getcwd().replace('\src','')
data_dir = home_dir + '\data\\'
output_dir = home_dir +'\output\\'


chromedriver = "C:\\Users\zachb\Documents\chromedriver_win32\chromedriver.exe"
os.environ["webdriver.chrome.driver"] = chromedriver

pass_words = ['confirmed','passed','agreed to','sustained']
yes_vote_words = ['Aye','Yes','Yea','Guilty']
no_vote_words = ['Nay','No','Not Guilty']

Congresses = range(111,107,-1)
chambers = ['house']
for chamber in chambers:
    for congress in Congresses:
        base_url = 'https://www.c-span.org/congress/votes/?chamber='+chamber
        
        senator_party_dict = {} # {senator: party}
        senator_vote_dict = {} # {senator: {bill name: vote}}
        bill_result_dict = {} # {bill name: {senator: vote}}
        
        print('Downloading the vote results of the ' + str(congress) + 'th '+chamber)
        congress_url = base_url + '&congress=' + str(congress)
        done = 0
        pageNo = 0
        while done == 0:
            pageNo += 1
            print('working on page number ' + str(pageNo))
            
            increment = False
            while increment == False:
                try:
                    driver = webdriver.Chrome(chromedriver)
                    page_url = congress_url + '&page=' + str(pageNo)
                    driver.get(page_url)
                    vote_detail_buttons = driver.find_elements_by_css_selector('i.icon-chevron-down')
                    increment = True
                except:
                    driver.quit()
                    time.sleep(120)
                    continue
                 
            for vote_detail_button in vote_detail_buttons[1:]:
                vote_detail_button.click()
                time.sleep(5)
                
            source = driver.page_source
            cspan_html = soup(source,features="lxml")
            
            try:
                senate_votes = cspan_html.find_all('section', attrs = {'class':'votes'})[0]
                votes = senate_votes.find_all('li',attrs = {'class':'vote'})
            except:
                done = 1
                continue
            
            for vote in votes:
                vote_name = vote.find_all('div')[0].find('h3').get_text()
                vote_label = vote.find_all('div')[0].find('span', attrs = {'class':'label'}).get_text()
                vote_name = vote_label.split()[0] + ' ' + str(congress) + ' ' + ' '.join(vote_label.split()[1:]) + ': ' + vote_name
                vote_date = vote.find_all('div')[0].find_all('span', attrs = {'class':'date'})[0].get_text()
                vote_time = vote.find_all('div')[0].find_all('span', attrs = {'class':'time'})[0].get_text().split(' ' )[0]
                vote_results = vote.find_all('div')[0].find_all('div', attrs = {'class':'details'})[0].find_all('div', attrs = {'class':'vote-counts'})
                vote_outcome = vote.find_all('div')[0].find_all('span', attrs = {'class':'result'})[0].get_text().lower()
                vote_status = 'FAIL'
                for word in pass_words:
                    if word in vote_outcome:
                        vote_status = 'PASS'
                
                try:
                    done_check = time.mktime(time.strptime(vote_date,'%B %d, %Y'))
                except:
                    done = 1
                    continue
                
                voter_votes = []
                voter_names = []
                for vote_result in vote_results:
                    voter_party = vote_result.find_all('h4')[0].get_text()
                    voter_vs = [vote_result.find_all('em')[i].get_text() for i in range(len(vote_result.find_all('em')))]
                    voter_ns = [vote_result.find_all('a')[i].get_text() for i in range(len(vote_result.find_all('a')))]
                    for voter_idx in range(len(voter_ns)):
                        voter_votes.append(voter_vs[voter_idx])
                        voter_names.append(voter_ns[voter_idx])
                        senator_party_dict[voter_ns[voter_idx]] = voter_party
                
                bill_result_dict[vote_name] = {'date':vote_date + ' ' + vote_time, 'status':vote_status, 'voters':{}}
                
                for voter_idx in range(len(voter_names)):
                    bill_result_dict[vote_name]['voters'][voter_names[voter_idx]] = voter_votes[voter_idx]
                    try:
                        senator_vote_dict[voter_names[voter_idx]][vote_name] = voter_votes[voter_idx]
                    except:
                        senator_vote_dict[voter_names[voter_idx]] = {vote_name: voter_votes[voter_idx]}
        
        dump_name = data_dir + 'cspan_c'+str(congress)+'_'+chamber+'.pkl'
        with open(dump_name,'wb') as f:
            dill.dump([bill_result_dict,senator_vote_dict,senator_party_dict],f)

driver.quit() 