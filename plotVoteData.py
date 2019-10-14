# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 08:39:20 2019

@author: zachb
"""


############################################################
#load data
############################################################

import dill
import os

os.chdir(os.path.dirname(__file__))

home_dir = os.getcwd().replace('\src','')
data_dir = home_dir + '\data\\'
output_dir = home_dir +'\output\\'

senate_votes = [{},{},{}]
house_votes = [{},{},{}]
congress_votes = [{},{},{}]

for congress_number in range(103,116):
    
    with open(data_dir + 'cspan_c' + str(congress_number) +'_senate.pkl','rb') as f:
        known_votes = dill.load(f)
        senate_votes[0].update(known_votes[0])
        senate_votes[1].update(known_votes[1])
        senate_votes[2].update(known_votes[2])

        congress_votes[0].update(known_votes[0])
        congress_votes[1].update(known_votes[1])
        congress_votes[2].update(known_votes[2])
        
    with open(data_dir + 'cspan_c' + str(congress_number) +'_house.pkl','rb') as f:
        known_votes = dill.load(f)
        house_votes[0].update(known_votes[0])
        house_votes[1].update(known_votes[1])
        house_votes[2].update(known_votes[2])

        congress_votes[0].update(known_votes[0])
        congress_votes[1].update(known_votes[1])
        congress_votes[2].update(known_votes[2])





######################################
# collect party records 
######################################

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import math
import datetime
import requests
from bs4 import BeautifulSoup as soup

def logistic(attack,defense):
    x = 1/(1+math.exp(-1*(attack-defense)))
    return x

party_approval_dict = {} # {time: {party:value}}

approval_url = 'https://news.gallup.com/poll/24655/party-images.aspx'
r = requests.get(approval_url)
approval_page = soup(r.text,'lxml')
democratic_approval_table = approval_page.find_all('table')[0]
republican_approval_table = approval_page.find_all('table')[1]

td = pd.read_html(str(democratic_approval_table))[0]
favorables_d = list(td.loc[:,'Favorable'][0:-1].loc[:,'%'])
unfavorables_d = list(td.loc[:,'Unfavorable'][0:-1].loc[:,'%'])

tr = pd.read_html(str(republican_approval_table))[0]
favorables_r = list(tr.loc[:,'Favorable'][0:-1].loc[:,'%'])
unfavorables_r = list(tr.loc[:,'Unfavorable'][0:-1].loc[:,'%'])

dates = list(td.iloc[:,[0]][0:-1].iloc[:,0])
dates = [' '.join(x.split()[0:2] + [x.split()[2]]).split('-')[0] for x in dates]

for i in range(len(dates)):
    
    try:
        favorable_d = float(favorables_d[i])/100
        unfavorable_d = float(unfavorables_d[i])/100
        
        favorable_r = float(favorables_r[i])/100
        unfavorable_r = float(unfavorables_r[i])/100
    except:
        continue
    
    competence_d = logistic(favorable_d,unfavorable_d)
    competence_r = logistic(favorable_r,unfavorable_r)
    
    party_approval_dict[dates[i]] = {'D':round(competence_d,3),'R':round(competence_r,3)}

def PartyRating(date): #takes date of format 'December 2012, 21' and finds party ratings for that date
    d_get_compare = time.mktime(time.strptime(date,'%B %d, %Y'))
    d_list = [time.mktime(time.strptime(x,'%Y %b %d')) for x in party_approval_dict.keys()]
    d_deltas = [abs(d_get_compare - x) for x in d_list]
    index_min = np.argmin(d_deltas)
    d_closest = d_list[index_min]
    d = time.strftime('%Y %b %d',time.localtime(d_closest))
    if d.split()[-1][0] == '0':
        d = ' '.join(d.split()[0:-1]) + ' ' + d.split()[-1][1:]
    return party_approval_dict[d]


rate_data = sorted([[time.mktime(time.strptime(x,'%Y %b %d')),party_approval_dict[x]] for x in party_approval_dict.keys()], key=lambda x: x[0])
ds = [datetime.datetime.fromtimestamp(x[0]) for x in rate_data]
dem_rates = [x[1]['D'] for x in rate_data]
rep_rates = [x[1]['R'] for x in rate_data]

plt.figure(figsize=(10,3))
plt.grid()
plt.plot(ds, dem_rates,'b')
plt.plot(ds, rep_rates,'r')

plt.xlabel('Date')
plt.ylabel('Competence')
plt.title('Party Competences 1993-2019')
plt.legend(['Democrats','Republicans'], loc=(.42,-.45))
plt.show()


############################################################
#select chamber
############################################################


chambers = ['House','Senate']
for chamber in chambers:
    
    if chamber == 'House':
        known_votes = house_votes     
    elif chamber == 'Senate':
        known_votes = senate_votes
    
    bill_result_dict = known_votes[0]
    senator_vote_dict = known_votes[1]
    senator_party_dict = known_votes[2]
    
    
    ############################################################
    #calculate probabilities
    ############################################################
    
    
    def NaiveBayes(pc,competences,votes):
        Q=1
        for i in range(len(votes)):
            Q = Q*(((-1)**(votes[i]))*(competences[i]-votes[i]))/float(((-1)**(1-votes[i]))*(competences[i]-votes[i])+1)
            
        return 1/float(1 + Q*(1-pc)/float(pc))
    
    
    pass_words = ['confirmed','passed','agreed to','sustained']
    yes_vote_words = ['Aye','Yes','Yea','Guilty']
    no_vote_words = ['Nay','No','Not Guilty']
    
    prob_dict = {}
    
    for bill in bill_result_dict.keys():
        date = ' '.join(bill_result_dict[bill]['date'].split()[0:-1])
        date_party_approval_dict = PartyRating(date)
        competences = []
        votes = []
        for senator in sorted(bill_result_dict[bill]['voters'].keys()):
            try:
                if senator_party_dict[senator] == 'Democratic':
                    competence = date_party_approval_dict['D']
                elif senator_party_dict[senator] == 'Republican':
                    competence = date_party_approval_dict['R']
                else:
                    print('why no favoribility poll for independents?',senator)
                    continue
                
                vote = bill_result_dict[bill]['voters'][senator]
                competences.append(competence)
                votes.append(vote)
            except:
                continue
        vs = []
        cs = []
        for voter_idx in range(len(votes)):
            if votes[voter_idx] in yes_vote_words:
                vs.append(1)
                cs.append(competences[voter_idx])
            elif votes[voter_idx] in no_vote_words:
                vs.append(0)
                cs.append(competences[voter_idx])
            else:
                continue
            
        prob = NaiveBayes(.5, cs, vs)
        prob_dict[bill] = prob
    
    
    ############################################################
    #calculate congress competency
    ############################################################
    

    
    def ForecastQuality(trues, forecast):
        a = 0
        b = 0
        c = 0
        d = 0
        for i in range(len(trues)):
            if forecast[i] == 1 and trues[i] == 1:
                a += 1
            elif forecast[i] == 1 and trues[i] == 0:
                b += 1
            elif forecast[i] == 0 and trues[i] == 0:
                d += 1
            elif forecast[i] == 0 and trues[i] == 1:
                c += 1
                
        pcorrect = (a+d)/float(a+b+c+d)
        quality = [round(pcorrect,3)]
        
        return quality
    
    
    def CongressQuality(t_i,t_f): 
        
        epistemic = []
        congressional = []
        for bill in prob_dict.keys():
            bill_date = ' '.join(bill_result_dict[bill]['date'].split()[0:-1])
            bill_date_compare = time.mktime(time.strptime(bill_date,'%B %d, %Y'))
            if t_i <= bill_date_compare < t_f:
                
                if prob_dict[bill] > .5:
                    epistemic.append(1)
                elif prob_dict[bill] < .5:
                    epistemic.append(0)   
                else:
                    continue
                
                if bill_result_dict[bill]['status'] == 'PASS':
                    congressional.append(1)
                else:
                    congressional.append(0)
       
        congress_quality = ForecastQuality(epistemic,congressional)
        return congress_quality
    
    
    max_date = max([time.mktime(time.strptime(' '.join(bill_result_dict[bill]['date'].split()[0:-1]),'%B %d, %Y')) for bill in bill_result_dict])
    min_date = min([time.mktime(time.strptime(' '.join(bill_result_dict[bill]['date'].split()[0:-1]),'%B %d, %Y')) for bill in bill_result_dict])
    n_points = 52
    date_increment = (max_date - min_date)/n_points
    date_ranges = [min_date + x*date_increment for x in range(n_points)]
    
    accuracies = []
    quality_dates = []
    t_f = 'init'
    for date_idx in range(len(date_ranges)):
        if t_f != date_ranges[-1]:
            t_i = date_ranges[date_idx]
            t_f = date_ranges[date_idx + 1]
            cq = CongressQuality(t_i,t_f)
            accuracies.append(cq[0])
            quality_dates.append(datetime.datetime.fromtimestamp(t_f))
        else:
            continue
        
        
    ############################################################
    # plot results
    ############################################################

    
    date_prob_pairs_passed = []
    date_prob_pairs_failed = []
    weird_ones = []
    for bill in bill_result_dict.keys():
        try:
            date = bill_result_dict[bill]['date']
            date_datetime = time.strptime(date,'%B %d, %Y %I:%M%p')
            date_epoch = time.mktime(date_datetime)
            prob = prob_dict[bill]
            if prob == .5:
                #these ones messed up in data download
                continue
            pair = [date_epoch,prob,bill]
            if bill_result_dict[bill]['status'] == 'PASS':
                date_prob_pairs_passed.append(pair)
            else:
                date_prob_pairs_failed.append(pair)
        except:
            continue
        
        
    plt.figure(figsize=(20,6))
    plt.grid()
    plt.rcParams["font.family"] = "Times New Roman"
    
    date_prob_pairs_passed = sorted(date_prob_pairs_passed, key=lambda x: x[0])
    dates_passed = [datetime.datetime.fromtimestamp(x[0]) for x in date_prob_pairs_passed]
    probs_passed = [x[1] for x in date_prob_pairs_passed]
    plt.plot(dates_passed, probs_passed,'g.',markersize = 5,alpha = .7)
    
    date_prob_pairs_failed = sorted(date_prob_pairs_failed, key=lambda x: x[0])
    dates_failed = [datetime.datetime.fromtimestamp(x[0]) for x in date_prob_pairs_failed]
    probs_failed = [x[1] for x in date_prob_pairs_failed]
    plt.plot(dates_failed, probs_failed, 'r.', markersize = 5,alpha = .5)    
    
    
    plt.plot(quality_dates, accuracies,'b',linewidth=2)
    
    plt.ylabel('Estimated Probability Taking the Action is in the Public Interest\n&\nAgreement of Institutional and Epistemic Decisions\n over last 6 months',fontsize=13)
    plt.xlabel('Date of Vote',fontsize=13)
    plt.title('U.S. ' + chamber + ' Epistemic Agreement Plot with Voters as Party Representitives\n',fontsize=18)
    plt.legend(['Vote Passed','Vote Failed','\nPercent Agreement Of Epistemic and Institutional Decisions over last 6 months\n' + r'$\frac{(green>.5+red<.5)}{(green>.5+red<.5) + (green<.5+red>.5)}$'], loc=(.29,-.45),fontsize=14)
    
    plt.savefig(output_dir + chamber + 'EpistemicAgreement')