# import streamlit as st
# import pandas as pd
# from ast import literal_eval
from helper import *
from datetime import date
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import time
import threading

st.set_page_config(
    page_title="Dashboard",
    initial_sidebar_state="expanded",
    page_icon="📊",
    layout="wide"
)

# Set other pages states to False
st.session_state['add_feeds'] = False
st.session_state['edit_feeds'] = False
st.session_state['search_feeds'] = False
st.session_state['delete_feeds'] = False

st.session_state['add_providers'] = False
st.session_state['edit_providers'] = False
st.session_state['delete_providers'] = False

st.session_state['add_publishers'] = False
st.session_state['edit_publishers'] = False
st.session_state['delete_publishers'] = False

# Set current page states
if "add_domains" not in st.session_state:
    st.session_state['add_domains'] = False
if "edit_domains" not in st.session_state:
    st.session_state['edit_domains'] = True
if "search_domains" not in st.session_state:
    st.session_state['search_domains'] = False
if "delete_domains" not in st.session_state:
    st.session_state['delete_domains'] = False
if "adding" not in st.session_state:
    st.session_state['adding'] = False

st.title("Domains")
st.sidebar.success("Select a page above.")
select = st.sidebar.selectbox('Select an action', ['Domains', 'OverView'], key='_selector')

