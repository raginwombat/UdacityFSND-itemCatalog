import os
from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from werkzeug import secure_filename


from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CatalogItem

#Session token imports
from flask import session as login_session
import string

#API endpoint
from werkzeug.contrib.atom import AtomFeed
from xml.etree.ElementTree import  SubElement, Comment, Element, ElementTree, tostring
from xml.dom import minidom

#Helper Functions
from helpers import *

#call back code imports
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Project 3"

#Connect to Database and create database session
engine = create_engine('sqlite:///itemCatalogDB.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#Image File location delcarions
UPLOAD_FOLDER = './static/images'


#Flask Declartions
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
	#limit size of uploaded picture
app.config['MAX_CONTENT_LENGTH'] = 16*1024*1024

#Support structures
@app.route('/login')
def showLogin():
	state =  createState()
	login_session['state'] = state
	# return "The current session state is %s" % login_session['state']
	return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
	# Validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Obtain authorization code
	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(
			json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
		   % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'),
								 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	# see if user exists, if it doesn't make a new one
	user_id = getUserID(session, data["email"])
	if not user_id:
		user_id = createUser(session, login_session)
	login_session['user_id'] = user_id



	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output




# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
		# Only disconnect a connected user.
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(
			json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = credentials.access_token
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]

	if result['status'] == '200':
		# Reset the user's sesson.
		del login_session['credentials']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']

		flash('Successfully disconnected.')
		return redirect(url_for('showCatalog'))
	else:
		# For whatever reason, the given token was invalid.
		flash('Failed to revoke token for given user')
		
		return redirect(url_for('showCatalog'))





##################################
#
#Main Catalog
#
#Start Displaying pages
#
##################################

@app.route('/')
@app.route('/catalog/')
def showCatalog():
	categories =  session.query(Category).all()
	#latest_Items = session.query(CatalogItem).limit(10)
	latest_Items = session.query(CatalogItem).order_by( CatalogItem.id.desc() ).limit(10)
	#latest_Items = session.query(CatalogItem).order_by( "id desc" ).limit(10)
	if 'username' in login_session:
		#logged in so present edit private page
		print login_session['username']
		#pull the catalog for the user first:
		#login_session['user_id']
		return render_template('catalogMain.html', categories = categories, latestItems=latest_Items, logged_in=1)
	else:
		return render_template('publicCatalogMain.html', categories = categories, latestItems=latest_Items, logged_in=None)


@app.route('/catalog/new', methods = ['GET', 'POST'])
def newCatalog():
	#check if user is logged in
	if 'username' in login_session:
		categories = session.query(Category).all()
		if request.method == 'POST':
			if request.form['token_id'] != login_session['securityState']:
				flash("Error, incorrect security Key. please try again")
				return redirect(url_for('showCatalog'))
			else:
				newCatalog = Catalog( name = request.form['name'], user_id = login_session['user_id'] )
				#post snippet            
				flash('Created New Catalog')
				return redirect( url_for('showCatalog') )
		else:
			#Get Block
			login_session['securityState']  =  createState()
		
			return render_template('catalogNew.html', state = login_session['securityState'], logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		#if user isn't logged in bounce them back to show catalog
		print "User isn't logged in"
		return redirect(url_for('showCatalog') )

@app.route('/catalog/<string:category_name>/edit', methods = ['GET', 'POST'])
	#edit catalog
def editCatalog(category_name):
		#check if user is logged in
	if 'username' in login_session:
		categories = session.query(Category).all()
		if request.method == 'POST':
			#post snippet
			#CSRF mitigation
			if request.form['token_id'] != login_session['securityState']:
				flash("Error, incorrect security Key. please try again")
				return redirect(url_for('showCatalog'))
			else:
				editCatalog = session.query(Category).filter_by(name = category_name).one()
				editCatalog.name = request.form['name']
				session.add(editCatalog)
				session.commit()
				flash("Created Edited Catlog")
				return redirect(url_for('showCatalog'))
		else:
			login_session['securityState'] =  createState()
			editCatalog = session.query(Category).filter_by(name = category_name).one()

			return render_template('catalogEdit.html', category = editCatalog, categories=categories, 
					state = login_session['securityState'], logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		return redirect(url_for('showCatalog') )

@app.route('/catalog/<string:category_name>/delete',  methods = ['GET', 'POST'])
def deleteCatalog(category_name):
	if 'username' in login_session:
		categories = session.query(Category).all()
		if request.method == 'POST':
			#post snippet
			#CSRF mitigation
			if request.form['token_id'] != login_session['securityState']:
				flash("Error, incorrect security Key. please try again")

			else:
				catalogDelete = session.query(Category).filter_by(name = category_name).one()
				session.delete(catalogDelete)
				session.commit()
				return redirect(url_for('showCatalog'))
		else:
			login_session['securityState']  =  createState()
			category = session.query(Category).filter_by(name=category_name ).one()
			
			return render_template('catalogDelete.html', category = category, categories=categories, 
					state = login_session['securityState'], logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		return redirect(url_for('showCatalog'))

@app.route('/catalog/new', methods = ['GET', 'POST'])
def newCatalog():
	if 'username' in login_session:
		categories = session.query(Category).all()
		if request.method == 'POST':
			#post snippet
			#CSRF mitigation
			if request.form['token_id'] != login_session['securityState']:
				flash("Error, incorrect security Key. please try again")

			else:
				newCategory = Category(name=request.form['name'], user_id=getUserID(session, login_session['email']) )
				session.add(newCategory)
				session.commit()
				return redirect(url_for('showCatalog'))
		else:
			login_session['securityState']  =  createState()			
			return render_template('catalogNew.html',  categories=categories, 
					state = login_session['securityState'], logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		return redirect(url_for('showCatalog'))


##################################
#
#Item and Details Catalog
#
#Manage lowest level objects
#
##################################



@app.route('/catalog/<string:category_name>/items')
def showItems(category_name):
	category = session.query(Category).filter_by(name = category_name).one()
	categories = session.query(Category).all()
	catalogItems = session.query(CatalogItem).filter_by(category_id = category.id).all()
	if 'username' in login_session:
		return render_template('ItemMain.html', category_name = category_name, catalogItems = catalogItems, 
				categories=categories, logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		return render_template('publicItemMain.html', category_name = category_name, catalogItems = catalogItems, 
				logged_in=None)


@app.route('/catalog/<string:category_name>/<string:item_name>')
def showItemDetail(category_name, item_name):
	category = session.query(Category).filter_by(name = category_name).one()
	categories = session.query(Category).all()
	detailItem = session.query(CatalogItem).filter_by(category_id = category.id, name = item_name).one()
	if 'username' in login_session:
		print detailItem.catalog_image_url
		return render_template('itemDetail.html', category_name = category_name, item = detailItem, 
				categories = categories, logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		return render_template('publicItemDetail.html', category_name = category_name, item = detailItem, 
				categories = categories, logged_in=None)

@app.route('/catalog/<string:category_name>/new', methods = ['GET', 'POST'])
def newItem(category_name):

	if 'username' in login_session:
		if request.method == 'POST':
			#Post Block
			#CSRF mitigation
			if request.form['token_id'] != login_session['securityState']:
				flash("Error, incorrect security Key. please try again")
				return redirect(url_for('showCatalog'))
			else: #Authenticated actuallly change
				#actually post change
				file = request.files['file']
				if file and allowed_file(file.filename):
					filename = secure_filename(file.filename)
					print "file to be saved: %s"%filename
					#should check to see if file exists, if so increment name
					#
					#
					#
					#
					#
					#
					file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
					print "file saved at: %s"%os.path.join(UPLOAD_FOLDER + "/" + file.filename)
				category = session.query(Category).filter_by(name=request.form['Category']).one()

				newItem = CatalogItem(user_id = login_session['user_id'], name = request.form['name'], 
					description = request.form['description'], category_id =category.id, 
					catalog_image_url = os.path.join(file.filename))
				session.add(newItem)
				session.commit()
				return redirect(url_for('showCatalog'))
		else :
			#GET Block
			#page to create new item
			login_session['securityState']  =  createState()
			categories = session.query(Category).all()
			return render_template('ItemNew.html', category_name =category_name, 
				state = login_session['securityState'], categories  = categories, logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		return redirect(url_for('login'))
	

@app.route('/catalog/<string:category_name>/<string:item_name>/edit', methods = ['GET', 'POST'])
def editItem(category_name, item_name):
	if 'username' in login_session:
		if request.method == 'POST':
			#post snippet
			#CSRF mitigation
			if request.form['token_id'] != login_session['securityState']:
				flash("Error, incorrect security Key. please try again")
				return redirect(url_for('showCatalog'))
			else: #Authenticated, actuallly change item
				#actually post change
				category = session.query(Category).filter_by( name=category_name).one()
				editItem = session.query(CatalogItem).filter_by( category_id=category.id, name=item_name).one()

				editItem.name = request.form['name']
  				editItem.description =  request.form['description']
  				editedCategory = session.query(Category).filter_by(name=request.form['Category']).one()
  				editItem.category_id = editedCategory.id
				
				#delete old image file
				#save new image file
				if request.files['file'].filename != '':
					editImage = request.files['file']
					if editImage and allowed_file(editImage.filename):
						editImageName = secure_filename(editImage.filename)
						#Print statments are debug statemnts to verify app functionaly from cli
						print "Image Name: %s"%editImageName
						editImage.save(os.path.join(app.config['UPLOAD_FOLDER'], editImageName))
						print "file saved at: %s"%os.path.join(app.config['UPLOAD_FOLDER'] , editImageName)
					
					oldImage = editItem.catalog_image_url
					#Check to make sure  uploading image with the same name is not deleted
					if oldImage != editImageName:
						os.remove(os.path.join(UPLOAD_FOLDER, oldImage))
						editItem.catalog_image_url = os.path.join(editImageName)
						session.add(editItem)
  				session.commit()
	    		return redirect(url_for('showItems', category_name = category_name))
		else:
			#get block
			#Find the catgory the edited Item belongs to
			category = session.query(Category).filter_by( name=category_name).one()
			#Get all of the categories to alllow selection of the category for the Item
			categories =  session.query(Category).all()
			#get the actual Item object
			editItem = session.query(CatalogItem).filter_by( name=item_name, category_id = category.id).one()
			#CSRF state otken
			login_session['securityState'] =  createState()
			return render_template('itemEdit.html', category_name = category_name, item = editItem, 
				categories = categories, state = login_session['securityState'], logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		return redirect(url_for('showItems', category_name = category_name))



@app.route('/catalog/<string:category_name>/<string:item_name>/delete', methods = ['GET', 'POST'])
def deleteItem(category_name, item_name):
	print "Delete Block"
	print "username type: %s"%type(login_session['username'])
	#userStateDebug()
	if 'username' in login_session:
		if request.method == 'POST':
			# Delete Item Post BLock
			#CSRF mitigation
			if request.form['token_id'] != login_session['securityState']:
				print "broken delete"
				flash("Error, incorrect security Key. please try again")
				return redirect(url_for('showCatalog'))
			else: #Authenticated actually delete sthe itme
				deleteItem = session.query(CatalogItem).filter_by(name = item_name).one()
				session.delete(deleteItem)
				session.commit()
				flash("Deleted item: %s" % deleteItem.name)
				return redirect(url_for('showItems', category_name = category_name) )
		else:
			#Delete Item Get Block
			deleteItem = session.query(CatalogItem).filter_by(name = item_name).one()
			login_session['securityState'] =  createState()

			return render_template('itemDelete.html', category_name=category_name, item = deleteItem, 
				state=login_session['securityState'], logged_in=1)
	 #if the user isnt' logged in they can't edit the catalog
	else:
		return redirect(url_for('showItems', category_name = category_name))



@app.route('/catalog/<string:exensivility_API>')
def APISupport(exensivility_API):
	if exensivility_API.lower() == 'json':
		return jsonify( category = [c.serialize for c in session.query(Category).all()], 
			item =[i.serialize for i in session.query(CatalogItem).all() ])


	elif exensivility_API.lower() == 'xml':
		nameString = 'Catalog for user %s'%login_session['username']
		catalog = Element('Catalog')
		print type(catalog)
		for category in session.query(Category).all():
			catalog.append(Element('Category Name') )		
			catalog.text = category.name
			for item in session.query(CatalogItem).filter_by(category_id = category.id).all():
				imgItem = SubElement(catalog, 'Image Name')
				imgItem.text = item.catalog_image_url
				descItem  = SubElement(catalog, 'Description')
				descItem.text =  item.description
				catItem  = SubElement(catalog, 'Item Name')
				catItem.text =  item.name


	#shoukd return pretry xml, aet jeader content type
		#return  minidom.parseString(ElementTree.tostring(catalog, 'utf-8') ).toprettyxml(indent="  ")
		#return  minidom.parseString(tostring(catalog, 'utf-8')).toprettyxml(indent=" ")
		return tostring(catalog, 'utf-8')


	else:
		#throw error
		return null


if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)

