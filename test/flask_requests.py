import requests
import threading


def flask_thread(num):
    response = requests.get(f'http://127.0.0.1:8888/test/{num}')
    print(response.json())


if __name__ == '__main__':
    for i in range(1000):
        threading.Thread(target=flask_thread, args=(i,)).start()
    # flask_thread(1)
