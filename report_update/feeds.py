import time
import requests
import json
# from google.cloud import bigquery
# from google.oauth2 import service_account
import pandas as pd


class FeedYMDJSON:
    def __init__(self, advertiser, url_format, headers=None):
        self.advertiser = advertiser
        self.url_format = url_format
        self.headers = headers

    def get_json_list(self, start_date, end_date):
        try:
            url = self.url_format.format(start_date, end_date)
            res = requests.get(url, headers=self.headers)
            if res.status_code == 200:
                return json.loads(res.text)
            else:
                print('Error: bad status code {}'.format(res.status_code))
                return None
        except Exception as e:
            print('Error: {}'.format(e))
            return None

class Ric(FeedYMDJSON):
    def __init__(self):
        advertiser = 'Ric'
        url_format = 'https://crm.adx1.com/api/stats/publisher?apiKey=aed96dcc97b3aeab43242345b9228a8f1685963104sfa647dc1608aaa4&startDate={}&endDate={}'
        self.id_map = {
                    '1126': 'Ric1',
                    '2022': 'Ric2',
                    '677f1c8': 'Ric3',
                    '111177': 'Ric4',
                    '139': 'Ric5',
                    '1fb9f83': 'Ric6',
                    '1004': 'Ric7',
                    'mfbhs151': 'Ric8',
                    '1530': 'Ric9',
                    '1543': 'Ric10',
                    '1956': 'Ric11',

        }
        super().__init__(advertiser, url_format)

    def get_df(self, start_date, end_date):
        res = self.get_json_list(start_date, end_date)
        lines = []
        for provider in res:
            provider_id = provider['providerId']
            for stat in provider['stats']:
                line = {
                    'advertiser': self.advertiser,
                    'adv_feed_id': provider_id,
                    'feed_id': self.id_map[provider_id] if provider_id in self.id_map else None,
                    'Date': stat['date'], 
                    'Total Searches': stat['impressions'], 
                    'Monetized Searches': stat['monetizedImpressions'],
                    'Clicks': stat['clicks'], 
                    'CTR': stat['ctr'], 
                    'Revenue': stat['publisherProfit'],
                }
                lines.append(line)
        df = pd.DataFrame(lines)
        df['RPM'] = df['Revenue'] / df['Monetized Searches'] * 1000
        df['Coverage'] = df['Monetized Searches'] / df['Total Searches'] * 100
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        return df

class Big(FeedYMDJSON):
    def __init__(self):
        advertiser = 'Big'
        url_format = 'https://stats.bigengagemarketing.com/api/stats/zikmedia/?key=wVDRFS2e3f7mUHWjrv2KRMHzygRCvVfd&date_from={}&date_to={}'
        self.id_map = {
                    '1056': 'Big1',
                    '1057': 'Big2',
        }
        super().__init__(advertiser, url_format)

    def get_df(self, start_date, end_date):
        df = pd.DataFrame(self.get_json_list(start_date, end_date))
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        df['Revenue'] = df['Revenue'].astype(float)
        df = df.groupby(['Date', 'Channel']).sum().reset_index()
        df['advertiser'] = self.advertiser
        df['adv_feed_id'] = df['Channel']
        df['feed_id'] = df['Channel'].apply(lambda x: self.id_map[x] if x in self.id_map else None)
        df['CTR'] = df['Clicks'] / df['Monetized Searches'] * 100
        df['RPM'] = df['Revenue'] / df['Monetized Searches'] * 1000
        df['Coverage'] = df['Monetized Searches'] / df['Total Searches'] * 100
        return df

