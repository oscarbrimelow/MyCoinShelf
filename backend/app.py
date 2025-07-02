# backend/app.py

import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import uuid # Import uuid for generating unique public IDs

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
    # New: One user can have one public collection link
    public_collection = db.relationship('PublicCollection', backref='user', uselist=False, lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g., Coin, Banknote
    country = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    denomination = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float) # Estimated value
    notes = db.Column(db.Text)
    referenceUrl = db.Column(db.String(500))
    localImagePath = db.Column(db.String(500)) # Path to local image
    # New fields for better data management and charting
    region = db.Column(db.String(100)) # e.g., Europe, Asia, North America
    isHistorical = db.Column(db.Boolean, default=False) # True if from a historical entity or pre-1900

    def __repr__(self):
        return f'<Coin {self.denomination} from {self.country} ({self.year})>'

# New: Model for Public Collection Links
class PublicCollection(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, nullable=False) # UUID for public link
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<PublicCollection ID: {self.id} for User: {self.user_id}>'

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


# --- Routes ---

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
    return jsonify({'message': 'Password changed successfully!'}), 200


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
            'notes': coin.notes,
            'referenceUrl': coin.referenceUrl,
            'localImagePath': coin.localImagePath,
            'region': coin.region, # Include region from DB
            'isHistorical': coin.isHistorical # Include isHistorical from DB
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
        notes=data.get('notes'),
        referenceUrl=data.get('referenceUrl'),
        localImagePath=data.get('localImagePath'),
        region=region, # Set calculated region
        isHistorical=is_historical # Set calculated historical flag
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
    coin.notes = data.get('notes', coin.notes)
    coin.referenceUrl = data.get('referenceUrl', coin.referenceUrl)
    coin.localImagePath = data.get('localImagePath', coin.localImagePath)

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
                notes=item_data.get('notes'),
                referenceUrl=item_data.get('referenceUrl'),
                localImagePath=item_data.get('localImagePath', "https://placehold.co/300x300/1f2937/d1d5db?text=No+Image"),
                region=region, # Set calculated region
                isHistorical=is_historical # Set calculated historical flag
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
            'notes': coin.notes,
            'referenceUrl': coin.referenceUrl,
            'localImagePath': coin.localImagePath,
            'region': coin.region,
            'isHistorical': coin.isHistorical,
            'owner_email': user.email # Include owner's email for display in public view
        }
        output.append(coin_data)
    
    return jsonify(output), 200


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
    # When running locally, you can access the backend at http://127.0.0.1:5000/
    app.run(debug=True)
