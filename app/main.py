import requests
import sys

import modem

test_url = 'https://icfpc2020-api.testkontur.ru/aliens/send'
server_url = sys.argv[1]
player_key = sys.argv[2]

def join_request():
    return (2, (player_key, ()))

def post(data, test = False):
    if test:
        pass
    else:
        response = requests.post(server_url, data = modem.mod(data))
        if response.status_code != 200:
            print("Status code:", response.status_code)
        return modem.dem(response.text)

def main():
    print('A')
    jr = join_request()
    response = post(jr)
    print('B', response)

if __name__ == '__main__':
    main()
