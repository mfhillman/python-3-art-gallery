import datetime
import os
from google.cloud import ndb
from flask import Flask, render_template, make_response, request, redirect
from models import Painting, Gallery, GalleryList, SchoolInfo, ResumeInfo

app = Flask(__name__)
client = ndb.Client()

HOME_PAINTING = 'fatgoldenchickenfinalforwebFB'

@app.route("/")
def root():
  year = datetime.datetime.now().year
  with client.context():
    header_painting = Painting.get_by_id(HOME_PAINTING)

  return render_template("home.html", year=year, painting=header_painting)

@app.route("/mission")
def mission():
  year = datetime.datetime.now().year
  return render_template("mission.html", year=year)

@app.route("/resume")
def resume():

  with client.context(): 
    resume = ResumeInfo.retrieve()
    
  year = datetime.datetime.now().year
  return render_template("resume.html", year=year, 
                         exhibitions=resume.exhibitions, 
                         honors=resume.honors, 
                         schools=resume.schools)
    
@app.route("/<pool_name>")
def galleries(pool_name):
  with client.context():  
    year = datetime.datetime.now().year
    gallery_list = GalleryList.get_by_id(pool_name);
    if gallery_list:
        gallery_keys = gallery_list.gallery_keys
        galleries = ndb.get_multi(gallery_keys)
        front_painting_keys = map(lambda g: ndb.Key(Painting,
                                                    g.front_painting_id),
                                  galleries)
        front_paintings = ndb.get_multi(front_painting_keys)
        pairs = zip(galleries, front_paintings)
  
  if gallery_list:
    return render_template("galleries.html",
                           year=year,
                           gallery_front_pairs=pairs,
                           pool_name=pool_name,
                           pool_title="Galleries")
  else:
    return "Bad path.", 404


@app.route("/<pool_name>/<gallery_id>")
def gallery(pool_name, gallery_id):
  with client.context():  
    year = datetime.datetime.now().year
    if gallery_id.isdigit():
      gallery = Gallery.get_by_id(gallery_id)
    else:
      gallery = None
    if gallery:
      paintings = ndb.get_multi(gallery.painting_keys)
 
  if gallery:
    return render_template("gallery.html",
                           year=year,
                           gallery=gallery,
                           paintings=paintings,
                           pool_name=pool_name)
  else:
    return "Gallery not found.", 404
  
@app.route("/<pool_name>/<gallery_id>/<painting_id>")
def painting(pool_name, gallery_id, painting_id):
  with client.context(): 
    year = datetime.datetime.now().year
    if len(painting_id) > 0:
      painting = Painting.get_by_id(painting_id)
    else:
      painting = None
    if gallery_id.isdigit():
      gallery = Gallery.get_by_id(gallery_id)
    else:
      gallery = None
      
  if painting and gallery:
    return render_template("painting.html",
                           year=year, painting=painting,
                           gallery_url_fragment=gallery_id,
                           pool_name=pool_name)
  else:
    return "Gallery or painting not found.", 404  
      
@app.route("/image.aspx")
def legacy_image():
  with client.context(): 
    gallery_id = request.args.get('GID')
    if gallery_id.isdigit():
      gallery = Gallery.get_by_id(gallery_id)
    else:
      gallery = None
    painting_param = request.args.get('PID')
    if painting_param.isdigit():
      old_painting_id = int(request.args.get('PID'))
      painting = Painting.get_from_old_id(old_painting_id)
      painting_key = painting.key.id()
    else:
      painting = None
  if painting and gallery:
    return redirect('/galleries/' + gallery_id + '/' + painting_key)
  else:
    return "Gallery or painting not found.", 404  

@app.route("/admin")
def adminroot():
  
  with client.context():
    resume = ResumeInfo.retrieve()
    exhibitions_text = '\n'.join(resume.exhibitions)
    honors_text = '\n'.join(resume.honors)
    school_strs = []
    for school in resume.schools:
      school_strs.append(school.to_admin_str())
    schools_text = '\n'.join(school_strs)

  return render_template("admin.html", 
                         exhibitions_text=exhibitions_text, 
                         honors_text=honors_text, 
                         schools_text=schools_text)

@app.route("/admin/confirm")
def admin_confirm():
    return ('Confirmed!<br>')

@app.route("/admin/update_exhibitions", methods=['POST'])
def admin_update_exhibitions():
    
  with client.context():
    new_exhibitions = request.form['content']
    exhibition_list = new_exhibitions.split('\n')
    resume = ResumeInfo.retrieve()
    resume.exhibitions = exhibition_list
    resume.save()
    
  return redirect('/admin/confirm')

@app.route("/admin/update_honors", methods=['POST'])
def admin_update_honors():
  with client.context():
    new_honors = request.form['content']
    honors_list = new_honors.split('\n')
    
    resume = ResumeInfo.retrieve()
    resume.honors = honors_list
    resume.save()
    
  return redirect('/admin/confirm')
    
