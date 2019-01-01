import geojson
import logging
import json
import urllib.error
import urllib.parse
import urllib.request

from swisshikingdata.storage import DatastoreClient
from swisshikingdata.utils.coordinates import CoordinatesConverter


class SchweizMobilUpdater(object):
  def __init__(self):
    self.storage_client = DatastoreClient('SchweizMobil')
    # Won't work with async calls
    self.cached_tracks = None
    self.update_index = self.storage_client.get('TrackList', 'update_index')
    if self.update_index is None:
      self.storage_client.upload('TrackList', 'update_index', value=0)
      self.update_index = 0
    else:
      self.update_index = self.update_index['value']
    self.logger = logging.getLogger(__name__)

  def getTrackList(self):
    base_url = 'https://www.schweizmobil.ch/en/json.cfm'
    params = {
      'funktion' : 'get',
      'skip' : 0,
      'limit' : 1024,  # arbitrary, should be larger than the total number of routes
      'filter[land_code]': 'wander',
      'collection': 'route',
      }
    params = urllib.parse.urlencode(params)
    url = base_url + '?' + params
    req = urllib.request.Request(url)
    try:
      response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
      self.logger.warn('The server couldn\'t fulfill the request.')
      self.logger.warn('Error code: ', e.code)
      return None
    except urllib.error.URLError as e:
      self.logger.warn('We failed to reach a server.')
      self.logger.warn('Reason: ', e.reason)
      return None
    else:
      res = response.read()
      raw_tracks = json.loads(res)

      tracks = [
        {
          'id': track['number'],
          'title': track['title_admin'],
          'stages': len(track['segment_ids']),
        } for track in raw_tracks['result']['items']
      ]
      return sorted(tracks, key=lambda track: track['id'])

  def updateTrackList(self):
    self.cached_tracks = self.getTrackList()
    self.logger.info('Fetched {} tracks.'.format(len(self.cached_tracks)))
    # Keep the string readable on Datastore UI
    tracks = json.dumps(self.cached_tracks, ensure_ascii=False)
    self.storage_client.upload('TrackList', 'list', value=tracks)

  def getTrackCoordinates(self, id: str, **kwargs):
    base_url = 'https://map.schweizmobil.ch/api/4/query/featuresmultilayers'
    if 'stage' in kwargs:
      id = '{}.{}'.format(id, kwargs.get('stage'))
      params = {
        'WanderlandEtappenNational' : id,
        'WanderlandEtappenRegional' : id,
        'WanderlandEtappenLokal' : id,
        'WanderlandEtappenHandicap' : id,
        }
    else:
      params = {
        'WanderlandRoutenNational' : id,
        'WanderlandRoutenRegional' : id,
        'WanderlandRoutenLokal' : id,
        'WanderlandRoutenHandicap' : id,
        }

    params = urllib.parse.urlencode(params)
    url = base_url + '?' + params
    req = urllib.request.Request(url)
    try:
      response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
      self.logger.warn('The server couldn\'t fulfill the request.')
      self.logger.warn('Error code: ', e.code)
      return id, None
    except urllib.error.URLError as e:
      self.logger.warn('We failed to reach a server.')
      self.logger.warn('Reason: ', e.reason)
      return id, None
    else:
      # everything is fine
      res = response.read()
      self.logger.info('Fetching is successful.')
      res = geojson.loads(res)
      res = geojson.utils.map_tuples(lambda x: CoordinatesConverter.ch1903ToWgs84(x[0], x[1]), res)

      return id, res

  def updateTrackCoordinates(self, id: str, **kwargs):
    self.logger.info('Updating track {} with arguments [{}].'.format(id, kwargs))
    id, route = self.getTrackCoordinates(id, **kwargs)
    route = geojson.dumps(route)
    self.storage_client.upload('Track', id, value=route)

  def updateTrack(self):
    # Get the list of all tracks
    if self.cached_tracks is None:
      tracks = self.storage_client.get('TrackList', 'list')['value']
      self.cached_tracks = json.loads(tracks)
    # Update one at a time
    track = self.cached_tracks[self.update_index]
    if track['stages'] > 0:
      for i in range(track['stages']):
        self.updateTrackCoordinates(track['id'], stage='{:02d}'.format(i + 1))
    else:
      self.updateTrackCoordinates(track['id'])
    # Record timestamp for future update
    self.update_index += 1
    self.storage_client.upload('TrackList', 'update_index', value=self.update_index) 
