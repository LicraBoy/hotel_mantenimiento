from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.habitaciones import habitaciones_bp
from routes.mantenimiento import mantenimiento_bp
from routes.inspecciones import inspecciones_bp
from routes.reportes import reportes_bp
from routes.analisis import analisis_bp
from routes.admin import admin_bp
from routes.predicciones import predicciones_bp
from routes.vision import vision_bp
from routes.limpieza import limpieza_bp
from routes.costos import costos_bp
from routes.tecnicos import tecnicos_bp
from routes.automatizacion import automatizacion_bp
from routes.operaciones import operaciones_bp
from routes.equipos import equipos_bp


def registrar_blueprints(app):
    """Registra todos los blueprints en la aplicación Flask."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(habitaciones_bp)
    app.register_blueprint(mantenimiento_bp)
    app.register_blueprint(inspecciones_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(analisis_bp)
    app.register_blueprint(admin_bp)
    # AI Modules v1
    app.register_blueprint(predicciones_bp)
    app.register_blueprint(vision_bp)
    app.register_blueprint(limpieza_bp)
    # AI Modules v2
    app.register_blueprint(costos_bp)
    app.register_blueprint(tecnicos_bp)
    app.register_blueprint(automatizacion_bp)
    app.register_blueprint(operaciones_bp)
    app.register_blueprint(equipos_bp)
