import hashlib
import logging
from datetime import datetime

from database import db
from sqlalchemy import distinct
from sqlalchemy.exc import SQLAlchemyError


class Call(db.Model):
    __tablename__ = 'calls'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    campaign_id = db.Column(db.String(32))
    member_id = db.Column(db.String(10))  # congress member sunlight identifier

    # user attributes
    user_id = db.Column(db.String(64))    # hashed phone number
    zipcode = db.Column(db.String(5))
    areacode = db.Column(db.String(3))    # first 3 digits of phone number
    exchange = db.Column(db.String(3))    # next 3 digits of phone number

    # twilio attributes
    call_id = db.Column(db.String(40))    # twilio call ID
    status = db.Column(db.String(25))     # twilio call status
    duration = db.Column(db.Integer)      # twilio call time in seconds

    @classmethod
    def hash_phone(cls, number):
        """
        Takes a phone number and returns a 64 character string
        """
        return hashlib.sha256(number).hexdigest()

    def __init__(self, campaign_id, member_id, zipcode=None, phone_number=None,
                 call_id=None, status='unknown', duration=0):
        self.timestamp = datetime.now()
        self.status = status
        self.duration = duration
        self.campaign_id = campaign_id
        self.member_id = member_id
        self.call_id = call_id

        if phone_number:
            phone_number = phone_number.replace('-', '').replace('.', '')
            self.user_id = self.hash_phone(phone_number)
            self.areacode = phone_number[:3]
            self.exchange = phone_number[3:6]

        self.zipcode = zipcode

    def __repr__(self):
        return '<Call {}-{}-xxxx to {}>'.format(
            self.areacode, self.exchange, self.member_id)


def log_call(params, campaign, request):
    try:
        i = int(request.values.get('call_index'))

        kwds = {
            'campaign_id': campaign['id'],
            'member_id': params['repIds'][i],
            'zipcode': params['zipcode'],
            'phone_number': params['userPhone'],
            'call_id': request.values.get('CallSid', None),
            'status': request.values.get('DialCallStatus', 'unknown'),
            'duration': request.values.get('DialCallDuration', 0)
        }

        db.session.add(Call(**kwds))
        db.session.commit()
    except SQLAlchemyError:
        logging.error('Failed to log call:', exc_info=True)


def call_count(campaign_id):
    try:
        return (db.session.query(db.func.Count(distinct(Call.id)))
                .filter(Call.campaign_id == campaign_id).all())[0][0]
    except SQLAlchemyError:
        logging.error('Failed to get call_count:', exc_info=True)

        return 0

def call_list(campaign_id, since, limit=50):
    try:
        calls = (db.session.query(Call)
                .order_by(Call.timestamp.desc())
                .filter(Call.campaign_id == campaign_id)
                .filter(Call.timestamp >= since)
                .limit(limit).all())
        return calls

    except SQLAlchemyError:
        logging.error('Failed to get call_list:', exc_info=True)

        return 0


def aggregate_stats(campaign_id):
    zipcodes = (db.session.query(Call.zipcode, db.func.Count(Call.zipcode))
                .filter(Call.campaign_id == campaign_id)
                .filter(Call.status == 'completed')
                .group_by(Call.zipcode).all())

    reps = (db.session.query(Call.member_id, db.func.Count(distinct(Call.user_id)))
            .filter(Call.campaign_id == campaign_id)
            .filter(Call.status == 'completed')
            .group_by(Call.member_id).all())

    total = (db.session.query(db.func.Count(distinct(Call.call_id)))
             .filter(Call.campaign_id == campaign_id)
             .filter(Call.status == 'completed').all())

    return {
        'campaign': campaign_id,
        'calls': {
            'zipcodes': dict(tuple(z) for z in zipcodes),
            'reps': dict(tuple(r) for r in reps)
        },
        'total': total
    }

if __name__ == "__main__":
    import socket
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy

    app = Flask('app')
    if '.local' in socket.gethostname():
        app.config.from_object('config.Config')
        print "local config",
    else:
        app.config.from_object('config.ConfigProduction')
        print "production config",
    db = SQLAlchemy(app)
    print db

    ok = raw_input("[ok] to proceed? ")
    if ok == 'ok':
        c = Call('test','test') #create before create_all, to ensure model is registered w/ sqlalchemy

        with app.app_context():
            print "creating tables"
            db.create_all()
            db.session.commit()
        
        db.session.add(c)
        db.session.commit()
        print "done"
    else:
        print "abort"
