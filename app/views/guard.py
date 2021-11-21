from os import stat
from werkzeug import utils
from app import *
from app.helperFunctions import *
from flask import (Blueprint, Flask, flash, g, redirect, render_template,
                   request, send_file, session, url_for)
from flask_mysqldb import MySQL
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail, Message  
from datetime import date
import pandas as pd
import json

guard = Blueprint('guard', __name__, url_prefix='/guard') 
BASE_URL = "http://18.221.229.66:5001/api/"

#Login page
@guard.route('/', methods=['GET','POST'])
def home():
	user = getCurrentGuardUser()
	if user:
		return redirect(url_for('guard.dashboard'))
	if request.method == 'POST':
		guardID = request.form['guard-login-userID']
		password = hashlib.md5(request.form['guard-login-password'].encode())
		result = query_db("select * from login_guard where userID=%s;",(guardID,))
		if result is not None:
			if result[0][1]==password.hexdigest():
				session['guardID']=guardID
				return redirect(url_for('guard.permissions'))
			else:
				return render_template('guard/login.html',loginFlag=0)
		else:
			return render_template('guard/login.html',loginFlag=0)
	else:
		return render_template('guard/login.html',loginFlag=1)


#permissions
@guard.route('/permissions', methods=['GET','POST'])
def permissions():
	user = getCurrentGuardUser()
	cur = mysql.connection.cursor()
	if user:

		#permissionsAdminControl
		permissionsAdminControlUrl = BASE_URL+"getPermissionsAdminControlls"
		permissionsAdminControlHeaders = {'Authorization': 'Basic Y2Fwc3RvbmU6Q2Fwc3RvbmVANTQzMjEj'}
		permissionsAdminControlResponse = requests.request("GET", permissionsAdminControlUrl, headers=permissionsAdminControlHeaders)
		permissionsAdminControls = json.loads(permissionsAdminControlResponse.text)
		permissionsAppActivated = permissionsAdminControls["activatePermissionsApp"]
		rulesInformation = permissionsAdminControls["informationToBeDisplayed"]
		inTime = permissionsAdminControls["inTime"]
		outTime = permissionsAdminControls["outTime"]
		studentDetails=[]
		permission=[]

		if request.method == 'GET':
			return render_template('/guard/permissions.html', appActivation = permissionsAppActivated, inTime = inTime, outTime = outTime, studentDetails = studentDetails, permisiion = permission)

		if request.method == 'POST':
			# fetch permission and student details from roll number
			if request.form['submit'].split(':')[0]=='search':
				rollNumber = request.form("rollNumber")
				searchParams = {'rollNumber':rollNumber}
				searchHeaders = {'Authorization': 'Basic Y2Fwc3RvbmU6Q2Fwc3RvbmVANTQzMjEj'}

				getStudentDetailsUrl = BASE_URL+"getStudentDetails"
				getStudentDetailsResponse = requests.request("GET", getStudentDetailsUrl, headers=searchHeaders, params=searchParams)

				getPermissionUrl = BASE_URL+"getPermission"
				getPermissionResponse = requests.request("GET", getPermissionUrl, headers=searchHeaders, params=searchParams)



		return render_template('guard/permissions.html')
	else:
		return redirect(url_for('guard.home'))

@guard.route('/forgot-password', methods=['GET','POST'])
def forgotPassword():
	pass

@guard.route('/logout')
def logout():
    user = getCurrentGuardUser()
    if user:
        session.pop('guardID', None)
        return redirect(url_for('guard.home'))
    else:
        return redirect(url_for('guard.home'))