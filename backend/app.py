# backend/app.py

import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

# Import configuration
from config import Config

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

    def __repr__(self):
        return f'<User {self.email}>'

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False, default='Coin') # Default added
    country = db.Column(db.String(100), nullable=True) # CHANGED to nullable=True
    year = db.Column(db.Integer, nullable=True)
    denomination = db.Column(db.String(100), nullable=True) # CHANGED to nullable=True
    value = db.Column(db.Float, nullable=False, default=0.0) # Default added
    notes = db.Column(db.Text, nullable=True)
    # MODIFIED: Changed from db.String(255) to db.Text to allow longer URLs
    referenceUrl = db.Column(db.Text, nullable=True)
    # MODIFIED: Changed from db.String(255) to db.Text to allow longer image paths/URLs
    localImagePath = db.Column(db.Text, nullable=True)
    region = db.Column(db.String(100), nullable=True)
    isHistorical = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'country': self.country,
            'year': self.year,
            'denomination': self.denomination,
            'value': self.value,
            'notes': self.notes,
            'referenceUrl': self.referenceUrl,
            'localImagePath': self.localImagePath,
            'region': self.region,
            'isHistorical': self.isHistorical
        }

    def __repr__(self):
        return f'<Coin {self.country} {self.denomination}>'

# --- JWT Authentication Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # JWT is passed in the Authorization header as "Bearer <token>"
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'Token is invalid or user not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# --- UTILITY FOR REGION MAPPING & HISTORICAL FLAG ---
def get_region_for_country(country_name):
    """
    Determines the geographic region for a given country name.
    If country_name is None or empty, defaults to "Other".
    """
    if not country_name:
        return "Other"

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
        "isle of man": "Europe", "germany": "Europe", "bulgaria": "Europe",
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
        "ancient greece": "Ancient", "?": "Ancient",
        "thessalonica": "Ancient", "ussr": "Ancient", "yugoslavia": "Ancient",
        "rhodesia": "Ancient", "czechoslovakia": "Ancient", "east germany": "Ancient",
        "german democratic republic": "Ancient",
    }
    normalized_country = country_name.lower().strip()
    return country_to_region_map.get(normalized_country, "Other")

def get_is_historical_flag(country_name, year):
    """
    Determines if a coin/banknote is historical based on country or year.
    """
    historical_countries = ["ussr", "yugoslavia", "rhodesia", "czechoslovakia", "east germany", "german democratic republic", "roman empire", "ancient greece", "seleucid", "siscia", "consz", "nicomedia", "constantinople", "rome", "thessalonica"]

    country_for_check = country_name.lower() if country_name else ''

    is_historical = country_for_check in historical_countries or \
                    (year is not None and year < 1900 and year != 0)
    return is_historical


# --- Routes ---

@app.route('/')
def home():
    return "CoinShelf Backend is Running!"

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required!'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists!'}), 409

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required!'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials!'}), 401

    # Generate JWT
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24) # Token expires in 24 hours
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token, 'user_id': user.id}), 200 # Return user_id with token

@app.route('/api/change_password', methods=['POST'])
@token_required
def change_password(current_user): # current_user is passed by the token_required decorator
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({"message": "Current and new passwords are required."}), 400

    # Verify current password
    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({"message": "Invalid current password."}), 401

    # Hash the new password
    hashed_new_password = generate_password_hash(new_password, method='pbkdf2:sha256')

    # Update user's password in the database
    current_user.password_hash = hashed_new_password
    db.session.commit()

    return jsonify({"message": "Password updated successfully!"}), 200


@app.route('/api/coins', methods=['GET'])
@token_required
def get_coins(current_user):
    coins = Coin.query.filter_by(user_id=current_user.id).all()
    return jsonify([coin.to_dict() for coin in coins]), 200

