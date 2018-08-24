import base64
import requests
import os


requests.adapters.DEFAULT_RETRIES = 5

headers = {'Content-type': 'application/json', 'Connection':'close'}

def test_face_detect_api():
	test_url = 'http://127.0.0.1:5000/api/face/detect'
	# img_path = os.path.abspath('../knn_examples/test/3.jpg')
	# f=open(img_path,'rb') #二进制方式打开图文件
	# f_encoded=base64.b64encode(f.read()) #读取文件内容，转换为base64编码 
	# f.close()
	
	# data = {'image':f_encoded.decode(), 'image_type':'base64'}
	# data = {'image':'https://www.whitehouse.gov/wp-content/uploads/2017/12/44_barack_obama1.jpg', 'image_type':'url'}
	data = {'image':'test.jpg', 'image_type':'face_token'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_face_match_api():
	test_url = 'http://127.0.0.1:5000/api/face/match'
	img_path = os.path.abspath('../knn_examples/train/trump/1.jpg')
	f=open(img_path,'rb') #二进制方式打开图文件
	f_encoded=base64.b64encode(f.read()) #读取文件内容，转换为base64编码 
	f.close()
	
	# data = {'image':f_encoded.decode(), 'image_type':'base64'}
	data =	[
		{'image':'test.jpg', 'image_type':'face_token'},
		# {'image':'https://www.whitehouse.gov/wp-content/uploads/2017/12/44_barack_obama1.jpg', 'image_type':'url'}
		{'image':f_encoded.decode(), 'image_type':'base64'}

	]
	
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_face_search_api():
	test_url = 'http://127.0.0.1:5000/api/face/search'
	img_path = os.path.abspath('../knn_examples/train/trump/1.jpg')
	f=open(img_path,'rb') #二进制方式打开图文件
	f_encoded=base64.b64encode(f.read()) #读取文件内容，转换为base64编码 
	f.close()
	
	data = {'image':f_encoded.decode(), 'image_type':'base64', 'group_id_list':'group1', 'user_id':'1'}
	
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)


# --------------------------------group apis --------------------------------
def test_faceset_group_add_api(group_id="group1"):
	test_url = 'http://127.0.0.1:5000/api/faceset/group/add'
	data = {'group_id':group_id}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_group_delete_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/group/delete'
	data = {'group_id':'group1'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_group_getlist_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/group/getlist'
	data = {'start':-1}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_group_getusers_api(group_id="group1"):
	test_url = 'http://127.0.0.1:5000/api/faceset/group/getusers'
	data = {'start':-1,'group_id':group_id}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

# ------------------------------------------------------------------


def test_faceset_user_add_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/user/add'
	# img_path = os.path.abspath('../knn_examples/test/3.jpg')
	# f=open(img_path,'rb') #二进制方式打开图文件
	# f_encoded=base64.b64encode(f.read()) #读取文件内容，转换为base64编码 
	# f.close()
	
	# data = {'image':f_encoded.decode(), 'image_type':'base64','group_id':'group1','user_id':'1'}
	data = {'image':'https://www.whitehouse.gov/wp-content/uploads/2017/12/44_barack_obama1.jpg', 'image_type':'url','group_id':'group1','user_id':'1'}
	# data = {'image':'test.jpg', 'image_type':'face_token','group_id':'group1','user_id':'1'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_user_update_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/user/update'
	# img_path = os.path.abspath('../knn_examples/test/3.jpg')
	# f=open(img_path,'rb') #二进制方式打开图文件
	# f_encoded=base64.b64encode(f.read()) #读取文件内容，转换为base64编码 
	# f.close()
	
	# data = {'image':f_encoded.decode(), 'image_type':'base64','group_id':'1','user_id':'1'}
	# data = {'image':'https://www.whitehouse.gov/wp-content/uploads/2017/12/44_barack_obama1.jpg', 'image_type':'url','group_id':'1','user_id':'1'}
	data = {'image':'test.jpg', 'image_type':'face_token','group_id':'group1','user_id':'1'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_user_get_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/user/get'
	data = {'group_id':'group1','user_id':'1'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_user_delete_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/user/delete'
	data = {'group_id':'group1','user_id':'1'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_user_copy_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/user/copy'
	data = {'src_group_id':'group1','dst_group_id':'group2','user_id':'1'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_face_delete_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/face/delete'
	data = {'group_id':'group1','user_id':'1','face_token':'2571c74e-119c-4164-8605-15bdeab6d0e9'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)

def test_faceset_face_getlist_api():
	test_url = 'http://127.0.0.1:5000/api/faceset/face/getlist'
	data = {'group_id':'group1','user_id':'1'}
	res = requests.post(test_url, json=data, auth=('jjchen','python'))
	print (res.text)


if __name__ == '__main__':

	# test_face_detect_api()

	# test_face_match_api()

	# test_faceset_group_add_api()

	# test_faceset_group_delete_api()

	# test_faceset_group_getlist_api()

	# test_faceset_user_add_api()
	# test_faceset_user_update_api()
	# test_faceset_face_delete_api()
	# test_faceset_user_get_api()
	# test_faceset_face_getlist_api()

	# test_faceset_group_getusers_api()
	# test_faceset_user_delete_api()
	# test_faceset_group_getusers_api()



	# print ("group1 get users")
	# test_faceset_group_getusers_api()
	# print ("copy user from group1 to group2")
	# test_faceset_user_copy_api()



	# print ("group2 get users")
	# test_faceset_group_getusers_api('group2')
	test_face_search_api()