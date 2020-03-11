import networkx as nx
import itertools

def user_interaction(collection):
    """
    Function to tally up user interactions in general tweets, retweets, and quote/replies
    :collection -> MongoDB collection obtained through find()
    """
    nm = {} # normal mentions
    rm = {} # retweet mentions
    qm = {} # quote and reply mentions

    for tweet in collection:
        tweeter = tweet["user"]["screen_name"]

        # RETWEETS
        if tweet.get("retweeted_status"):
            rt_user = tweet["retweeted_status"]["user"]["screen_name"]
            if not rm.get(tweeter):
                rm[tweeter] = {rt_user: 1}
            else:
                if not rm[tweeter].get(rt_user):
                    rm[tweeter][rt_user] = 1
                else:
                    rm[tweeter][rt_user] += 1

        # QUOTES
        if tweet.get("quoted_status"):
            q_user = tweet["quoted_status"]["user"]["screen_name"]
            if not qm.get(tweeter):
                qm[tweeter] = {q_user: 1}
            else:
                if not qm[tweeter].get(q_user):
                    qm[tweeter][q_user] = 1
                else:
                    qm[tweeter][q_user] += 1

        # REPLIES
        r_user = tweet.get("in_reply_to_screen_name", None)
        if r_user is not None:
            if not qm.get(tweeter):
                qm[tweeter] = {r_user: 1}
            else:
                if not qm[tweeter].get(r_user):
                    qm[tweeter][r_user] = 1
                else:
                    qm[tweeter][r_user] += 1

        # NORMAL
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


def hashtag_interaction(collection):
    """
    Function to tally up hashtag co-occurence information ("interaction")
    :collection -> MongoDB collection obtained through find()
    """
    hashtags = []

    for tweet in collection:
        tweet = get_body(tweet)
        if tweet["entities"].get("hashtags"):
            current = []
            for h in tweet["entities"]["hashtags"]:
                current.append(h["text"].lower())
            hashtags.append(sorted(current))

    return hashtags

def get_network_information(G):
    """
    Function to get basic network information
    :G -> graph built with networkx
    """

    nodes = G.number_of_nodes()
    edges = G.number_of_edges()
    Gu = G.to_undirected()
    ncc = nx.number_connected_components(Gu)
    print("Number of nodes: {}".format(nodes))
    print("Number of edges: {}".format(edges))
    print("Number of subgraphs: {}".format(ncc))
    print("Average group size: {}".format(nodes//ncc))

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
                        ties += sum(1 for ignore in itertools.combinations(tag_list, 2))
                    if len(tag_list) > 2:
                        triads += sum(1 for ignore in itertools.combinations(tag_list, 3))
                for h in tag_list:
                    for other in tag_list:
                        if h != other:
                            for visited_list in visited:
                                if other in visited_list:
                                    triads += len(visited_list)-1
                visited.append(tag_list)

    return ties, triads

def user_network_statistics(users):
    """
    Function to get ties/loops/triads/transitive information from a directed user network
    :users -> dictionary of user connections obtained with user_interaction()
    """

    ties = 0
    triads = 0
    transitive = 0
    links = 0
    visited = set()
    for user, friends in users.items():
        if len(friends)==2:
            triads += 1
        elif len(friends) > 2:
            triads += sum(1 for ignore in itertools.combinations(friends, 3))
        for friend in friends:
            links += 1
            if users.get(friend):
                if users[friend].get(user):
                    if (user, friend) not in visited:
                        ties += 1
                        transitive += len(users[friend])
                        if len(users[friend]) > 2:
                            triads += sum(1 for ignore in itertools.combinations(users[friend], 3))
                        else:
                            triads += 1
            visited.add((user, friend))
            visited.add((friend, user))

    print("ties", "links", "transitive", "triads")
    return ties, links, transitive, triads
