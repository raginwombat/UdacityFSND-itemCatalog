from sqlalchemy import Column, ForeignKey, Integer, String, Unicode, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

 
Base = declarative_base()

#Constructor string: User(name= '', email='', picture='')
class User(Base):
  __tablename__ = 'user'

  id = Column(Integer, primary_key=True)
  name = Column(String(250), nullable=False)
  email = Column(String(250), nullable=False)
  picture = Column(String(250))

  @property
  def serialize(self):
      return {
      'name'        :self.name,
      'email'        :self.name,
      'picture'       :self.picture
  }

    
#Constructor string: Catalog(name= '', user_id='')    
class Category(Base):
    __tablename__ = 'category'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False, unique=True)
    user_id=Column(Integer, ForeignKey('user.id'))
    user = relationship(User, cascade="all, delete-orphan", single_parent=True)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id
       }
 


#Constructor string: CatalogItem(name= '', description = '', category = '',  catalog_id =, user_id=, catalog_image_url=)
class CatalogItem(Base):
    __tablename__ = 'CatalogItem'

    name =Column(String(80), nullable = False, unique=True)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    catalog_image_url =  Column(String(512))
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category, cascade="all, delete-orphan", single_parent=True)
    user_id=Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
          'id'                 : self.id,
           'name'              : self.name,
           'description'       : self.description,
           'image file name'   : self.catalog_image_url
       }






engine = create_engine('sqlite:///itemCatalogDB.db')
 

Base.metadata.create_all(engine)
