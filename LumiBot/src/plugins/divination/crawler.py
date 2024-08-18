import requests
from bs4 import BeautifulSoup
import json
import time
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def fetch_link(url):
    response = requests.get(url, headers=headers)
    time.sleep(1)
    soup = BeautifulSoup(response.text, 'html.parser')
    # print(soup)
    links = soup.find(class_='ling_list').find_all('a')
    data = []
    for link in links:
        num = int(link.text.replace('观音灵签第', '').replace('签', ''))
        data.append({'num': num, 'src_url': link['href']})
        print(f"第{num}签: {link['href']}")
    return data

def fetch_details(url):
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=2)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    img_tag = soup.find('div', class_='content').find('img')
    img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

    detail = {}
    divs = soup.find_all('div', class_='first')
    
    # print(divs)
    
    for div in divs:
        title_tag = div.find('div', class_='tab_tit')
        content_div = div.find('div', class_='tab_contet')
        
        if title_tag and content_div:
            title = title_tag.text.strip()
            if content_div:
                content = ' '.join(p.text.strip() for p in content_div.find_all('p'))
                if not content:
                    content = content_div.text.strip() 
            detail[title] = content

    return {'img_url': img_url, 'detail': detail}


def save_json():
    print("存储中...")
    
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'guanyin_signs.json')

        if sign_data:
            with open(json_path, 'w' , encoding='utf-8') as f:
                json.dump(sign_data, f, ensure_ascii=False, indent=4)
            print(f"存储到 {json_path}")
        else:
            print("存储失败，没有sign_data")
    except IOError as e:
        print(f"写入错误： {e}")
    except Exception as e:
        print(f"错误： {e}")

if __name__ == '__main__':

    sign_data = fetch_link("https://www.k366.com/guanyin/28761.htm")

    for sign in sign_data:
        details = fetch_details(sign['src_url'])
        sign.update(details)
        
    save_json()
