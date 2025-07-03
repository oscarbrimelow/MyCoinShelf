# backend/app.py

import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timezone, timedelta # Corrected: Added datetime, timezone, timedelta to import
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
    name = db.Column(db.String(100), nullable=False)
    mint_year = db.Column(db.Integer)
    denomination = db.Column(db.String(50))
    country = db.Column(db.String(100))
    purchase_price = db.Column(db.Float)
    current_value = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    # Corrected: Use datetime.now(timezone.utc)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    image_url = db.Column(db.String(255))
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Coin {self.name}>'

class PublicCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # Corrected: Use datetime.now(timezone.utc)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<PublicCollection {self.public_id}>'

# --- NEW BULLION MODEL ---
class Bullion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    metal = db.Column(db.String(50), nullable=False) # e.g., Gold, Silver, Platinum
    weight_grams = db.Column(db.Float, nullable=False)
    purchase_price_usd = db.Column(db.Float, nullable=False)
    current_value_usd = db.Column(db.Float) # Optional: Can be updated via external API
    quantity = db.Column(db.Integer, default=1, nullable=False)
    # Corrected: Use datetime.now(timezone.utc)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    image_url = db.Column(db.String(255)) # Optional
    notes = db.Column(db.Text) # Optional

    def __repr__(self):
        return f'<Bullion {self.name}>'

# Add relationship to User model
User.bullions = db.relationship('Bullion', backref='owner', lazy=True)


