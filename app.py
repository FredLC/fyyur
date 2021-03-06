#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
from datetime import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
from config import basedir
from models import db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value

  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.all()
  return render_template('pages/venues.html', venues=venues);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form['search_term']
  response = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

def append_artist_data(show_list, data_list):
  for show in show_list:
    artist = Artist.query.get(show.artist_id)
    data_list.append({
      "artist_image_link": artist.image_link,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "start_time": show.start_time
    })

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), venue.shows))
  past_shows = list(filter(lambda show: show.start_time < datetime.now(), venue.shows))
  upcoming_shows_data = []
  past_shows_data = []

  append_artist_data(upcoming_shows, upcoming_shows_data)
  append_artist_data(past_shows, past_shows_data)  

  return render_template('pages/show_venue.html', venue=venue, upcoming_shows_data=upcoming_shows_data, past_shows_data=past_shows_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website_link = request.form['website_link']
    seeking_talent = request.form.get('seeking_talent')
    seeking_description = request.form['seeking_description']

    if seeking_talent == 'y':
      seeking_talent = True
    else:
      seeking_talent = False

    venue = Venue(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link, seeking_talent=seeking_talent, seeking_description=seeking_description)

    db.session.add(venue)
    db.session.commit()
  except ():
    db.session.rollback()
    error = True
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  venue = Venue.query.get(venue_id)
  try:
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    flash('An error occurred. Venue could not be deleted.')
    return jsonify({'success': False})
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Venue was successfully deleted!')
    return jsonify({'success': True})
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form['search_term']
  response = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

def append_venue_data(show_list, data_list):
  for show in show_list:
    venue = Venue.query.get(show.venue_id)
    data_list.append({
      "venue_image_link": venue.image_link,
      "venue_id": venue.id,
      "venue_name": venue.name,
      "start_time": show.start_time
    })

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), artist.shows))
  past_shows = list(filter(lambda show: show.start_time < datetime.now(), artist.shows))
  upcoming_shows_data = []
  past_shows_data = []

  append_venue_data(upcoming_shows, upcoming_shows_data)
  append_venue_data(past_shows, past_shows_data)
  
  return render_template('pages/show_artist.html', artist=artist, upcoming_shows_data=upcoming_shows_data, past_shows_data=past_shows_data)


@app.route('/artists/<artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
  error = False
  artist = Artist.query.get(artist_id)
  try:
    db.session.delete(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    flash('An error occurred. Artist could not be deleted.')
    return jsonify({'success': False})
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Artist was successfully deleted!')
    return jsonify({'success': True})

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist) 
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  artist = Artist.query.get(artist_id)
  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form['genres']
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = request.form.get('seeking_venue')
    artist.seeking_description = request.form['seeking_description']

    if artist.seeking_venue == 'y':
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False

    db.session.commit()
  except ():
    db.session.rollback()
    error = True
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Artist ' + request.form['name'] + ' was successfully edited!')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  venue = Venue.query.get(venue_id)
  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.genres = request.form['genres']
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website_link = request.form['website_link']
    venue.seeking_talent = request.form.get('seeking_talent')
    venue.seeking_description = request.form['seeking_description']

    if venue.seeking_talent == 'y':
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False

    db.session.commit()
  except ():
    db.session.rollback()
    error = True
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website_link = request.form['website_link']
    seeking_venue = request.form.get('seeking_venue')
    seeking_description = request.form['seeking_description']

    if seeking_venue == 'y':
      seeking_venue = True
    else:
      seeking_venue = False

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)

    db.session.add(artist)
    db.session.commit()
  except ():
    db.session.rollback()
    error = True
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.filter(Show.start_time > datetime.now()).order_by('start_time')
  showData = []

  for show in shows:
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)
    showData.append({
      "artist_image_link": artist.image_link,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "venue_id": venue.id,
      "venue_name": venue.name,
      "start_time": show.start_time
    })
  return render_template('pages/shows.html', shows=showData)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)

    db.session.add(show)
    db.session.commit()
  except ():
    db.session.rollback()
    error = True
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Show was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
