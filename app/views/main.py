import re
from app import *
from flask import (Blueprint, Flask, flash, g, redirect, render_template,
                   request, send_file, session, url_for)
from flask_mysqldb import MySQL
import hashlib
import os
from datetime import date
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail, Message  
import subprocess
import string
import secrets
import json
from app.helperFunctions import *


main = Blueprint('main', __name__) 
mail= Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cmstiet@gmail.com'
app.config['MAIL_PASSWORD'] = 'Test@1234'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
BASE_URL = "http://18.221.229.66:5001/api/"

#email
def email(msgBody,subject,userID,senderEmail='cmstiet@gmail.com' ):
	receiversEmail = query_db("select emailStudent from student_details where userID=%s",(userID,))
	if receiversEmail is None:
		receiversEmail=senderEmail
	msg = Message(subject, sender = senderEmail, recipients = [receiversEmail[0][0]])
	msg.body = msgBody
	mail.send(msg)
	return "OK"

def emailRoll(msgBody,subject,rollNumber,senderEmail='cmstiet@gmail.com' ):
	receiversEmail = query_db("select emailStudent from student_details where rollNumber=%s",(rollNumber,))
	if receiversEmail is None:
		receiversEmail=senderEmail
	msg = Message(subject, sender = senderEmail, recipients = [receiversEmail[0][0]])
	msg.body = msgBody
	mail.send(msg)
	return "OK"

@app.route("/cron/refreshApprovals", methods=['POST'])
def refreshApprovals():
	cur=mysql.connection.cursor()
	temp=query_db('select complaintID,subject,userID,dateCompleted from cms where status in (5);')
	d=" "
	if temp is None:
		temp=[]
	for complaint in temp:
		complainID = complaint[0]
		complaintDesc = complaint[1]
		userID=complaint[2]
		dateOfComplaint = complaint[3]
		curDate = date.today()
		complaintDate = date.today()
		if dateOfComplaint== None:
			complaintDate=curDate
		else:
			dateOfComplaint=str(dateOfComplaint)
			complaintDate = date(int(dateOfComplaint.split('-')[2]),int(dateOfComplaint.split('-')[1]),int(dateOfComplaint.split('-')[0]))
		delta = curDate-complaintDate
		if(delta.days==2):
			body="Dear Student\n\nYour Complaint with Complaint ID = "+str(complainID)+" and Subject : '"+str(complaintDesc)+"' awaits a feedback. Incase you fail to provide a feedback by today, it shall be auto-approved by the system. Please check your dashboard at http://cmmstiet.in for further details.\nTHIS IS AN AUTOMATED MESSAGE- PLEASE DO NOT REPLY.\n\nThank You!"
			subject = "Complaint feedback required for complaintID:"+str(complainID)
			email(body,subject,userID)
		if(delta.days>3):
			d=delta.days
			cur.execute('update cms set status=7 where complaintID=%s;',(complainID,))
			mysql.connection.commit()
			body="Dear Student\n\nYour Complaint with Complaint ID = "+str(complainID)+" and Subject : '"+str(complaintDesc)+"' has been auto-approved. Please check your dashboard at http://cmmstiet.in for further details.\nTHIS IS AN AUTOMATED MESSAGE- PLEASE DO NOT REPLY.\n\nThank You!"
			subject = "Complaint Auto-approved (complaintID:"+str(complainID)+")"
			email(body,subject,userID)
	cur.close()
	return "OK", 200

@app.route("/cron/dbSync", methods=['POST'])
def dbSync():
	os.system("python3 database\ updation/dbSyncAutomated.py")
	return "OK", 200


def getCurrentStudent():
	userResult = None
	if 'rollNumber' in session:
		rollNumber = session['rollNumber']
		for key in list(session.keys()):
			if key != "rollNumber":
				session.pop(key)
		userResult = query_db("select userID, rollNumber from login_student where rollNumber=%s;",(rollNumber,))
	return userResult


