import streamlit as st
from helper import feeds_per_provider, remove_feed_from_provider
import pandas as pd
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from ast import literal_eval

st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊",
)

# Set other pages states to False
st.session_state['add_domains'] = False
st.session_state['edit_domains'] = True
st.session_state['search_domains'] = False
st.session_state['delete_domains'] = False
st.session_state['adding'] = False

st.session_state['add_providers'] = False
st.session_state['edit_providers'] = False
st.session_state['delete_providers'] = False

st.session_state['add_publishers'] = False
st.session_state['edit_publishers'] = False
st.session_state['delete_publishers'] = False

# Set current page states
if "add_feeds" not in st.session_state:
    st.session_state['add_feeds'] = False
if "edit_feeds" not in st.session_state:
    st.session_state['edit_feeds'] = False
if "search_feeds" not in st.session_state:
    st.session_state['search_feeds'] = False
if "delete_feeds" not in st.session_state:
    st.session_state['delete_feeds'] = False

st.sidebar.success("Select a page above.")
select = st.sidebar.selectbox('Select an action', ['All Feeds', 'Feeds per Provider'])

if select == 'All Feeds':   
    st.title("Feeds")

    if st.session_state['add_feeds']:
        st.write("Add new Feed")
        providers = pd.read_csv('dashboard/providers.csv', index_col=0, converters={'Feeds': literal_eval})
        select_provider = st.selectbox('Select a provider', providers['Name'].unique(), help='Select a provider')
        new_feed_name = st.text_input("Name", max_chars=100, help='Enter a name')
        new_feed_url = st.text_input("URL", max_chars=100, help='Enter a URL')
        new_feed_cap = st.number_input("Cap", help='Enter a cap')
        new_feed_description = st.text_input("Description", max_chars=100, help='Enter a description')
        new_feed_status = st.selectbox('Select a status', ['Active', 'Inactive'], help='Select a status')
        col1, col2 = st.columns([1,9])

        if col1.button("Submit", key='ddd'):
            if new_feed_name == '':
                st.error("Please enter a name")
            elif new_feed_name in pd.read_csv('dashboard/feeds.csv')['Name'].unique():
                st.error("This feed already exists")
            elif new_feed_url == '':
                st.error("Please enter a URL")
            else:
                if new_feed_description == '':
                    new_feed_description = 'none'
                df = pd.read_csv('dashboard/feeds.csv', index_col=0)
                df.loc[len(df)] = [len(df), new_feed_name, select_provider, new_feed_url, new_feed_cap, None, None, new_feed_description, new_feed_status]
                df.to_csv('dashboard/feeds.csv')
                providers.loc[providers[providers.Name == select_provider].index[0], "Feeds"].append(new_feed_name)
                providers.to_csv('dashboard/providers.csv')
                st.session_state['add_feeds'] = False   
                st.session_state['search_feeds'] = False
                st.session_state['delete_feeds'] = False
                st.session_state['edit_feeds'] = False
                st.experimental_rerun()
        
        if col2.button("Cancel", key='cancel7'):
            st.session_state['add_feeds'] = False
            st.session_state['search_feeds'] = False
            st.session_state['delete_feeds'] = False
            st.session_state['edit_feeds'] = False
            st.experimental_rerun()

    else:
        df = pd.read_csv('dashboard/feeds.csv', index_col=0)
        df.Cap = df.Cap.astype(int)
        search = st.text_input("Search", key='search_feeds2')
        radio = st.radio("Search by", ('Feed name', 'Provider name'), key='radio11')
        col1, _, col3 = st.columns([1, 1, 1])
        if col1.button("Search", key='search25'):
            st.session_state['add_feeds'] = False
            st.session_state['search_feeds'] = True
            st.session_state['delete_feeds'] = False
            st.session_state['edit_feeds'] = False
            st.experimental_rerun()

        # Change table if search is active
        if st.session_state.search_feeds == True:
            df_search = pd.DataFrame(columns=df.columns)
            if st.session_state['radio11'] == 'Feed name':
                for item in df.iterrows():
                    if search.lower() in item[1]['Name'].lower():
                        df_search.loc[len(df_search)] = item[1]
                df_view = df_search.copy()
            else:
                for item in df.iterrows():
                    if search.lower() in item[1]['Provider'].lower():
                        df_search.loc[len(df_search)] = item[1]
                df_view = df_search.copy()
        else:
            df_view = df.copy()

        if col3.button("Add new Feed", key='add87'):
            st.session_state['add_feeds'] = True
            st.session_state['search_feeds'] = False
            st.session_state['delete_feeds'] = False
            st.session_state['edit_feeds'] = False
            st.experimental_rerun()

        # Set configures for the table
        gd = GridOptionsBuilder.from_dataframe(df_view)
        gd.configure_selection(use_checkbox=True, selection_mode='multiple', groupSelectsChildren=True)
        gd.configure_default_column(flex=1, resizable=False, editable=False, sortable=False, filterable=False, groupable=False)
        gd.configure_column("ID", maxWidth=100, minWidth=100)
        gd.configure_column("Name", maxWidth=100, minWidth=90)
        gd.configure_column("Provider", maxWidth=100, minWidth=90)
        gd.configure_column("Cap", maxWidth=100, minWidth=70)
        gd.configure_column("Domains", maxWidth=120, minWidth=100)
        gd.configure_column("Publisher", maxWidth=120, minWidth=100)
        gd.configure_column("Description", maxWidth=120, minWidth=110)
        gd.configure_column("Status", maxWidth=100, minWidth=80)
        gridoptions = gd.build()
        grid_table = AgGrid(df_view, gridOptions=gridoptions, fit_columns_on_grid_load=True)
        selected_row = grid_table["selected_rows"]

        # Set the indexes of the selected rows
        indexes = []
        for row in selected_row:
            indexes.append(int(row['ID']))

        if st.session_state.edit_feeds == False and st.button('Delete', key='gdelete'):
            if len(indexes) == 0:
                st.error('Please select a row to delete')
            else: 
                st.session_state['add_feeds'] = False
                st.session_state['delete_feeds'] = True
                st.session_state['edit_feeds'] = False
                st.experimental_rerun()

        # Delete the selected rows
        if st.session_state['delete_feeds'] == True:
            flag = False
            for index in indexes:
                if df.loc[index, 'Publisher'] in pd.read_csv('dashboard/publishers.csv')['Name'].unique():
                    flag = True
                    break

            if len(indexes) == 0:
                st.error("Please select Publishers to delete")
                st.session_state['delete_feeds'] = False
                st.session_state['add_feeds'] = False
                st.session_state['edit_feeds'] = False
                st.stop()

            elif flag:
                st.error("🚨🚨🚨 You can't remove feeds that connected to domains! 🚨🚨🚨")
                st.session_state['delete_feeds'] = False
                st.session_state['add_feeds'] = False
                st.session_state['edit_feeds'] = False
            else:
                st.warning("Are you sure?")
                col1, col2 = st.columns([1,10])
                if col1.button("OK", key='delete43'):
                    for index in indexes:
                        remove_feed_from_provider(df.iloc[index]['Name'])
                    
                    df = df.drop(indexes)
                    df.reset_index(drop=True, inplace=True)
                    df.ID = df.index
                    df.to_csv('dashboard/feeds.csv')
                
                    st.session_state['add_feeds'] = False
                    st.session_state['search_feeds'] = False
                    st.session_state['delete_feeds'] = False
                    st.session_state['edit_feeds'] = False
                    st.experimental_rerun()

                if col2.button("Cancel", key='c'):
                    st.session_state['add_feeds'] = False
                    st.session_state['search_feeds'] = False
                    st.session_state['delete_feeds'] = False
                    st.session_state['edit_feeds'] = False
                    st.experimental_rerun()

        if st.session_state.delete_feeds == False and st.button("Edit", key='h'):
            if len(indexes) != 1:
                st.error("Please select only one row")
                st.stop()
            else:                    
                st.session_state['add_feeds'] = False
                st.session_state['delete_feeds'] = False
                st.session_state['edit_feeds'] = True
                st.experimental_rerun()

        # Edit the selected row
        if st.session_state['edit_feeds'] == True:
            if len(indexes) != 1:
                st.error("Please select only one row")
                st.session_state['add_feeds'] = False
                st.session_state['delete_feeds'] = False
                st.session_state['edit_feeds'] = False
                st.stop()

            st.write("Edit Feed")     
            feed_name = st.text_input("Feed Name", value=df.loc[indexes[0], "Name"], disabled=True)
            provider_name = st.text_input("Provider", value=df.loc[indexes[0], "Provider"], disabled=True)
            new_feed_url = st.text_input("URL", value=df.loc[indexes[0], "URL"], disabled=True)
            new_feed_cap = st.number_input("Cap", value = df.loc[indexes[0], "Cap"], step=1, key='cap')
            new_feed_description = st.text_input("Description", value=df.loc[indexes[0], "Description"], key='desc')
            new_feed_status = st.selectbox('Select a status', ['Active', 'Inactive'], key='status')
            col1, col2 = st.columns([1, 10])
            if col1.button("Save", key='save235'):
                if new_feed_url == ""  or new_feed_description == "" or new_feed_cap == "":
                    st.error("Please fill all the fields")
                else:
                    df.loc[indexes[0], "Cap"] = st.session_state['cap']
                    df.loc[indexes[0], "Description"] = st.session_state['desc']
                    df.loc[indexes[0], "Status"] = st.session_state['status']
                    df.to_csv('dashboard/feeds.csv')
                    st.session_state['add_feeds'] = False
                    st.session_state['search_feeds'] = False
                    st.session_state['delete_feeds'] = False
                    st.session_state['edit_feeds'] = False
                    st.experimental_rerun()
            
            if col2.button("Cancel", key='cancel445'):
                st.session_state['add_feeds'] = False
                st.session_state['search_feeds'] = False
                st.session_state['delete_feeds'] = False
                st.session_state['edit_feeds'] = False
                st.experimental_rerun()


if select == 'Feeds per Provider':
    st.session_state['delete_feeds'] = False
    st.session_state['edit_feeds'] = False
    st.session_state['search_feeds'] = False
    st.session_state['add_feeds'] = False
    df = pd.read_csv('dashboard/feeds.csv', index_col=0)
    st.markdown("<br><h2>Feeds per Provider</h2>", unsafe_allow_html=True)
    st.dataframe(feeds_per_provider(df))

