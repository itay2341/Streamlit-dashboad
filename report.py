# streamlit app to show reports
import streamlit as st
import pandas as pd
import logging
import google.cloud.logging

client = google.cloud.logging.Client()
client.setup_logging()


st.title('Zik Reports')
try:
    report_link = 'gs://search-it-prod-reports/reports/' + st.experimental_get_query_params()['name'][0] + '.csv'
    df = pd.read_csv(report_link) \
        .sort_values(by=['Date'], ascending=True).reset_index(drop=True)
    logging.info(df.info())
    logging.info(df.head())
    df['Total Searches'] = df['Total Searches'].astype(int)
    df['Monetized Searches'] = df['Monetized Searches'].astype(int)
    df['Clicks'] = df['Clicks'].astype(int)
    df['CTR'] = df['CTR'].astype(float).map('{:.2f}'.format)
    df['RPM'] = df['RPM'].astype(float).map('{:.2f}'.format)
    df['Coverage'] = df['Coverage'].astype(float).map('{:.2f}'.format)
    df['Revenue'] = df['Revenue'].astype(float).map('${:,.2f}'.format)
    vc = df['src'].value_counts()

    for i in vc.index:
        st.subheader(i)
        src_report = df[df['src'] == i].drop(columns=['src'])
        st.write(src_report)

    st.subheader('JSON Endpoint')
    st.write('https://us-central1-search-it-prod.cloudfunctions.net/viewrepjs?name=' + st.experimental_get_query_params()['name'][0])
except Exception as e:
    st.write('No report found')
    logging.exception(e, exc_info=True)