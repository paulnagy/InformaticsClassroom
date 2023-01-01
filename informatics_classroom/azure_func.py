from azure.cosmos import CosmosClient, PartitionKey
from azure.storage.blob import BlobServiceClient
from informatics_classroom.config import Keys


def init_cosmos(container_name,db_name):
    client=CosmosClient(Keys.url,Keys.cosmos_key,consistency_level="Session")
    database=client.get_database_client(db_name)
    container = database.create_container_if_not_exists(
        id=container_name, 
        partition_key=PartitionKey(path="/id"),
        offer_throughput=400
    )
    return container

def init_blob_service_client():
    blob_service_client = BlobServiceClient.from_connection_string(conn_str=Keys.blob_connect_str) # create a blob service client to interact with the storage account
    try:
        container_client = blob_service_client.get_container_client(container=Keys.blob_container_name) # get container client to interact with the container in which images will be stored
        container_client.get_container_properties() # get properties of the container to force exception to be thrown if container does not exist
    except Exception as e:
        print(e)
        print("Creating container...")
        container_client = blob_service_client.create_container(Keys.blob_container_name) # create a container in the storage account if it does not exist
    return container_client