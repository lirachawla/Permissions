from datetime import datetime
from flask import session
from app import *
from flask_mysqldb import MySQL

# Gets current parent user
def getCurrentParentUser():
	userResult = None
	if 'parentID' in session:
		parentID = session['parentID']
		for key in list(session.keys()):
			if key == "parentID":
				continue
			session.pop(key)
		userResult = query_db("select userID from login_parent where userID=%s;",(parentID,))
	return userResult

# Gets current guard user
def getCurrentGuardUser():
	userResult = None
	if 'guardID' in session:
		guardID = session['guardID']
		for key in list(session.keys()):
			if key == "guardID":
				continue
			session.pop(key)
		userResult = query_db("select userID from login_guard where userID=%s;",(guardID,))
	return userResult

# Mapping requested permissions to a list
def mapRequestedPermissionsToList(data):
	tempResponse = data["requestedPermissions"]
	finalResponse = []
	for i in tempResponse:
		permissionID = i[0]
		permissionDate = i[2]
		permissionOutTime = i[3]
		permissionInTime = i[4]
		reason = i[5]
		location = i[6]
		permissionRequestedAt = i[8]
		permissionRequestedOn = i[9]
		curResponse = [permissionID, permissionDate, permissionOutTime, permissionInTime, reason, location, permissionRequestedAt, permissionRequestedOn]
		finalResponse.append(curResponse)
	return finalResponse

# Mapping active permissions to a list
def mapActivePermissionsToList(data):
	tempResponse = data["activePermissions"]
	finalResponse = []
	for i in tempResponse:
		permissionID = i[0]
		permissionDate = i[2]
		permissionOutTime = i[3]
		permissionInTime = i[4]
		reason = i[5]
		location = i[6]
		status = i[7]
		permissionRequestedAt = i[8]
		permissionRequestedOn = i[9]
		approvedByParentsAt = i[10]
		approvedByParentsOn = i[11]
		leftCampusAt = i[13]
		if leftCampusAt is None:
			leftCampusAt="Time unavailable"
		campusExitApprovedByGaurd = i[14]
		if campusExitApprovedByGaurd is None:
			campusExitApprovedByGaurd = "Unavailable"
		curResponse = [permissionID, permissionDate, permissionOutTime, permissionInTime, reason, location, status, permissionRequestedAt, permissionRequestedOn, approvedByParentsAt, approvedByParentsOn, leftCampusAt, campusExitApprovedByGaurd]
		finalResponse.append(curResponse)
	return finalResponse

# Mapping expired permissions to a list
def mapExpiredPermissionsToList(data):
	tempResponse = data["expiredPermissions"]
	finalResponse = []
	for i in tempResponse:
		permissionID = i[0]
		permissionDate = i[2]
		permissionOutTime = i[3]
		permissionInTime = i[4]
		reason = i[5]
		location = i[6]
		status = i[7]
		permissionRequestedAt = i[8]
		permissionRequestedOn = i[9]
		approvedByParentsAt = i[10]
		approvedByParentsOn = i[11]
		returnedToCampusAt = i[12]
		if returnedToCampusAt is None:
			returnedToCampusAt = "Time unavailable"
		leftCampusAt = i[13]
		if leftCampusAt is None:
			leftCampusAt = "Time unavailable"
		campusExitApprovedByGaurd = i[14]
		campusEntryApprovedByGaurd = i[15]
		if campusEntryApprovedByGaurd is None:
			campusEntryApprovedByGaurd = "Unavailable"
		if campusExitApprovedByGaurd is None:
			campusExitApprovedByGaurd = "Unavailable"
		curResponse = [permissionID, permissionDate, permissionOutTime, permissionInTime, reason, location, status, permissionRequestedAt, permissionRequestedOn, approvedByParentsAt, approvedByParentsOn, returnedToCampusAt, leftCampusAt, campusEntryApprovedByGaurd, campusExitApprovedByGaurd]
		finalResponse.append(curResponse)
	return finalResponse

# Check for the following conditions:
# 1) if permisison in time is after allowed in time
# 2) if permisison out time is after allowed out time
# 3) if permisison in date-time before current time
# 4) if in time is before out time
def checkForValidTimestamp(toTime, fromTime, date, inTime, outTime):
	inTimeObeject = datetime.strptime(inTime, '%H:%M:%S')
	outTimeObject = datetime.strptime(outTime, '%H:%M:%S')
	curDateTimeObject = datetime.now()
	toTimeObject = datetime.strptime(toTime, '%H:%M')
	fromTimeObject = datetime.strptime(fromTime, '%H:%M')
	permissionDateTimeObject = datetime.strptime(date+" "+toTime, '%d-%m-%Y %H:%M')
	if inTimeObeject<toTimeObject or outTimeObject<fromTimeObject:
		return False
	if curDateTimeObject>permissionDateTimeObject:
		return False
	if inTimeObeject<outTimeObject:
		return False	
	return True

# Checks if a permission already exists for the asked date. (Only one permission per date)
def checkIfPermissionAlreadyExists(userId, date):
	permission = query_db("select * from permissions where rollNumber=%s and permDate=%s;",(userId, date,))
	if permission is None:
		return False
	return True

# Maps permission admin controls to dictionary with appropriate data
def mapPermissionsAdminControlsToDict(adminControlsDb):
	data = {}
	if len(adminControlsDb)==0:
		data["inTime"]="Not Available"
		data["outTime"]="Not Available"
		data["informationToBeDisplayed"]=["Not Available"]
		data["activatePermissionsApp"]=0
		data["mailReportsToWardens"]="Configure accordingly"
	else:
		data["inTime"]=adminControlsDb[0][1]
		data["outTime"]=adminControlsDb[0][2]
		data["informationToBeDisplayed"]=list(adminControlsDb[0][3].split("#$#"))
		data["activatePermissionsApp"]=adminControlsDb[0][4]
		data["mailReportsToWardens"]=list(adminControlsDb[0][5].split(" "))
	return data

# Maps student details to dictionary with appropriate data
def mapStudentDetailsToList(studentDetails):
	data = []
	# Check if details are present
	if len(studentDetails)==0:
		data.append(0)
	else:
		data.append(1)
		data.append(studentDetails[0][1])
		data.append(studentDetails[0][2])
		data.append(studentDetails[0][3])
		data.append(studentDetails[0][4])
		data.append(studentDetails[0][5])
		data.append(studentDetails[0][6])
		data.append(studentDetails[0][7])
		data.append(studentDetails[0][8])
		data.append(studentDetails[0][9])
		data.append(studentDetails[0][10])
		data.append(studentDetails[0][11])
		data.append(studentDetails[0][12])
		data.append(studentDetails[0][13])
		data.append(studentDetails[0][14])
		data.append(studentDetails[0][15])
		data.append(studentDetails[0][16])
	return data
	

# Maps current permission to dictionary with appropriate data
def mapPermissionToList(permission):
	data = []
	# Check if permission is present
	if len(permission)==0:
		data.append(0)
	else:
		data.append(1)
		data.append(permission[0][0])  # permissionId
		data.append(permission[0][3])  # permOutTime
		data.append(permission[0][4])  # permInTime
		data.append(permission[0][5])  # reason
		data.append(permission[0][6])  # location
		if permission[0][13] is None:  # outTime
			data.append("Not Available")
		else:
			data.append(permission[0][13]) 
		if permission[0][13] is None:  # inTime
			data.append("Not Available")
		else:
			data.append(permission[0][12])
	return data