class UDMS(FeedYMDJSON):
    def __init__(self):
        advertiser = 'UDMS'
        url_format = 'https://platform.upperate.com/api/v1/publisher/report/all_campaigns?start_date={}&end_date={}'
        headers = {
            'Authorization': 'Bearer 37sopnQRXKMhAV6o0fCsYIDHzzGmpFqlOioy9vWp',
            }
        super().__init__(advertiser, url_format, headers)

    def get_df(self, start_date, end_date):
        res = self.get_json_list(start_date, end_date)
        lines = []
        for num, line in res['data'].items():
            line['Date'] = line['date']
            line['Total Searches'] = line['total_searches']
            line['Monetized Searches'] = line['monetized_searches']
            line['Clicks'] = line['clicks']
            line['Revenue'] = line['revenue']
            line['advertiser'] = self.advertiser
            line['adv_feed_id'] = line['campaign']
            line['feed_id'] = 'UDMS1'
            lines.append(line)
        df = pd.DataFrame(lines)
        df['Coverage'] = df['Monetized Searches'] / df['Total Searches'] * 100
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        return df

class IL(FeedYMDJSON):
    def __init__(self):
        advertiser = 'IL'
        url_format = 'https://api.trafficjunction.com/api/stats/?token=30d360e2b9faca1472a06dd219f275af&start={}&end={}'
        self.id_map = {
                    'k=277': 'il1',
        }
        super().__init__(advertiser, url_format)

    def get_df(self, start_date, end_date):
        res = self.get_json_list(start_date, end_date)
        df = pd.DataFrame(res)
        # df['ts'] is str in format 2023-07-07 00:00:00
        df['Date'] = pd.to_datetime(df['ts'], format='%Y-%m-%d %H:%M:%S')
        df = df.groupby(['Date', 'product']).apply(
            lambda x: pd.Series({
                'Total Searches': ((100*x['requests'].iloc[0]) / (100 - x['bad_request_percentage'].iloc[0])).astype(int),
                'Monetized Searches' : x['monetized_searches'].sum().astype(int),
                'Clicks' : x['clicks'].sum().astype(int),
                'Revenue' : x['net_amount'].sum(),
            })
        ).reset_index()
        df['advertiser'] = self.advertiser
        df['adv_feed_id'] = df['product']
        df['feed_id'] = df['product'].map(self.id_map)
        df['CTR'] = df['Clicks'] / df['Monetized Searches'] * 100
        df['RPM'] = df['Revenue'] / df['Monetized Searches'] * 1000
        df['Coverage'] = df['Monetized Searches'] / df['Total Searches'] * 100
        return df

class Fin(FeedYMDJSON):
    def __init__(self):
        advertiser = 'Fin'
        url_format = 'http://www.teqfire.com/report?apiKey=AwgdFD0lMytTZ3ZXGDYzMzwIIDp9YQ4N&start_date={}&end_date={}'
        self.id_map = {
            "1225": 'Fin1',
            "1231": 'Fin2',
            "1264": 'Fin3',
            "1225": 'Fin4(20K)',
            "1278": 'Fin5-1278(2k)',
        }
        # safari header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)',
        }
        super().__init__(advertiser, url_format, headers)

    
    def get_df(self, start_date, end_date):
        res = self.get_json_list(start_date, end_date)
        df = pd.DataFrame(res['data'])
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        df['advertiser'] = self.advertiser
        df['adv_feed_id'] = df['Tagid']
        df['feed_id'] = df['Tagid'].str.strip().map(self.id_map)
        df['Total Searches'] = df['Total Searches'].astype(int)
        df['Monetized Searches'] = df['Monetized Searches'].astype(int)
        df['Revenue'] = df['Revenue'].str.replace('$', '').astype(float)
        df['Clicks'] = df['Clicks'].astype(int)
        df['CTR'] = df['Clicks'] / df['Monetized Searches'] * 100
        df['RPM'] = df['Revenue'] / df['Monetized Searches'] * 1000
        df['Coverage'] = df['Monetized Searches'] / df['Total Searches'] * 100
        return df

