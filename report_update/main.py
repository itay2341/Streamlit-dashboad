import time
from google.cloud import storage
import feeds as f
import pandas as pd
import functions_framework

feeds = [
    f.Ric(), 
    # f.Big(), 
    f.Adv(), 
    # f.UDMS(), 
    f.AE(), 
    f.ET(), 
    f.Fin(), 
    f.IL()
    ]

def get_new_reports():
    date_format = '%Y-%m-%d'
    end_date = time.strftime(date_format)
    # start date is 14 days before end date
    start_date = (pd.to_datetime(end_date) - pd.Timedelta(days=14)).strftime(date_format)
    # start_date = '2023-07-01'
    print(f'Getting data from {start_date} to {end_date}')
    dfs = []
    for feed in feeds:
        print(f'Getting {feed.advertiser} data')
        try:
            df = feed.get_df(start_date, end_date)
            dfs.append(df)
        except Exception as e:
            print(f'Error getting {feed.advertiser} data: {e}')
    df_feed = pd.concat(dfs, ignore_index=True)
    df_feed = df_feed[['advertiser', 'adv_feed_id', 'feed_id', 'Date', 'Total Searches', 'Monetized Searches', 'Clicks', 'Revenue']]
    return df_feed

@functions_framework.http
def main(request):
    print('Updating feed report')
    df_new = get_new_reports()
    df_old = pd.read_csv('gs://search-it-prod-reports/feed_report.csv')
    df_old['Date'] = pd.to_datetime(df_old['Date'])
    df_combined = pd.concat([df_new, df_old], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['advertiser', 'adv_feed_id', 'feed_id', 'Date'], keep='first')
    print(f'{len(df_combined) - len(df_old)} new rows added')

    bucket = storage.Client().bucket('search-it-prod-reports')
    blob = bucket.blob('feed_report.csv')
    blob.upload_from_string(df_combined.to_csv(index=False), content_type='text/csv')
    print('Feed report updated')
    return 'done'