import playground
from .protocol import PassthroughClientFactory, PassthroughServerFactory

passthroughConnector = playground.Connector(protocolStack=(
    PassthroughClientFactory(),
    PassthroughServerFactory()))
playground.setConnector("passthrough", passthroughConnector)
playground.setConnector("mystack", passthroughConnector)