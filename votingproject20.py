#################################
##### Name: David Josue Molina
##### Uniqname: djmolina 
#################################

from bs4 import BeautifulSoup
import requests
import json
import webbrowser 

base_url = "https://www.vote.org" 

def build_state_url_dict(cache={}):
    state_link ={}
    soup = make_url_request_using_cache( "https://www.vote.org/", cache)
    state_main__page_link_elements = soup.select(".ul-quicklinks li a")
    for link in state_main__page_link_elements:
        # get the link tezt, split on spaces, get rid of last two words (election center), and join back together
        state_name = " ".join(link.text.lower().split()[:-2])
        state_link[state_name] = base_url + link['href']
    return state_link

def build_state_object(cache, state_link):
    '''
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
    def __init__(self, name, state_url, covid_url, state_election_url):
        self.state_url = state_url
        self.name = name
        self.covid_url = covid_url
        self.state_election_url = state_election_url
        
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







if __name__ == "__main__":
    print('Running votingproject20...')
    cache = load_cache()
    state_urls = build_state_url_dict(cache=cache)
    print(state_urls)

    state_objects_dict = build_state_object(cache,state_urls)
    state_response = input('Type in a state: ')
    chosen_state = state_objects_dict[state_response]
    print(chosen_state)
    webbrowser.open(chosen_state.state_url)
    webbrowser.open(chosen_state.covid_url)
    webbrowser.open(chosen_state.state_election_url)

    