# --- JWT Token Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            # Corrected: Use datetime.now(timezone.utc) for expiration
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            return jsonify({'message': f'Token error: {str(e)}'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# --- User Authentication Routes ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(email=data['email'], password_hash=hashed_password)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'User registration failed', 'error': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Could not verify', 'WWW-Authenticate': 'Basic realm="Login required!"'}), 401

    user = User.query.filter_by(email=auth['email']).first()
    if not user or not check_password_hash(user.password_hash, auth['password']):
        return jsonify({'message': 'Could not verify', 'WWW-Authenticate': 'Basic realm="Login required!"'}), 401

    # Corrected: Ensure the dictionary for jwt.encode is properly structured
    token = jwt.encode(
        {
            'user_id': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(minutes=30) # Corrected: Use datetime.now(timezone.utc) and timedelta
        },
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )

    return jsonify({'token': token}), 200

@app.route('/api/check_token', methods=['GET'])
@token_required
def check_token(current_user):
    return jsonify({'message': 'Token is valid', 'user_id': current_user.id, 'email': current_user.email}), 200


# --- Coin Management Endpoints ---
@app.route('/api/coins', methods=['GET'])
@token_required
def get_coins(current_user):
    coins = Coin.query.filter_by(user_id=current_user.id).all()
    output = []
    for coin in coins:
        output.append({
            'id': coin.id,
            'name': coin.name,
            'mint_year': coin.mint_year,
            'denomination': coin.denomination,
            'country': coin.country,
            'purchase_price': coin.purchase_price,
            'current_value': coin.current_value,
            'quantity': coin.quantity,
            'date_added': coin.date_added.isoformat(),
            'image_url': coin.image_url,
            'notes': coin.notes
        })
    return jsonify({'coins': output}), 200

@app.route('/api/coins', methods=['POST'])
@token_required
def add_coin(current_user):
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'country', 'denomination']):
        return jsonify({'message': 'Missing data for coin'}), 400

    new_coin = Coin(
        user_id=current_user.id,
        name=data['name'],
        mint_year=data.get('mint_year'),
        denomination=data['denomination'],
        country=data['country'],
        purchase_price=data.get('purchase_price'),
        current_value=data.get('current_value'),
        quantity=data.get('quantity', 1),
        image_url=data.get('image_url'),
        notes=data.get('notes')
    )
    try:
        db.session.add(new_coin)
        db.session.commit()
        return jsonify({'message': 'Coin added successfully!', 'id': new_coin.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error adding coin: {str(e)}'}), 500

@app.route('/api/coins/<int:coin_id>', methods=['GET'])
@token_required
def get_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first()
    if not coin:
        return jsonify({'message': 'Coin not found or unauthorized'}), 404
    output = {
        'id': coin.id,
        'name': coin.name,
        'mint_year': coin.mint_year,
        'denomination': coin.denomination,
        'country': coin.country,
        'purchase_price': coin.purchase_price,
        'current_value': coin.current_value,
        'quantity': coin.quantity,
        'date_added': coin.date_added.isoformat(),
        'image_url': coin.image_url,
        'notes': coin.notes
    }
    return jsonify(output), 200

@app.route('/api/coins/<int:coin_id>', methods=['PUT'])
@token_required
def update_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first()
    if not coin:
        return jsonify({'message': 'Coin not found or unauthorized'}), 404

    data = request.get_json()
    coin.name = data.get('name', coin.name)
    coin.mint_year = data.get('mint_year', coin.mint_year)
    coin.denomination = data.get('denomination', coin.denomination)
    coin.country = data.get('country', coin.country)
    coin.purchase_price = data.get('purchase_price', coin.purchase_price)
    coin.current_value = data.get('current_value', coin.current_value)
    coin.quantity = data.get('quantity', coin.quantity)
    coin.image_url = data.get('image_url', coin.image_url)
    coin.notes = data.get('notes', coin.notes)

    try:
        db.session.commit()
        return jsonify({'message': 'Coin updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating coin: {str(e)}'}), 500

@app.route('/api/coins/<int:coin_id>', methods=['DELETE'])
@token_required
def delete_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first()
    if not coin:
        return jsonify({'message': 'Coin not found or unauthorized'}), 404
    try:
        db.session.delete(coin)
        db.session.commit()
        return jsonify({'message': 'Coin deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting coin: {str(e)}'}), 500


# --- Public Collection Endpoints ---
@app.route('/api/public_collection/generate', methods=['POST'])
@token_required
def generate_public_collection_link(current_user):
    public_collection = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if public_collection:
        # If exists, update activity status if needed
        if not public_collection.is_active:
            public_collection.is_active = True
            db.session.commit()
        return jsonify({
            'message': 'Public link already exists and is active.',
            'public_id': public_collection.public_id,
            'link': f"{request.url_root.replace('api/', '')}?public={public_collection.public_id}"
        }), 200
    else:
        new_public_collection = PublicCollection(user_id=current_user.id)
        db.session.add(new_public_collection)
        db.session.commit()
        return jsonify({
            'message': 'Public link generated!',
            'public_id': new_public_collection.public_id,
            'link': f"{request.url_root.replace('api/', '')}?public={new_public_collection.public_id}"
        }), 201

@app.route('/api/public_collection/deactivate', methods=['POST'])
@token_required
def deactivate_public_collection_link(current_user):
    public_collection = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if public_collection:
        public_collection.is_active = False
        db.session.commit()
        return jsonify({'message': 'Public link deactivated.'}), 200
    return jsonify({'message': 'No active public link found for this user.'}), 404

@app.route('/api/public_collection/status', methods=['GET'])
@token_required
def get_public_collection_status(current_user):
    public_collection = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if public_collection:
        return jsonify({
            'is_active': public_collection.is_active,
            'public_id': public_collection.public_id,
            'link': f"{request.url_root.replace('api/', '')}?public={public_collection.public_id}"
        }), 200
    return jsonify({'is_active': False, 'message': 'No public collection link.'}), 200


@app.route('/api/public/collection/<string:public_id>', methods=['GET'])
def get_public_collection(public_id):
    public_collection = PublicCollection.query.filter_by(public_id=public_id, is_active=True).first()
    if not public_collection:
        return jsonify({'message': 'Public collection not found or inactive'}), 404

    user = User.query.get(public_collection.user_id)
    if not user: # Should not happen if foreign key is correctly enforced
        return jsonify({'message': 'User associated with public collection not found'}), 500

    coins = Coin.query.filter_by(user_id=user.id).all()
    bullions = Bullion.query.filter_by(user_id=user.id).all() # Fetch bullions for public view

    coin_output = []
    for coin in coins:
        coin_output.append({
            'id': coin.id,
            'name': coin.name,
            'mint_year': coin.mint_year,
            'denomination': coin.denomination,
            'country': coin.country,
            'current_value': coin.current_value,
            'quantity': coin.quantity,
            'image_url': coin.image_url,
            'notes': coin.notes
        })

    bullion_output = []
    for bullion in bullions:
        bullion_output.append({
            'id': bullion.id,
            'name': bullion.name,
            'metal': bullion.metal,
            'weight_grams': bullion.weight_grams,
            'current_value_usd': bullion.current_value_usd,
            'quantity': bullion.quantity,
            'image_url': bullion.image_url,
            'notes': bullion.notes
        })

    total_value = sum(c.current_value * c.quantity for c in coins if c.current_value is not None)
    total_bullion_value = sum(b.current_value_usd * b.quantity for b in bullions if b.current_value_usd is not None)

    return jsonify({
        'user_email': user.email, # Or a public username if you add one
        'coins': coin_output,
        'bullion': bullion_output, # Include bullion in public view
        'total_collection_value': total_value + total_bullion_value # Sum of coins and bullion
    }), 200


# --- NEW Bullion Management Endpoints ---
@app.route('/api/bullion', methods=['GET'])
@token_required
def get_bullion(current_user):
    """Get all bullion for the authenticated user."""
    bullions = Bullion.query.filter_by(user_id=current_user.id).all()
    output = []
    for bullion in bullions:
        output.append({
            'id': bullion.id,
            'name': bullion.name,
            'metal': bullion.metal,
            'weight_grams': bullion.weight_grams,
            'purchase_price_usd': bullion.purchase_price_usd,
            'current_value_usd': bullion.current_value_usd,
            'quantity': bullion.quantity,
            'date_added': bullion.date_added.isoformat(),
            'image_url': bullion.image_url,
            'notes': bullion.notes
        })
    return jsonify({'bullion': output}), 200

@app.route('/api/bullion', methods=['POST'])
@token_required
def add_bullion(current_user):
    """Add a new bullion item."""
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'metal', 'weight_grams', 'purchase_price_usd']):
        return jsonify({'message': 'Missing data for bullion'}), 400

    try:
        new_bullion = Bullion(
            user_id=current_user.id,
            name=data['name'],
            metal=data['metal'],
            weight_grams=float(data['weight_grams']),
            purchase_price_usd=float(data['purchase_price_usd']),
            current_value_usd=float(data.get('current_value_usd', data['purchase_price_usd'])),
            quantity=int(data.get('quantity', 1)),
            image_url=data.get('image_url'),
            notes=data.get('notes')
        )
        db.session.add(new_bullion)
        db.session.commit()
        return jsonify({'message': 'Bullion added successfully!', 'id': new_bullion.id}), 201
    except ValueError:
        return jsonify({'message': 'Invalid numerical data provided'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error adding bullion: {str(e)}'}), 500

@app.route('/api/bullion/<int:bullion_id>', methods=['PUT'])
@token_required
def update_bullion(current_user, bullion_id):
    """Update an existing bullion item."""
    bullion = Bullion.query.filter_by(id=bullion_id, user_id=current_user.id).first()
    if not bullion:
        return jsonify({'message': 'Bullion not found or unauthorized'}), 404

    data = request.get_json()
    try:
        bullion.name = data.get('name', bullion.name)
        bullion.metal = data.get('metal', bullion.metal)
        bullion.weight_grams = float(data.get('weight_grams', bullion.weight_grams))
        bullion.purchase_price_usd = float(data.get('purchase_price_usd', bullion.purchase_price_usd))
        bullion.current_value_usd = float(data.get('current_value_usd', bullion.current_value_usd))
        bullion.quantity = int(data.get('quantity', bullion.quantity))
        bullion.image_url = data.get('image_url', bullion.image_url)
        bullion.notes = data.get('notes', bullion.notes)

        db.session.commit()
        return jsonify({'message': 'Bullion updated successfully!'}), 200
    except ValueError:
        return jsonify({'message': 'Invalid numerical data provided'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating bullion: {str(e)}'}), 500

@app.route('/api/bullion/<int:bullion_id>', methods=['DELETE'])
@token_required
def delete_bullion(current_user, bullion_id):
    """Delete a bullion item."""
    bullion = Bullion.query.filter_by(id=bullion_id, user_id=current_user.id).first()
    if not bullion:
        return jsonify({'message': 'Bullion not found or unauthorized'}), 404

    try:
        db.session.delete(bullion)
        db.session.commit()
        return jsonify({'message': 'Bullion deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting bullion: {str(e)}'}), 500


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
            print(f"Default user '{default_email}' created. Please change this in production!'")

if __name__ == '__main__':
    app.run(debug=True)
