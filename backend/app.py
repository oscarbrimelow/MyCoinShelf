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
    type = db.Column(db.String(50), nullable=False) # 'coin' or 'banknote'
    country = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    denomination = db.Column(db.String(100))
    value = db.Column(db.Float) # Estimated value in USD
    notes = db.Column(db.Text)
    reference_url = db.Column(db.String(500))
    local_image_path = db.Column(db.String(500)) # Path to locally stored image

    def __repr__(self):
        return f'<Coin {self.denomination} from {self.country} ({self.year})>'

class PublicCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    public_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    def __repr__(self):
        return f'<PublicCollection for User {self.user_id} with ID {self.public_id}>'

# --- JWT Authentication Helper ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            print(f"Token decoding error: {e}")
            return jsonify({'message': 'Token processing error!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# --- Routes ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(email=data['email'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24) # Token valid for 24 hours
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'token': token})

@app.route('/api/user', methods=['GET'])
@token_required
def get_user(current_user):
    return jsonify({
        'id': current_user.id,
        'email': current_user.email
    })

# Route to change password
@app.route('/api/change_password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({'message': 'Current password incorrect.'}), 400

    current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    return jsonify({'message': 'Password updated successfully!'}), 200

@app.route('/api/coins', methods=['GET'])
@token_required
def get_coins(current_user):
    coins = Coin.query.filter_by(user_id=current_user.id).all()
    output = []
    for coin in coins:
        output.append({
            'id': coin.id,
            'type': coin.type,
            'country': coin.country,
            'year': coin.year,
            'denomination': coin.denomination,
            'value': coin.value,
            'notes': coin.notes,
            'reference_url': coin.reference_url,
            'local_image_path': coin.local_image_path
        })
    return jsonify(output)

@app.route('/api/coins', methods=['POST'])
@token_required
def add_coin(current_user):
    data = request.get_json()
    new_coin = Coin(
        user_id=current_user.id,
        type=data['type'],
        country=data['country'],
        year=data.get('year'),
        denomination=data.get('denomination'),
        value=data.get('value'),
        notes=data.get('notes'),
        reference_url=data.get('reference_url'),
        local_image_path=data.get('local_image_path')
    )
    db.session.add(new_coin)
    db.session.commit()
    return jsonify({'message': 'Coin added successfully!', 'id': new_coin.id}), 201

@app.route('/api/coins/<int:coin_id>', methods=['PUT'])
@token_required
def update_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    coin.type = data.get('type', coin.type)
    coin.country = data.get('country', coin.country)
    coin.year = data.get('year', coin.year)
    coin.denomination = data.get('denomination', coin.denomination)
    coin.value = data.get('value', coin.value)
    coin.notes = data.get('notes', coin.notes)
    coin.reference_url = data.get('reference_url', coin.reference_url)
    coin.local_image_path = data.get('local_image_path', coin.local_image_path)
    db.session.commit()
    return jsonify({'message': 'Coin updated successfully!'})

@app.route('/api/coins/<int:coin_id>', methods=['DELETE'])
@token_required
def delete_coin(current_user, coin_id):
    coin = Coin.query.filter_by(id=coin_id, user_id=current_user.id).first_or_404()
    db.session.delete(coin)
    db.session.commit()
    return jsonify({'message': 'Coin deleted successfully!'})

@app.route('/api/coins/clear', methods=['DELETE'])
@token_required
def clear_all_coins(current_user):
    # Delete all coins associated with the current user
    num_deleted = Coin.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'message': f'{num_deleted} coins deleted successfully for user {current_user.email}.'}), 200

@app.route('/api/coins/import', methods=['POST'])
@token_required
def import_coins(current_user):
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({'message': 'Payload must be a JSON array of coin objects.'}), 400

    imported_count = 0
    for item_data in data:
        try:
            new_coin = Coin(
                user_id=current_user.id,
                type=item_data.get('type', 'coin'), # Default to 'coin' if not specified
                country=item_data['country'],
                year=item_data.get('year'),
                denomination=item_data.get('denomination'),
                value=item_data.get('value'),
                notes=item_data.get('notes'),
                reference_url=item_data.get('reference_url'),
                local_image_path=item_data.get('local_image_path')
            )
            db.session.add(new_coin)
            imported_count += 1
        except KeyError as e:
            # Log the error but continue with other items
            print(f"Skipping malformed import item: Missing key {e} in {item_data}")
            continue
        except Exception as e:
            print(f"Error importing item {item_data}: {e}")
            continue

    db.session.commit()
    return jsonify({'message': f'Successfully imported {imported_count} items.'}), 200

# New: Public Collection Link Routes
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
    public_link = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if public_link:
        # If a link already exists, update its public_id to effectively refresh it
        public_link.public_id = str(uuid.uuid4())
    else:
        # Otherwise, create a new one
        public_link = PublicCollection(user_id=current_user.id)
        db.session.add(public_link)
    db.session.commit()
    return jsonify({'message': 'Public link generated/updated successfully!', 'public_id': public_link.public_id}), 200

@app.route('/api/public_collection_link', methods=['DELETE'])
@token_required
def revoke_public_collection_link(current_user):
    public_link = PublicCollection.query.filter_by(user_id=current_user.id).first()
    if public_link:
        db.session.delete(public_link)
        db.session.commit()
        return jsonify({'message': 'Public link revoked successfully!'}), 200
    return jsonify({'message': 'No public link found to revoke.'}), 404

@app.route('/api/public_collection/<public_id>', methods=['GET'])
def get_public_collection_data(public_id):
    public_link = PublicCollection.query.filter_by(public_id=public_id).first()
    if not public_link:
        return jsonify({'message': 'Public collection not found.'}), 404

    user = User.query.get(public_link.user_id)
    if not user:
        return jsonify({'message': 'Associated user not found.'}), 404

    coins = Coin.query.filter_by(user_id=user.id).all()
    output = []
    for coin in coins:
        output.append({
            'id': coin.id,
            'type': coin.type,
            'country': coin.country,
            'year': coin.year,
            'denomination': coin.denomination,
            'value': coin.value,
            'notes': coin.notes,
            'reference_url': coin.reference_url,
            'local_image_path': coin.local_image_path
        })
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
    app.run(debug=True)
