# backend/app.py

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import uuid # Import uuid for generating unique public IDs
import requests # Import requests for metal price API calls
from sqlalchemy import text # Import text for raw SQL queries
# Email functionality - using Resend for permanent free email delivery
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    print("Warning: Resend not available, using fallback email method")
    RESEND_AVAILABLE = False
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

# Import configuration
from config import Config

# Import the new reliable price fetcher (optional)
try:
    from google_finance_prices import price_fetcher
    PRICE_FETCHER_AVAILABLE = True
except ImportError:
    print("Warning: google_finance_prices module not found, using fallback price fetching")
    PRICE_FETCHER_AVAILABLE = False
    price_fetcher = None

# Simple Yahoo Finance price fetcher as fallback
def fetch_yahoo_finance_prices():
    """Fetch prices from Yahoo Finance (no API key required)"""
    try:
        import requests
        from datetime import datetime
        
        # Yahoo Finance symbols for gold and silver
        symbols = {
            'gold': 'GC=F',  # Gold futures
            'silver': 'SI=F',  # Silver futures
            'usd_zar': 'USDZAR=X'  # USD to ZAR
        }
        
        prices = {}
        
        for metal, symbol in symbols.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                # Check if response is valid
                if response.status_code != 200:
                    print(f"Yahoo Finance HTTP error for {symbol}: {response.status_code}")
                    continue
                
                # Check if response has content
                if not response.text.strip():
                    print(f"Yahoo Finance empty response for {symbol}")
                    continue
                
                # Try to parse JSON
                try:
                    data = response.json()
                except ValueError as json_error:
                    print(f"Yahoo Finance JSON parse error for {symbol}: {json_error}")
                    print(f"Response content: {response.text[:200]}...")
                    continue
                
                if data.get('chart', {}).get('result'):
                    result = data['chart']['result'][0]
                    if result.get('meta', {}).get('regularMarketPrice'):
                        prices[metal] = result['meta']['regularMarketPrice']
                        print(f"Successfully fetched {metal} price: {prices[metal]}")
                    else:
                        print(f"No price data in Yahoo Finance response for {symbol}")
                else:
                    print(f"No chart result in Yahoo Finance response for {symbol}")
                    
            except requests.RequestException as req_error:
                print(f"Yahoo Finance request error for {symbol}: {req_error}")
                continue
        
        if len(prices) == 3:  # All prices fetched
            return {
                'gold_usd_per_oz': prices['gold'],
                'silver_usd_per_oz': prices['silver'],
                'gold_zar_per_oz': prices['gold'] * prices['usd_zar'],
                'silver_zar_per_oz': prices['silver'] * prices['usd_zar'],
                'lastUpdate': datetime.utcnow().isoformat()
            }
        else:
            print(f"Yahoo Finance: Only got {len(prices)} out of 3 prices: {list(prices.keys())}")
        
    except Exception as e:
        print(f"Yahoo Finance general error: {e}")
    
    return None

app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize CORS for cross-origin requests from your frontend
# For production, replace "*" with your actual frontend domain (e.g., 'https://your-netlify-app.netlify.app')
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    coins = db.relationship('Coin', backref='owner', lazy=True) # One user has many coins
    # New: One user can have one public collection link
    public_collection = db.relationship('PublicCollection', backref='user', uselist=False, lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g., Coin, Banknote, Gold Bullion, Silver Bullion
    country = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    denomination = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float) # Estimated value
    quantity = db.Column(db.Integer, default=1) # Number of duplicates
    notes = db.Column(db.Text)
    referenceUrl = db.Column(db.String(500))
    localImagePath = db.Column(db.String(500)) # Path to local image
    # New fields for better data management and charting
    region = db.Column(db.String(100)) # e.g., Europe, Asia, North America
    isHistorical = db.Column(db.Boolean, default=False) # True if from a historical entity or pre-1900
    # New fields for bullion tracking
    weight_grams = db.Column(db.Float, nullable=True) # Weight in grams for bullion
    purity_percent = db.Column(db.Float, nullable=True) # Purity percentage for bullion (e.g., 99.9)

    def __repr__(self):
        return f'<Coin {self.denomination} from {self.country} ({self.year})>'

# New: Model for Public Collection Links
class PublicCollection(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, nullable=False) # UUID for public link
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<PublicCollection ID: {self.id} for User: {self.user_id}>'

# New: Model for Password Reset Tokens
class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<PasswordResetToken for User: {self.user_id}>'

# --- JWT Authentication Decorator ---
def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            print("DEBUG: Token is missing from Authorization header.")
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                print(f"DEBUG: User with ID {data['user_id']} not found for token.")
                return jsonify({'message': 'User not found!'}), 401
        except jwt.ExpiredSignatureError:
            print("DEBUG: JWT ExpiredSignatureError caught.")
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            print("DEBUG: JWT InvalidTokenError caught.")
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            print(f"DEBUG: Unexpected error in jwt_required: {e}")
            return jsonify({'message': 'An error occurred during authentication.'}), 500
        return f(current_user, *args, **kwargs)
    return decorated

