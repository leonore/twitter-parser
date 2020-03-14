import networkx as nx
import itertools

from helpers import get_body

def user_interaction(collection, condition={"$exists": True}):
    """
    Function to tally up user interactions in general tweets, retweets, and quote/replies
    :collection -> MongoDB collection obtained through find()
    """
    nm = {} # normal mentions
    rm = {} # retweet mentions
    qm = {} # quote and reply mentions

    for tweet in collection.find({"sentiment": condition}):
        tweeter = tweet["user"]["screen_name"]

        # RETWEETS
        if tweet.get("retweeted_status"):
            rt_user = tweet["retweeted_status"]["user"]["screen_name"]
            if not rm.get(tweeter): # we haven't seen this user yet, add this mention as his first
                rm[tweeter] = {rt_user: 1}
            else: # we have seen this user
                if not rm[tweeter].get(rt_user): # but not the user he has retweeted
                    rm[tweeter][rt_user] = 1
                else: # this user has already retweeted from this person, increment tally
                    rm[tweeter][rt_user] += 1

        # QUOTES
        if tweet.get("quoted_status"):
            q_user = tweet["quoted_status"]["user"]["screen_name"]
            if not qm.get(tweeter): # we haven't seen this user yet, add this mention as his first
                qm[tweeter] = {q_user: 1}
            else: # we have seen this user
                if not qm[tweeter].get(q_user):  # but not the user he has quoted
                    qm[tweeter][q_user] = 1
                else: # this user has already quoted this person, increment tally
                    qm[tweeter][q_user] += 1

        # REPLIES: same thinking as quotes
        r_user = tweet.get("in_reply_to_screen_name", None)
        if r_user is not None:
            if not qm.get(tweeter):
                qm[tweeter] = {r_user: 1}
            else:
                if not qm[tweeter].get(r_user):
                    qm[tweeter][r_user] = 1
                else:
                    qm[tweeter][r_user] += 1

        # NORMAL: same thinking as above, but go through all the users mentioned in the tweets
        body = get_body(tweet)
        if body['entities'].get("user_mentions"):
            if not nm.get(tweeter):
                nm[tweeter] = {}
            for friend in body["entities"]["user_mentions"]:
                friend = friend["screen_name"]
                if not nm[tweeter].get(friend):
                    nm[tweeter][friend] = 1
                else:
                    nm[tweeter][friend] += 1

    return nm, rm, qm


def hashtag_interaction(collection, condition={"$exists": True}):
    """
    Function to tally up hashtag co-occurence information ("interaction")
    :collection -> MongoDB collection
    """
    hashtags = set() # we use a set so as to not to repeat lists of hashtags

    for tweet in collection.find({"sentiment": condition}):
        tweet = get_body(tweet)
        if tweet["entities"].get("hashtags"):
            current = []
            for h in tweet["entities"]["hashtags"]:
                current.append(h["text"].lower()) # capitalisation of hashtags does not matter
            hashtags.add(sorted(current)) # order of hashtags does not matter

    return hashtags

def build_interaction_graph(s):
    if type(s) is dict: # user network, we have direction information
        G = nx.DiGraph()
        for user, friends in s.items():
            for f, m in friends.items():
                G.add_edge(user, f, weight=m)

    else: # hashtag network
        G = nx.Graph()
        for ht_list in s:
            for h1 in ht_list:
                G.add_node(h1)
                for h2 in ht_list:
                    if h1 != h2:
                        G.add_edge(h1, h2)

    return G

def get_network_information(G):
    """
    Function to get basic network information
    :G -> graph built with networkx
    return nodes, edges, subgraph #, number of nodes per subgraph
    """

    nodes = G.number_of_nodes()
    edges = G.number_of_edges()
    Gu = G.to_undirected()
    ncc = nx.number_connected_components(Gu) # number of subgraphs
    return nodes, edges, ncc, nodes//ncc

def hashtag_network_statistics(hashtags):
    """
    Function to get ties/triads information from a hashtag network
    :hashtag -> nested lists of hashtags obtained with hashtag_interaction()
    """
    ties = 0
    visited = []
    triads = 0
    for tag_list in hashtags:
        # single used hashtags aren't used in conjuction with others
        if len(tag_list) > 1:
            # we don't want to count duplicates ties or triads
            if tag_list not in visited:
                if len(tag_list) > 1:
                    if len(tag_list) >= 2:
                        # get all (non-ordered, non-repetitive) combinations of 2 (a tie) from the list
                        ties += sum(1 for ignore in itertools.combinations(tag_list, 2))
                    if len(tag_list) > 2:
                        # get all (non-ordered, non-repetitive) combinations of 3 (a triad) from the list
                        triads += sum(1 for ignore in itertools.combinations(tag_list, 3))
                for h in tag_list: # compare each hashtag to other hashtags in its list
                    for other in tag_list:
                        if h != other:
                            for visited_list in visited: # if the other hashtag has been mentioned in another list
                                if other in visited_list:
                                    triads += len(visited_list)-1 # create the appropriate number of triads (A-B-X for X in B's hashtag list)
                visited.append(tag_list)

    return triads, ties

def user_network_statistics(users):
    """
    Function to get ties/loops/triads/transitive information from a directed user network
    :users -> dictionary of user connections obtained with user_interaction()
    """

    loops = 0
    triads = 0
    transitive = 0
    links = 0
    visited = set()
    for user, friends in users.items():
        if len(friends)==2: # user A: user B, user C = one triad
            triads += 1
        elif len(friends) > 2: # user A: B, C, D, E --> get all non-ordered, non-repetitive combinations of 3 (2 + main user) from the list
            triads += sum(1 for ignore in itertools.combinations(friends, 2))
        for friend in friends:
            links += 1 # create a new link for all the users he has mentioned
            if users.get(friend):
                if users[friend].get(user):
                    if (user, friend) not in visited: # if we haven't seen this pair of users yet
                        loops += 1 # they have both mentioned each other
                        transitive += len(users[friend]) # B is the transitive link for A with his mentions
                        triads += len(users[friend]) # create the appropriate number of triads (A-B-X for X in B's hashtag list)
            visited.add((user, friend))
            visited.add((friend, user))

    return triads, loops, links, transitive
