import os
from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from flask_httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

import face_recognition
import base64
import tempfile
import requests
from common.util import detect_parser, faceset_user_add_parser, faceset_group_getlist_parser, faceset_group_parser, MatchParamsSchema,\
                        faceset_face_delete_parser, faceset_user_parser, faceset_group_getusers_parser, faceset_user_copy_parser, face_search_parser
from marshmallow import ValidationError
import uuid
# create user
# curl -i -X POST -H "Content-Type: application/json" -d '{"username":"jjchen","password":"python"}' http://127.0.0.1:5000/api/users

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

person_group = db.Table('person_group',
    db.Column('person_id', db.Integer, db.ForeignKey('persons.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)

class Face(db.Model):
    __tablename__ = 'faces'
    id = db.Column(db.Integer, primary_key=True)
    face_token = db.Column(db.String(128), unique=True)
    # path = db.Column(db.String(200))
    encoding = db.Column(db.PickleType(), unique=True, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id', ondelete='CASCADE'), nullable=False)





class Person(db.Model):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key=True)
    # client user_id
    uid = db.Column(db.String(128), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    info = db.Column(db.String(128))
    faces = db.relationship('Face', backref='person', lazy=True, cascade='all, delete-orphan', passive_deletes = True)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    persons = db.relationship('Person',secondary=person_group, lazy='subquery',
        backref=db.backref('groups', lazy=True))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))
    groups = db.relationship('Group',backref='user', lazy=True)



    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)    # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)    # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
@auth.login_required
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})






@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})





@app.route('/api/resource', methods=['POST'])
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.user.username})



def isGroupExists(group_id,user_id):
    return Group.query.filter_by(group_id=group_id, user_id=user_id).first() != None

def retrieveImage(param):
    image = None
    if param.get('image_type').upper() == 'BASE64':
        img_data = base64.b64decode(param.get('image')) 

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(img_data) 
            image = face_recognition.load_image_file(tmp)

    elif param.get('image_type').upper() == 'URL':
        with tempfile.NamedTemporaryFile() as tmp:
            r = requests.get(param.get('image'))
            tmp.write(r.content)
            image = face_recognition.load_image_file(tmp)

    elif param.get('image_type').upper() == 'FACE_TOKEN':
        if os.path.exists(param.get('image')):
            image = face_recognition.load_image_file(param.get('image'))
        else:
            abort(400)
    else:
        abort(400)
    return image

# curl -u jjchen:python -X POST  --data '{"image":"test.jpg","image_type":"FACE_TOKEN","face_field":"faceshape,facetype"}' -H 'Content-Type:application/json; charset=UTF-8' http://127.0.0.1:5000/api/face/detect
@app.route('/api/face/detect', methods=['POST'])
@auth.login_required
def face_detect():
    """
    人脸检测
    Args:
        image:
        image_type:
        max_face_num: 最多处理人脸的数目，默认值为1，仅检测图片中面积最大的那个人脸；最大值10，检测图片中面积最大的几张人脸。
        face_type:
    Returns:
        face_num:
        face_list
            +face_token
            +top
            +right
            +bottom
            +left
            +face_probability ? 

    """
    args = detect_parser.parse_args()
    image = retrieveImage(args)

    face_locations = face_recognition.face_locations(image)
    face_list = []
    for face_location in face_locations:
        top, right, bottom, left = face_location
        face = {}
        face['top'] = top
        face['right'] = right
        face['bottom'] = bottom
        face['left'] = left
        face_list.append(face)


    return jsonify({
            'face_num': len(face_locations),
            'face_list': face_list
        })


# curl -u jjchen:python -X POST  --data '{"image":"test.jpg","image_type":"FACE_TOKEN"}' --data '{"image":"test.jpg","image_type":"FACE_TOKEN"}' -H 'Content-Type:application/json; charset=UTF-8' http://127.0.0.1:5000/api/face/match
@app.route('/api/face/match', methods=['POST'])
@auth.login_required
def face_match():
    """
    人脸对比
    Args:
        image:
        image_type:
        face_type:
    Returns:
        score:
        face_list
            +face_token

    """

    try:
        args = MatchParamsSchema(many=True).load(request.json)
        data = args.data
        if len(data) != 2:
            abort(400)
        else:
            first_image = retrieveImage(data[0])
            second_image = retrieveImage(data[1])

            first_image_encoding = face_recognition.face_encodings(first_image)
            second_image_encoding = face_recognition.face_encodings(second_image)
            if len(first_image_encoding) == 0 or len(second_image_encoding) == 0:
                abort(400)
            else:
                first_image_encoding = first_image_encoding[0]
                second_image_encoding = second_image_encoding[0]
            face_distances = face_recognition.face_distance([first_image_encoding], second_image_encoding)
            return jsonify({'distance':face_distances[0]}) 

    except ValidationError as e:
        print (e.messages)
        abort(400)