class Adv():
    def __init__(self):
        self.advertiser = 'Adv'
        self.links = [
            {
                'adv_feed_id': '1122',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=0',
                'feed_id': 'Adv1',
            }, {
                'adv_feed_id': '1281',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=1411002891',
                'feed_id': 'Adv2',
            }, {
                'adv_feed_id': '1179',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=1237215449',
                'feed_id': 'Adv3',
            }, {
                'adv_feed_id': '1037',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=395591621',
                'feed_id': 'Adv4',
            }, {
                'adv_feed_id': '1162',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=47615425',
                'feed_id': 'Adv5',
            }, {
                'adv_feed_id': '402',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=263421618',
                'feed_id': 'Adv6',
            }, {
                'adv_feed_id': '37',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=2035776917',
                'feed_id': 'Adv7',
            },{
                'adv_feed_id': '1424',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=215121760',
                'feed_id': 'Adv8',
            },{
                'adv_feed_id': '1459',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=1886310315',
                'feed_id': 'Adv9',
            },{
                'adv_feed_id': '1509',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=1817297840',
                'feed_id': 'Adv10',
            }, {
                'adv_feed_id': '261',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=1771580815',
                'feed_id': 'Adv-m1',
            }, {
                'adv_feed_id': '1042',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=875374153',
                'feed_id': 'Adv13',
            }, {
                'adv_feed_id': '1346',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=1936510097',
                'feed_id': 'Adv14',
            }, {
                'adv_feed_id': '1345',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=1049154440',
                'feed_id': 'Adv15',
            }, {
                'adv_feed_id': '1217',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=1450875487',
                'feed_id': 'Adv16',
            },{
                'adv_feed_id': '1679',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=156911766',
                'feed_id': 'Adv17-1679(10K)',
            },{
                'adv_feed_id': '1673',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=775499953',
                'feed_id': 'Adv18-1673(10K)',
            }, {
            #     'adv_feed_id': '1549',
            #     'url': '',
            #     'feed_id': 'Adv19-1549(5K)',
            # }, {
                'adv_feed_id': '1391',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=222000146',
                'feed_id': 'Adv20-1391(10K)',
            }, {
            #     'adv_feed_id': '1705',
            #     'url': '',
            #     'feed_id': 'Adv21-1705(20K)',
            # }, {
                'adv_feed_id': '1700',
                'url': 'https://docs.google.com/spreadsheets/d/1mZ8i3kBIsuo9Bq8GylkcaCtS90Oo1Arre4r08samIPQ/edit#gid=912771401',
                'feed_id': 'Adv22-1700(10K)',
            # }, {
            #     'adv_feed_id': '1684',
            #     'url': '',
            #     'feed_id': 'Adv23-1684(10K)',
            # }, {
            #     'adv_feed_id': '1615',
            #     'url': '',
            #     'feed_id': 'Adv24-1615(5K)',
            # }, {
            #     'adv_feed_id': '1417',
            #     'url': '',
            #     'feed_id': 'Adv25-1417(10K)',
            # }, {
            #     'adv_feed_id': '1414',
            #     'url': '',
            #     'feed_id': 'Adv26-1414(10K)',
            # }, {
            #     'adv_feed_id': '1148',
            #     'url': '',
            #     'feed_id': 'Adv27-1148(10K)',
            },
        ]

    def get_df(self, start_date, end_date):
        dfs = []
        for item in self.links:
            link = item['url']
            feed_id = item['feed_id']
            adv_feed_id = item['adv_feed_id']
            csv_export_url = link.replace('/edit#gid=', '/export?format=csv&gid=')
            df = pd.read_csv(csv_export_url)
            df['feed_id'] = feed_id
            df['adv_feed_id'] = adv_feed_id
            df['Monetized Searches'] = df['Page Views With Ads']
            df['Total Searches'] = df['Total searches']
            df['Revenue'] = df['Net Revenue'].str.replace('$', '').str.replace(',', '').astype(float)
            dfs.append(df)
        df = pd.concat(dfs)
        df = df[df['Total Searches'].notna()].reset_index(drop=True)

        df['Total Searches'] = df['Total Searches'].\
            apply(lambda x: float(str(x).replace(',', '').\
                                  replace(' ', ''))).astype(int)
        df['advertiser'] = self.advertiser
        df['RPM'] = df['Revenue'] / df['Monetized Searches'] * 1000
        df['Coverage'] = df['Monetized Searches'] / df['Total Searches'] * 100
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        df.dropna(inplace=True)
        df['CTR'] =  df['CTR'].str.replace('%', '').str.replace('#DIV/0!', '0').astype(float)

        df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        return df

