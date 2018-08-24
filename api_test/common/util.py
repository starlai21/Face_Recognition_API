from flask_restful import reqparse
from marshmallow import Schema, fields



parser = reqparse.RequestParser()
parser.add_argument(
    'image', type=str, location='json', required=True, help='Image info'
)
parser.add_argument(
    'image_type', type=str, location='json', required=True, help='Image type'
)



face_search_parser = parser.copy()
face_search_parser.add_argument(
    'group_id_list', type=str, location='json', required=True
)
face_search_parser.add_argument(
    'user_id', type=str, location='json', required=False
)
face_search_parser.add_argument(
    'max_user_num', type=int, location='json', required=False
)



faceset_group_getlist_parser = reqparse.RequestParser()
faceset_group_getlist_parser.add_argument(
	'start', type=int, location='json', required=False
)
faceset_group_getlist_parser.add_argument(
	'length', type=int, location='json', required=False
)


faceset_group_getusers_parser = faceset_group_getlist_parser.copy()
faceset_group_getusers_parser.add_argument(
	'group_id', type=str, location='json', required=True
)


faceset_group_parser = reqparse.RequestParser()
faceset_group_parser.add_argument(
	'group_id', type=str, location='json', required=True
)



detect_parser = parser.copy()
detect_parser.add_argument(
    'max_face_num', type=int, location='json', required=False
)
detect_parser.add_argument(
    'face_type', type=str, location='json', required=False
)



faceset_user_add_parser = parser.copy()
faceset_user_add_parser.add_argument(
	'group_id', type=str, location='json', required=True
)

faceset_user_add_parser.add_argument(
	'user_id', type=str, location='json', required=True
)
faceset_user_add_parser.add_argument(
	'user_info', type=str, location='json', required=False
)



faceset_user_parser = reqparse.RequestParser()
faceset_user_parser.add_argument(
	'group_id', type=str, location='json', required=True
)

faceset_user_parser.add_argument(
	'user_id', type=str, location='json', required=True
)


faceset_user_copy_parser = reqparse.RequestParser()
faceset_user_copy_parser.add_argument(
	'src_group_id', type=str, location='json', required=True
)
faceset_user_copy_parser.add_argument(
	'dst_group_id', type=str, location='json', required=True
)
faceset_user_copy_parser.add_argument(
	'user_id', type=str, location='json', required=True
)






faceset_face_delete_parser = faceset_user_parser.copy()

faceset_face_delete_parser.add_argument(
	'face_token', type=str, location='json', required=True
)



class MatchParamsSchema(Schema):
	image = fields.String(required=True)
	image_type = fields.String(required=True)
	face_type = fields.String(required=False)

