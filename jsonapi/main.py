import pandas as pd
import flask
import json

def json_ep(request: flask.Request) -> flask.Response:
    request_json = request.get_json()
    report_link = 'gs://search-it-prod-reports/reports/' + request_json['name'] + '.csv'
    df = pd.read_csv(report_link) \
        .sort_values(by=['Date'], ascending=False).reset_index(drop=True)
   
    vc = df['src'].value_counts()
    response = {}
    for i in vc.index:
        src_report = df[df['src'] == i].drop(columns=['src'])
        response[i] = src_report.to_dict('records')
    str_response = json.dumps(response)
    return str_response

