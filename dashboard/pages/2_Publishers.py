import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from ast import literal_eval

st.set_page_config(
    page_title="Dashboard",
    initial_sidebar_state="expanded",
    page_icon="📊",
    layout="wide"
)

# Set other pages states to False
st.session_state['add_domains'] = False
st.session_state['edit_domains'] = True
st.session_state['search_domains'] = False
st.session_state['delete_domains'] = False
st.session_state['adding'] = False

st.session_state['add_feeds'] = False
st.session_state['edit_feeds'] = False
st.session_state['search_feeds'] = False
st.session_state['delete_feeds'] = False

st.session_state['add_providers'] = False
st.session_state['edit_providers'] = False
st.session_state['delete_providers'] = False


# Set current page states
if "add_publishers" not in st.session_state:
    st.session_state['add_publishers'] = False
if "edit_publishers" not in st.session_state:
    st.session_state['edit_publishers'] = False
if "delete_publishers" not in st.session_state:
    st.session_state['delete_publishers'] = False

st.title("Publishers")
st.sidebar.success("Select a page above.")

df = pd.read_csv("dashboard/publishers.csv", index_col=0, converters={'Domains': literal_eval})

gd = GridOptionsBuilder.from_dataframe(df)
gd.configure_selection(use_checkbox=True, selection_mode='multiple', groupSelectsChildren=True)
gd.configure_column("Domains", maxWidth=500, minWidth=300)
gd.configure_column("ID", maxWidth=100, minWidth=50)
gd.configure_default_column(flex=1, resizable=False, editable=False, sortable=False, filterable=False, groupable=False)
gridoptions = gd.build()
grid_table = AgGrid(df, gridOptions=gridoptions, fit_columns_on_grid_load=True)
selected_row = grid_table["selected_rows"]

indexes = []
for row in selected_row:
    indexes.append(int(row['_selectedRowNodeInfo']['nodeRowIndex']))

col1, col2, col3 = st.columns([1,1,1])

if col1.button('Delete', key="delete9"):
    if len(indexes) == 0:
        st.error('Please select row to delete')
    else:
        st.session_state['delete_publishers'] = True
        st.session_state['edit_publishers'] = False
        st.session_state['add_publishers'] = False
        st.experimental_rerun()

if col2.button("Edit", key="edit_publishers2"):
    st.session_state['edit_publishers'] = True
    st.session_state['delete_publishers'] = False
    st.session_state['add_publishers'] = False
    st.experimental_rerun()

if col3.button("Add New Publisher", key="add_publishers78"):
    st.session_state['add_publishers'] = True
    st.session_state['delete_publishers'] = False
    st.session_state['edit_publishers'] = False
    st.experimental_rerun()

# Delete row/rows
if st.session_state['delete_publishers']:
    flag = False
    for index in indexes:
        for domain in df.loc[index, "Domains"]:
            if domain in pd.read_csv('dashboard/feeds.csv', index_col=0).Domains.values:
                flag = True
                break

    if len(indexes) == 0:
        st.error('Please select row to delete')
        st.session_state['delete_publishers'] = False
        st.session_state['add_publishers'] = False
        st.session_state['edit_publishers'] = False
        st.stop()
    elif flag:
        st.warning("Some Publishers have Domains. Please delete them first.")
        st.session_state['delete_publishers'] = False
        st.session_state['add_publishers'] = False
        st.session_state['edit_publishers'] = False
        st.stop()
    else:
        st.warning("Are you sure?")
        col1, col2 = st.columns([1,10])
        if col1.button("OK", key="ok34"):
            df = df.drop(indexes)
            df.reset_index(drop=True, inplace=True)
            df.ID = range(len(df))
            df.to_csv("dashboard/publishers.csv")
            st.session_state['delete_publishers'] = False
            st.session_state['add_publishers'] = False
            st.session_state['edit_publishers'] = False
            st.experimental_rerun()

        if col2.button("Cancel", key="cancel34"):
            st.session_state['delete_publishers'] = False
            st.session_state['add_publishers'] = False
            st.session_state['edit_publishers'] = False
            st.experimental_rerun()

# Add new Publisher
if st.session_state['add_publishers']:

    st.write("Add new Publisher")
    new_publisher_name = st.text_input("Publisher name")
    col1, col2 = st.columns([1,10])
    if col1.button("Save", key="save25"):
        if new_publisher_name == "":
            st.error("Please enter a name")
        elif new_publisher_name in df.Name.values:
            st.error("This name already exists")
        else:
            df.loc[len(df)] = [len(df), new_publisher_name, []]
            df.to_csv("dashboard/publishers.csv")
            st.session_state['delete_publishers'] = False
            st.session_state['add_publishers'] = False
            st.session_state['edit_publishers'] = False
            st.experimental_rerun()

    if col2.button("Cancel", key="cancel25"):
        st.session_state['delete_publishers'] = False
        st.session_state['add_publishers'] = False
        st.session_state['edit_publishers'] = False
        st.experimental_rerun()

# Edit Publisher
if st.session_state['edit_publishers']: 

    if len(indexes) != 1:
        st.error("Please select only one row")
        st.session_state['delete_publishers'] = False
        st.session_state['add_publishers'] = False
        st.session_state['edit_publishers'] = False
        st.stop()
    
    st.write("Edit Provider")
    new_publisher_name = st.text_input(label="Publisher name", value=df.loc[indexes[0], "Name"])
    
    col1, col2 = st.columns([1,10])
    if col1.button("Save", key="save411"):

        if new_publisher_name == "":
            st.error("Please enter a name")
        elif new_publisher_name in df.Name.values:
            st.error("This name already exists")
        else:
            f = pd.read_csv('dashboard/feeds.csv', index_col=0)
            f.Publisher = f.Publisher.apply(lambda x: new_publisher_name if x == df.loc[indexes[0], "Name"] else x)
            f.to_csv('dashboard/feeds.csv')

            df.loc[indexes[0], "Name"] = new_publisher_name
            df.to_csv("dashboard/publishers.csv")
            st.session_state['delete_publishers'] = False
            st.session_state['add_publishers'] = False
            st.session_state['edit_publishers'] = False
            st.experimental_rerun()

    if col2.button("Cancel", key="cancel15"):
        st.session_state['delete_publishers'] = False
        st.session_state['add_publishers'] = False
        st.session_state['edit_publishers'] = False
        st.experimental_rerun()