@main.route('/', methods=['GET','POST'])
def home():
	user = getCurrentStudent()
	cur = mysql.connection.cursor()
	try:
		if user:
			return redirect(url_for('main.dashboard'))
		if request.method == 'POST':
			rollNumber = request.form['student-login-roll']
			password = hashlib.md5(request.form['student-login-password'].encode())
			result=None
			result = query_db("select * from login_student where rollNumber=%s;",(rollNumber,))
			if result:
				if result[0][2]==password.hexdigest():
					if str(result[0][3])=="1":
						session['rollNumber']=rollNumber
						return redirect(url_for('main.dashboard'))
					else:
						return render_template('login.html',loginFlag=2) 
				else:
					return render_template('login.html',loginFlag=0)
			else:
				return render_template('login.html',loginFlag=0)
		else:
			return render_template('login.html',loginFlag=1)
	except Exception as e:
		mysql.connection.rollback()
		flash("Something went wrong!", 'danger')
		return redirect(url_for('main.home'))
	finally:
		cur.close()

#webhook for auto pull
@app.route("/autoPull", methods=['POST'])
def autoPull():
	try:
		os.system("sudo git pull")
		return "SUCCESS",200
	except:
		return "FAIL",200
	

@main.route('/dashboard', methods=['GET'])
def dashboard():
	user=getCurrentStudent()
	cur = mysql.connection.cursor()
	if user:
		#remove next line when dashboard is ready
		return redirect(url_for('main.userProfile'))
		userDetails = query_db("select userID, rollNumber, firstName, lastName from student_details where userID=%s;",(user[0][0],))
		return render_template('dashboard.html',user=userDetails)
	else:
		return redirect(url_for('main.home'))


@main.route('/logout')
def logout():
    user = getCurrentStudent()
    if user:
        session.pop('rollNumber', None)
        return redirect(url_for('main.home'))
    else:
        return redirect(url_for('main.home'))
        
@main.route('/user-profile', methods=['GET', 'POST'])
def userProfile():
	user=getCurrentStudent()
	cur = mysql.connection.cursor()
	if user:
		userDetails = query_db("select userID, rollNumber, firstName, lastName, emailStudent, DOB, course, branch from student_details where userID=%s;",(user[0][0],))
		hostelLog = query_db("select hostelRoomID from hostel_log where userID=%s;",(user[0][0],))
		hostelDetails = query_db("select hostelID, roomNumber, type from hostel_details where hostelRoomID=%s",(hostelLog[0][0],))
		hostelData = query_db("select hostelName, caretakerID, nightCaretakerID, wardenID from hostel_data where hostelID=%s",(hostelDetails[0][0],))
		hostelPeeps = []
		wardenDeets = query_db("select firstName, lastName, mobile, email, hostelEmail from warden_details where userID=%s;",(hostelData[0][3],))
		ctDeets = query_db("select firstName, lastName, mobile, email from caretaker_details where userID=%s;",(hostelData[0][1],))
		ntctDeets = query_db("select firstName, lastName, mobile, email from night_caretaker_details where userID=%s;",(hostelData[0][2],))
		hostelPeeps.append(wardenDeets[0])
		hostelPeeps.append(ctDeets[0])
		hostelPeeps.append(ntctDeets[0])
		if request.method=='GET':
			return render_template('changePassword.html',user=userDetails,hostelDetails=hostelDetails,hostelPeeps=hostelPeeps,hostelData=hostelData,passwordCheck=0,success=0)
		if request.method=='POST':
			if request.form['submit']=='Change Password':
				oldPassword = hashlib.md5(request.form['student-old-password'].encode())
				newPassword = hashlib.md5(request.form['student-new-password'].encode())
				result = query_db("select * from login_student where rollNumber=%s;",(user[0][1],))
				if result[0][2]==oldPassword.hexdigest():
					cur.execute("update login_student set password=%s where rollNumber=%s;", (newPassword.hexdigest(),user[0][1],))
					mysql.connection.commit()
					return render_template('changePassword.html',user=userDetails,hostelDetails=hostelDetails,hostelPeeps=hostelPeeps,hostelData=hostelData, passwordCheck=0,success=1)
				else:
					return render_template('changePassword.html',user=userDetails,hostelDetails=hostelDetails,hostelPeeps=hostelPeeps,hostelData=hostelData, passwordCheck=1,success=0)
			
	else:
		return redirect(url_for('main.home'))
	cur.close()
		
