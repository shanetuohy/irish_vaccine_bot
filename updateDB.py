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

    print(previous_day_str)
    total_vac_yesterday = covid_table.find(date=previous_day_str).next()['totalVaccinations']
    pfizer_today = today['pf'] - covid_table.find(date=previous_day_str).next()['pfizer'] 
    moderna_today = today['modern'] - covid_table.find(date=previous_day_str).next()['moderna'] 
    az_today = today['az'] - covid_table.find(date=previous_day_str).next()['astraZeneca']
    
    johnson_today =  (today['totalAdministered'] - total_vac_yesterday) - (pfizer_today + moderna_today + az_today) 
    johnson_total = johnson_today + covid_table.find(date=previous_day_str).next()['jj']
    today_dict = OrderedDict(date=returned_date_str,
                             firstDose=today['firstDose'] - johnson_total,
                             secondDose=today['secondDose'] + johnson_total,
                             totalVaccinations=today['totalAdministered'],
                             pfizer=today['pf'],
                             moderna=today['modern'],
                             astraZeneca=today['az'],
                             dailyVaccinations=today['totalAdministered'] - total_vac_yesterday,
                             jj=johnson_total
                             )

    try:
        match = covid_table.find(date=returned_date_str)
        todays = match.next()
        if todays == today_dict:
            return 10
        else:
            print("Didn't get the same object, so let's insert a new entry")
            covid_table.insert(today_dict)
            return 10
    except StopIteration as e:
        print("Returned date " + returned_date_str_short + " did not exist in DB. Adding.")
        print("Sleeping for 60")
        covid_table.insert(today_dict)
        return 60

while 1:
    now = datetime.datetime.now()
    minutes_to_sleep = check_rest_api()
    dt = datetime.datetime.now() + datetime.timedelta(minutes = minutes_to_sleep)
    print(".", end="")
    while datetime.datetime.now() < dt:
        time.sleep(1)
