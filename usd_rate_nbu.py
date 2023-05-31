from datetime import date

# import urllib library
from urllib.request import urlopen

# import json
import json


CURRENCY = 'USD'

def main():
  by_date = input('YYYYMMDD: ')

  url_today = f'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={CURRENCY}&date={by_date}&json'

  response = urlopen(url_today)
  data = json.loads(response.read())
  #print(data)
  nbu_rate = data[0]['rate']

  print(nbu_rate)

if __name__ == '__main__':
    main()