# NEW: Public read-only endpoint for collections
@app.route('/api/public/collection/<int:user_id>', methods=['GET'])
def get_public_collection(user_id):
    """
    Retrieves a read-only collection for a given user ID.
    This endpoint does NOT require authentication.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found.'}), 404

    coins = Coin.query.filter_by(user_id=user_id).all()
    
    # You might want to filter out more sensitive data here if Coin.to_dict()
    # includes anything that shouldn't be publicly visible.
    # For now, Coin.to_dict() is fine as it doesn't expose User details.
    return jsonify({
        'owner_id': user_id, # Can be useful for frontend to display "Collection of User X"
        'collection': [coin.to_dict() for coin in coins]
    }), 200


@app.route('/api/coins', methods=['POST'])
@token_required
def add_coin(current_user):
    data = request.get_json()

    country_input = data.get('country')
    year_input = data.get('year') or None

    # Calculate region and isHistorical on the backend
    region = get_region_for_country(country_input)
    is_historical = get_is_historical_flag(country_input, year_input)

    new_coin = Coin(
        user_id=current_user.id,
        type=data.get('type', 'Coin'),
        country=country_input,
        year=year_input,
        denomination=data.get('denomination'),
        value=data.get('value', 0.0),
        notes=data.get('notes'),
        referenceUrl=data.get('referenceUrl'),
        localImagePath=data.get('localImagePath', "https://placehold.co/300x300/1f2937/d1d5db?text=No+Image"),
        region=region, # Set region from backend logic
        isHistorical=is_historical # Set isHistorical from backend logic
    )
    db.session.add(new_coin)
    db.session.commit()
    return jsonify({'message': 'Coin added successfully!', 'coin_id': new_coin.id}), 201

@app.route('/api/coins/<int:coin_id>', methods=['PUT'])
@token_required
def update_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first()
    if not coin:
        return jsonify({'message': 'Coin not found or unauthorized!'}), 404

    data = request.get_json()

    country_input = data.get('country', coin.country) # Use existing if not provided
    year_input = data.get('year', coin.year) or None # Use existing if not provided

    # Calculate region and isHistorical on the backend
    region = get_region_for_country(country_input)
    is_historical = get_is_historical_flag(country_input, year_input)

    # Update fields if provided in the request
    coin.type = data.get('type', coin.type)
    coin.country = country_input # Use potentially updated country
    coin.year = year_input # Use potentially updated year
    coin.denomination = data.get('denomination', coin.denomination)
    coin.value = data.get('value', coin.value)
    coin.notes = data.get('notes', coin.notes)
    coin.referenceUrl = data.get('referenceUrl', coin.referenceUrl)
    coin.localImagePath = data.get('localImagePath', coin.localImagePath)
    coin.region = region # Update region from backend logic
    coin.isHistorical = is_historical # Update isHistorical from backend logic

    db.session.commit()
    return jsonify({'message': 'Coin updated successfully!'}), 200

@app.route('/api/coins/<int:coin_id>', methods=['DELETE'])
@token_required
def delete_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first()
    if not coin:
        return jsonify({'message': 'Coin not found or unauthorized!'}), 404

    db.session.delete(coin)
    db.session.commit()
    return jsonify({'message': 'Coin deleted successfully!'}), 200

@app.route('/api/coins/bulk_upload', methods=['POST'])
@token_required
def bulk_upload_coins(current_user):
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({'message': 'Expected a JSON array of coin objects.'}), 400

    imported_count = 0
    errors = []

    for item_data in data_list:
        try:
            # Ensure 'id' is not set for new items, as the database generates it
            item_data.pop('id', None)

            # Handle year parsing
            year_input = item_data.get('year')
            parsed_year = year_input if isinstance(year_input, int) else (int(year_input) if str(year_input).isdigit() else None)

            # Use provided country for region/historical check, default to empty string if not present
            country_input_for_logic = item_data.get('country', '')

            # Calculate region and isHistorical on the backend
            final_region = get_region_for_country(country_input_for_logic)
            final_is_historical = get_is_historical_flag(country_input_for_logic, parsed_year)

            new_coin = Coin(
                user_id=current_user.id,
                type=item_data.get('type', 'Coin'),
                country=item_data.get('country'), # Will be None if not provided in JSON
                year=parsed_year,
                denomination=item_data.get('denomination'), # Will be None if not provided in JSON
                value=item_data.get('value', 0.0),
                notes=item_data.get('notes'),
                referenceUrl=item_data.get('referenceUrl'),
                localImagePath=item_data.get('localImagePath', "https://placehold.co/300x300/1f2937/d1d5db?text=No+Image"),
                region=final_region, # Set region from backend logic
                isHistorical=final_is_historical # Set isHistorical from backend logic
            )
            db.session.add(new_coin)
            imported_count += 1
        except Exception as e:
            errors.append(f"Error processing item (raw data: {item_data}): {str(e)}") # Added raw data for better debugging
            db.session.rollback() # Rollback current transaction if an error occurs

    db.session.commit() # Commit all successfully added items that didn't error out

    if errors:
        return jsonify({
            'message': f'Successfully imported {imported_count} items with some errors.',
            'errors': errors
        }), 207 # 207 Multi-Status
    else:
        return jsonify({'message': f'Successfully imported {imported_count} items.'}), 201

@app.route('/api/coins/clear_all', methods=['DELETE'])
@token_required
def clear_all_coins(current_user):
    try:
        # Delete all coins belonging to the current user
        num_deleted = Coin.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'message': f'Successfully deleted {num_deleted} items from your collection.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to clear collection: {str(e)}'}), 500


# --- Database Initialization (Run once to create tables) ---
# NOTE: @app.before_request is used instead of @app.before_first_request due to Flask version compatibility.
# This function will run before each request, but db.create_all() only creates tables if they don't exist.
@app.before_request
def create_tables():
    # Only create tables if they don't exist. This is safe to call on every request.
    # We use app.app_context() to ensure we're in the right Flask application context.
    with app.app_context():
        db.create_all()
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
    # When running locally, you can access the backend at http://127.0.0.1:5000
    app.run(debug=True, host='0.0.0.0', port=5000)
