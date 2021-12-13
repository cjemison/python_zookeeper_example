#!/usr/bin/env python

import logging
import sys

from lib.election import ZooKeeperRegistry, ZooKeeperContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
fmt_str = '[%(asctime)s] %(filename)s %(levelname)s @ line %(lineno)d: %(message)s'
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def run():
    with ZooKeeperContext() as context:
        logger.info("Connected to ZooKeeper")
        with ZooKeeperRegistry(context) as registry:
            while True:
                registry.register_node()
                logger.debug("Registered - Leader: {} Instance Id: {}".format(registry.get_leader(),
                                                                             registry.get_id()))
                if registry.is_leader():
                    logger.info("I am the leader")


if __name__ == "__main__":
    run()