@main.route('/forgot-password', methods=['GET','POST'])
def forgotPassword():
	cur = mysql.connection.cursor()
	if request.method=='GET':
		return render_template('forgotPassword.html',detailsCheck=0,success=0)
	if request.method=='POST':
		rollNumber = request.form['student-roll']
		emailX= request.form['student-email']
		rollResult = query_db("select * from login_student where rollNumber=%s;", (rollNumber,))
		if rollResult is not None:
			emailResult = None
			emailResult = query_db("select emailStudent from student_details where rollNumber=%s;", (rollNumber,))
			if emailResult and emailResult[0][0]==emailX:
				password=None
				alphabet = string.ascii_letters + string.digits
				while True:
    					password = ''.join(secrets.choice(alphabet) for i in range(10))
    					if (any(c.islower() for c in password)
            							and any(c.isupper() for c in password)
            							and sum(c.isdigit() for c in password) >= 3):
        					break
				mailBody="Dear Student\n\nHere is your updated password for the hostel webkiosk.\n{}\nKindly change it as soon as possible.\nTHIS IS AN AUTOMATED MESSAGE- PLEASE DO NOT REPLY.\n\nThank You!".format(password)
				curDateTime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
				mailSubject="Hostel Webkiosk Password Reset at "+str(curDateTime)
				if emailRoll(mailBody,mailSubject,rollNumber)=="OK":
					cur.execute("update login_student set password=%s where rollNumber=%s;", (hashlib.md5(password.encode()).hexdigest(),rollNumber,))
					mysql.connection.commit()
					return render_template('forgotPassword.html',detailsCheck=0,success=1)
				else:
					return render_template('forgotPassword.html',detailsCheck=0,success=0) 
			else:
				return render_template('forgotPassword.html',detailsCheck=1,success=0)
		else:
			return render_template('forgotPassword.html',detailsCheck=1,success=0)
	cur.close()

