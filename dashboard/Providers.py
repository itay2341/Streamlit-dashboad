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

st.session_state['add_publishers'] = False
st.session_state['edit_publishers'] = False
st.session_state['delete_publishers'] = False

# Set current page states
if "add_providers" not in st.session_state:
    st.session_state['add_providers'] = False
if "edit_providers" not in st.session_state:
    st.session_state['edit_providers'] = False
if "delete_providers" not in st.session_state:
    st.session_state['delete_providers'] = False

st.title("Providers")
st.sidebar.success("Select a page above.")
df = pd.read_csv("dashboard/providers.csv", index_col=0, converters={'Feeds': literal_eval})

gd = GridOptionsBuilder.from_dataframe(df)
gd.configure_selection(
    use_checkbox=True, selection_mode='multiple', groupSelectsChildren=True)
gd.configure_column("Feeds", maxWidth=500, minWidth=300)
gd.configure_column("ID", maxWidth=100, minWidth=50)
gd.configure_default_column(flex=1, resizable=False, editable=False,
                            sortable=False, filterable=False, groupable=False)
gridoptions = gd.build()
grid_table = AgGrid(df, gridOptions=gridoptions, fit_columns_on_grid_load=True)
selected_row = grid_table["selected_rows"]

indexes = []
for row in selected_row:
    indexes.append(int(row['_selectedRowNodeInfo']['nodeRowIndex']))

col1, col2, col3 = st.columns([1, 1, 1])

if col1.button('Delete', key="delete"):
    if len(indexes) == 0:
        st.session_state['add_providers'] = False
        st.session_state['edit_providers'] = False
        st.error('Please select row to delete')
    else:
        st.session_state['delete_providers'] = True
        st.session_state['add_providers'] = False
        st.session_state['edit_providers'] = False
        st.experimental_rerun()

if col2.button("Edit", key="edit909"):
    st.session_state['edit_providers'] = True
    st.session_state['add_providers'] = False
    st.session_state['delete_providers'] = False
    st.experimental_rerun()

if col3.button("Add New Provider", key="ADD"):
    st.session_state['add_providers'] = True
    st.session_state['delete_providers'] = False
    st.session_state['edit_providers'] = False
    st.experimental_rerun()

# Delete row/rows
if st.session_state['delete_providers']:
    flag = False
    for index in indexes:
        for feed in df.loc[index, "Feeds"]:
            if feed in pd.read_csv("dashboard/feeds.csv", index_col=0).Name.values:
                flag = True
                break

    if len(indexes) == 0:
        st.error('Please select row to delete')
        st.session_state['delete_providers'] = False
        st.session_state['add_providers'] = False
        st.session_state['edit_providers'] = False
        st.stop()

    elif flag:
        st.warning("Some Providers have Feeds. Please delete them first.")
        st.session_state['delete_providers'] = False
        st.session_state['add_providers'] = False
        st.session_state['edit_providers'] = False
        st.stop()
    else:
        st.warning("Are you sure?")
        col1, col2 = st.columns([1, 10])

        if col1.button("OK", key="ok3"):
            df = df.drop(indexes)
            df.reset_index(drop=True, inplace=True)
            df.ID = range(len(df))
            df.to_csv("dashboard/providers.csv")
            st.session_state['delete_providers'] = False
            st.session_state['add_providers'] = False
            st.session_state['edit_providers'] = False
            st.experimental_rerun()

        if col2.button("Cancel", key="cancel3"):
            st.session_state['delete_providers'] = False
            st.session_state['add_providers'] = False
            st.session_state['edit_providers'] = False
            st.experimental_rerun()

# Add new provider
if st.session_state['add_providers']:
    st.write("Add new Provider")
    provider_name = st.text_input("Provider Name")
    col1, col2 = st.columns([1, 10])
    if col1.button("Save", key="save2"):
        if provider_name == "":
            st.error("Please enter a name")
        elif provider_name in df.Name.values:
            st.error("This name already exists")
        else:
            df.loc[len(df)] = [len(df), provider_name, []]
            df.to_csv("dashboard/providers.csv")
            st.session_state['add_providers'] = False
            st.session_state['delete_providers'] = False
            st.session_state['edit_providers'] = False
            st.experimental_rerun()

    if col2.button("Cancel", key="cancel2"):
        st.session_state['add_providers'] = False
        st.session_state['delete_providers'] = False
        st.session_state['edit_providers'] = False
        st.experimental_rerun()

# Edit provider
if st.session_state['edit_providers']:

    if len(indexes) != 1:
        st.error("Please select only one row")
        st.session_state['delete_providers'] = False
        st.session_state['add_providers'] = False
        st.session_state['edit_providers'] = False
        st.stop()

    st.write("Edit Provider")
    new_provider_name = st.text_input(
        label="Provider name", value=df.loc[indexes[0], "Name"])

    col1, col2 = st.columns([1, 10])
    if col1.button("Save", key="save1"):
        if new_provider_name == "":
            st.error("Please enter a name")
        elif new_provider_name in df.Name.values:
            st.error("This name already exists")
        else:
            f = pd.read_csv('dashboard/feeds.csv', index_col=0)
            f.Provider = f.Provider.apply(
                lambda p: p if p != df.loc[indexes[0], "Name"] else new_provider_name)
            df.loc[indexes[0], "Name"] = new_provider_name
            df.to_csv("dashboard/providers.csv")
            f.to_csv('dashboard/feeds.csv')
            st.session_state['edit_providers'] = False
            st.session_state['delete_providers'] = False
            st.session_state['add_providers'] = False
            st.experimental_rerun()

    if col2.button("Cancel", key="cancel1"):
        st.session_state['edit_providers'] = False
        st.session_state['delete_providers'] = False
        st.session_state['add_providers'] = False
        st.experimental_rerun()
