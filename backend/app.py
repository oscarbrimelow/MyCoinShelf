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
import requests # NEW: Import requests for making HTTP requests to external APIs

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
    # Changed 'coins' to 'items' to better reflect different collection types
    items = db.relationship('Item', backref='owner', lazy=True) # One user has many items (coins, banknotes, bullion)
    # New: One user can have one public collection link
    public_collection = db.relationship('PublicCollection', backref='user', uselist=False, lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

# RENAMED: 'Coin' model is now 'Item' to be more generic for coins, banknotes, and bullion
class Item(db.Model):
    __tablename__ = 'item' # Ensure the table name is 'item'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False, default='coin') # NEW: 'coin', 'banknote', 'bullion'
    country = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    denomination = db.Column(db.String(100), nullable=True) # Changed to nullable=True for bullion
    value = db.Column(db.Float) # This will be the user-inputted value for coins/banknotes, or the calculated value for bullion.
    notes = db.Column(db.Text)
    reference_url = db.Column(db.String(500))
    image_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # NEW: Fields for Bullion
    bullion_type = db.Column(db.String(50), nullable=True) # 'gold', 'silver'
    weight_grams = db.Column(db.Float, nullable=True)
    purity_percent = db.Column(db.Float, nullable=True) # e.g., 99.9, 92.5

    def __repr__(self):
        if self.type == 'bullion':
            return f'<Bullion {self.bullion_type} {self.weight_grams}g ({self.purity_percent}%)>'
        else:
            return f'<Item {self.denomination} from {self.country} ({self.year})>'

# NEW: PublicCollection model for public sharing feature
class PublicCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    def __repr__(self):
        return f'<PublicCollection for User {self.user_id} with ID {self.public_id}>'

# --- JWT Authentication Helper ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# --- API Endpoints ---

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(email=data['email'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60) # Token expires in 60 minutes
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token})

