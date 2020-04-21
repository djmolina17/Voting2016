#################################
##### Name: David Josue Molina
##### Uniqname: djmolina 
#################################

from bs4 import BeautifulSoup
import requests
import json
import sys
import webbrowser 
import sqlite3 
import plotly.graph_objects as go
from state_abbr import state_abbr as ab

base_url = "https://www.vote.org" 

def build_state_url_dict(cache={}):
    '''  Creates a dictionary with key value pair of state and link
    
    Parameters
    ----------
    cache
    Returns
    -------
    dictionary:
    state name and link 
    '''
    state_link ={}
    soup = make_url_request_using_cache( "https://www.vote.org/", cache)
    state_main__page_link_elements = soup.select(".ul-quicklinks li a")
    for link in state_main__page_link_elements:
        # get the link tezt, split on spaces, get rid of last two words (election center), and join back together
        state_name = " ".join(link.text.lower().split()[:-2])
        state_link[state_name] = base_url + link['href']
    return state_link

def build_state_object(cache, state_link):
    '''Creates a dictionary with key value pair of state name and state object
    
    Parameters
    ----------
    cache
    state_link
   
    Returns
    =============
    dict:
        {
            'michigan': <State Object>,
            ...
        }
    '''
    # print("state_link=", state_link)
    # print('==============')
    output = {}
    for state_name, state_url in state_link.items():
    #    print('===============')
        soup = make_url_request_using_cache(state_url, cache)
        state_election_url = soup.select("div.offsite-links a")[0]['href']
        covid_url = f"https://www.vote.org/covid-19/#{state_name.replace(' ', '-')}"
        # print("state_name=", state_name)
        # print("state_url=", state_url)
        # print("state_election_url=", state_election_url)
        # print("covid_url=", covid_url)
        newState = State(name=state_name, state_url= state_url, covid_url = covid_url, state_election_url= state_election_url)
        output[state_name] = newState
    return output





class State():
    '''A state object
    Attributes
    ----------
    name : string
        The state name 
    state_url: string
        the state's link
    covid_url: string
        page of state-specific covid-19 information 
    state_election_url: string
        government election website that is state-specifc
    short_name: string
        state's abbreviation (sourced from state_abbr.py) 
    '''
    def __init__(self, name, state_url, covid_url, state_election_url):
        self.state_url = state_url
        self.name = name
        self.covid_url = covid_url
        self.state_election_url = state_election_url
        self.short_name = ab[name]
        
    
    def __str__(self):
        return f'''{self.name}
==================
{self.state_url}
{self.covid_url}
{self.state_election_url} '''

