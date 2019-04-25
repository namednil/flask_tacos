import os
import string
import random
import logging
import subprocess

import click

from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS
from flask_cors import cross_origin
from flask.cli import with_appcontext

# from flask_mail import Mail, Message

from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename


from flask_tacos.crossdomain import crossdomain

from flask_tacos.db import get_db
from flask_tacos.db import init_app

from datetime import date

# mail_settings = {
#     "MAIL_SERVER": 'mail.coli.uni-saarland.de',
#     "MAIL_PORT": 465,
#     "MAIL_USE_TLS": False,
#     "MAIL_USE_SSL": True,
#     "MAIL_USERNAME": "moritzw",
#     "MAIL_PASSWORD": ""
#     "MAIL_DEBUG": True
# }
fee_path = "/home/tacos2019/flask_tacos/fees.txt" #"/Users/mo/Dropbox/Uni/TaCos/flask_tacos/fees.txt" # "/home/tacos2019/flask_tacos/fees.txt"

UPLOAD_FOLDER = '/home/tacos2019/flask_tacos/talk_papers'
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])


def create_app(test_config=None):
    
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'tacos.sqlite'),
    )

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    # app.config.update(mail_settings)
    # mail = Mail(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    app.config['CORS_HEADERS'] = 'Content-Type'

    CORS(app)
    # a simple page that says hello
    #@app.route('/hello')
    #def hello():
    #    return 'Hello, World!'

    @app.route('/register', methods=["POST", "OPTIONS"])
    #@crossdomain(origin="*")
    def register():
        response={}

        email = request.form['email']
        given_name = request.form['given_name']
        surname = request.form['surname']
        nutrition = request.form['nutrition']
        university = request.form['university']
        busticket = "ticket" in request.form

        # check if something required is missing
        formTags = ["email", "given_name", "surname", "nutrition"]
        for tag in formTags:
             if request.form[tag] == "" or request.form[tag] is None:
                response['status']='ERROR'
                response['message']="Please fill in your " + tag[0].upper() + tag[1:]
                app.logger.info('Register error '+ tag)
                return jsonify(response)

        # check if user is already registered
        db = get_db()
        if db.execute(
            'SELECT id FROM user WHERE email = ?', (email,)
        ).fetchone() is not None:
            response['status']='ERROR'
            response['message'] = 'User {0} is already registered.'.format(email)
            return jsonify(response)
        else:
            check = True
            # generate new uid
            uid = ''.join(random.choice(string.ascii_letters) for _ in range(8))
            while check:
                if db.execute('SELECT id FROM user WHERE id = ?', (uid,)).fetchone() is not None:
                    uid = ''.join(random.choice(string.ascii_letters) for _ in range(8))
                else:
                    check = False
            
            # insert new user into db
            db.execute(
                'INSERT INTO user (id, email, given_name, surname, university, nutrition, busticket) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (uid, email, given_name, surname, university, nutrition, busticket)
            )
            db.commit()
            response['status']='OK'
            response['message']="Successfully registered"
            
            today = date.today()
            if today <= date(2019, 5,26): #Early Bird Deadline: 26th of May
                fee = 20
            else:
                fee = 25

            # build email text
            html_message = "Hi {0},<br>".format(given_name)
            html_message += "Thank you for registering for TaCoS 29!<br>"
            html_message += "Your code is {0}.<br><br>".format(uid)
            html_message += "If you want to check your registration status, enter your code under ''Check Registration Status'' on <a href='https://tacos2019.coli.uni-saarland.de/registration/#status'>https://tacos2019.coli.uni-saarland.de/registration/#status</a>.<br>"
            html_message += "To complete your registration please pay the attendence fee of {}&euro;. Please also consider presenting something: <a href='https://tacos2019.coli.uni-saarland.de/call/'>https://tacos2019.coli.uni-saarland.de/call/</a>.<br><br>".format(fee)
            html_message += "Recipient: Verein der Freunde der FR Sprachwissenschaft und Sprachtechnologie<br>"
            html_message += "IBAN: DE48 5919 0000 0117 1620 01<br>"
            html_message += "BIC: SABADE5S<br>"
            html_message += "Bank: Bank 1 Saar <br>"
            html_message += "Reference (Verwendungszweck): TaCoS Teilnehmer {0}<br>".format(uid)
            html_message += "Amount (Betrag): {}&euro;<br><br>".format(fee)
            html_message += "If you have any questions or comments, simply reply to this e-mail.<br><br>"
            html_message += "Best,<br>Your TaCoS team"

            # send email via terminal (a bit hacky but with this we don't need to save the password
            # and flask-mail didn't want to work on the server)
            echo = subprocess.Popen(["echo", "",html_message, ""], stdout=subprocess.PIPE)
            output = subprocess.check_output(["mail", "-s", "Registration at TaCoS 29", "-a", "Content-type: text/html", email], stdin=echo.stdout)

            response['status']='OK'
            response['message']="Successfully registered"
            app.logger.info(" ".join([email, uid, 'has succesfully registered']))

            return jsonify(response)
        return jsonify(response)

    @app.route('/talk', methods=["POST", "OPTIONS"])
    # @crossdomain(origin="*")
    def talk():
        response = {}

        uid = request.form['uid']
        title = request.form['title']
        subtitle = request.form['subtitle']
        presentation = request.form['presentation']
        abstract = request.form['abstract']
        notes = request.form['notes']
        # app.logger.info(request.form)

        # check if something required is missing
        formTags = ["uid", "title", "subtitle", "presentation"]
        for tag in formTags:
            if request.form[tag] == "" or request.form[tag] is None:
                if tag == 'uid':
                    tag = "code"
                response['status']='ERROR'
                response['message']="Please fill in the " + tag
                app.logger.info('Register error '+ tag)
                return jsonify(response)
        db = get_db()
        user = db.execute('SELECT * FROM user WHERE id=?', (uid,)).fetchone()
        # check if user is registered or not
        if user is None:
            response['status']='ERROR'
            response['message']="Mhm. We can't find that registration code in our database. You might have to register first."
            return jsonify(response)

        # save file in form uid + unique index number + .pdf to upload folder
        index = 0
        for f in request.files:
            app.logger.info(f)
            path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uid + str(index) + request.files[f].filename))
            while os.path.isfile(path):
                index += 1
                path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uid + str(index) + request.files[f].filename))
            request.files[f].save(path)

        # write into database
        db.execute(
            'INSERT INTO talk (uid, title, subtitle, type, abstract, notes) VALUES (?, ?, ?, ?, ?, ?)',
            (uid, title, subtitle, presentation, abstract, notes)
        )
        db.commit()


        # send email if everything went fine
        # build email text
        html_message = "Hi {0},<br><br>".format(user["given_name"])
        html_message += 'Thank you very much for registering a presentation for TaCoS 29 titled "{0}"!<br>'.format(title)
        html_message += "We will review what you sent us and come back to you as soon as possible.<br>"
        html_message += "The presentation is associated with the code {0}.<br><br>".format(uid)
        if presentation in {"longtalk","tutorial"}:
            html_message += "Since you registered a long talk or a tutorial, you don't have to pay any attendence fee. <br><br>"
        else:
            today = date.today()
            if today <= date(2019, 5,26): #Early Bird Deadline: 26th of May
                fee = 10
            else:
                fee = 12.5
            html_message += "In case you haven't payed the attendence fee yet, please send us half of the regular/early bird attendence fee. Currently that's {}&euro;.<br><br>".format(fee)
            html_message += "Recipient: Verein der Freunde der FR Sprachwissenschaft und Sprachtechnologie<br>"
            html_message += "IBAN: DE48 5919 0000 0117 1620 01<br>"
            html_message += "BIC: SABADE5S<br>"
            html_message += "Bank: Bank 1 Saar <br>"
            html_message += "Reference (Verwendungszweck): TaCoS Teilnehmer {0}<br>".format(uid)
            html_message += "Amount (Betrag): {}&euro;<br><br>".format(fee)
        html_message += "If you have any questions, simply reply to this e-mail.<br><br>"
        html_message += "Best,<br>Your TaCoS team"

        # send email via terminal (a bit hacky but with this we don't need to save the password
        # and flask-mail didn't want to work on the server)
        echo = subprocess.Popen(["echo", "",html_message, ""], stdout=subprocess.PIPE)
        output = subprocess.check_output(["mail", "-s", "TaCoS29 talk registration", "-a", "Content-type: text/html", user["email"]], stdin=echo.stdout)

        response['status']='OK'
        response['message']="Successfully registered"
        
        html_message = "New presentation at TaCoS with following info:<br>"
        html_message += "<br><br> ".join([title, subtitle, presentation, abstract, notes])
        echo = subprocess.Popen(["echo", "",html_message, ""], stdout=subprocess.PIPE)
        output = subprocess.check_output(["mail", "-s", "New presentation", "-a", "Content-type: text/html", "tacos2019@coli.uni-saarland.de"], stdin=echo.stdout)
        app.logger.info('email sent '+ str(output))
        
        return jsonify(response)



    @app.route('/fee', methods=["GET"])
    @crossdomain(origin="*")
    def fee():

        uid = request.args.get('uid')
        if uid is not None and uid != "":
            
            #check in some textfile
            with open(fee_path, "r") as f:
                for feeid in f:
                    if feeid.strip() == uid.strip():
                        return "You are registered and your fee is paid. :)"
            db = get_db()
            if db.execute('SELECT id FROM user WHERE id = ?', (uid,)
                ).fetchone() is not None:
                return "You are registered, but we didn't receive your fee yet."
            else:
                return "You are not registered yet. Please register above."
        else:
            return "Please insert a code."
        return "N/A"

    @app.route('/test', methods=["GET"])
    @crossdomain(origin="*")
    def test():
        # app.logger.debug('this is a DEBUG message')
        # app.logger.info('this is an INFO message')
        # app.logger.warning('this is a WARNING message')
        # app.logger.error('this is an ERROR message')
        # app.logger.critical('this is a CRITICAL message')
        uid = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        
        today = date.today()
        if today <= date(2019, 5,26): #Early Bird Deadline: 26th of May
            fee = 20
        else:
            fee = 25

        html_message = "Hi [NAME],<br>"
        html_message += "Thank you for registering for TaCoS 29!<br>"
        html_message += "Your code is {0}.<br><br>".format(uid)
        html_message += "If you want to check your registration status, enter your code under ''Check Registration Status'' on <a href='https://tacos2019.coli.uni-saarland.de/registration/#status'>https://tacos2019.coli.uni-saarland.de/registration/#status</a>.<br>"
        html_message += "To complete your registration please pay the attendence fee of {}&euro;. Please also consider presenting something: <a href='https://tacos2019.coli.uni-saarland.de/call/'>https://tacos2019.coli.uni-saarland.de/call/</a>.<br><br>".format(fee)
        html_message += "Recipient: Verein der Freunde der FR Sprachwissenschaft und Sprachtechnologie<br>"
        html_message += "IBAN: DE48 5919 0000 0117 1620 01<br>"
        html_message += "BIC: SABADE5S<br>"
        html_message += "Bank: Bank 1 Saar <br>"
        html_message += "Reference (Verwendungszweck): TaCoS Teilnehmer {0}<br>".format(uid)
        html_message += "Amount (Betrag): {}&euro;<br><br>".format(fee)
        html_message += "If you have any questions or comments, simply reply to this e-mail.<br><br>"
        html_message += "Best,<br>Your TaCoS team"

        echo = subprocess.Popen(["echo", "",html_message, ""], stdout=subprocess.PIPE)
        output = subprocess.check_output(["mail", "-s", "Registration at TaCoS 29", "-a", "Content-type: text/html", "mlinde@coli.uni-saarland.de"], stdin=echo.stdout)
        app.logger.info('email sent '+ str(output))

        # this doesn't work because of the pipe
        # subprocess.call(["echo", html_message, "|", "mail", "-s", "'subject'", "-a", "'Content-type: text/html'", "moritzw@coli.uni-saarland.de"])

        return "N/A"
    
    init_app(app)


    # enable logging
    if __name__ != '__main__':
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
    
    return app



@click.command('extract-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    pass
    click.echo('Copied database csv to ')
