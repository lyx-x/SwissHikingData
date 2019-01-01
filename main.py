"""Entry point for Cloud Functions."""
import logging

from swisshikingdata.updaters.schweizmobil import SchweizMobilUpdater


def update_pubsub(data, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata.
    """
    import base64
    import json

    if 'attributes' in data:
      # process argument
      request_json = data['attributes']
      source = 'SchweizMobil'
      update_list = False
      update_track = False
      if 'source' in request_json:
        source = request_json['source']
      if 'update_list' in request_json and request_json['update_list'] == 'true':
        update_list = True
      if 'update_track' in request_json and request_json['update_track'] == 'true':
        update_track = True
      update(source, update_list, update_track)
    else:
      logging.info('Nothing to be performed with message {}'.format(data))


def update(source, update_list, update_track):
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
