import json
from bs4 import BeautifulSoup

def main():
    try:
        with open('downloads/error_売上.html', 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        labels = [b.get('aria-label') for b in soup.find_all('button') if b.get('aria-label')]
        print(json.dumps(list(set(labels)), indent=2, ensure_ascii=False))
        
        # visual-containerっぽいクラスやIDを探す
        visuals = soup.find_all(lambda tag: tag.has_attr('data-automation-id') and 'visual' in tag.get('data-automation-id', '').lower())
        print("\n--- Visual Containers ---")
        for v in visuals[:10]:
            print(f"Tag: {v.name}, AutomationID: {v.get('data-automation-id')}, Class: {v.get('class')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