if select == 'Domains':
    st.session_state['search_domains'] = False

    df = load_domains_from_file('dashboard/save')
    # save_domains_to_files(df)

    if st.session_state['edit_domains']:
        if st.session_state['adding'] == False:
            i = 0
        else:
            i = df.Name.unique().tolist().index(st.session_state['adding'])
            # st.session_state['adding'] = False
        selector_domain = st.selectbox('Select a domain', df.Name.unique().tolist(), key='selector_domain', on_change=clear_session_state, index=i)

        indexes = df[df.Name == selector_domain].index.tolist()

        col1, col2 = st.columns([1,9])

        if col1.button('Delete', key='delete4'):
            st.session_state['delete_domains'] = True
            st.session_state['add_domains'] = False
            st.session_state['search_domains'] = False
            st.session_state['edit_domains'] = True
            st.session_state['adding'] == False
            st.experimental_rerun()

        if col2.button("Add new Domain", key='add8'):
            st.session_state['add_domains'] = True
            st.session_state['delete_domains'] = False
            st.session_state['search_domains'] = False
            st.session_state['edit_domains'] = False
            st.session_state['adding'] == False
            st.experimental_rerun()
        
        if st.session_state['delete_domains']: 
            st.warning("Are you sure you want to delete this domain?")
            col1, col2 = st.columns([1,10])
            if col1.button("OK", key='dd'):

                feeds = pd.read_csv('dashboard/feeds.csv', index_col=0)
                for index in indexes:
                    feeds = feeds.apply(lambda x: desconnect_feeds_from_domain(x, df.loc[index].Name), axis=1)
                feeds.to_csv('dashboard/feeds.csv')
                
                df = df.drop(indexes)
                df.reset_index(drop=True, inplace=True)
                df.ID = range(len(df))

                publishers = pd.read_csv('dashboard/publishers.csv', index_col=0, converters={'Domains': literal_eval})
                publishers.Domains = publishers.Domains.apply(lambda x: change_domains(x, df.Name.unique().tolist()))
                publishers.to_csv('dashboard/publishers.csv')
                save_domains_to_files(df)

                st.session_state['delete_domains'] = False
                st.session_state['search_domains'] = False
                st.session_state['add_domains'] = False
                st.session_state['edit_domains'] = True

                progress_thread = threading.Thread(target=deploy_cloud_function, args=(selector_domain,))
                progress_thread.start()

                progress_text = "Operation in progress. Please wait."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                st.success("Domain deleted successfully")
                time.sleep(1)
                st.experimental_rerun()

            if col2.button("Cancel", key='cc'):
                st.session_state['delete_domains'] = False
                st.session_state['search_domains'] = False
                st.session_state['add_domains'] = False
                st.session_state['edit_domains'] = True
                st.experimental_rerun()
    
        tab1, tab2 = st.tabs(["📈 Details", "🗃 Revenue share"])

        with tab1:
            publisher = tab1.text_input('Publisher',value=df.loc[indexes[0], "Publisher"], disabled=True)
            name = tab1.text_input("Name",value=df.loc[indexes[0], "Name"])
            feeds = pd.read_csv("dashboard/feeds.csv").Name.unique().tolist()
            arr = dict()
            for index in indexes:
                arr[df.loc[index, "Feed"]] = df.loc[index, "Weight"]
            
            selected_feeds = tab1.multiselect('Select feeds',default=arr.keys(), options=feeds, key='selected_feeds')
            
            for item in selected_feeds:
                if item in arr.keys():
                    tab1.slider(item, 1, 100, value=int(arr[item]), key=item, help="Select a weight for the feed")
                else:
                    tab1.slider(item, 1, 100, value=5, key=item, help="Select a weight for the feed")
            
            if tab1.button("Save", key='save503'):
                if name == "":
                    tab1.error("Please enter name")
                    st.stop()
                elif name in df.Name.values and name != df.loc[indexes[0], "Name"]:
                    tab1.error("This name already exists")
                    st.stop()
                if len(selected_feeds) == 0:
                    tab1.error("Please choose feeds")
                    st.stop()
                elif name != df.loc[indexes[0], "Name"]:
                    publishers = pd.read_csv('dashboard/publishers.csv', index_col=0)
                    publishers['Domains'] = publishers['Domains'].apply(literal_eval)
                    publishers.Domains = publishers.Domains.apply(lambda x: change_domain_name_on_publishers(x, df.loc[indexes[0], "Name"], name))
                    publishers.to_csv('dashboard/publishers.csv')
                    feeds = pd.read_csv('dashboard/feeds.csv', index_col=0)
                    feeds = feeds.apply(lambda x: change_domain_name_and_publisher_on_feeds(x, df.loc[indexes[0], "Name"], name), axis=1)
                    feeds.to_csv('dashboard/feeds.csv')
                    df.loc[indexes, "Name"] = name
                    save_domains_to_files(df)
                
                df = load_domains_from_file('dashboard/save')
                df_feeds = pd.DataFrame(columns=['ID', 'Name', 'Publisher'
                , 'URL', 'Feed', 'Weight'])
                for selected in selected_feeds:
                    df_feeds.loc[len(df_feeds)] = [1, name, publisher, get_url_from_feed(selected), selected, st.session_state[selected]]
                df_feeds.reset_index(drop=True, inplace=True)
                df_feeds.ID = range(len(df_feeds))
                df = df.drop(indexes)
                df.reset_index(drop=True, inplace=True)
                df.ID = range(len(df))
                for row in df_feeds.iterrows():
                    df.loc[len(df)] = [len(df), row[1]['Name'], row[1]['Publisher'], row[1]['URL'], row[1]['Feed'], row[1]['Weight']]
                df.reset_index(drop=True, inplace=True)
                df.ID = range(len(df))
                save_domains_to_files(df)

                feeds = pd.read_csv('dashboard/feeds.csv', index_col=0)
                ind = 0
                feeds_names_connected_to_this_domain = feeds[feeds.Domains == name].Name.unique().tolist()
                for feed_selected in selected_feeds:
                    if feed_selected in feeds_names_connected_to_this_domain: continue
                    flag = True
                    for _, row in feeds.iterrows():
                        if row['Name'] == feed_selected and row['Publisher'] not in pd.read_csv('dashboard/publishers.csv').Name.unique().tolist():
                            ind = row['ID']
                            flag = False
                            break
                    if flag:
                        feeds.loc[len(feeds)] = [len(feeds), feed_selected, get_provider_name_from_feed(feed_selected), get_url_from_feed(feed_selected), 100, name, publisher, 'none', 'Active']
                    else:
                        feeds.loc[ind, 'Publisher'] = publisher
                        feeds.loc[ind, 'Domains'] = name
                arr = [feed for feed in feeds_names_connected_to_this_domain if feed not in selected_feeds]
                for feed in arr:
                    feeds = feeds.apply(lambda x: desconnect_feed_from_domain(x, name, feed), axis=1)
                feeds.reset_index(drop=True, inplace=True)
                feeds.ID = range(len(feeds))
                feeds.to_csv('dashboard/feeds.csv')
                st.session_state['delete_domains'] = False
                st.session_state['search_domains'] = False
                st.session_state['add_domains'] = False
                st.session_state['edit_domains'] = True

                progress_thread = threading.Thread(target=deploy_cloud_function, args=(name,))
                progress_thread.start()
                # progress_thread.join()
                progress_text = "Operation in progress. Please wait."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                st.success("Domain updated successfully")
                time.sleep(1)
                st.experimental_rerun()

        with tab2:
            profit_table = pd.read_json('profit_table.json')
            profit_table = profit_table[profit_table['Domain Name'] == df.loc[indexes[0], "Name"]]

            gd = GridOptionsBuilder.from_dataframe(profit_table)
            gd.configure_selection(use_checkbox=True, selection_mode='single', groupSelectsChildren=True)
            gd.configure_default_column(flex=1, resizable=False, editable=False, sortable=False, filterable=False, groupable=False)
            gridoptions = gd.build()
            grid_table = AgGrid(profit_table, gridOptions=gridoptions, fit_columns_on_grid_load=True)
            selected_row = grid_table["selected_rows"]
           
            index_to_delete = []
            for row in selected_row:
                index_to_delete.append(int(row['ID']))
            if len(index_to_delete) > 0:
                if tab2.button("Delete", key='delete_revenue_share'):
                    profit_table = profit_table.drop(index_to_delete)
                    profit_table.reset_index(drop=True, inplace=True)
                    profit_table.ID = range(len(profit_table))
                    profit_table.to_json('profit_table.json')
                    st.session_state['edit_domains'] = True
                    st.session_state['delete_domains'] = False
                    st.session_state['search_domains'] = False
                    st.session_state['add_domains'] = False
                    deploy_revenue_share(profit_table)
                    st.experimental_rerun()
            tab2.subheader("Add new revenue share")
            revenue_share = tab2.number_input("Revenue Share", value=0.0, key='revenue_share')
            rev_date = tab2.date_input("Date", value=date.today(), key='date')

            if tab2.button("Add", key='add_revenue_share'):
                profit_table = pd.read_json('profit_table.json')
                profit_table.loc[len(profit_table)] = [len(profit_table), rev_date,df.loc[indexes[0], "Publisher"], selector_domain, revenue_share]
                profit_table.reset_index(drop=True, inplace=True)
                profit_table.ID = range(len(profit_table))
                profit_table.to_json('profit_table.json')
                st.session_state['edit_domains'] = True
                st.session_state['delete_domains'] = False
                st.session_state['search_domains'] = False
                st.session_state['add_domains'] = False
                progress_thread = threading.Thread(target=deploy_revenue_share, args=(profit_table,))
                progress_thread.start()
                # progress_thread.join()
                progress_text = "Operation in progress. Please wait."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(.01)
                    my_bar.progress(percent_complete + 1, text=progress_text)
                st.success("Revenue Share updated successfully")
                time.sleep(1)
                st.experimental_rerun()
    
    elif st.session_state['add_domains']:
     
        col1, col2 = st.columns([1,4])
        col1.write("Add new Domain")
        if col2.button("Cancel & Back", key='cancel341'):
            st.session_state['delete_domains'] = False
            st.session_state['search_domains'] = False
            st.session_state['add_domains'] = False
            st.session_state['edit_domains'] = True
            st.experimental_rerun()
        
        tab1, tab2 = st.tabs(["📈 Details", "🗃 Revenue share"])
        
        tab1.subheader("Details")
        name = tab1.text_input("Name", key='name', help="Enter a name for the domain")
        selector = pd.read_csv("dashboard/publishers.csv").Name.tolist()
        publisher = tab1.selectbox('Publisher', selector, key='publisher', help="Select a publisher for the domain")
        feeds = pd.read_csv("dashboard/feeds.csv").Name.unique().tolist()
        selected_feeds = tab1.multiselect('Feeds', feeds, help="Select feeds for the domain")

        tab2.subheader("Revenue share")
        tab2.number_input("Revenue share", key='revenue_share', min_value=1, max_value=100, value=80)
        tab2.date_input("Date", key='start_date')
        
        feeds_dict = {}
        for selected in selected_feeds:
            feeds_dict[selected] = tab1.slider(selected, 1, 100, 5, key=selected, help="Select a weight for the feed")
        df_feeds = pd.DataFrame(columns=['ID', 'Name', 'Publisher'
            , 'URL', 'Feed', 'Weight'])
        for key, value in feeds_dict.items():
            df_feeds.loc[len(df_feeds)] = [1, st.session_state['name'], st.session_state['publisher'], get_url_from_feed(st.session_state['name']), key, value]
        df_feeds.reset_index(drop=True, inplace=True)
        df_feeds.ID = range(len(df_feeds))

        if tab1.button("Save", key='23save'):

                if name == '':
                    st.error("Please enter name")
                elif name in df.Name.values:
                    st.error("This name already exists")
                elif len(selected_feeds) == 0:
                    st.error("Please choose feeds")

                else:
                    publishers = pd.read_csv('dashboard/publishers.csv', index_col=0)
                    publishers['Domains'] = publishers['Domains'].apply(literal_eval)
                    ind = 0
                    for row in publishers.iterrows():
                        if row[1]['Name'] == st.session_state['publisher']:
                            ind = row[1]['ID']
                            break
                    
                    publishers.loc[ind, 'Domains'].append(st.session_state['name'])
                    publishers.to_csv('dashboard/publishers.csv')

                    feeds = pd.read_csv('dashboard/feeds.csv', index_col=0)
                    for feed_selected in selected_feeds:
                        flag = False
                        for row in feeds.iterrows():
                            if row[1]['Name'] == feed_selected and row[1]['Publisher'] not in pd.read_csv('dashboard/publishers.csv').Name.unique().tolist():
                                flag = True
                                ind = row[1]['ID']
                                break
                        if flag:
                            feeds.loc[ind, 'Publisher'] = st.session_state['publisher']
                            feeds.loc[ind, 'Domains'] = st.session_state['name']
                        else:
                            feeds.loc[len(feeds)] = [len(feeds), feed_selected, get_provider_name_from_feed(feed_selected), get_url_from_feed(feed_selected), 100, st.session_state['name'], st.session_state['publisher'], 'none', 'Active']


                    feeds.reset_index(drop=True, inplace=True)
                    feeds.ID = range(len(feeds))
                    feeds.to_csv('dashboard/feeds.csv')

                    profit_table = pd.read_json('profit_table.json')
                    profit_table.loc[len(profit_table)] = [len(profit_table), st.session_state['start_date'],st.session_state['publisher'], st.session_state['name'], st.session_state['revenue_share']]
                    profit_table.reset_index(drop=True, inplace=True)
                    profit_table.ID = range(len(profit_table))
                    profit_table.to_json('profit_table.json')

                    df = load_domains_from_file('dashboard/save')
                    for row in df_feeds.iterrows():
                        df.loc[len(df)] = [len(df), row[1]['Name'], row[1]['Publisher'], get_url_from_feed(row[1]['Feed']), row[1]['Feed'], row[1]['Weight']]
                    df.reset_index(drop=True, inplace=True)
                    df.ID = range(len(df))
                    save_domains_to_files(df)
                    st.session_state['delete_domains'] = False
                    st.session_state['search_domains'] = False
                    st.session_state['add_domains'] = False
                    st.session_state['edit_domains'] = True
                    st.session_state['adding'] = name

                    progress_thread = threading.Thread(target=deploy_cloud_function, args=(name,))
                    progress_thread.start()
                    progress_thread_rev = threading.Thread(target=deploy_revenue_share, args=(profit_table,))
                    progress_thread_rev.start()

                    progress_text = "Operation in progress. Please wait."
                    my_bar = st.progress(0, text=progress_text)
                    for percent_complete in range(100):
                        time.sleep(.01)
                        my_bar.progress(percent_complete + 1, text=progress_text)
                    st.success("Domain added successfully")
                    time.sleep(1)
                    st.experimental_rerun()
                    