# --- Helper function for region and historical flag ---
# Map for standardizing country names for Google Charts GeoChart
country_alias_map = {
    "united states of america": "United States", "usa": "United States", "uk": "United Kingdom",
    "britain": "United Kingdom", "russia": "Russia", "china": "China", "india": "India",
    "japan": "Japan", "germany": "Germany", "deutschland": "Germany", "france": "France",
    "italy": "Italy", "brazil": "Brazil", "brasil": "Brazil", "south africa": "South Africa",
    "eswatini": "Eswatini", "rome": "Italy", "constantinople": "Turkey", "nicomedia": "Turkey",
    "antioch": "Syria", "ancient greece": "Greece", "seleucid": "Syria", "ussr": "Russia",
    "yugoslavia": "Serbia", "east germany": "Germany", "german democratic republic": "Germany",
    "phillipines": "Philippines",
}

# Map for determining geographic region
country_to_region_map = {
    "south africa": "Africa", "eswatini": "Africa", "kenya": "Africa", "central african states": "Africa",
    "mauritius": "Africa", "ghana": "Africa", "rwanda": "Africa", "zimbabwe": "Africa",
    "tanzania": "Africa", "mozambique": "Africa", "botswana": "Africa", "zambia": "Africa",
    "eritrea": "Africa", "somalia": "Africa", "sudan": "Africa", "malawi": "Africa",
    "ethiopia": "Africa", "nigeria": "Africa", "egypt": "Africa", "algeria": "Africa", "angola": "Africa",
    "benin": "Africa", "burkina faso": "Africa", "burundi": "Africa", "cabo verde": "Africa",
    "cameroon": "Africa", "chad": "Africa", "comoros": "Africa", "congo (brazzaville)": "Africa",
    "congo (kinshasa)": "Africa", "djibouti": "Africa", "equatorial guinea": "Africa",
    "gabon": "Africa", "gambia": "Africa", "guinea": "Africa", "guinea-bissau": "Africa",
    "lesotho": "Africa", "liberia": "Africa", "libya": "Africa", "liechtenstein": "Europe", "madagascar": "Africa",
    "mali": "Africa", "mauritania": "Africa", "morocco": "Africa", "niger": "Africa",
    "sao tome and principe": "Africa", "senegal": "Africa", "sierra leone": "Africa",
    "south sudan": "Africa", "togo": "Africa", "uganda": "Africa",

    "taiwan": "Asia", "india": "Asia", "china": "Asia", "japan": "Asia", "philippines": "Asia",
    "united arab emirates": "Asia", "israel": "Asia", "vietnam": "Asia", "bangladesh": "Asia",
    "mongolia": "Asia", "myanmar (burma)": "Asia", "cambodia": "Asia", "lebanon": "Asia",
    "uzbekistan": "Asia", "indonesia": "Asia", "laos": "Asia", "nepal": "Asia",
    "sri lanka": "Asia", "iran": "Asia", "pakistan": "Asia", "jordan": "Asia",
    "kazakhstan": "Asia", "kuwait": "Asia", "kyrgyzstan": "Asia", "malaysia": "Asia",
    "maldives": "Asia", "north korea": "Asia", "oman": "Asia", "palestine": "Asia",
    "qatar": "Asia", "saudi arabia": "Asia", "singapore": "Asia", "south korea": "Asia",
    "syria": "Asia", "tajikistan": "Asia", "turkey": "Asia", "turkmenistan": "Asia",
    "yemen": "Asia", "afghanistan": "Asia", "azerbaijan": "Asia", "bahrain": "Asia",
    "brunei": "Asia", "east timor (timor-leste)": "Asia", "georgia": "Asia",
    "iraq": "Asia",

    "netherlands": "Europe", "united kingdom": "Europe", "belgium": "Europe",
    "eu": "Europe", "ireland": "Europe", "spain": "Europe", "portugal": "Europe",
    "isle of man": "Europe", "germany": "Germany", "bulgaria": "Europe",
    "france": "Europe", "croatia": "Europe", "moldova": "Europe",
    "ukraine": "Europe", "denmark": "Europe", "finland": "Europe",
    "norway": "Europe", "san marino": "Europe", "switzerland": "Europe",
    "belarus": "Europe", "albania": "Europe",
    "andorra": "Europe", "austria": "Europe", "bosnia and herzegovina": "Europe",
    "czechia (czech republic)": "Europe", "estonia": "Europe",
    "greece": "Europe", "hungary": "Europe", "iceland": "Europe",
    "italy": "Europe", "latvia": "Europe", "lithuania": "Europe",
    "luxembourg": "Europe", "malta": "Europe",
    "monaco": "Europe", "montenegro": "Europe", "north macedonia (macedonia)": "Europe",
    "poland": "Europe", "romania": "Europe", "serbia": "Europe",
    "slovakia": "Europe", "slovenia": "Europe", "sweden": "Europe",
    "vatican city": "Europe", "russia": "Europe",

    "canada": "North America", "united states": "North America", "mexico": "North America",
    "antigua and barbuda": "North America", "bahamas": "North America", "barbados": "North America",
    "belize": "North America", "costa rica": "North America", "cuba": "North America",
    "dominica": "North America", "dominican republic": "North America", "el salvador": "North America",
    "grenada": "North America", "guatemala": "North America", "haiti": "North America",
    "honduras": "North America", "jamaica": "North America", "nicaragua": "North America",
    "panama": "North America", "saint kitts and nevis": "North America", "saint lucia": "North America",
    "saint vincent and the grenadines": "North America", "trinidad and tobago": "North America",

    "brazil": "South America", "argentina": "South America", "peru": "South America",
    "colombia": "South America", "chile": "South America", "bolivia": "South America",
    "ecuador": "South America", "guyana": "South America", "paraguay": "South America",
    "suriname": "South America", "uruguay": "South America", "venezuela": "South America",

    "australia": "Oceania", "new zealand": "Oceania", "fiji": "Oceania",
    "kiribati": "Oceania", "marshall islands": "Oceania", "micronesia": "Oceania",
    "nauru": "Oceania", "palau": "Oceania", "papua new guinea": "Oceania",
    "samoa": "Oceania", "solomon islands": "Oceania", "tonga": "Oceania",
    "tuvalu": "Oceania", "vanuatu": "Oceania",

    "siscia": "Ancient", "consz": "Ancient", "rome": "Ancient", "nicomedia": "Ancient",
    "constantinople": "Ancient", "mediolanum (milan)": "Ancient", "antioch": "Ancient",
    "ancient greece": "Ancient", "?": "Ancient", # Add "?" if it's used for unknown countries
    "thessalonica": "Ancient", "ussr": "Ancient", "yugoslavia": "Ancient",
    "rhodesia": "Ancient", "czechoslovakia": "Ancient", "east germany": "Ancient",
    "german democratic republic": "Ancient",
}

