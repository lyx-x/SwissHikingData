import logging

from google.cloud import datastore


class DatastoreClient(object):
  def __init__(self, namespace: str):
    self.namespace = namespace
    # Instantiates a client
    self.client = datastore.Client()
    self.logger = logging.getLogger(__name__)

  def upload(self, kind: str, name: str, **kwargs):
    """Upload an entity to Google Cloud Datastore.

    Upload an entity to Datastore with the correct kind, key and labels.

    Args:
      kind: A string used by Datastore to group entities.
      name: A string forming the key for the new entity.
      kwargs: Labels of the entity.

    Returns:
      N/A

    Raises:
      N/A
    """
    # The Cloud Datastore key for the new entity
    entity_key = self.client.key(kind, name, namespace=self.namespace)

    # Prepares the new entity
    entity = datastore.Entity(key=entity_key, exclude_from_indexes=['value', 'description'])
    entity.update(kwargs)

    # Saves the entity
    self.client.put(entity)

    self.logger.info('Saved {} {} {}.'.format(self.namespace, kind, name))

  def get(self, kind: str, name: str):
    """Get an entity from Google Cloud Datastore.

    Get an entity from Datastore using the key formed by kind and name.

    Args:
      kind: A string used by Datastore to group entities.
      name: A string forming the key for the new entity.

    Returns:
      The requested entity if it exists.

    Raises:
      N/A
    """
    # The Cloud Datastore key for the new entity
    entity_key = self.client.key(kind, name, namespace=self.namespace)
    return self.client.get(entity_key)
