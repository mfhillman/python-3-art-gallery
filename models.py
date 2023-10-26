import string

from google.cloud import ndb

client = ndb.Client()

# Example painting URL: https://storage.googleapis.com/timmurley_art/images/1billionserved.jpg
# Example thumb URL: https://storage.googleapis.com/timmurley_art/thumbs/1billionserved_thumb.jpg

_PAINTING_BASE_URL = 'https://storage.googleapis.com/'
_PAINTING_BUCKET = 'timmurley_art'
_PAINTING_URL = _PAINTING_BASE_URL + _PAINTING_BUCKET + '/images/{0}.jpg'
_THUMB_URL = _PAINTING_BASE_URL + _PAINTING_BUCKET + '/thumbs/{0}_thumb.jpg'

# Example painting URL: https://storage.googleapis.com/timmurley_art/images/1billionserved.jpg

_RESUME_KEY_LOCATION = 'resume'

class Painting(ndb.Model):
  # file name is stored in id
  title = ndb.StringProperty()
  width = ndb.IntegerProperty(indexed=False)
  height = ndb.IntegerProperty(indexed=False)
  old_id = ndb.IntegerProperty(indexed=True)
	
  def full_size_image(self) :
    return _PAINTING_URL.format(self.key.id())
	
  def thumbnail_image(self) :
    return _THUMB_URL.format(self.key.id())
    
  def url_fragment(self) :
    return self.key.id()
    
  @classmethod
  def get_from_old_id(cls, old_id):
    query = cls.query(cls.old_id == old_id)
    results = query.fetch(1)
    if len(results) > 0:
      return results[0]
    else:
      return None
		
class Gallery(ndb.Model):
  name = ndb.StringProperty()
  front_painting_id = ndb.StringProperty()
  painting_keys = ndb.KeyProperty(repeated=True)
  
  def url_fragment(self) :
    return self.key.id()
    
  def save(self) :
    history_entry = GalleryHistory(gallery=self)
    self.put()
    history_entry.put()
 
  @classmethod
  def get_orphan_galleries(cls, listed_keys):
    orphans = []
    all_galleries = Gallery.query().fetch()
    
    for gallery in all_galleries:
      if gallery.key not in listed_keys:
        orphans.append(gallery)
        
    return orphans

  @classmethod
  def get_fresh_id(cls):
    all_galleries = Gallery.query().fetch()
    sorted_galleries = sorted(all_galleries, key=lambda gal: int(gal.key.id()))
        
    if len(sorted_galleries) > 0:
      return int(sorted_galleries[len(sorted_galleries)-1].key.id()) + 1;
    else:
      return 1
    
class GalleryHistory(ndb.Model):
  gallery = ndb.StructuredProperty(Gallery)
  date = ndb.DateTimeProperty(auto_now_add=True)
    
class GalleryList(ndb.Model):
  gallery_keys = ndb.KeyProperty(repeated=True)
  
  def save(self) :
    history_entry = GalleryListHistory(gallery_list=self, pool_name=self.key.id())
    self.put()
    history_entry.put()

class GalleryListHistory(ndb.Model):
  pool_name = ndb.StringProperty()
  gallery_list = ndb.StructuredProperty(GalleryList)
  date = ndb.DateTimeProperty(auto_now_add=True)
  
class SchoolInfo(ndb.Model):
  school = ndb.StringProperty()
  school_detail = ndb.StringProperty()
  
  def to_admin_str(self):
    if self.school_detail:
      return self.school + '|' + self.school_detail
    else:
      return self.school
      
  def from_admin_str(self, str):
    strs = str.split('|')
    self.school = strs[0]
    if len(strs) > 1:
      self.school_detail = strs[1]
    else:
      self.school_detail = ''

class ResumeInfo(ndb.Model):
  exhibitions = ndb.StringProperty(repeated=True)
  honors = ndb.StringProperty(repeated=True)
  schools = ndb.StructuredProperty(SchoolInfo, repeated=True)
  
  @classmethod
  def retrieve(cls) :
    return cls.get_or_insert(_RESUME_KEY_LOCATION)
    
  def save(self) :
    history_entry = ResumeHistory(resume=self)
    self.put()
    history_entry.put()
  
class ResumeHistory(ndb.Model):
  resume = ndb.StructuredProperty(ResumeInfo)
  date = ndb.DateTimeProperty(auto_now_add=True)