@app.route('/api/change_password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'message': 'Current and new password are required.'}), 400

    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({'message': 'Incorrect current password.'}), 401

    current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    return jsonify({'message': 'Password changed successfully!'}), 200

# NEW: Utility function to fetch live metal prices
# IMPORTANT: This is a placeholder. You will need to sign up for a free API (e.g., GoldAPI.io, Metals-API, or via RapidAPI for Yahoo Finance)
# and replace the placeholder API_KEY and API_URL with actual values.
# Store your API_KEY securely in environment variables (e.g., in your Render dashboard).
def fetch_live_metal_prices():
    """
    Fetches current prices of gold and silver per gram in USD.
    Replace with actual API integration.
    """
    # --- Configuration for Metals-API (Example) ---
    # Sign up at https://metals-api.com/ to get your API key.
    # Make sure your free plan allows for XAU and XAG (Gold and Silver)
    # You might need to make two separate calls for gold and silver on some free tiers.
    # Base URL for Metals-API: https://api.metals-api.com/api/
    # Endpoint to get latest rates: /latest
    # Parameters: base=USD, symbols=XAU,XAG, access_key=YOUR_API_KEY

    METALS_API_KEY = os.environ.get('METALS_API_KEY')
    if not METALS_API_KEY:
        print("METALS_API_KEY not set in environment variables. Using mock data.")
        # MOCK DATA (REMOVE IN PRODUCTION AFTER SETTING UP API KEY)
        return {
            'gold_price_per_gram_usd': 75.00,  # Example: $75 per gram of gold
            'silver_price_per_gram_usd': 0.90   # Example: $0.90 per gram of silver
        }

    try:
        # Example for Metals-API (might require 'base' currency as USD and 'symbols' for gold/silver)
        # Note: Free tier of some APIs might only allow EUR as base, or limit requests.
        # Check Metals-API documentation for exact endpoint and parameters.
        api_url = f"https://api.metals-api.com/api/latest?access_key={METALS_API_KEY}&base=USD&symbols=XAU,XAG"
        response = requests.get(api_url)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if data and data.get('success'):
            rates = data.get('rates', {})
            # Metals-API typically returns rates for 1 unit of base currency.
            # So, if base is USD, rates['XAU'] is how many XAU per 1 USD.
            # We need USD per 1 XAU. So, 1 / rates['XAU'] for 1 unit of Gold (TROY OUNCE).
            # Then convert from Troy Ounce to Grams (1 Troy Ounce = 31.1035 grams)

            gold_price_per_troy_ounce_usd = 1 / rates.get('XAU', 0) if rates.get('XAU') else 0
            silver_price_per_troy_ounce_usd = 1 / rates.get('XAG', 0) if rates.get('XAG') else 0

            # Convert per troy ounce to per gram
            gold_price_per_gram_usd = gold_price_per_troy_ounce_usd / 31.1035
            silver_price_per_gram_usd = silver_price_per_troy_ounce_usd / 31.1035

            return {
                'gold_price_per_gram_usd': gold_price_per_gram_usd,
                'silver_price_per_gram_usd': silver_price_per_gram_usd
            }
        else:
            print(f"Metals-API response error: {data.get('error', 'Unknown error')}")
            return None # Fallback to mock or error if API call is unsuccessful

    except requests.exceptions.RequestException as e:
        print(f"Error fetching metal prices from Metals-API: {e}")
        return None # Return None if API call fails

# NEW: Endpoint to get live metal prices
@app.route('/api/metal_prices', methods=['GET'])
def get_metal_prices():
    prices = fetch_live_metal_prices()
    if prices:
        return jsonify(prices), 200
    return jsonify({'message': 'Could not fetch metal prices.'}), 500


@app.route('/api/collection', methods=['POST'])
@token_required
def add_item(current_user): # RENAMED: from add_coin to add_item
    data = request.get_json()

    # Determine item type, defaulting to 'coin' if not provided
    item_type = data.get('type', 'coin').lower() # 'coin', 'banknote', 'bullion'

    new_item = Item( # Use the new 'Item' model
        user_id=current_user.id,
        country=data['country'],
        year=data.get('year'),
        notes=data.get('notes'),
        reference_url=data.get('reference_url'),
        image_path=data.get('image_path'),
        type=item_type # Set the item type
    )

    # Handle denomination for non-bullion types
    if item_type != 'bullion':
        new_item.denomination = data.get('denomination')
        new_item.value = data.get('value') # For 'coin' or 'banknote', use the value provided by the user
    else:
        # NEW: Handle bullion-specific fields and calculate value
        new_item.bullion_type = data.get('bullion_type').lower() # 'gold' or 'silver'
        new_item.weight_grams = data.get('weight_grams')
        new_item.purity_percent = data.get('purity_percent')

        # Validate bullion fields
        if not all([new_item.bullion_type, new_item.weight_grams, new_item.purity_percent is not None]):
            return jsonify({'message': 'Bullion type, weight, and purity are required for bullion items.'}), 400
        if new_item.weight_grams <= 0 or not (0 <= new_item.purity_percent <= 100):
             return jsonify({'message': 'Invalid weight or purity for bullion.'}), 400

        # Fetch current metal prices to calculate value
        metal_prices = fetch_live_metal_prices()
        if not metal_prices or (metal_prices.get('gold_price_per_gram_usd', 0) == 0 and metal_prices.get('silver_price_per_gram_usd', 0) == 0):
            # If prices can't be fetched, store 0 or a placeholder, and log.
            # Frontend should display a warning.
            print("Warning: Could not fetch live metal prices to calculate initial bullion value. Setting to 0.")
            new_item.value = 0.0
        else:
            current_price_per_gram = 0
            if new_item.bullion_type == 'gold':
                current_price_per_gram = metal_prices.get('gold_price_per_gram_usd', 0)
            elif new_item.bullion_type == 'silver':
                current_price_per_gram = metal_prices.get('silver_price_per_gram_usd', 0)
            else:
                return jsonify({'message': 'Unsupported bullion type.'}), 400

            # Calculate bullion value: (weight * purity_factor * price_per_gram)
            # Purity percent needs to be converted to a factor (e.g., 99.9% -> 0.999)
            purity_factor = new_item.purity_percent / 100
            new_item.value = new_item.weight_grams * purity_factor * current_price_per_gram


    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Item added successfully!', 'item': {
        'id': new_item.id,
        'type': new_item.type,
        'country': new_item.country,
        'year': new_item.year,
        'denomination': new_item.denomination,
        'value': new_item.value,
        'notes': new_item.notes,
        'reference_url': new_item.reference_url,
        'image_path': new_item.image_path,
        'bullion_type': new_item.bullion_type, # NEW
        'weight_grams': new_item.weight_grams, # NEW
        'purity_percent': new_item.purity_percent # NEW
    }}), 201

