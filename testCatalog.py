from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CatalogItem
engine = create_engine('sqlite:///itemCatalogDB.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


#catalog 1


user1 = User(name="Jaque Pepin", email="test@tester.com", 
 	picture="")

session.add(user1)
session.commit()

user1Pull= session.query(User).filter_by(email='test@tester.com').one()
category1 = Category(name= "Headphones", user_id=user1Pull.id)   
category2 = Category(name= "sunglasses", user_id=user1Pull.id)  
session.add(category1)
session.add(category2)
session.commit()

catalog1Pull = session.query(Category).filter_by(name='Headphones').one()
item1 =  CatalogItem(name= "Item 1", description = "This is the first item", category_id  = category1.id,  user_id=user1Pull.id)
session.add(item1)
item2 =  CatalogItem(name= "Item 2", description = "This is the second item", category_id  = category1.id,   user_id=user1Pull.id)
session.add(item2)
item3 =  CatalogItem(name= "Item 3", description = "This is the third item", category_id  = category2.id,   user_id=user1Pull.id)
session.add(item3)
item4 =  CatalogItem(name= "Item 4", description = "This is the fourth item", category_id  = category2.id,   user_id=user1Pull.id)
session.add(item4)
session.commit()

