from app import *
from flask import (Blueprint, Flask, flash, g, redirect, render_template,
                   request, send_file, session, url_for)
from flask_mysqldb import MySQL
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime
import re
import csv
from datetime import date
import json
from flask_httpauth import HTTPBasicAuth
import hashlib
from app.helperFunctions import *


apiController = Blueprint('apiController', __name__, url_prefix='/api') 
auth = HTTPBasicAuth()

users = {
    "capstone": "95c5022d6ccb62cf4634f653246c003a"
}

# Verify Authentication
@auth.verify_password
def verify_password(username, password):
	hashedPass = hashlib.md5(password.encode())
	if username=="capstone" and users[username]==hashedPass.hexdigest():
		return username

# Swagger
@apiController.route('/', methods=['GET'])
@auth.login_required
def apiSwagger():
	listOfApis = {}
	listOfApis["/setNewPermission"] = {"Method":"POST",
	"Description":"adds a new permission",
	"parameters":{
		"date":"Date when permission is required", 
		"fromTime":"Campus exit time", 
		"toTime":"Campus entry time",
		"location":"Location of visit",
		"reason":"Purpose of visit",
		"rollNumber":"Roll Number of student"
		},
	"Authentication":"Required",
	"Return type":"msg,STATUS_CODE"
	}
	return listOfApis

# Saves new permission to db
@apiController.route('/setNewPermission', methods=['POST'])
@auth.login_required
def setNewPermission():
	cur = mysql.connection.cursor()
	try:
		if request.form['submit']=='submitPermission':
			date = request.form['date']
			fromTime = request.form['fromTime']
			toTime = request.form['toTime']
			location = request.form['location']
			reason = request.form['reason']
			rollNumber = request.form["rollNumber"]
			curDate = datetime.now().strftime("%d-%m-%Y")
			curTime = datetime.now().strftime("%H:%M:%S")
			cur.execute('insert into permissions (rollNumber, permDate, permOutTime, permInTime, reason, location, status, permRequestTime, PermRequestDate) values(%s,%s,%s,%s,%s,%s,%s,%s,%s);',(rollNumber, date, fromTime, toTime, reason,location, 0, curTime, curDate,))
			mysql.connection.commit()
			return "OK",200
	except:
		return "Internal Server Error",500

# Delete a permission from db
@apiController.route('/deletePermission', methods=['POST'])
@auth.login_required
def deletePermission():
	cur = mysql.connection.cursor()
	try:
		permisisonId = request.form['permissionId']
		cur.execute("UPDATE permissions SET `status` = '-1' WHERE (`permissionID` = %s);",(permisisonId,))
		mysql.connection.commit()
		return "OK",200
	except:
		return "Internal Server Error",500

# Approve a permission parent
@apiController.route('/acceptPermission', methods=['POST'])
@auth.login_required
def acceptPermission():
	cur = mysql.connection.cursor()
	try:
		permisisonId = request.form['permissionId']
		cur.execute("UPDATE permissions SET `status` = '1' WHERE (`permissionID` = %s);",(permisisonId,))
		mysql.connection.commit()
		return "OK",200
	except:
		return "Internal Server Error",500

# Reject a permission parent
@apiController.route('/rejectPermission', methods=['POST'])
@auth.login_required
def rejectPermission():
	cur = mysql.connection.cursor()
	try:
		permisisonId = request.form['permissionId']
		cur.execute("UPDATE permissions SET `status` = '2' WHERE (`permissionID` = %s);",(permisisonId,))
		mysql.connection.commit()
		return "OK",200
	except:
		return "Internal Server Error",500

# Gets permissions where status is = 0 (i.e requested by student)
@apiController.route('/getRequestedPermissions', methods=['GET'])
@auth.login_required
def getRequestedPermissions():
	try:
		rollNumber = request.args.get('rollNumber')
		requestedPermission = query_db("select * from permissions where rollNumber=%s and status=0;",(rollNumber,))
		if requestedPermission is None:
			requestedPermission=[]
		data = {"requestedPermissions":list(requestedPermission)}
		return data,200
	except:
		return "Internal Server Error",500

