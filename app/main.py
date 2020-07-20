import requests
import sys

import modem

local = False

if local:
    import secret
    test_url = 'https://icfpc2020-api.testkontur.ru/aliens/send?apiKey=' + secret.apikey
else:
    server_url = sys.argv[1] + '/aliens/send'
    player_key = int(sys.argv[2])

def create_request():
    return (1, (0, ()))

def join_request(key):
    return (2, (key, ((), ())))

def start_request(key):
    xs = (32, (0, (32, (1, ()))))
    return (3, (key, (xs, ())))

def issue_commands(key):
    return (4, (key, ((), ())))

def post(data):
    m = modem.mod(data)
    print("Sending:", data, m)
    if local:
        response = requests.post(test_url, data = m)
    else:
        response = requests.post(server_url, data = m)
    if response.status_code != 200:
        print("Status code:", response.status_code)
    d = modem.dem(response.text)
    print("Receiving:", d)
    return d

# 0 = attacker
# 1 = defender
def play(role, key):
    jr = join_request(key)
    post(jr)
    sr = start_request(key)
    gr = post(sr)

    cmds = issue_commands(key)

    while gr[1][0] < 2:
        print('Game stage:', gr[1][0])
        gr = post(cmds)

def main_local():
    import threading

    cr = create_request()
    response = post(cr)

    p1 = response[1][0][0][1][0]
    p2 = response[1][0][1][0][1][0]

    t1 = threading.Thread(target = lambda : play(0, p1))
    t2 = threading.Thread(target = lambda : play(1, p2))
    t1.start()
    t2.start()

    while t1.is_alive() and t2.is_alive():
        t1.join(1)
        t2.join(1)


def main_submission():
    print("Server:", server_url)
    print("Player key:", player_key)
    play(None, player_key)

def main():
    if local:
        main_local()
    else:
        main_submission()

if __name__ == '__main__':
    main()