@app.route("/admin/update_schools", methods=['POST'])
def admin_update_schools():
  with client.context():
    new_schools = request.form['content']
    schools_list = new_schools.split('\n')
    schools = []
    
    for school_text in schools_list:
      info = SchoolInfo()
      info.from_admin_str(school_text)
      schools.append(info)
      
    resume = ResumeInfo.retrieve()
    resume.schools = schools
    resume.save()
    
  return redirect('/admin/confirm')

  def get_orphan_galleries(listed_keys):
    orphans = []
    all_galleries = Gallery.query().fetch()
    
    for gallery in all_galleries:
      if gallery.key not in listed_keys:
        orphans.append(gallery)
        
    return orphans
  
@app.route("/admin/edit_galleries")
def admin_edit_galleries():
  with client.context():
    galleryList = GalleryList.get_by_id('galleries');
    if galleryList != None:
      gallery_keys = galleryList.gallery_keys
      galleries = ndb.get_multi(gallery_keys)
    else:
      gallery_keys = []
      galleries = []
      
    archiveList = GalleryList.get_by_id('archives');
    if archiveList != None:
      archive_keys = archiveList.gallery_keys
      archives = ndb.get_multi(archive_keys)
    else:
      archive_keys = []
      archives = []
    
    gallery_strs = []
    for gallery in galleries:
      gallery_strs.append(','.join([gallery.url_fragment(), gallery.name]))
    main_galleries_text = '\n'.join(gallery_strs)

    archive_strs = []
    for gallery in archives:
      archive_strs.append(','.join([gallery.url_fragment(), gallery.name]))
    archive_galleries_text = '\n'.join(archive_strs)
    
    orphan_strs = []
    orphans = Gallery.get_orphan_galleries(gallery_keys + archive_keys)
    for gallery in orphans:
      orphan_strs.append(','.join([gallery.url_fragment(), gallery.name]))
    orphan_galleries_text = '\n'.join(orphan_strs)
    
  return render_template("admin_edit_galleries.html", 
                         main_galleries_text=main_galleries_text,
                         archive_galleries_text=archive_galleries_text,
                         orphans_galleries_text=orphan_galleries_text)

@app.route("/admin/update_galleries/<pool_name>", methods=['POST'])
def admin_update_galleries(pool_name):
  with client.context():
    # Content is one gallery per line: id, name.
    # When saving gallery lists, name is ignored
    new_galleries_content = request.form['content']
    new_galleries_list = new_galleries_content.split('\n')
    
    gallery_list = GalleryList(id=pool_name)
    gallery_list.gallery_keys = []
    for gal in new_galleries_list:
      gal_id = gal.split(',')[0]
      gallery_list.gallery_keys.append(ndb.Key(Gallery, gal_id))

    gallery_list.save()
    
  return redirect('/admin/confirm')

@app.route("/admin/nav_to_gallery", methods=['POST'])
def admin_nav_to_gallery():
  with client.context():
    gallery_id_content = request.form['content']
    return redirect('/admin/edit_gallery/' + gallery_id_content)

@app.route("/admin/edit_gallery/<gallery_id>")
def admin_edit_gallery(gallery_id):    
  with client.context():
    if gallery_id.isdigit():
      gallery = Gallery.get_by_id(gallery_id)
      paintings = ndb.get_multi(gallery.painting_keys)
    else:
      gallery_id = Gallery.get_fresh_id()
      gallery = Gallery(id=gallery_id)      
      paintings = []
      
    painting_strs = []
    for painting in paintings:
      painting_strs.append(','.join([painting.title,str(painting.height),
                                     str(painting.width),painting.key.id()]))
    painting_text = '\n'.join(painting_strs)

    template_values = {
        'gallery': gallery,
        'paintings_text': painting_text
    }
    
  return render_template("admin_edit_gallery.html", 
                         gallery=gallery,
                         paintings_text=painting_text)

@app.route("/admin/update_gallery", methods=['POST'])
def admin_update_gallery():
  with client.context():  
    gallery = Gallery(id=request.form['gallery_id'],
                      name=request.form['gallery_name'],
                      front_painting_id=request.form['front_painting_id'])
        
    # Note that columns are expected to be title, height, width, id
    paintings_text = request.form['paintings_text']
    painting_strs = paintings_text.split('\n')
 
    paintings = []
    for painting_str in painting_strs:
      row = painting_str.split(',')
      painting = Painting(
          id=row[3].strip(),
          title=row[0].strip(), 
          height=int(row[1]) if row[1] else 0,
          width=int(row[2]) if row[2] else 0)  
      paintings.append(painting)
      gallery.painting_keys.append(painting.key)
      
    response_txt = 'painting count ' + str(len(paintings)) + '<BR>'
    
    # Write back only changed paintings
    changed_paintings = []
    old_paintings = ndb.get_multi(gallery.painting_keys)
    
    for i in range(0, len(old_paintings)):
      old = old_paintings[i]
      new = paintings[i]
      if old == None or (old.title != new.title or old.height != new.height or old.width != new.width):
        changed_paintings.append(new)
          
    if len(changed_paintings) > 0:
      response_txt += str(changed_paintings)
      ndb.put_multi(changed_paintings)
    else:
      response_txt += '<BR> no changed paintings!<BR>'
      
    response_txt += '<BR>' + str(gallery) + '<BR>'
    
    gallery.save()
    
  return response_txt

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)