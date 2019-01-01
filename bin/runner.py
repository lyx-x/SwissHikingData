import argparse
import logging
from swisshikingdata.updaters.schweizmobil import SchweizMobilUpdater


def main():
  logger = logging.getLogger(__name__)
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--source', action='store', dest='source',
                      default='SchweizMobil', choices=['SchweizMobil'],
                      type=str, help='Content provider')
  parser.add_argument("--update-list", action="store_true",
                      help="Update track list")
  parser.add_argument("--update-track", action="store_true",
                      help="Update one or more tracks")
  args = parser.parse_args()
  if args.source == 'SchweizMobil':
    logger.info('Creating SchweizMobilUpdater.')
    updater = SchweizMobilUpdater()
  else:
    raise NotImplementedError('{} is not supported yet.'.format(args.source))
  
  if args.update_list:
    logger.info('Updating {} track list.'.format(args.source))
    updater.updateTrackList()
  if args.update_track:
    logger.info('Updating {} track.'.format(args.source))
    updater.updateTrack()


if __name__ == '__main__':
  main()
