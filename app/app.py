from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'devops-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

APP_VERSION = "1.2.0"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

# ─── Modèles ───────────────────────────────────────────────

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='etudiant')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

class Matiere(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    ressources = db.relationship('Ressource', backref='matiere', lazy=True)

class Ressource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(300))
    lien = db.Column(db.String(300))
    type_ressource = db.Column(db.String(50))
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)
    matiere_id = db.Column(db.Integer, db.ForeignKey('matiere.id'), nullable=False)
    auteur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    auteur = db.relationship('User', backref='ressources')

# ─── Login Manager ─────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── Routes ────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('login.html', version=APP_VERSION)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    matieres = Matiere.query.all()
    total_ressources = Ressource.query.count()
    total_users = User.query.count()
    now = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    return render_template('dashboard.html',
        matieres=matieres,
        total_ressources=total_ressources,
        total_users=total_users,
        version=APP_VERSION,
        now=now
    )

@app.route('/ressources/<int:matiere_id>')
@login_required
def ressources(matiere_id):
    matiere = Matiere.query.get_or_404(matiere_id)
    ressources = Ressource.query.filter_by(matiere_id=matiere_id).all()
    return render_template('ressources.html',
        matiere=matiere,
        ressources=ressources,
        version=APP_VERSION
    )

@app.route('/ajouter-ressource', methods=['GET', 'POST'])
@login_required
def ajouter_ressource():
    if current_user.role not in ['prof', 'admin']:
        flash('Accès refusé. Réservé aux professeurs.', 'danger')
        return redirect(url_for('dashboard'))
    matieres = Matiere.query.all()
    if request.method == 'POST':
        nouvelle = Ressource(
            titre=request.form.get('titre'),
            description=request.form.get('description'),
            lien=request.form.get('lien'),
            type_ressource=request.form.get('type_ressource'),
            matiere_id=int(request.form.get('matiere_id')),
            auteur_id=current_user.id
        )
        db.session.add(nouvelle)
        db.session.commit()
        flash('Ressource ajoutée avec succès !', 'success')
        return redirect(url_for('dashboard'))
    return render_template('ajouter_ressource.html', matieres=matieres, version=APP_VERSION)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Accès refusé.', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    matieres = Matiere.query.all()
    return render_template('admin.html', users=users, matieres=matieres, version=APP_VERSION)

@app.route('/admin/ajouter-matiere', methods=['POST'])
@login_required
def ajouter_matiere():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    matiere = Matiere(
        nom=request.form.get('nom'),
        description=request.form.get('description')
    )
    db.session.add(matiere)
    db.session.commit()
    flash('Matière ajoutée !', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/ajouter-user', methods=['POST'])
@login_required
def ajouter_user():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    user = User(
        nom=request.form.get('nom'),
        email=request.form.get('email'),
        password=generate_password_hash(request.form.get('password')),
        role=request.form.get('role')
    )
    db.session.add(user)
    db.session.commit()
    flash('Utilisateur créé !', 'success')
    return redirect(url_for('admin'))

# ─── Initialisation DB ─────────────────────────────────────

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@ecole.mg').first():
            admin = User(
                nom='Administrateur',
                email='admin@ecole.mg',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            prof = User(
                nom='Prof Dupont',
                email='prof@ecole.mg',
                password=generate_password_hash('prof123'),
                role='prof'
            )
            etudiant = User(
                nom='Étudiant Demo',
                email='etudiant@ecole.mg',
                password=generate_password_hash('etudiant123'),
                role='etudiant'
            )
            db.session.add_all([admin, prof, etudiant])
            matiere1 = Matiere(nom='Mathématiques', description='Cours de maths')
            matiere2 = Matiere(nom='Informatique', description='Cours d\'informatique')
            matiere3 = Matiere(nom='Physique', description='Cours de physique')
            db.session.add_all([matiere1, matiere2, matiere3])
            db.session.commit()

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
