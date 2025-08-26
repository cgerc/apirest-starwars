"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favorite
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/people', methods=['GET'])
def get_all_people():
    people = Character.query.all()
    return jsonify([person.serialize() for person in people]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = Character.query.get(people_id)
    if not person:
        raise APIException("Personaje no encontrado", status_code=404)
    return jsonify(person.serialize()), 200

@app.route('/users/favorites', methods=['GET'])
def get_users_favorites():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        raise APIException("Se requiere el ID del usuario", status_code=400)
    user = User.query.get(user_id)
    if not user:
        raise APIException("Usuario no encontrado", status_code=404)
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    return jsonify([favorite.serialize() for favorite in favorites]), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    data = request.get_json()
    if not data:
        raise APIException("JSON inválido", status_code=400)
    user_id = data.get('user_id') if data else None
    if not user_id:
        raise APIException("Se requiere el ID del usuario", status_code=400)
    user = User.query.get(user_id)
    if not user:
        raise APIException("Usuario no encontrado", status_code=404)
    planet = Planet.query.get(planet_id)
    if not planet:
        raise APIException("Planeta no encontrado", status_code=404)

    existing_favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if existing_favorite:
        raise APIException("El planeta ya está en los favoritos del usuario", status_code=400)
    favorite = Favorite(user_id=user_id, planet_id=planet_id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify(favorite.serialize()), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    data = request.get_json()
    if not data:
        raise APIException("JSON inválido", status_code=400)
    user_id = data.get('user_id') if data else None
    if not user_id:
        raise APIException("Se requiere el ID del usuario", status_code=400)

    user = User.query.get(user_id)
    if not user:
        raise APIException("Usuario no encontrado", status_code=404)

    person = Character.query.get(people_id)
    if not person:
        raise APIException("Personaje no encontrado", status_code=404)

    existing_favorite = Favorite.query.filter_by(user_id=user_id, character_id=people_id).first()
    if existing_favorite:
        raise APIException("El personaje ya está en los favoritos del usuario", status_code=400)
    favorite = Favorite(user_id=user_id, character_id=people_id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify(favorite.serialize()), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        raise APIException("Se requiere el ID del usuario", status_code=400)

    user = User.query.get(user_id)
    if not user:
        raise APIException("Usuario no encontrado", status_code=404)
    favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if not favorite:
        raise APIException("Favorito no encontrado", status_code=404)

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"msg": "Planeta favorito eliminado correctamente"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        raise APIException("Se requiere el ID del usuario", status_code=400)

    user = User.query.get(user_id)
    if not user:
        raise APIException("Usuario no encontrado", status_code=404)
    favorite = Favorite.query.filter_by(user_id=user_id, character_id=people_id).first()
    if not favorite:
        raise APIException("Favorito no encontrado", status_code=404)

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"msg": "Personaje favorito eliminado correctamente"}), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)