@app.route('/api/face/search', methods=['POST'])
@auth.login_required
def face_search():
    args = face_search_parser.parse_args()
    user = g.user
    image = retrieveImage(args)
    image_encoding = face_recognition.face_encodings(image)
    if len(image_encoding) == 0:
        abort(400)
    if args.user_id != None:
        person = Person.query.filter_by(user_id=user.id, uid=args.user_id).first()
        if person == None:
            abort(400)
        else:
            faces = person.faces
            if len(faces) == 0:
                abort(400)
            face_encodings = [ face.encoding for face in faces]
            face_distances = face_recognition.face_distance(face_encodings, image_encoding[0])

            min_distance = 1
            min_index = -1
            for index, distance in enumerate(face_distances):
                if min_distance > distance:
                    min_distance = distance
                    min_index = index
            return jsonify({'face_token': faces[min_index].face_token, 'min_distance':min_distance})

    else:
        group_id_list = args.group_id_list.split(',')
        
        return jsonify({'distance': '?'})
    


@app.route('/api/faceset/group/add', methods=['POST'])
@auth.login_required
def faceset_group_add():
    arg = faceset_group_parser.parse_args()
    group_id = arg.group_id
    user = g.user

    if Group.query.filter_by(user_id=user.id, group_id=group_id).first() == None:
        # if the current user's dir has not been created
            # create it
        # create this group's dir under the current user's dir.
        group = Group(group_id=group_id, user_id=user.id)
        db.session.add(group)
        db.session.commit()
        return jsonify({'msg':'success'})
    else:
        return jsonify({'msg':'failure'})


@app.route('/api/faceset/group/delete', methods=['POST'])
@auth.login_required
def faceset_group_delete():
    arg = faceset_group_parser.parse_args()
    group_id = arg.group_id
    user = g.user
    group = Group.query.filter_by(user_id=user.id, group_id=group_id).first() 
    if  group != None:
        db.session.delete(group)
        db.session.commit()
        return jsonify({'msg':'success'})
    else:
        return jsonify({'msg':'failure'})


@app.route('/api/faceset/group/getlist', methods=['POST'])
@auth.login_required
def faceset_group_getlist():
    args = faceset_group_getlist_parser.parse_args()
    start = args.start
    length = args.length
    if start == None or start < 0:
        start = 0
    if length == None or length < 0:
        length = 100
    elif length > 1000:
        length = 1000

    user = g.user
    groups = Group.query.filter_by(user_id=user.id).offset(start).limit(length).all()
    group_id_list = []
    for group in groups:
        group_id_list.append(group.group_id)
    return jsonify({'group_id_list':group_id_list})


@app.route('/api/faceset/group/getusers', methods=['POST'])
@auth.login_required
def faceset_group_getusers():
    args = faceset_group_getusers_parser.parse_args()
    start = args.start
    length = args.length
    if start == None or start < 0:
        start = 0
    if length == None or length < 0:
        length = 100
    elif length > 1000:
        length = 1000

    user = g.user
    group = Group.query.filter_by(user_id=user.id, group_id=args.group_id).first()
    if group == None:
        abort(400)
    


    return jsonify({'user_id_list':[ person.uid for person in group.persons]})

@app.route('/api/faceset/user/add', methods=['POST'])
@auth.login_required
def faceset_user_add():
    args = faceset_user_add_parser.parse_args()
    user = g.user
    group = Group.query.filter_by(user_id=user.id, group_id=args.group_id).first() 
    face_token = str(uuid.uuid4())
    if group != None:

        person = Person.query.filter_by(uid=args.user_id, user_id=user.id).first()

        # # check if this face is valid.
        # # save the face under a specified dir.
        image = retrieveImage(args)
        
        image_encoding = face_recognition.face_encodings(image)
        if len(image_encoding) == 0:
            abort(400)
        else:
            image_encoding = image_encoding[0]

        face = Face(face_token=face_token, encoding=image_encoding)

        # do some face stuff.

        # this guy does not exist so far.
        if person == None:

            # create this person in the database and relate him with this group
            person = Person(uid=args.user_id, user_id=user.id, info=args.user_info)


            person.faces.append(face)
            
            db.session.add(person)

            group.persons.append(person)

            db.session.add(group)

        else:
            _face = Face.query.filter_by(encoding=image_encoding, person_id=person.id).first()
            if _face != None:
                return jsonify({'msg':'This image has been uploaded before.'})
            person.faces.append(face)

            db.session.add(person)


            _group = Group.query.filter_by(user_id=user.id, group_id=args.group_id)\
                            .filter(Group.persons.any(uid=args.user_id)).first()

            # first time to add this person to this group       
            if _group == None:
                group.persons.append(person)
                db.session.add(group)
        
            # second / third ... time to add this person to this group
        
        db.session.commit()
        
    else:
        abort(400)

    return jsonify({'log_id':'', 'face_token':face_token})