class AE():
    def __init__(self):
        self.advertiser = 'AE'
        self.url_format = 'https://stats.aemdays.com/statistic/pub-search-stats?from={}&key=97f98299&pubid=750&to={}'
        self.id_map = {
            8612: 'AE1',
            8639: 'AE2',
            8690: 'AE3',
            8804: 'AE4',
            8961: 'AE5',
            9013: 'AE6-9013(10K)',
            9055: 'AE7-9055(5K)',
            9069: 'AE8-9069(100K)',
            9193: 'AE10-9193(10K)',
            9269: 'AE11-9269(10K)',
        }

    def get_df(self, start_date, end_date):
        url = self.url_format.format(start_date, end_date)
        df =  pd.read_csv(url)
        df['advertiser'] = self.advertiser
        df['adv_feed_id'] = df['CampaignID']
        df['feed_id'] = df['CampaignID'].apply(lambda x: self.id_map[x] if x in self.id_map else None)
        df['Clicks'] = df['Paid clicks']
        df['Revenue'] = df['Publisher Revenue']
        df['CTR'] = df['Monetized CTR']
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        df['Coverage'] = df['Coverage'].str.replace('%', '').astype(float)
        return df

class ET():
    def __init__(self):
        self.advertiser = 'ET'
        url='https://drive.google.com/file/d/1lWHWs23D_zklXjDPRU9rqu1cFSQFIjdf/view?usp=drive_link'
        url='https://drive.google.com/uc?id=' + url.split('/')[-2]
        self.url = url
        self.id_map = {
            '1000': 'ET1',
            '1001': 'ET2(10K)',
            '1002': 'ET3(10K)',
        }
    
    def get_df(self, start_date, end_date):
        df = pd.read_csv(self.url)
        df['advertiser'] = self.advertiser
        df['adv_feed_id'] = df['Search Channel']
        df['feed_id'] = df['Search Channel'].apply(lambda x: self.id_map[str(x)] if str(x) in self.id_map else None)
        df['Revenue'] = df['Amount']
        df['CTR'] = df['Clicks'] / df['Monetized Searches'] * 100
        df['RPM'] = df['Revenue'] / df['Monetized Searches'] * 1000
        df['Coverage'] = df['Monetized Searches'] / df['Total Searches'] * 100
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        return df
        

# credentials = service_account.Credentials.from_service_account_file(
#     "/Users/leon/Desktop/cred/search-it-prod-0bdb24ad30df.json", 
#     scopes=["https://www.googleapis.com/auth/cloud-platform"],
# )
# client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# def get_stuts(start, end):
#     """
#     strart and end are in the format of '2020-01-01'
#     """
#     query = f"""SELECT
#     DATE(TIMESTAMP_MILLIS(timestamp)) as date,
#     src,
#     feed_name,
#     COUNT(*) as count
#     FROM `feeds.feed-short`
#     WHERE DATE(TIMESTAMP_MILLIS(timestamp)) BETWEEN '{start}' AND '{end}'
#     GROUP BY date, src, feed_name
#     ORDER BY date"""

#     # Run the query
#     query_job = client.query(query)

#     # Get the results in a pandas DataFrame
#     df = query_job.to_dataframe()
#     df['Date'] = pd.to_datetime(df['date'])
#     df['feed_id'] = df['feed_name']
#     df.drop(['date', 'feed_name'], axis=1, inplace=True)
#     return df

       
if __name__ == '__main__':
    # start = '2023-07-01'
    # end = '2023-07-08'

    # # df_status = get_stuts(start, end)
    # # # print(df_status)
    # # print(df_status.info())
    # print(Ric().get_df(start, end)

    date_format = '%Y-%m-%d'
    time_delta_days = 15
    start_date= time.strftime(date_format, time.localtime(time.time() - time_delta_days * 24 * 60 * 60))
    end_date = time.strftime(date_format)
    print(start_date, end_date)
    print(ET().get_df(start_date, end_date)
)