from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def audit_etsy_shop(url_or_name):
    clean_input = url_or_name.strip().rstrip('/')
    if 'etsy.com' in clean_input:
        shop_url = clean_input if clean_input.startswith('http') else 'https://' + clean_input
        shop_name = shop_url.split('/shop/')[-1].split('/')[0]
    else:
        shop_name = clean_input
        shop_url = f"https://www.etsy.com/shop/{shop_name}"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(shop_url, headers=headers, timeout=12)
        if response.status_code != 200:
            return None, "Store not found or inaccessible. Please verify the shop name or URL."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        issues = []
        passes = []
        score = 100

        # Check Announcement
        announcement = soup.find('div', {'class': re.compile('.*announcement.*|.*shop-message.*')})
        if not announcement or len(announcement.text.strip()) < 15:
            issues.append("Weak or missing Shop Announcement. Essential for Etsy SEO indexing.")
            score -= 20
        else:
            passes.append("Active and clear Shop Announcement detected.")

        # Check About Section
        about_section = soup.find('div', {'id': 'about'}) or soup.find('section', {'class': re.compile('.*about.*')})
        if not about_section:
            issues.append("Missing 'About Section'. Stores with brand stories convert 35% better.")
            score -= 25
        else:
            passes.append("Brand 'About Section' is properly structured.")

        # Check Listings & Titles
        listings = soup.find_all(['h3', 'h2'], {'class': re.compile('.*card-title.*|.*listing-title.*')})
        if listings:
            passes.append(f"Successfully indexed active store listings ({len(listings)} items found).")
        else:
            issues.append("No active listings detected or store is currently under vacation mode.")
            score -= 30

        # Final Score Calculations
        score = max(score, 30)
        score_color = "#10b981" if score >= 75 else ("#f59e0b" if score >= 50 else "#ef4444")
        status_text = "Optimized" if score >= 75 else ("Needs Improvement" if score >= 50 else "Critical Issues")

        return {
            'shop_name': shop_name.capitalize(),
            'score': score,
            'score_color': score_color,
            'status_text': status_text,
            'issues': issues,
            'passes': passes
        }, None

    except Exception as e:
        return None, "An error occurred while connecting to Etsy. Please try again."

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        shop_url = request.form.get('shop_url')
        if not shop_url:
            return render_template('index.html', error="Please enter a valid shop URL or name.")
        
        audit_result, error = audit_etsy_shop(shop_url)
        if error:
            return render_template('index.html', error=error)
            
        return render_template('index.html', audit=audit_result, shop_name=shop_url)
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