@main.route('/permissions', methods=['GET','POST'])
def permissions():
	user=getCurrentStudent()
	cur = mysql.connection.cursor()
	if user:
		#getUserDetails
		userDetails = query_db("select userID, rollNumber, firstName, lastName from student_details where userID=%s;",(user[0][0],))
		
		#permissionsAdminControl
		permissionsAdminControlUrl = BASE_URL+"getPermissionsAdminControlls"
		permissionsAdminControlHeaders = {'Authorization': 'Basic Y2Fwc3RvbmU6Q2Fwc3RvbmVANTQzMjEj'}
		permissionsAdminControlResponse = requests.request("GET", permissionsAdminControlUrl, headers=permissionsAdminControlHeaders)
		permissionsAdminControls = json.loads(permissionsAdminControlResponse.text)
		permissionsAppActivated = permissionsAdminControls["activatePermissionsApp"]
		rulesInformation = permissionsAdminControls["informationToBeDisplayed"]
		inTime = permissionsAdminControls["inTime"]
		outTime = permissionsAdminControls["outTime"]

		#requestedPermissions
		requestedPermissionsUrl = BASE_URL+"getRequestedPermissions"
		requestedPermissionsparams = {'rollNumber': user[0][0]}
		requestedPermissionsheaders = {'Authorization':'Basic Y2Fwc3RvbmU6Q2Fwc3RvbmVANTQzMjEj','Cookie':'session=be2ba009-a267-4aa3-a3d4-528df54b4466'}
		requestedPermissionsresponse = requests.request("GET", requestedPermissionsUrl, headers=requestedPermissionsheaders, params=requestedPermissionsparams)
		requestedPermissionsList = mapRequestedPermissionsToList(requestedPermissionsresponse.json())
		#activePermissions
		activePermissionsUrl = BASE_URL+"getActivePermissions"
		activePermissionsparams={'rollNumber': user[0][0]}
		activePermissionsheaders = {'Authorization':'Basic Y2Fwc3RvbmU6Q2Fwc3RvbmVANTQzMjEj','Cookie':'session=be2ba009-a267-4aa3-a3d4-528df54b4466'}
		activePermissionsresponse = requests.request("GET", activePermissionsUrl, headers=activePermissionsheaders, params=activePermissionsparams)
		activePermissionsList = mapActivePermissionsToList(activePermissionsresponse.json())
		#expiredPermissions
		expiredPermissionsUrl = BASE_URL+"getExpiredPermissions"
		expiredPermissionsparams={'rollNumber': user[0][0]}
		expiredPermissionsheaders = {'Authorization':'Basic Y2Fwc3RvbmU6Q2Fwc3RvbmVANTQzMjEj','Cookie':'session=be2ba009-a267-4aa3-a3d4-528df54b4466'}
		expiredPermissionsresponse = requests.request("GET", expiredPermissionsUrl, headers=expiredPermissionsheaders, params=expiredPermissionsparams)
		expiredPermissionsList = mapExpiredPermissionsToList(expiredPermissionsresponse.json())
		
		if request.method == 'GET':
			return render_template('permissions.html', user = userDetails, requestedPermissionsList = requestedPermissionsList, activePermissionsList = activePermissionsList, expiredPermissionsList = expiredPermissionsList, appActivation = permissionsAppActivated, rejectRequestFlag = 0, inTime = inTime, outTime = outTime, rulesInformation = rulesInformation)
		
		if request.method=='POST':
			#submit permission
			if request.form['submit']=='submitPermission':
				date = request.form['date']
				fromTime = request.form['fromTime']
				toTime = request.form['toTime']
				location = request.form['location']
				reason = request.form['reason']
				if not checkForValidTimestamp(toTime, fromTime, date, inTime, outTime):
					return render_template('permissions.html', user = userDetails, requestedPermissionsList = requestedPermissionsList, activePermissionsList = activePermissionsList, expiredPermissionsList = expiredPermissionsList, appActivation = permissionsAppActivated, rejectRequestFlag = 1,  inTime = inTime, outTime = outTime, rulesInformation = rulesInformation)
				if checkIfPermissionAlreadyExists(user[0][0],date):
					return render_template('permissions.html', user = userDetails, requestedPermissionsList = requestedPermissionsList, activePermissionsList = activePermissionsList, expiredPermissionsList = expiredPermissionsList, appActivation = permissionsAppActivated, rejectRequestFlag = 2,  inTime = inTime, outTime = outTime, rulesInformation = rulesInformation)
				url = BASE_URL+"setNewPermission"
				payload={'submit': 'submitPermission','date': date,'fromTime': fromTime,'toTime': toTime,'location': location,'reason': reason,'rollNumber':user[0][0]}
				headers = {'Authorization': 'Basic Y2Fwc3RvbmU6Q2Fwc3RvbmVANTQzMjEj','Cookie': 'session=be2ba009-a267-4aa3-a3d4-528df54b4466'}
				response = requests.request("POST", url, headers=headers, data=payload)
				return redirect(url_for("main.permissions"))
				
			#delete permission
			elif request.form['submit'].split(':')[0]=='deletePermission':
				permissionId = request.form['submit'].split(':')[1]
				url = BASE_URL+"deletePermission"
				payload={"permissionId":permissionId}
				headers = {'Authorization': 'Basic Y2Fwc3RvbmU6Q2Fwc3RvbmVANTQzMjEj','Cookie': 'session=be2ba009-a267-4aa3-a3d4-528df54b4466'}
				response = requests.request("POST", url, headers=headers, data=payload)
				return redirect(url_for("main.permissions"))
	else:
		return redirect(url_for('main.home'))
	cur.close()
