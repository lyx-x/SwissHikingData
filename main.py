"""Entry point for Cloud Functions."""
import logging

from swisshikingdata.updaters.schweizmobil import SchweizMobilUpdater


def updater(request):
  """HTTP Cloud Function.
  Args:
    request (flask.Request): The request object.
    <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
  Returns:
    The response text, or any set of values that can be turned into a
    Response object using `make_response`
    <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
  """
  request_json = request.get_json(silent=True)
  request_args = request.args

  if request_json and 'name' in request_json:
    # process argument
    source = 'SchweizMobil'
    update_list = False
    update_track = False
    if 'source' in request_json:
      source = request_json['source']
    if 'update_list' in request_json:
      update_list = request_json['update_list']
    if 'update_track' in request_json:
      update_track = request_json['update_track']
    
    # start update
    if source == 'SchweizMobil':
      updater = SchweizMobilUpdater()
    else:
      return '{} is not supported yet.'.format(source)
    
    if update_list:
      logging.info('Updating {} track list.'.format(source))
      updater.updateTrackList()
    if update_track:
      logging.info('Updating {} track.'.format(source))
      updater.updateTrack()
  else:
    return 'Nothing to be performed with json {}'.format(request_json)

  return 'Update successful.'