def get_region_for_country(country_name):
    """Retrieves the geographic region for a given country."""
    if not country_name:
        return "Unknown"
    normalized_country = country_name.lower().strip()
    return country_to_region_map.get(normalized_country, "Other")

def is_historical_item(country_name, year):
    """Determines if an item is historical based on country or year."""
    historical_countries = [
        "ussr", "yugoslavia", "rhodesia", "czechoslovakia", "east germany", "german democratic republic",
        "roman empire", "ancient greece", "seleucid", "siscia", "consz", "nicomedia", "constantinople",
        "rome", "thessalonica"
    ]
    if country_name and country_name.lower() in historical_countries:
        return True
    if year is not None and year < 1900 and year != 0:
        return True
    return False

# --- Email Functions ---
def send_email(to_email, subject, html_content, text_content=None):
    """Send email using Resend or fallback to SMTP"""
    try:
        if RESEND_AVAILABLE:
            # Use Resend
            resend.api_key = os.environ.get('RESEND_API_KEY', 're_iuKwsuj8_ANTNfGNb2w5BwHQqCtz1DxvL')
            from_email = os.environ.get('RESEND_FROM_EMAIL', 'noreply@mycoinshelf.com')
            
            params = {
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
            
            if text_content:
                params["text"] = text_content
            
            response = resend.Emails.send(params)
            print(f"Resend email sent successfully to {to_email}")
            return True
            
        else:
            # Fallback to SMTP (Gmail)
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = os.environ.get('SMTP_FROM_EMAIL', 'noreply@mycoinshelf.com')
            msg['To'] = to_email
            
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            smtp_email = os.environ.get('SMTP_EMAIL')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            
            if smtp_email and smtp_password:
                server.login(smtp_email, smtp_password)
                server.send_message(msg)
                server.quit()
                print(f"SMTP email sent successfully to {to_email}")
                return True
            else:
                print("SMTP credentials not configured")
                return False
            
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False

def generate_welcome_email(user_email):
    """Generate welcome email content for new users"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Welcome to CoinShelf!</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10b981, #3b82f6); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            .feature {{ background: #e5f3ff; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #3b82f6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🪙 CoinShelf</h1>
                <p>Welcome to Your Digital Coin Collection!</p>
            </div>
            <div class="content">
                <h2>Welcome to CoinShelf!</h2>
                <p>Thank you for joining CoinShelf! You're now part of a community of coin collectors and numismatists who are organizing their collections digitally.</p>
                
                <div class="feature">
                    <h3>🚀 What You Can Do:</h3>
                    <ul>
                        <li><strong>Track Your Collection:</strong> Add coins, banknotes, and bullion with detailed information</li>
                        <li><strong>Live Metal Prices:</strong> Get real-time gold and silver prices for your bullion</li>
                        <li><strong>World Map View:</strong> Visualize your collection by country on an interactive map</li>
                        <li><strong>Value Analytics:</strong> Track the total value of your collection over time</li>
                        <li><strong>Share Your Collection:</strong> Generate public links to showcase your treasures</li>
                    </ul>
                </div>
                
                <p><strong>Ready to get started?</strong> Log in to your account and add your first item!</p>
                <a href="https://mycoinshelf.com" class="button">Start Your Collection</a>
                
                <p><strong>Need Help?</strong> Check out our features and start building your digital collection today.</p>
            </div>
            <div class="footer">
                <p>Happy Collecting!<br>The CoinShelf Team</p>
                <p>Created with passion by <a href="https://www.instagram.com/oscarbrimelow/" style="color: #3b82f6;">Oscar Brimelow</a></p>
                <p>This email was sent to {user_email}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to CoinShelf!
    
    Thank you for joining CoinShelf! You're now part of a community of coin collectors and numismatists who are organizing their collections digitally.
    
    What You Can Do:
    - Track Your Collection: Add coins, banknotes, and bullion with detailed information
    - Live Metal Prices: Get real-time gold and silver prices for your bullion
    - World Map View: Visualize your collection by country on an interactive map
    - Value Analytics: Track the total value of your collection over time
    - Share Your Collection: Generate public links to showcase your treasures
    
    Ready to get started? Log in to your account and add your first item!
    Visit: https://mycoinshelf.com
    
    Need Help? Check out our features and start building your digital collection today.
    
    Happy Collecting!
    The CoinShelf Team
    
    Created with passion by Oscar Brimelow
    This email was sent to {user_email}
    """
    
    return html_content, text_content

def send_welcome_email(user_email):
    """Send welcome email to new users"""
    try:
        html_content, text_content = generate_welcome_email(user_email)
        
        success = send_email(
            to_email=user_email,
            subject="Welcome to CoinShelf! 🪙",
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            print(f"Welcome email sent successfully to {user_email}")
        else:
            print(f"Failed to send welcome email to {user_email}")
            
    except Exception as e:
        print(f"Error sending welcome email to {user_email}: {e}")

def generate_password_change_notification_email(user_email):
    """Generate password change notification email content"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>CoinShelf Password Changed</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10b981, #3b82f6); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .alert {{ background: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🪙 CoinShelf</h1>
                <p>Password Changed Successfully</p>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>Your CoinShelf account password has been successfully changed.</p>
                
                <div class="alert">
                    <strong>🔒 Security Notice:</strong> If you did not make this change, please contact us immediately and consider resetting your password.
                </div>
                
                <p><strong>When this happened:</strong> {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                
                <p>Your account is now secured with your new password. You can continue using CoinShelf as normal.</p>
                
                <p><strong>Need help?</strong> If you have any questions or concerns, please don't hesitate to reach out.</p>
            </div>
            <div class="footer">
                <p>Best regards,<br>The CoinShelf Team</p>
                <p>This email was sent to {user_email}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    CoinShelf Password Changed
    
    Hello!
    
    Your CoinShelf account password has been successfully changed.
    
    SECURITY NOTICE: If you did not make this change, please contact us immediately and consider resetting your password.
    
    When this happened: {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
    
    Your account is now secured with your new password. You can continue using CoinShelf as normal.
    
    Need help? If you have any questions or concerns, please don't hesitate to reach out.
    
    Best regards,
    The CoinShelf Team
    
    This email was sent to {user_email}
    """
    
    return html_content, text_content

def send_password_change_notification(user_email):
    """Send password change notification email"""
    try:
        html_content, text_content = generate_password_change_notification_email(user_email)
        
        success = send_email(
            to_email=user_email,
            subject="CoinShelf Password Changed - Security Alert",
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            print(f"Password change notification sent successfully to {user_email}")
        else:
            print(f"Failed to send password change notification to {user_email}")
            
    except Exception as e:
        print(f"Error sending password change notification to {user_email}: {e}")

def generate_password_reset_email(user_email, reset_token, reset_url):
    """Generate password reset email content"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reset Your CoinShelf Password</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10b981, #3b82f6); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🪙 CoinShelf</h1>
                <p>Password Reset Request</p>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>We received a request to reset your password for your CoinShelf account.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_url}" class="button">Reset Password</a>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you didn't request this password reset, you can safely ignore this email.</p>
                <p>If you're having trouble clicking the button, copy and paste this URL into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_url}</p>
            </div>
            <div class="footer">
                <p>Best regards,<br>The CoinShelf Team</p>
                <p>This email was sent to {user_email}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    CoinShelf Password Reset
    
    Hello!
    
    We received a request to reset your password for your CoinShelf account.
    
    Click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request this password reset, you can safely ignore this email.
    
    Best regards,
    The CoinShelf Team
    
    This email was sent to {user_email}
    """
    
    return html_content, text_content




# --- Routes ---

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    if path != "" and os.path.exists(os.path.join("frontend", path)):
        return send_from_directory('frontend', path)
    else:
        return send_from_directory('frontend', 'index.html')

@app.route('/api/test_email', methods=['POST'])
def test_email():
    """Test endpoint to verify email setup"""
    try:
        test_email_address = request.json.get('email')
        if not test_email_address:
            return jsonify({'message': 'Email address required'}), 400
        
        # Test email content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CoinShelf Email Test</title>
        </head>
        <body>
            <h1>🎉 Email Test Successful!</h1>
            <p>Your CoinShelf email setup is working correctly.</p>
            <p>This email was sent from: noreply@mycoinshelf.com</p>
            <p>Timestamp: """ + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC") + """</p>
        </body>
        </html>
        """
        
        text_content = """
        CoinShelf Email Test
        
        Your CoinShelf email setup is working correctly.
        This email was sent from: noreply@mycoinshelf.com
        Timestamp: """ + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        success = send_email(
            to_email=test_email_address,
            subject="CoinShelf Email Test",
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            return jsonify({'message': 'Test email sent successfully!'}), 200
        else:
            return jsonify({'message': 'Failed to send test email'}), 500
            
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        print("DEBUG: Registration failed - missing email or password.")
        return jsonify({'message': 'Email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        print(f"DEBUG: Registration failed - user with email {email} already exists.")
        return jsonify({'message': 'User with that email already exists'}), 409

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    # Send welcome email
    send_welcome_email(email)
    
    print(f"DEBUG: User {email} registered successfully.")
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    print(f"DEBUG: Attempting login for email: {email}")

    if not email or not password:
        print("DEBUG: Login failed - Missing email or password in request.")
        return jsonify({'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        print(f"DEBUG: Login failed - User with email {email} not found.")
        return jsonify({'message': 'Invalid credentials'}), 401

    print(f"DEBUG: User found: {user.email}")
    print(f"DEBUG: Provided password: {password}")
    print(f"DEBUG: Stored password hash: {user.password_hash}")

    if not check_password_hash(user.password_hash, password):
        print("DEBUG: Login failed - Password hash mismatch.")
        return jsonify({'message': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24) # Token expires in 24 hours
    }, app.config['JWT_SECRET_KEY'], algorithm="HS256")

    print(f"DEBUG: User {email} logged in successfully. Token generated.")
    return jsonify({'token': token}), 200

@app.route('/api/change_password', methods=['POST'])
@jwt_required
def change_password(current_user):
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'message': 'Current and new passwords are required'}), 400

    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({'message': 'Incorrect current password'}), 401

    if len(new_password) < 6:
        return jsonify({'message': 'New password must be at least 6 characters long'}), 400

    current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    
    # Send password change notification email
    send_password_change_notification(current_user.email)
    
    return jsonify({'message': 'Password changed successfully!'}), 200

@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    """Request a password reset email"""
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return jsonify({'message': 'If an account with that email exists, a password reset link has been sent.'}), 200

    # Generate reset token
    reset_token = str(uuid.uuid4())
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    # Save reset token to database
    reset_token_obj = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    db.session.add(reset_token_obj)
    db.session.commit()

    # Generate reset URL - point to main app with token parameter
    reset_url = f"https://mycoinshelf.com/?token={reset_token}"

    # Generate email content
    html_content, text_content = generate_password_reset_email(email, reset_token, reset_url)

    # Send email
    email_sent = send_email(
        to_email=email,
        subject="Reset Your CoinShelf Password",
        html_content=html_content,
        text_content=text_content
    )

    if email_sent:
        return jsonify({'message': 'If an account with that email exists, a password reset link has been sent.'}), 200
    else:
        return jsonify({'message': 'Failed to send password reset email. Please try again later.'}), 500

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    """Reset password using token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({'message': 'Token and new password are required'}), 400

    if len(new_password) < 6:
        return jsonify({'message': 'New password must be at least 6 characters long'}), 400

    # Find valid reset token
    reset_token_obj = PasswordResetToken.query.filter_by(
        token=token,
        used=False
    ).first()

    if not reset_token_obj:
        return jsonify({'message': 'Invalid or expired reset token'}), 400

    # Check if token is expired
    if datetime.datetime.utcnow() > reset_token_obj.expires_at:
        return jsonify({'message': 'Reset token has expired'}), 400

    # Get user and update password
    user = User.query.get(reset_token_obj.user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Update password
    user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    
    # Mark token as used
    reset_token_obj.used = True
    
    db.session.commit()

    return jsonify({'message': 'Password reset successfully!'}), 200


@app.route('/api/coins', methods=['GET'])
@jwt_required
def get_coins(current_user):
    coins = Coin.query.filter_by(user_id=current_user.id).all()
    # Serialize coins, including calculated region and isHistorical
    output = []
    for coin in coins:
        coin_data = {
            'id': coin.id,
            'type': coin.type,
            'country': coin.country,
            'year': coin.year,
            'denomination': coin.denomination,
            'value': coin.value,
            'quantity': coin.quantity, # Include quantity from DB
            'notes': coin.notes,
            'referenceUrl': coin.referenceUrl,
            'localImagePath': coin.localImagePath,
            'region': coin.region, # Include region from DB
            'isHistorical': coin.isHistorical, # Include isHistorical from DB
            'weight_grams': coin.weight_grams, # Include weight for bullion
            'purity_percent': coin.purity_percent # Include purity for bullion
        }
        output.append(coin_data)
    return jsonify(output), 200

@app.route('/api/coins', methods=['POST'])
@jwt_required
def add_coin(current_user):
    data = request.get_json()
    
    # Required fields validation
    if not data.get('country') or not data.get('denomination'):
        return jsonify({'message': 'Country and Denomination are required fields.'}), 400

    # Calculate region and isHistorical on the backend
    country_name = data.get('country').strip()
    year_value = data.get('year')
    region = get_region_for_country(country_name)
    is_historical = is_historical_item(country_name, year_value)

    new_coin = Coin(
        user_id=current_user.id,
        type=data.get('type'),
        country=country_name,
        year=year_value,
        denomination=data.get('denomination').strip(),
        value=data.get('value'),
        quantity=data.get('quantity', 1), # Set quantity, default to 1
        notes=data.get('notes'),
        referenceUrl=data.get('referenceUrl'),
        localImagePath=data.get('localImagePath'),
        region=region, # Set calculated region
        isHistorical=is_historical, # Set calculated historical flag
        weight_grams=data.get('weight_grams'), # Set weight for bullion
        purity_percent=data.get('purity_percent') # Set purity for bullion
    )
    db.session.add(new_coin)
    db.session.commit()
    return jsonify({'message': 'Coin added successfully!', 'id': new_coin.id}), 201

@app.route('/api/coins/<int:coin_id>', methods=['PUT'])
@jwt_required
def update_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first()
    if not coin:
        return jsonify({'message': 'Coin not found or unauthorized'}), 404

    data = request.get_json()

    # Required fields validation
    if not data.get('country') or not data.get('denomination'):
        return jsonify({'message': 'Country and Denomination are required fields.'}), 400

    # Calculate region and isHistorical on the backend
    country_name = data.get('country').strip()
    year_value = data.get('year')
    coin.region = get_region_for_country(country_name)
    coin.isHistorical = is_historical_item(country_name, year_value)

    coin.type = data.get('type', coin.type)
    coin.country = country_name
    coin.year = year_value
    coin.denomination = data.get('denomination').strip()
    coin.value = data.get('value', coin.value)
    coin.quantity = data.get('quantity', coin.quantity) # Update quantity
    coin.notes = data.get('notes', coin.notes)
    coin.referenceUrl = data.get('referenceUrl', coin.referenceUrl)
    coin.localImagePath = data.get('localImagePath', coin.localImagePath)
    coin.weight_grams = data.get('weight_grams', coin.weight_grams) # Update weight for bullion
    coin.purity_percent = data.get('purity_percent', coin.purity_percent) # Update purity for bullion

    db.session.commit()
    return jsonify({'message': 'Coin updated successfully!'}), 200

@app.route('/api/coins/<int:coin_id>', methods=['DELETE'])
@jwt_required
def delete_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first()
    if not coin:
        return jsonify({'message': 'Coin not found or unauthorized'}), 404

    db.session.delete(coin)
    db.session.commit()
    return jsonify({'message': 'Coin deleted successfully!'}), 200

@app.route('/api/coins/bulk_upload', methods=['POST'])
@jwt_required
def bulk_upload_coins(current_user):
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({'message': 'Payload must be a JSON array of coin objects'}), 400

    added_count = 0
    errors = []
    for item_data in data:
        try:
            # Validate essential fields
            if not item_data.get('country') or not item_data.get('denomination'):
                errors.append(f"Skipping item due to missing country or denomination: {item_data.get('denomination')} from {item_data.get('country')}")
                continue

            # Calculate region and isHistorical on the backend
            country_name = item_data.get('country').strip()
            year_value = item_data.get('year') # Corrected: Was year_data.get('year')
            region = get_region_for_country(country_name)
            is_historical = is_historical_item(country_name, year_value)

            new_coin = Coin(
                user_id=current_user.id,
                type=item_data.get('type', 'Coin'), # Default to Coin if not provided
                country=country_name,
                year=year_value, # Corrected: Was year_data.get('year')
                denomination=item_data.get('denomination').strip(),
                value=item_data.get('value', 0.0),
                quantity=item_data.get('quantity', 1), # Set quantity, default to 1
                notes=item_data.get('notes'),
                referenceUrl=item_data.get('referenceUrl'),
                localImagePath=item_data.get('localImagePath', "https://placehold.co/300x300/1f2937/d1d5db?text=No+Image"),
                region=region, # Set calculated region
                isHistorical=is_historical, # Set calculated historical flag
                weight_grams=item_data.get('weight_grams'), # Set weight for bullion
                purity_percent=item_data.get('purity_percent') # Set purity for bullion
            )
            db.session.add(new_coin)
            added_count += 1
        except Exception as e:
            errors.append(f"Error adding item '{item_data.get('denomination', 'unknown')}': {str(e)}")
            db.session.rollback() # Rollback the current transaction on error

    db.session.commit() # Commit all successfully added coins

    if added_count > 0 and len(errors) == 0:
        return jsonify({'message': f'Successfully added {added_count} items.', 'added_count': added_count}), 200
    elif added_count > 0 and len(errors) > 0:
        return jsonify({'message': f'Added {added_count} items with {len(errors)} errors.', 'added_count': added_count, 'errors': errors}), 200
    else:
        return jsonify({'message': f'Failed to add any items. Total errors: {len(errors)}', 'errors': errors}), 400

@app.route('/api/coins/clear_all', methods=['DELETE'])
@jwt_required
def clear_all_coins(current_user):
    # Delete all coins associated with the current user
    num_deleted = Coin.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'message': f'{num_deleted} coins deleted successfully.'}), 200

# --- New Metal Prices API Endpoint ---
@app.route('/api/prices/metals', methods=['GET'])
def get_metal_prices():
    """Fetch live gold and silver prices using multiple reliable sources"""
    try:
        # Try Yahoo Finance first (no API key required)
        yahoo_prices = fetch_yahoo_finance_prices()
        if yahoo_prices and yahoo_prices['gold_usd_per_oz'] > 0 and yahoo_prices['silver_usd_per_oz'] > 0:
            return jsonify({
                'gold_usd_per_oz': round(yahoo_prices['gold_usd_per_oz'], 2),
                'silver_usd_per_oz': round(yahoo_prices['silver_usd_per_oz'], 2),
                'gold_zar_per_oz': round(yahoo_prices['gold_zar_per_oz'], 2),
                'silver_zar_per_oz': round(yahoo_prices['silver_zar_per_oz'], 2),
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'source': 'Yahoo Finance',
                'lastUpdate': yahoo_prices.get('lastUpdate')
            }), 200
        
        # Use the new reliable price fetcher if available
        if PRICE_FETCHER_AVAILABLE and price_fetcher:
            prices = price_fetcher.get_prices()
            
            if prices and prices['gold_usd_per_oz'] > 0 and prices['silver_usd_per_oz'] > 0:
                return jsonify({
                    'gold_usd_per_oz': round(prices['gold_usd_per_oz'], 2),
                    'silver_usd_per_oz': round(prices['silver_usd_per_oz'], 2),
                    'gold_zar_per_oz': round(prices['gold_zar_per_oz'], 2),
                    'silver_zar_per_oz': round(prices['silver_zar_per_oz'], 2),
                    'timestamp': datetime.datetime.utcnow().isoformat(),
                    'source': 'reliable_apis',
                    'lastUpdate': prices.get('lastUpdate')
                }), 200
        
        # Fallback to CoinGecko if reliable fetcher is not available or fails
        return _fallback_to_coingecko()
            
    except Exception as e:
        print(f"Error with reliable price fetcher: {e}")
        return _fallback_to_coingecko()

def _fallback_to_coingecko():
    """Fallback to CoinGecko API"""
    try:
        print("Trying CoinGecko API as fallback...")
        
        # First try to get USD/ZAR exchange rate
        zar_rate = 18.5  # Default fallback rate
        try:
            zar_url = "https://api.coingecko.com/api/v3/simple/price"
            zar_params = {
                'ids': 'usd-coin',
                'vs_currencies': 'zar'
            }
            zar_response = requests.get(zar_url, params=zar_params, timeout=10)
            if zar_response.status_code == 200:
                zar_data = zar_response.json()
                zar_rate = zar_data.get('usd-coin', {}).get('zar', 18.5)
                print(f"CoinGecko ZAR rate: {zar_rate}")
        except Exception as zar_error:
            print(f"CoinGecko ZAR rate error: {zar_error}")
        
        # Get gold and silver prices
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'gold,silver',
            'vs_currencies': 'usd'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract gold and silver prices (prices are per gram, convert to per ounce)
            gold_price_per_gram = data.get('gold', {}).get('usd', 0)
            silver_price_per_gram = data.get('silver', {}).get('usd', 0)
            
            # Convert from per gram to per ounce (1 ounce = 31.1035 grams)
            gold_price_per_oz = gold_price_per_gram * 31.1035
            silver_price_per_oz = silver_price_per_gram * 31.1035
            
            if gold_price_per_oz > 0 and silver_price_per_oz > 0:
                print(f"CoinGecko prices - Gold: ${gold_price_per_oz:.2f}, Silver: ${silver_price_per_oz:.2f}")
                return jsonify({
                    'gold_usd_per_oz': round(gold_price_per_oz, 2),
                    'silver_usd_per_oz': round(silver_price_per_oz, 2),
                    'gold_zar_per_oz': round(gold_price_per_oz * zar_rate, 2),
                    'silver_zar_per_oz': round(silver_price_per_oz * zar_rate, 2),
                    'timestamp': datetime.datetime.utcnow().isoformat(),
                    'source': 'CoinGecko'
                }), 200
            else:
                print("CoinGecko returned zero prices")
        else:
            print(f"CoinGecko HTTP error: {response.status_code}")
        
        # Final fallback to static prices
        print("Using static fallback prices")
        return jsonify({
            'gold_usd_per_oz': 2300.00,
            'silver_usd_per_oz': 29.50,
            'gold_zar_per_oz': 42550.00,  # 2300 * 18.5
            'silver_zar_per_oz': 545.75,  # 29.50 * 18.5
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'note': 'Using fallback prices - all APIs unavailable',
            'source': 'fallback'
        }), 200
        
    except Exception as e:
        print(f"Error in CoinGecko fallback: {e}")
        return jsonify({
            'gold_usd_per_oz': 2300.00,
            'silver_usd_per_oz': 29.50,
            'gold_zar_per_oz': 42550.00,  # 2300 * 18.5
            'silver_zar_per_oz': 545.75,  # 29.50 * 18.5
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'note': 'Using fallback prices - network error',
            'source': 'fallback'
        }), 200

# --- New Public Collection Endpoints ---

@app.route('/api/generate_public_collection_link', methods=['POST'])
@jwt_required
def generate_public_collection_link(current_user):
    # Check if a public link already exists for this user
    public_collection_link = PublicCollection.query.filter_by(user_id=current_user.id).first()

    if public_collection_link:
        # If exists, update it with a new UUID to make the old link invalid
        public_collection_link.id = str(uuid.uuid4())
        public_collection_link.created_at = datetime.datetime.utcnow()
        message = "Public link updated successfully!"
    else:
        # If not, create a new one
        new_public_link = PublicCollection(user_id=current_user.id)
        db.session.add(new_public_link)
        public_collection_link = new_public_link # Reference the new object
        message = "Public link generated successfully!"

    db.session.commit()
    return jsonify({'message': message, 'public_id': public_collection_link.id}), 200

@app.route('/api/public_collection_link', methods=['GET'])
@jwt_required
def get_public_collection_link(current_user):
    public_collection_link = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if public_collection_link:
        return jsonify({'public_id': public_collection_link.id}), 200
    return jsonify({'message': 'No public link found for this user.'}), 404

@app.route('/api/revoke_public_collection_link', methods=['POST'])
@jwt_required
def revoke_public_collection_link(current_user):
    public_collection_link = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if public_collection_link:
        db.session.delete(public_collection_link)
        db.session.commit()
        return jsonify({'message': 'Public link revoked successfully!'}), 200
    return jsonify({'message': 'No public link found to revoke.'}), 404

@app.route('/api/public_coins/<string:public_id>', methods=['GET'])
def get_public_coins(public_id):
    # Find the user associated with the public_id
    public_link_entry = PublicCollection.query.filter_by(id=public_id).first()

    if not public_link_entry:
        return jsonify({'message': 'Public collection not found or invalid ID.'}), 404

    user = User.query.get(public_link_entry.user_id)
    if not user:
        return jsonify({'message': 'Associated user not found.'}), 404 # Should ideally not happen if DB integrity is maintained

    # Fetch coins belonging to this user
    coins = Coin.query.filter_by(user_id=user.id).all()

    # Serialize coins for public view
    output = []
    for coin in coins:
        coin_data = {
            'id': coin.id, # Include ID for sorting/reference if needed in public view
            'type': coin.type,
            'country': coin.country,
            'year': coin.year,
            'denomination': coin.denomination,
            'value': coin.value,
            'quantity': coin.quantity, # Include quantity for public view
            'notes': coin.notes,
            'referenceUrl': coin.referenceUrl,
            'localImagePath': coin.localImagePath,
            'region': coin.region,
            'isHistorical': coin.isHistorical,
            'weight_grams': coin.weight_grams, # Include weight for bullion
            'purity_percent': coin.purity_percent, # Include purity for bullion
            'owner_email': user.email # Include owner's email for display in public view
        }
        output.append(coin_data)
    
    return jsonify(output), 200

# --- Database Migration Endpoint ---
@app.route('/api/migrate_database', methods=['GET', 'POST'])
def migrate_database():
    """Add missing columns to existing database"""
    try:
        print("Starting database migration...")
        
        # Check if weight_grams column exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'coin' AND column_name = 'weight_grams'
        """))
        
        if not result.fetchone():
            # Add weight_grams column
            db.session.execute(text("ALTER TABLE coin ADD COLUMN weight_grams FLOAT"))
            print("Added weight_grams column to coin table")
        else:
            print("weight_grams column already exists")
        
        # Check if purity_percent column exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'coin' AND column_name = 'purity_percent'
        """))
        
        if not result.fetchone():
            # Add purity_percent column
            db.session.execute(text("ALTER TABLE coin ADD COLUMN purity_percent FLOAT"))
            print("Added purity_percent column to coin table")
        else:
            print("purity_percent column already exists")
        
        # Check if quantity column exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'coin' AND column_name = 'quantity'
        """))
        
        if not result.fetchone():
            # Add quantity column with default value 1
            db.session.execute(text("ALTER TABLE coin ADD COLUMN quantity INTEGER DEFAULT 1"))
            print("Added quantity column to coin table")
        else:
            print("quantity column already exists")
        
        db.session.commit()
        print("Database migration completed successfully!")
        return jsonify({'message': 'Database migration completed successfully!'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Migration error: {e}")
        return jsonify({'message': f'Migration failed: {str(e)}'}), 500

# --- Database Initialization (Run once to create tables) ---
# NOTE: @app.before_request is used instead of @app.before_first_request due to Flask version compatibility.
# This function will run before each request, but db.create_all() only creates tables if they don't exist.
@app.before_request
def create_tables():
    # Only create tables if they don't exist. This is safe to call on every request.
    # We use app.app_context() to ensure we're in the right Flask application context.
    with app.app_context():
        db.create_all()
        
        # Check and add missing columns if needed
        try:
            # Check if weight_grams column exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'coin' AND column_name = 'weight_grams'
            """))
            
            if not result.fetchone():
                # Add weight_grams column
                db.session.execute(text("ALTER TABLE coin ADD COLUMN weight_grams FLOAT"))
                print("Added weight_grams column to coin table")
            
            # Check if purity_percent column exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'coin' AND column_name = 'purity_percent'
            """))
            
            if not result.fetchone():
                # Add purity_percent column
                db.session.execute(text("ALTER TABLE coin ADD COLUMN purity_percent FLOAT"))
                print("Added purity_percent column to coin table")
            
            # Check if quantity column exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'coin' AND column_name = 'quantity'
            """))
            
            if not result.fetchone():
                # Add quantity column with default value 1
                db.session.execute(text("ALTER TABLE coin ADD COLUMN quantity INTEGER DEFAULT 1"))
                print("Added quantity column to coin table")
            
            db.session.commit()
        except Exception as e:
            print(f"Database migration check failed: {e}")
            db.session.rollback()
        
        # Optional: Create a default user if none exists for easy setup
        if not User.query.first():
            print("No users found. Creating a default admin user.")
            # CHANGE THIS DEFAULT EMAIL/PASSWORD for your own initial setup!
            default_email = os.environ.get('DEFAULT_ADMIN_EMAIL') or 'admin@example.com'
            default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD') or 'password123'
            hashed_password = generate_password_hash(default_password, method='pbkdf2:sha256')
            default_user = User(email=default_email, password_hash=hashed_password)
            db.session.add(default_user)
            db.session.commit()
            print(f"Default user '{default_email}' created. Please change this in production!")

if __name__ == '__main__':
    # When running locally, you can access the backend at http://127.0.0.1:5000/
    app.run(debug=True)