# {'michigan': <State Object>, 'nebraska': <StateObject>}
def load_cache(): # called only once, when we run the program
    '''Looks for cache file and formats it to a dictionary. If file doesnt exit, returns a empty dictionary. 
    
    Parameters
    ----------
    
    Returns
    -------
    dict
        a converted cache object
    '''
    try:
        cache_file = open("cache.json", 'r')
        cache_file_contents = cache_file.read() #string
        cache = json.loads(cache_file_contents) # python dictionary
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache): # called whenever the cache is changed
    ''' Takes the cache objects and coverts it to a string of json. It overwrites the json file. 
    
    Parameters
    ----------
    cache
    Returns
    -------
    
    '''
    cache_file = open('cache.json', 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    ''' Determines if it using cache or not if information is saved and returns html as a BeautifulSoup Object. 
    
    Parameters
    ----------
    url
    cache
    Returns
    -------
    BeautifulSoup Object:
    html code
    '''
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        html = cache[url]     # we already have it, so return it
    else:
        print("Fetching")
        response = requests.get(url) # gotta go get it
        cache[url] = response.text # add the TEXT of the web page to the cache
        save_cache(cache)          # write the cache to disk
        html = cache[url]
    return BeautifulSoup(html, 'html.parser')     



def create_visualizations(chosen_state: State):
    '''  Creates 4 bar graphs based on user's state input. Provides information about voting in 2016 and unemployment in 2016 as well.
    
    Parameters
    ----------
    chosen_state:State object
    Returns
    -------
    None
    '''
    connection = sqlite3.connect("2016_POTUS_Election.db")
    cursor = connection.cursor()

    #1
    query = "SELECT cand, votes FROM pres16results WHERE st = \"US\" ORDER BY votes DESC LIMIT 4"
    result = cursor.execute(query).fetchall()
    #print(result)
    canditate_list = []
    vote_general_count = []
    for r in result:
        canditate_list.append(r[0])
        vote_general_count.append(r[1])
    #print("canditate_list=", canditate_list)
    #print("vote_general_count=", vote_general_count)
    fig = go.Figure([go.Bar(x=canditate_list, y=vote_general_count)])
    fig.update_layout(title='General Election Vote Count for POTUS Election 2016', xaxis={'title': 'Candidate Names'}, yaxis={'title': 'Popular Vote'})
    fig.write_html("general-election.html", auto_open=True)

    #2
    query = f'SELECT cand, votes FROM pres16results WHERE st = "{chosen_state.short_name}" and county = "NA" ORDER BY votes DESC LIMIT 4'
    result = cursor.execute(query).fetchall()
    #print(result)
    canditate_list = []
    vote_state_count = []
    for r in result:
        canditate_list.append(r[0])
        vote_state_count.append(r[1])
    fig = go.Figure([go.Bar(x=canditate_list, y=vote_state_count)])
    fig.update_layout(title=f'{chosen_state.name.title()} Election Vote Count for POTUS Election 2016', xaxis={'title': 'Candidate Names'}, yaxis={'title': 'Popular Vote'})
    fig.write_html("state-election.html", auto_open=True)

    # Unemployment dataset does not include these 3 states (and did not mention that in the description!)
    if chosen_state.name in ["florida", "alaska", "georgia"]:
        print("Sorry, unemployment data was not provided. Please check Bureau of Labor Statitics")
        return

    #3
    query = f'SELECT Year, AVG(Rate) as avgRate FROM (SELECT * FROM Unemployment WHERE lower(State) = "{chosen_state.name}") GROUP BY year '
    result = cursor.execute(query).fetchall()
    #print("==========\n","query=", query, "result=", result)
    year_list = []
    state_unemployment_list = []
    for r in result:
        year_list.append(r[0])
        state_unemployment_list.append(r[1])
    fig = go.Figure([go.Bar(x=year_list, y=state_unemployment_list)])
    fig.update_layout(title=f'{chosen_state.name.title()}\'s Average Unemployment Rate Across Time ', xaxis={'title': 'Year'}, yaxis={'title': 'Unemployment Average Rate'})
    fig.write_html("state-unemployment.html", auto_open=True)

    """
    SELECT * FROM (SELECT County, AVG(Rate) as avgRate FROM (SELECT * FROM Unemployment WHERE Year = 2016 AND State = "Michigan") GROUP BY County ORDER BY avgRate DESC LIMIT 10) as countyRates JOIN (SELECT * FROM pres16results WHERE st = "MI") as presElectionState on countyRates.County = presElectionState.county
    """

    # 4 
    query = f'SELECT County, AVG(Rate) as avgRate FROM (SELECT * FROM Unemployment WHERE Year = 2016 AND lower(State) = "{chosen_state.name}") GROUP BY County ORDER BY avgRate DESC LIMIT 10'
    result = cursor.execute(query).fetchall()
    #print("==========\n","query=", query, "result=", result)
    county_list = []
    unemployment_rate = []
    for r in result:
        county_list.append(r[0])
        unemployment_rate.append(r[1])
    fig = go.Figure([go.Bar(x=county_list, y=unemployment_rate)])
    fig.update_layout(title=f'Top 10 Uemployment Rate By County in {chosen_state.name.title()} in 2016', xaxis={'title': 'County Names'}, yaxis={'title': 'Unemployment Rate'})
    fig.write_html("county-unemployment.html", auto_open=True)


    connection.close()



if __name__ == "__main__":
    print('Running votingproject20...')
    cache = load_cache()
    state_urls = build_state_url_dict(cache=cache)
    #print(state_urls)
    state_objects_dict = build_state_object(cache,state_urls)
    while True:
        state_response = input('Type in a state: ').lower()
        if state_response == 'quit':
            sys.exit()
        while state_response not in state_objects_dict.keys():
            print("Hey that's not real state!")
            state_response = input('Type in a state: ').lower()
            if state_response == 'quit':
                sys.exit()
        chosen_state = state_objects_dict[state_response]
        print(chosen_state)
        webbrowser.open(chosen_state.state_url)
        webbrowser.open(chosen_state.covid_url)
        webbrowser.open(chosen_state.state_election_url)
        create_visualizations(chosen_state)

    
