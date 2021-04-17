import datetime, time, requests, dataset
from collections import OrderedDict



def check_rest_api():
    # Connect to our sqlite db
    DB = dataset.connect("sqlite:///covid.db")

    # Query API for todays data.
    url = 'https://services-eu1.arcgis.com/z6bHNio59iTqqSUY/arcgis/rest/services' \
          '/Covid19_Vaccine_Administration_Hosted_View/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry' \
          '=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0' \
          '&units=esriSRUnit_Meter&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault' \
          '&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation' \
          '=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false' \
          '&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields' \
          '=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false' \
          '&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=json&token= '

    # Get request & JSONify
    try:
        resp = requests.get(url)
        data = resp.json()
    except:
        print("Got an exception when doing request, let's just try again later")
        return 30
    # Select 'covid' table from sqlite db
    covid_table = DB['covid']
    today = data['features'][0]['attributes']

    # Calculate the returned date from API, and yesterdays date.
    # so we can work out "dailyVaccinations" from total today vs yesterday
    returned_date = datetime.datetime.utcfromtimestamp(int(today['relDate'] / 1000))
    returned_date_str = str(returned_date.day) + "/" + "{:02d}".format(returned_date.month) + "/" + str(returned_date.year)
    returned_date_str_short = str(returned_date.day) + "-" + str(returned_date.month) + "-" + str(returned_date.year)
    previous_day = returned_date - datetime.timedelta(days=1)
    previous_day_str = str(previous_day.day) + "/" + "{:02d}".format(previous_day.month) + "/" + str(previous_day.year)

    total_vac_yesterday = covid_table.find(date=previous_day_str).next()['totalVaccinations']

    today_dict = OrderedDict(date=returned_date_str,
                             firstDose=today['firstDose'],
                             secondDose=today['secondDose'],
                             totalVaccinations=today['totalAdministered'],
                             pfizer=today['pf'],
                             moderna=today['modern'],
                             astraZeneca=today['az'],
                             dailyVaccinations=today['totalAdministered'] - total_vac_yesterday
                             )

    try:
        match = covid_table.find(date=returned_date_str)
        todays = match.next()
        if todays == today_dict:
            print(returned_date_str_short + " exists in the DB. No update needed")
            return 30
    except StopIteration as e:
        print("Returned date " + returned_date_str_short + " did not exist in DB. Adding.")
        covid_table.insert(today_dict)
        return 1200

while 1:
    now = datetime.datetime.now()
    print("Checking API for updates at " + str(now.hour) + ":" + str(now.minute))
    minutes_to_sleep = check_rest_api()
    dt = datetime.datetime.now() + datetime.timedelta(minutes = minutes_to_sleep)
    print("Going to sleep for " + str(minutes_to_sleep) + " minutes")
    while datetime.datetime.now() < dt:
        time.sleep(1)
