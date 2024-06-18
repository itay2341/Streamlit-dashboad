import streamlit as st
import pandas as pd
import os
import json
from ast import literal_eval

# -----------------Feeds-----------------
def feeds_per_provider(df):
    """
    Get the Feeds (DataFrame)
    Return DataFrame with the number of feeds per provider.
    """
    res = df.groupby(['Provider']).agg({'ID': 'count'}).copy()
    res = res.rename(columns={'ID': 'Number of Feeds'})
    res = res.reset_index()
    return res

def remove_feed_from_provider(feed_name):
    """
    When feed is deleted (desconnected feed):
    Delete the feed from the provider.
    """
    providers = pd.read_csv('dashboard/providers.csv', index_col=0, converters={'Feeds': literal_eval})
    for provider in providers.iterrows():
        if feed_name in provider[1]['Feeds']:
            providers.loc[provider[0], "Feeds"].remove(feed_name)
    providers.to_csv('dashboard/providers.csv')


# -----------------Domains-----------------
def domains_per_publisher(df):
    """
    Get the Domains (DataFrame)
    Return DataFrame with the number of domains per publisher
    and the number of feeds per domain."""
    res = df.groupby(['Publisher', 'Name']).agg({'ID':'count'}).copy()
    res = res.rename(columns={'ID': 'Feeds Conected', 'Name': 'Domain Name'})
    res = res.reset_index()
    return res

def desconnect_feed_from_domain(row, domain, feed):
    """
    When desconnect feed from domain:
    Apply this function to Feeds (DataFrame) to desconnect 
    the feed from the domain.
    """
    if row['Domains'] == domain and row['Name'] == feed:
        row['Publisher'] = None
        row['Domains'] = None
    return row

def desconnect_feeds_from_domain(row, domain):
    """
    When domain is deleted: 
    Apply this function to Feeds (DataFrame) to desconnect 
    all the feeds that match the domain.
    """
    if row.Domains == domain:
        row.Domains = None
        row.Publisher = None
    return row

def clear_session_state():
    """
    When domain is selected:
    On change callback to clear session state.
    """
    st.session_state['add'] = False
    st.session_state['button'] = False
    st.session_state['edit_domain'] = True
    st.session_state['Search'] = False

def get_provider_name_from_feed(feed):
    """
    Return provider name of this feed.
    """
    providers = pd.read_csv('dashboard/providers.csv', index_col=0, converters={'Feeds': literal_eval})
    for provider in providers.iterrows():
        for feed_ in provider[1]['Feeds']:
            if feed_ == feed:
                return provider[1]['Name']
    return 'Unknown'

def get_publisher_name_from_domain(domain):
    """
    Return publisher name of this domain.
    """
    publishers = pd.read_csv('dashboard/publishers.csv', index_col=0, converters={'Domains': literal_eval})
    for item in publishers.iterrows():
        if domain in item[1]['Domains']:
            return item[1]['Name']
    return 'Unknown'

def change_domains(domains, new_domains):
    """
    When domain is deleted:
    Apply this function to Publishers (DataFrame) to delete
    the domain from the publisher.
    """
    arr = []
    for i, domain in enumerate(domains):
        if domain not in new_domains:
            arr.append(i)
    for i in arr[::-1]:
        domains.pop(i)
    return domains

def delete_domain_from_publisher(domains, domains_new):
    """
    When feed desconnected from domain:
    Apply this function to Publishers (DataFrame) to delete
    the domain from the publisher if needed."""
    if domains == []:
        return domains
    ind = 0
    for i, domain in enumerate(domains):
        if domain not in domains_new:
            ind = i
            break
    else: domains.pop(ind)
    return domains

def change_domain_name_on_publishers(domains, old, new):
    """
    When domain name is changed:
    Apply this function to Publishers (DataFrame) to change
    the domain name.
    """
    if old not in domains:
        return domains
    ind = 0
    for i, domain in enumerate(domains):
        if domain == old:
            ind = i
            break
    domains[ind] = new
    return domains

def change_domain_name_and_publisher_on_feeds(row, old, new):
    """
    When domain name is changed:
    Apply this function to Feeds (DataFrame) to change
    the domain name and the publisher.
    """
    if old != row['Domains']:
        return row
    row['Domains'] = new
    row['Publisher'] = get_publisher_name_from_domain(new)
    return row


# save and load
def load_domains_from_file(path):
    domains = []
    ind = 0
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            with open(os.path.join(path, filename)) as f:
                domain = json.load(f)
                for i, feed in enumerate(domain['feeds']):
                    if i > 0 and feed['name'] == domain['feeds'][i-1]['name']:
                        domains[-1][-1] += 1
                        continue
                    domains.append([ind, domain['id'], "l", feed['url_format'], feed['name'], 1])
                    ind += 1
    domains = pd.DataFrame(domains, columns=['ID', 'Name', 'Publisher', 'URL', 'Feed' , 'Weight'])
    domains = domains.reset_index(drop=True)
    domains.Publisher = domains.Name.apply(lambda x: get_publisher_name_from_domain(x))
    return domains

def save_domains_to_files(df):
    for filename in os.listdir('dashboard/save'):
        os.remove(os.path.join('dashboard/save', filename))

    domains = df.copy().Name.unique().tolist()
    for domain in domains:
        domain_to_file = {
            "id": str(domain),
            "feeds": []
        }
        feeds_conected_this_domain = df[df.Name == domain].copy()
        for feed in feeds_conected_this_domain.iterrows():
            for _ in range(feed[1]['Weight']):
                domain_to_file['feeds'].append({"name": feed[1]['Feed'],"url_format": feed[1]['URL']})
        with open(os.path.join('dashboard/save', domain + '.json'), 'w') as f:
            json.dump(domain_to_file, f)

def deploy_cloud_function(domain_name):
    print('deploy_cloud_function', domain_name)


def delete_cloud_function(domain_name):
    print('delete_cloud_function', domain_name)

def deploy_revenue_share(df_revuene_share):
    print('deploy_revenue_share', df_revuene_share)

def upload_provider_csv(provider_name, df_provider):
    pass

def on_load():
    pass

def suffixes_and_prefixes(df):
    """
    Get the Suffixes and Prefixes (DataFrame)
    Return DataFrame with the number of suffixes and prefixes per publisher.
    """
    res = df[['Publisher', 'Name']].rename(columns={'Name':'Domain'}).drop_duplicates().copy()
    suffix = 'a'
    prefix = 'b'
    res.Domain = res.Domain.apply(lambda x: suffix + x + prefix)
    return res.sort_values(by=['Publisher', 'Domain']).reset_index(drop=True)

def get_url_from_feed(feed_name):
    """
    Return url of this feed.
    """
    feeds = pd.read_csv('dashboard/feeds.csv', index_col=0)
    for row in feeds.iterrows():
        if feed_name == row[1]['Name']:
            return row[1]['URL']
    return 'Unknown'

def reset_data():
    df = pd.read_json("providers.json")
    df.to_csv('dashboard/providers.csv')

    df = pd.read_json("feeds.json")
    df.to_csv("dashboard/feeds.csv")

    df = pd.read_json("publishers.json")
    df.to_csv("dashboard/publishers.csv")

    df = load_domains_from_file('dashboard/save')
    save_domains_to_files(df)