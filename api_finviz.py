from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def parse_number(value):
    """Parse Finviz number formats (B, M, K, %)"""
    if not value or value == '-':
        return None
    
    # Remove % sign
    value = value.replace('%', '')
    
    # Handle B (Billion), M (Million), K (Thousand)
    multiplier = 1
    if 'B' in value:
        multiplier = 1e9
        value = value.replace('B', '')
    elif 'M' in value:
        multiplier = 1e6
        value = value.replace('M', '')
    elif 'K' in value:
        multiplier = 1e3
        value = value.replace('K', '')
    
    try:
        return float(value) * multiplier
    except:
        return None

@app.route('/api/finviz', methods=['GET'])
def get_finviz_data():
    ticker = request.args.get('ticker', '').upper()
    
    if not ticker:
        return jsonify({'error': 'Ticker parameter required'}), 400
    
    try:
        # Scrape Finviz
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'error': f'Finviz returned status {response.status_code}'}), 502
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get company name
        company_name = soup.find('h1', class_='quote-header_ticker-wrapper_company')
        if company_name:
            company_name = company_name.text.strip()
        else:
            company_name = ticker
        
        # Get all tables
        tables = soup.find_all('table')
        
        # Financial data is in table index 8 or 9 (varies by Finviz version)
        data_dict = {}
        
        for table_idx in [8, 9]:
            if table_idx >= len(tables):
                continue
                
            rows = tables[table_idx].find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                for i in range(0, len(cells) - 1, 2):
                    label = cells[i].text.strip()
                    value = cells[i + 1].text.strip()
                    data_dict[label] = value
        
        # Parse into clean JSON structure
        result = {
            'ticker': ticker,
            'company': company_name,
            'price': parse_number(data_dict.get('Price')),
            'marketCap': parse_number(data_dict.get('Market Cap')),
            'pe': parse_number(data_dict.get('P/E')),
            'forwardPE': parse_number(data_dict.get('Forward P/E')),
            'peg': parse_number(data_dict.get('PEG')),
            'pb': parse_number(data_dict.get('P/B')),
            'ps': parse_number(data_dict.get('P/S')),
            'dividend': parse_number(data_dict.get('Dividend %')),
            'roe': parse_number(data_dict.get('ROE')),
            'roa': parse_number(data_dict.get('ROA')),
            'roi': parse_number(data_dict.get('ROI')),
            'eps': parse_number(data_dict.get('EPS (ttm)')),
            'epsNextY': parse_number(data_dict.get('EPS next Y')),
            'epsGrowth': parse_number(data_dict.get('EPS this Y')),
            'epsNext5Y': parse_number(data_dict.get('EPS next 5Y')),
            'salesGrowth': parse_number(data_dict.get('Sales Y/Y TTM')),
            'margin': parse_number(data_dict.get('Profit Margin')),
            'operMargin': parse_number(data_dict.get('Oper. Margin')),
            'grossMargin': parse_number(data_dict.get('Gross Margin')),
            'debt': parse_number(data_dict.get('Debt/Eq')),
            'currentRatio': parse_number(data_dict.get('Current Ratio')),
            'quickRatio': parse_number(data_dict.get('Quick Ratio')),
            'beta': parse_number(data_dict.get('Beta')),
            'atr': parse_number(data_dict.get('ATR')),
            'volume': parse_number(data_dict.get('Volume')),
            'avgVolume': parse_number(data_dict.get('Avg Volume')),
            'performance': {
                'week': parse_number(data_dict.get('Perf Week')),
                'month': parse_number(data_dict.get('Perf Month')),
                'quarter': parse_number(data_dict.get('Perf Quarter')),
                'halfYear': parse_number(data_dict.get('Perf Half Y')),
                'year': parse_number(data_dict.get('Perf Year')),
                'ytd': parse_number(data_dict.get('Perf YTD'))
            },
            'raw': data_dict  # Include raw data for debugging
        }
        
        return jsonify(result)
        
    except requests.Timeout:
        return jsonify({'error': 'Request timeout'}), 504
    except requests.RequestException as e:
        return jsonify({'error': f'Request failed: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Finviz API Proxy'})

if __name__ == '__main__':
    app.run(debug=True)
