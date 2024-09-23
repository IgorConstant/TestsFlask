from flask import Flask

# Importa as rotas do diretório routes
from routes.main__route import main_bp
from routes.healthcheck__route import healthcheck_bp
from routes.details__route import details_bp

app = Flask(__name__)

# Registra as blueprints
app.register_blueprint(main_bp)
app.register_blueprint(healthcheck_bp)
app.register_blueprint(details_bp)
