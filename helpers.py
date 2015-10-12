
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CatalogItem

import random, string

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif', 'jpeg', 'tiff', 'bmp', 'svg'])


#user state debug block
def userStateDebug(login_session):
	print "User State:"
	print "username: %s"% login_session['username']
	print "securityState: %s"%login_session['securityState']
	print "email: %s"%login_session['email']




def createState():
	#create new state token to pass during post requests to mitigate XSS and CSRF attacks
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
					for x in xrange(32))
	return state



#Check that image file is valid and sanditize name for saving
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.')[1] in ALLOWED_EXTENSIONS


def prettify(elem):
	#Return a pretty-printed XML string for the Element.

	rough_string = ElementTree.tostring(elem, 'utf-8')
	reparsed = minidom.parseString(rough_string)
	return reparsed.toprettyxml(indent="  ")



# User Helper Functions
def createUser(session, login_session):
	newUser = User(name=login_session['username'], email=login_session[
				   'email'], picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id


def getUserInfo(session, user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user


def getUserID(session, email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None