# Gets permissions where status is = 1, 3, 4 (i.e Active Permisisions)
@apiController.route('/getActivePermissions', methods=['GET'])
@auth.login_required
def getActivePermissions():
	try:
		rollNumber = request.args.get('rollNumber')
		activePermission = query_db("select * from permissions where rollNumber=%s and status in (1,3,4);",(rollNumber,))
		if activePermission is None:
			activePermission=[]
		data = {"activePermissions":list(activePermission)}
		return data,200
	except:
		return "Internal Server Error",500

# Gets permissions where status is = 2, 5, 6, 7 (i.e  expired Permissions)
@apiController.route('/getExpiredPermissions', methods=['GET'])
@auth.login_required
def getexpiredPermissions():
	try:
		rollNumber = request.args.get('rollNumber')
		expiredPermission = query_db("select * from permissions where rollNumber=%s and status in (2, 5, 6, 7);",(rollNumber,))
		if expiredPermission is None:
			expiredPermission=[]
		data = {"expiredPermissions":list(expiredPermission)}
		return data,200
	except:
		return "Internal Server Error",500

# Gets admin controlls
@apiController.route('/getPermissionsAdminControlls', methods=['GET'])
@auth.login_required
def getPermissionsAdminControlls():
	try:
		adminControlsDb = query_db("select * from permissions_admin_controls;")
		if adminControlsDb is None:
			adminControlsDb=[]
		data = mapPermissionsAdminControlsToDict(list(adminControlsDb))
		return data,200
	except:
		return "Internal Server Error",500

# Gets student details from roll number
@apiController.route('/getStudentDetails', methods=['GET'])
@auth.login_required
def getStudentDetails():
	try:
		rollNumber = request.args.get('rollNumber')
		studentDetails = query_db("select * from student_details where rollNumber=%s;",(rollNumber,))
		if studentDetails is None:
			studentDetails=[]
		studentDetails = mapStudentDetailsToList(list(studentDetails))
		return studentDetails,200
	except:
		return "Internal Server Error",500

# Gets permission for current date and status 1,3 from roll number 
# (Approved by parent but not returned to campus)
@apiController.route('/getPermission', methods=['GET'])
@auth.login_required
def getPermission():
	try:
		rollNumber = request.args.get('rollNumber')
		curDate=datetime.today()
		curDate=datetime.strftime(curDate,"%d-%m-%Y")
		permission = query_db("select * from permissions where rollNumber=%s and permDate=%s and status in (1,3);",(rollNumber, curDate,))
		if permission is None:
			permission=[]
		permission = mapPermissionToList(list(permission))
		return permission,200
	except:
		return "Internal Server Error",500

# Mark exit by guard
@apiController.route('/markExit', methods=['POST'])
@auth.login_required
def markExit():
	cur = mysql.connection.cursor()
	try:
		permisisonId = request.form['permissionId']
		guardId = request.form['guardId']
		status = 3
		now = datetime.now()
		curTime = now.strftime("%H:%M")
		cur.execute("UPDATE permissions SET `status` = %s, `outTime` = %s, `guardIdOut` = %s WHERE (`permissionID` = %s);",(status, curTime, guardId, permisisonId,))
		mysql.connection.commit()
		cur.close()
		return "OK",200
	except:
		cur.close()
		return "Internal Server Error",500

# Mark entry by guard
@apiController.route('/markEntry', methods=['POST'])
@auth.login_required
def markEntry():
	cur = mysql.connection.cursor()
	try:
		permisisonId = request.form['permissionId']
		guardId = request.form['guardId']
		now = datetime.now()
		curTime = now.strftime("%H:%M")
		inTime = list(query_db("select permInTime from permissions where permissionID=%s;",(permisisonId,)))[0][0]
		curTimeObj = datetime.strptime(curTime,"%H:%M")
		inTimeObj = datetime.strptime(inTime,"%H:%M")
		status=0
		if(curTimeObj>inTimeObj):
			status=6
		else:
			status=5
		cur.execute("UPDATE permissions SET `status` = %s, `inTime` = %s, `gaurdIdIn` = %s WHERE (`permissionID` = %s);",(status, curTime, guardId, permisisonId,))
		mysql.connection.commit()
		cur.close()
		return "OK",200
	except:
		cur.close()
		return "Internal Server Error",500