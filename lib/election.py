import random
import logging
import time
import os

from kazoo.client import KazooClient, KazooState

logger = logging.getLogger(__name__)


def my_listener(state):
    if state == KazooState.LOST:
        # Register somewhere that the session was lost
        logger.error("Zookeeper connection lost.")
        pass
    elif state == KazooState.SUSPENDED:
        # Handle being disconnected from Zookeeper
        logger.error("Zookeeper connection suspend.")
    else:
        # Handle being connected/reconnected to Zookeeper
        logger.info("Zookeeper connection made.")


class ZooKeeperContext(object):

    def __init__(self):
        self.zk = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("Closing Connection.")
        if self.zk:
            self.zk.stop()
        return True

    def connect(self):
        servers = os.environ["ZOOKEEPER_SERVERS"]
        logger.info("ZooKeeper Servers: {}".format(servers))
        self.zk = KazooClient(servers)
        self.zk.add_listener(my_listener)
        self.zk.start()

    def get_client(self) -> KazooClient:
        return self.zk


class ZooKeeperRegistry:

    def __init__(self, context: ZooKeeperContext):
        self.id: int = random.randint(1, 5000)
        self.id_bytes: bytes = self.id.to_bytes(2, 'big')
        self.lock = None
        self.servers_path: str = "/cdc/nodes/servers"
        self.node_path: str = self.servers_path + "/" + str(self.id)
        self.context = context
        self.zk = None

    def __enter__(self):
        # will check zookeeper context.
        self.check_context()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def register_node(self) -> None:
        """
        Adds server node to Apache Zookeeper
        :return None:
        """
        self.check_context()
        zk_node = None
        try:
            zk_node = self.zk.get(self.node_path)
            logger.info("Registered: {}".format(self.node_path))
        except:
            # logger.warning("node not found.")
            pass
        if not zk_node:
            self.lock = self.zk.create(self.node_path,
                                       value=self.id_bytes,
                                       makepath=True,
                                       ephemeral=True)
            # wait block
            time.sleep(0.5)

    def get_leader(self) -> int:
        """
        Gets current leader in server node.
        :return: int
        """
        self.check_context()
        leader_server_node = 0
        data, node = self.zk.get_children(self.servers_path,
                                          include_data=True)
        if data:
            logger.debug("Server IDs: {}".format(data))
            l = []
            for server_id in data:
                logger.debug("Server: {}".format(server_id))
                zk_node = self.zk.get(self.servers_path + "/" + server_id)
                if zk_node:
                    l.append((server_id, zk_node[1].czxid,))
            l.sort(key=lambda y: y[1])
            logger.debug("Servers: {}".format(l))
            if len(l) >= 2:
                # at least two nodes need to be running before election declared.
                # return the server id
                leader_server_node = l[0][0]
            else:
                logger.error("Not enough servers for quorum: {}".format(len(l)))
        return int(leader_server_node)

    def is_leader(self) -> bool:
        """
        Returns bool if current node is the leader.
        :param zk:
        :return bool:
        """
        self.check_context()
        leader_id = self.get_leader()
        logger.debug("Current leader: {}".format(leader_id))
        return leader_id == self.id

    def get_id(self) -> int:
        return self.id

    def check_context(self):
        if self.context.get_client().client_state != "CONNECTED":
            logger.error("Not Connected to Zookeeper: {}".format(self.zk.client_state))
            raise Exception("Not Connected to Zookeeper.")
            # set ZooKeeper Client to class
        self.zk = self.context.get_client()
