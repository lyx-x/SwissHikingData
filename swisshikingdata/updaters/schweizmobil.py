import geojson
import logging
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request

from ..storage import DatastoreClient
from ..utils.coordinates import CoordinatesConverter


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
      self.logger.warn('The server couldn\'t fulfill the request {}.'.format(url))
      self.logger.warn('Error code: {}'.format(e.code))
      return None
    except urllib.error.URLError as e:
      self.logger.warn('We failed to reach a server.')
      self.logger.warn('Reason: {}'.format(e.reason))
      return None
    else:
      res = response.read()
      raw_tracks = json.loads(res)

      tracks = [
        {
          'id': int(track['number']),
          # All routes have at least one stage
          'stages': max(1, len(track['segment_ids'])),
        } for track in raw_tracks['result']['items']
      ]
      return sorted(tracks, key=lambda track: track['id'])

  def updateTrackList(self):
    self.cached_tracks = self.getTrackList()
    self.logger.info('Fetched {} tracks.'.format(len(self.cached_tracks)))
    # Keep the string readable on Datastore UI
    tracks = json.dumps(self.cached_tracks, ensure_ascii=False)
    self.storage_client.upload('TrackList', 'list', value=tracks)

  def getTrackCoordinates(self, id: int, stage: int, max_retry: int=10):
    base_url = 'https://map.schweizmobil.ch/api/4/query/featuresmultilayers'
    key = '{}.{:02d}'.format(id, stage)
    params = {
      'WanderlandEtappenNational' : key,
      'WanderlandEtappenRegional' : key,
      'WanderlandEtappenLokal' : key,
      'WanderlandEtappenHandicap' : key,
      }

    params = urllib.parse.urlencode(params)
    url = base_url + '?' + params
    req = urllib.request.Request(url)
    try:
      response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
      self.logger.warn('The server couldn\'t fulfill the request {}.'.format(url))
      self.logger.warn('Error code: {}'.format(e.code))
      return key, None
    except urllib.error.URLError as e:
      self.logger.warn('We failed to reach a server.')
      self.logger.warn('Reason: {}'.format(e.reason))
      self.logger.warn(url)
      return key, None
    else:
      # everything is fine
      res = response.read()
      res = geojson.loads(res)['features']
      # if something is wrong with the coordinates, the route/stage doesn't exist
      if len(res) == 0:
        return key, None
      res = res[0]
      self.logger.info('Fetching coordinates is successful.')
      
      # new coordinates
      new_res = geojson.utils.map_tuples(lambda x: CoordinatesConverter.ch1903ToWgs84(x[0], x[1]), res)

      # randomize the position of bbox to make the url work
      for i in range(max_retry):

        if i == 0:
          rand_index = 0
        elif i == max_retry - 1:
          rand_index = -1
        else:
          rand_index = random.randint(0, len(res['geometry']['coordinates'][0]) - 1)
        if res['geometry']['type'] == 'MultiLineString':
          ch1903_mid = res['geometry']['coordinates'][0][rand_index]
        else:
          ch1903_mid = res['geometry']['coordinates'][rand_index]
        ch1903_id = res['id']

        # get track info
        base_url = 'https://map.schweizmobil.ch/api/4/feature/query'
        params = {
          'attributes' : 'yes',
          'restriction' : 8,
          'type' : 'etappen',
          'language': 'en',
          'land' : 'all',
          'category': 'all',
          'simplify': '100',
          'layers': 'WanderlandEtappenNational,WanderlandEtappenRegional,WanderlandEtappenLokal,WanderlandEtappenHandicap',
          'bbox': '{0},{1},{0},{1}'.format(int(ch1903_mid[0]), int(ch1903_mid[1]))
          }

        params = urllib.parse.urlencode(params)
        url = base_url + '?' + params
        req = urllib.request.Request(url)
        try:
          response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
          self.logger.warn('The server couldn\'t fulfill the request {} {}.'.format(ch1903_id, url))
          self.logger.warn('Error code: {}'.format(e.code))
          continue
        except urllib.error.URLError as e:
          self.logger.warn('We failed to reach a server.')
          self.logger.warn('Reason: {}'.format(e.reason))
          continue
        else:
          infos = response.read()
          infos = geojson.loads(infos)['features']
          infos = [x for x in infos if x['id'] == ch1903_id]
          if len(infos) == 0:
            continue
          else:
            # overwrite the old info
            new_res['properties'] = infos[0]['properties']

          if new_res['properties']['e_number'] != key:
            raise AssertionError(
              'e_number for id={}, stage={} is expected to be {}, found {}.'.format(
                id, stage, key, new_res['properties']['e_number']))

          self.logger.info('Fetching track info is successful.')
          return key, new_res
      
      return key, None

  def updateTrackCoordinates(self, id: int, stage: int):
    self.logger.info('Updating track id={}, stage={}.'.format(id, stage))
    key, route = self.getTrackCoordinates(id, stage)

    if route is None:
      self.logger.warn('Updated failed for id={}, stage={}.'.format(id, stage))
      return False
    else:
      # generate description from an up-to-date track info
      info = route['properties']
      description = '{:04d}.{:02d} {} ({} - {})'.format(id, stage, info['title'], info['start'], info['end'])
      
      route = geojson.dumps(route)
      self.storage_client.upload('Track', key, value=route, description=description)
      return True

  def updateTrack(self, timeout=240):
    start_time = time.time()
    # get the list of all tracks
    if self.cached_tracks is None:
      tracks = self.storage_client.get('TrackList', 'list')['value']
      self.cached_tracks = json.loads(tracks)
    # update one track at a time, oculd be multiple stages
    track = self.cached_tracks[self.update_index]
    # record timestamp for future update
    self.update_index = (self.update_index + 1) % len(self.cached_tracks)
    self.storage_client.upload('TrackList', 'update_index', value=self.update_index)

    # some stage are missing, we need to figure out the number by trying
    count_updated = 1
    count_successful = 0
    # we limit the number of max retries
    while count_successful < track['stages'] and count_updated < 64 and time.time() - start_time < timeout:
      if self.updateTrackCoordinates(track['id'], stage=count_updated):
        count_successful += 1
      count_updated += 1