@app.route('/api/collection', methods=['GET'])
@token_required
def get_collection(current_user):
    # Fetch all items (coins, banknotes, bullion) for the current user
    user_items = Item.query.filter_by(user_id=current_user.id).all() # Use 'Item' model
    output = []
    total_value = 0.0

    # NEW: Fetch live metal prices once for calculation
    metal_prices = fetch_live_metal_prices()
    if not metal_prices or (metal_prices.get('gold_price_per_gram_usd', 0) == 0 and metal_prices.get('silver_price_per_gram_usd', 0) == 0):
        # Log error but don't fail the entire collection retrieval.
        # Bullion values might be incorrect if prices aren't fetched, or display 0.
        print("Warning: Could not fetch live metal prices for collection value recalculation. Bullion values might be outdated.")
        # We will proceed, using stored value for bullion or 0 if recalculation fails.
        metal_prices = {'gold_price_per_gram_usd': 0, 'silver_price_per_gram_usd': 0} # Ensure it's a dict to avoid errors below

    for item in user_items:
        item_value_for_total = item.value # Start with stored value from DB

        # NEW: Recalculate bullion value if live prices are available
        if item.type == 'bullion' and item.weight_grams and item.purity_percent is not None:
            current_price_per_gram = 0
            if item.bullion_type == 'gold':
                current_price_per_gram = metal_prices.get('gold_price_per_gram_usd', 0)
            elif item.bullion_type == 'silver':
                current_price_per_gram = metal_prices.get('silver_price_per_gram_usd', 0)

            if current_price_per_gram > 0: # Only recalculate if we have a valid price
                purity_factor = item.purity_percent / 100
                recalculated_bullion_value = item.weight_grams * purity_factor * current_price_per_gram
                item_value_for_total = recalculated_bullion_value # Use live calculated value for total

        total_value += item_value_for_total # Add (re)calculated value to total

        output.append({
            'id': item.id,
            'type': item.type, # NEW
            'country': item.country,
            'year': item.year,
            'denomination': item.denomination,
            'value': item_value_for_total, # Always send the (re)calculated value to frontend
            'notes': item.notes,
            'reference_url': item.reference_url,
            'image_path': item.image_path,
            'bullion_type': item.bullion_type, # NEW
            'weight_grams': item.weight_grams, # NEW
            'purity_percent': item.purity_percent # NEW
        })
    return jsonify({'collection': output, 'total_value': total_value}), 200


@app.route('/api/collection/<int:item_id>', methods=['PUT'])
@token_required
def update_item(current_user, item_id): # RENAMED: from update_coin to update_item
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first() # Use 'Item' model
    if not item:
        return jsonify({'message': 'Item not found'}), 404

    data = request.get_json()

    # Update common fields
    item.country = data.get('country', item.country)
    item.year = data.get('year', item.year)
    item.notes = data.get('notes', item.notes)
    item.reference_url = data.get('reference_url', item.reference_url)
    item.image_path = data.get('image_path', item.image_path)
    item.type = data.get('type', item.type).lower() # Allow changing type during update

    # NEW: Update bullion-specific fields or non-bullion fields based on type
    if item.type == 'bullion':
        item.bullion_type = data.get('bullion_type', item.bullion_type).lower()
        item.weight_grams = data.get('weight_grams', item.weight_grams)
        item.purity_percent = data.get('purity_percent', item.purity_percent)

        # Clear non-bullion specific fields
        item.denomination = None
        # Recalculate value for bullion on update
        if not all([item.bullion_type, item.weight_grams, item.purity_percent is not None]):
            return jsonify({'message': 'Bullion type, weight, and purity are required for bullion items.'}), 400
        if item.weight_grams <= 0 or not (0 <= item.purity_percent <= 100):
             return jsonify({'message': 'Invalid weight or purity for bullion.'}), 400

        metal_prices = fetch_live_metal_prices()
        if not metal_prices or (metal_prices.get('gold_price_per_gram_usd', 0) == 0 and metal_prices.get('silver_price_per_gram_usd', 0) == 0):
             print("Warning: Could not fetch live metal prices for update. Bullion value might be outdated.")
             # Keep old value or set to 0, frontend should indicate issue
             item.value = item.value if item.value is not None else 0.0
        else:
            current_price_per_gram = 0
            if item.bullion_type == 'gold':
                current_price_per_gram = metal_prices.get('gold_price_per_gram_usd', 0)
            elif item.bullion_type == 'silver':
                current_price_per_gram = metal_prices.get('silver_price_per_gram_usd', 0)

            if current_price_per_gram > 0:
                purity_factor = item.purity_percent / 100
                item.value = item.weight_grams * purity_factor * current_price_per_gram
            else:
                item.value = item.value if item.value is not None else 0.0 # Maintain existing value or set to 0
    else:
        # For 'coin' or 'banknote', update value and denomination from user input
        item.denomination = data.get('denomination', item.denomination)
        item.value = data.get('value', item.value)
        # Clear bullion specific fields
        item.bullion_type = None
        item.weight_grams = None
        item.purity_percent = None


    db.session.commit()
    return jsonify({'message': 'Item updated successfully!'}), 200