if select == 'OverView':
    st.session_state['add_domains'] = False
    st.session_state['delete_domains'] = False
    st.session_state['edit_domains'] = True

    df = load_domains_from_file('dashboard/save')
    search = st.text_input("Search", key='search1')
    radio = st.radio("Search by", ('Domain name', 'Publisher name'), key='radio1')

    if st.button("Search", key='search2'):
        st.session_state['search_domains'] = True
        st.session_state['add_domains'] = False
        st.session_state['delete_domains'] = False
        st.session_state['edit_domains'] = True
        st.experimental_rerun()
    
    if st.session_state.search_domains == True:
        df_search = pd.DataFrame(columns=df.columns)
        if st.session_state['radio1'] == 'Domain name':
            for item in df.iterrows():
                if search.lower() in item[1]['Name'].lower():
                    df_search.loc[len(df_search)] = item[1]
            df_view = df_search.copy()
        else:
            for item in df.iterrows():
                if search.lower() in item[1]['Publisher'].lower():
                    df_search.loc[len(df_search)] = item[1]
            df_view = df_search.copy()
    else: 
        df_view = df.copy() 

    st.write(df_view)
    st.write("Domains per Publisher")
    st.write(domains_per_publisher(df))

    st.write("Suffixes and Prefixes of domains")
    st.write(suffixes_and_prefixes(df))