@app.route('/api/faceset/user/update', methods=['POST'])
@auth.login_required
def faceset_user_update():
    args = faceset_user_add_parser.parse_args()
    user = g.user
    group = Group.query.filter_by(user_id=user.id, group_id=args.group_id).first() 
    
    if group != None:

        person = Person.query.filter_by(uid=args.user_id, user_id=user.id).first()

        if person == None:
            abort(400)
        else:
            _group = Group.query.filter_by(user_id=user.id, group_id=args.group_id)\
                .filter(Group.persons.any(uid=args.user_id)).first()
            if _group == None:
                abort(400)
            image = retrieveImage(args)
            face_token = str(uuid.uuid4())
            face = Face(face_token=face_token, encoding=image)
            Face.query.filter_by(person_id=person.id).delete()
            person.faces = []
            person.faces.append(face)
            db.session.add(person)
            db.session.commit()
            return jsonify({'log_id':'', 'face_token':face_token})

    else:
        abort(400)

@app.route('/api/faceset/user/get', methods=['POST'])
@auth.login_required
def faceset_user_get():
    args = faceset_user_parser.parse_args()
    user = g.user
    group = Group.query.filter_by(user_id=user.id, group_id=args.group_id).first() 
    
    if group != None:

        person = Person.query.filter_by(uid=args.user_id, user_id=user.id).first()

        if person == None:
            abort(400)
        else:
            _group = Group.query.filter_by(user_id=user.id, group_id=args.group_id)\
                .filter(Group.persons.any(uid=args.user_id)).first()
            if _group == None:
                abort(400)
            return jsonify({'log_id':'', 'user_list':[g.group_id for g in person.groups]})

    else:
        abort(400)

@app.route('/api/faceset/user/delete', methods=['POST'])
@auth.login_required
def faceset_user_delete():
    args = faceset_user_parser.parse_args()
    user = g.user
    group = Group.query.filter_by(user_id=user.id, group_id=args.group_id).first() 
    
    if group != None:

        person = Person.query.filter_by(uid=args.user_id, user_id=user.id).first()

        if person == None:
            abort(400)
        else:
            _group = Group.query.filter_by(user_id=user.id, group_id=args.group_id)\
                .filter(Group.persons.any(uid=args.user_id)).first()
            if _group == None:
                abort(400)
            _group.persons.remove(person)
            db.session.commit()
            return jsonify({'log_id':''})

    else:
        abort(400)

@app.route('/api/faceset/user/copy', methods=['POST'])
@auth.login_required
def faceset_user_copy():
    args = faceset_user_copy_parser.parse_args()
    user = g.user
    src_group = Group.query.filter_by(user_id=user.id, group_id=args.src_group_id).first() 
    dst_group = Group.query.filter_by(user_id=user.id, group_id=args.dst_group_id).first() 
    
    if src_group != None and dst_group != None:

        person = Person.query.filter_by(uid=args.user_id, user_id=user.id).first()

        if person == None:
            abort(400)
        else:
            _src_group = Group.query.filter_by(user_id=user.id, group_id=args.src_group_id)\
                .filter(Group.persons.any(uid=args.user_id)).first()
            if _src_group == None:
                abort(400)
            _dst_group = Group.query.filter_by(user_id=user.id, group_id=args.dst_group_id)\
                .filter(Group.persons.any(uid=args.user_id)).first()
            if _dst_group == None:
                dst_group.persons.append(person)
                db.session.commit()
                return jsonify({'log_id':''})
            else:
                return jsonify({'log_id':'', 'msg':'The person exists in '+args.dst_group_id})

    else:
        abort(400)

@app.route('/api/faceset/face/delete', methods=['POST'])
@auth.login_required
def faceset_face_delete():
    args = faceset_face_delete_parser.parse_args()
    user = g.user
    group = Group.query.filter_by(user_id=user.id, group_id=args.group_id).first() 
    
    if group != None:

        person = Person.query.filter_by(uid=args.user_id, user_id=user.id).first()

        if person == None:
            abort(400)
        else:
            _group = Group.query.filter_by(user_id=user.id, group_id=args.group_id)\
                .filter(Group.persons.any(uid=args.user_id)).first()
            if _group == None:
                abort(400)


            face = Face.query.filter_by(person_id=person.id, face_token = args.face_token).first()
            if face == None:
                return jsonify({'log_id':'', 'error_code':1,'error_msg':'The face is not exist.'})
            
            db.session.delete(face)
            db.session.commit()
            return jsonify({'log_id':'', 'error_code':0})

    else:
        abort(400)


@app.route('/api/faceset/face/getlist', methods=['POST'])
@auth.login_required
def faceset_face_getlist():
    args = faceset_user_parser.parse_args()
    user = g.user
    group = Group.query.filter_by(user_id=user.id, group_id=args.group_id).first() 
    
    if group != None:

        person = Person.query.filter_by(uid=args.user_id, user_id=user.id).first()

        if person == None:
            abort(400)
        else:
            _group = Group.query.filter_by(user_id=user.id, group_id=args.group_id)\
                .filter(Group.persons.any(uid=args.user_id)).first()
            if _group == None:
                abort(400)

            return jsonify({'log_id':'', 'face_list':[ face.face_token for face in person.faces]})

    else:
        abort(400)




if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    db.create_all()
    app.run(debug=True)