@app.route('/api/collection/<int:item_id>', methods=['DELETE'])
@token_required
def delete_item(current_user, item_id): # RENAMED: from delete_coin to delete_item
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first() # Use 'Item' model
    if not item:
        return jsonify({'message': 'Item not found'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully!'}), 200

@app.route('/api/clear_collection', methods=['POST'])
@token_required
def clear_collection(current_user):
    try:
        num_deleted = Item.query.filter_by(user_id=current_user.id).delete() # Use 'Item' model
        db.session.commit()
        return jsonify({'message': f'Successfully deleted {num_deleted} items from your collection.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error clearing collection: {str(e)}'}), 500

# NEW: Public Collection Link Endpoints
@app.route('/api/public_collection_link', methods=['GET'])
@token_required
def get_public_collection_link(current_user):
    public_link = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if public_link:
        return jsonify({'public_id': public_link.public_id}), 200
    return jsonify({'message': 'No public link generated yet.'}), 404

@app.route('/api/public_collection_link', methods=['POST'])
@token_required
def generate_public_collection_link(current_user):
    existing_link = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if existing_link:
        # If already exists, return the existing one. Or you could regenerate.
        return jsonify({'message': 'Public link already exists', 'public_id': existing_link.public_id}), 200

    new_public_link = PublicCollection(user_id=current_user.id)
    db.session.add(new_public_link)
    db.session.commit()
    return jsonify({'message': 'Public link generated successfully', 'public_id': new_public_link.public_id}), 201

@app.route('/api/public_collection_link', methods=['DELETE'])
@token_required
def revoke_public_collection_link(current_user):
    public_link = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if not public_link:
        return jsonify({'message': 'No public link to revoke.'}), 404
    db.session.delete(public_link)
    db.session.commit()
    return jsonify({'message': 'Public link revoked successfully!'}), 200

# NEW: Public View of Collection (Read-only)
@app.route('/api/public_collection/<public_id>', methods=['GET'])
def get_public_collection(public_id):
    public_link = PublicCollection.query.filter_by(public_id=public_id).first()
    if not public_link:
        return jsonify({'message': 'Public collection not found.'}), 404

    # Fetch all items for the user associated with this public_id
    user_items = Item.query.filter_by(user_id=public_link.user_id).all()
    output = []
    total_value = 0.0

    # Fetch live metal prices for public view as well
    metal_prices = fetch_live_metal_prices()
    if not metal_prices or (metal_prices.get('gold_price_per_gram_usd', 0) == 0 and metal_prices.get('silver_price_per_gram_usd', 0) == 0):
        print("Warning: Could not fetch live metal prices for public collection view. Bullion values might be outdated.")
        metal_prices = {'gold_price_per_gram_usd': 0, 'silver_price_per_gram_usd': 0}

    for item in user_items:
        item_value_for_total = item.value

        if item.type == 'bullion' and item.weight_grams and item.purity_percent is not None:
            current_price_per_gram = 0
            if item.bullion_type == 'gold':
                current_price_per_gram = metal_prices.get('gold_price_per_gram_usd', 0)
            elif item.bullion_type == 'silver':
                current_price_per_gram = metal_prices.get('silver_price_per_gram_usd', 0)

            if current_price_per_gram > 0:
                purity_factor = item.purity_percent / 100
                recalculated_bullion_value = item.weight_grams * purity_factor * current_price_per_gram
                item_value_for_total = recalculated_bullion_value
        
        total_value += item_value_for_total

        output.append({
            'id': item.id,
            'type': item.type,
            'country': item.country,
            'year': item.year,
            'denomination': item.denomination,
            'value': item_value_for_total,
            'notes': item.notes,
            'reference_url': item.reference_url,
            'image_path': item.image_path,
            'bullion_type': item.bullion_type,
            'weight_grams': item.weight_grams,
            'purity_percent': item.purity_percent
        })

    return jsonify({'collection': output, 'total_value': total_value}), 200

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
    # Ensure tables are created when running directly
    with app.app_context():
        db.create_all()
    app.run(debug=True)
