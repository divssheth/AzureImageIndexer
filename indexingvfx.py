import os
import requests
import json
from dotenv import load_dotenv

def create_azure_ai_search_index(index_name):
    headers = {'Content-Type': 'application/json','api-key': os.environ['AZURE_SEARCH_KEY']}
    params = {'api-version': os.environ['AZURE_SEARCH_API_VERSION']}
    index_payload = {
        "name": index_name,
        "vectorSearch": {
            "algorithms": [
                {
                    "name": "myalgo",
                    "kind": "hnsw"
                },
                {
                    "name": "myimagealgo",
                    "kind": "hnsw",
                    "hnswParameters":{
                        "efConstruction": 400,
                        "efSearch": 500,
                        "m": 4,
                        "metric": "cosine"
                    }
                }
            ],
            "compressions": [
                {
                    "name": "my-scalar-quantization",
                    "kind": "scalarQuantization",
                    "rerankWithOriginalVectors": "true",
                    "defaultOversampling": 10.0,
                    "scalarQuantizationParameters": {
                        "quantizedDataType": "int8"
                    }
                }
            ],
            "vectorizers": [
                {
                    "name": "openai",
                    "kind": "azureOpenAI",
                    "azureOpenAIParameters":
                    {
                        "resourceUri" : os.environ['AZURE_OPENAI_ENDPOINT'],
                        "apiKey" : os.environ['AZURE_OPENAI_API_KEY'],
                        "deploymentId" : os.environ['EMBEDDING_DEPLOYMENT_NAME'],
                        "modelName": os.environ['EMBEDDING_MODEL_NAME']
                    }
                },
                {
                    "name": "my-ai-services-vision-vectorizer",
                    "kind": "aiServicesVision",
                    "aiServicesVisionParameters": {
                        "resourceUri" : os.environ['AZURE_VISION_ENDPOINT'],
                        "apiKey" : os.environ['AZURE_VISION_API_KEY'],
                        "authIdentity" : None,
                        "modelVersion": os.environ['AZURE_VISION_API_VERSION'],
                    },
                }
            ],
            "profiles": [
                {
                    "name": "myprofile",
                    "algorithm": "myalgo",
                    "vectorizer":"openai"
                },
                {
                    "name": "myImageprofile",
                    "algorithm": "myalgo",
                    "vectorizer":"my-ai-services-vision-vectorizer",
                    "compression": "my-scalar-quantization"
                }
            ]
        },
        "semantic": {
            "configurations": [
                {
                    "name": "my-semantic-config",
                    "prioritizedFields": {
                        "prioritizedContentFields": [
                            {
                                "fieldName": "imgdesc"
                            },
                            {
                                "fieldName": "imgentity"
                            }
                        ],
                        "prioritizedKeywordsFields": []
                    }
                }
            ]
        },
        "fields": [
            {"name": "id", "type": "Edm.String", "key": "true", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "true","facetable": "false"},
            {"name": "name", "type": "Edm.String", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "true", "facetable": "false"},
            {"name": "imgloc", "type": "Edm.String", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"},
            {"name": "imgdesc", "type": "Edm.String", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "false", "facetable": "false"},
            {"name": "imgentity", "type": "Edm.String", "searchable": "true", "retrievable": "true", "sortable": "false", "filterable": "true", "facetable": "false"},
            {
                "name": "imgdescVector",
                "type": "Collection(Edm.Single)",
                "dimensions": 3072,   # IMPORTANT: Make sure these dimmensions match your embedding model name
                "vectorSearchProfile": "myprofile",
                "searchable": "true",
                "retrievable": "true",
                "filterable": "false",
                "sortable": "false",
                "facetable": "false"
            },
            {
                "name": "imageVector",
                "type": "Collection(Edm.Single)",
                "dimensions": 1024,   # IMPORTANT: Make sure these dimmensions match your embedding model name
                "vectorSearchProfile": "myImageprofile",
                "searchable": "true",
                "retrievable": "true",
                "filterable": "false",
                "sortable": "false",
                "facetable": "false"
            }
        ]
    }

    r = requests.put(os.environ['AZURE_SEARCH_ENDPOINT'] + "/indexes/" + index_name,
                    data=json.dumps(index_payload), headers=headers, params=params)
    print(r.text)
    print(r.status_code)
    print(r.ok) 

def create_skillset(index_name, skillset_name):
    # Create a skillset
    headers = {'Content-Type': 'application/json','api-key': os.environ['AZURE_SEARCH_KEY']}
    params = {'api-version': os.environ['AZURE_SEARCH_API_VERSION']}
    skillset_payload = {
        "name": skillset_name,
        "description": "e2e Skillset for RAG - Files",
        "skills":[
            {
                "@odata.type": "#Microsoft.Skills.Vision.VectorizeSkill",
                "context": "/document",
                "modelVersion": "2023-04-15", 
                "inputs": [
                    {
                        "name": "url",
                        "source": "/document/metadata_storage_path"
                    },
                    {
                        "name": "queryString",
                        "source": "/document/metadata_storage_sas_token"
                    }
                ],
                "outputs": [
                    {
                        "name": "vector"
                    }
                ]
            },
            {
                "@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
                "description": "A custom skill that describes the image sent to OpenAI",
                "uri": os.environ['CUSTOM_SKILL_URL'],
                "batchSize": 4,
                "context": "/document",
                "httpHeaders": {
                    "x-functions-key": os.environ['CUSTOM_SKILL_KEY']
                },
                "inputs": [
                    {
                        "name": "url",
                        "source": "/document/metadata_storage_path"
                    },
                    {
                        "name": "queryString",
                        "source": "/document/metadata_storage_sas_token"
                    }
                ],
                "outputs": [
                {
                    "name": "description",
                    "targetName": "imgdesc"
                },
                {
                    "name": "entity",
                    "targetName": "imgentity"
                }
                ]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
                "description": "Azure OpenAI Embedding Skill",
                "context": "/document",
                "resourceUri": os.environ['AZURE_OPENAI_ENDPOINT'],
                "apiKey": os.environ['AZURE_OPENAI_API_KEY'],
                "deploymentId": os.environ['EMBEDDING_DEPLOYMENT_NAME'],
                "modelName": os.environ['EMBEDDING_MODEL_NAME'],
                "inputs": [
                    {
                        "name": "text",
                        "source": "/document/metadata_storage_path"
                    }
                ],
                "outputs": [
                    {
                        "name": "embedding",
                        "targetName": "imgdescVector"
                    }
                ]
            }
        ],
        "knowledgeStore": {
            "storageConnectionString": os.environ['KNOWLEDGE_STORE_CONN'],
            "projections": [
                {
                    "tables": [
                        { "tableName": "imagesTable", "generatedKeyName": "Documentid", "source": "/document"}
                    ],
                    "objects": []
                }
            ]
        },
        "cognitiveServices": {
            "@odata.type": "#Microsoft.Azure.Search.CognitiveServicesByKey",
            "description": os.environ['COG_SERVICES_NAME'],
            "key": os.environ['COG_SERVICES_KEY']
        }
    }

    r = requests.put(os.environ['AZURE_SEARCH_ENDPOINT'] + "/skillsets/" + skillset_name,
                    data=json.dumps(skillset_payload), headers=headers, params=params)
    print(f"Skillset call returned with \n Text: {r.text} \n Code: {r.status_code}")

def create_indexer(indexer_name, skillset_name, index_name, datasource_name):
    headers = {'Content-Type': 'application/json','api-key': os.environ['AZURE_SEARCH_KEY']}
    params = {'api-version': os.environ['AZURE_SEARCH_API_VERSION']}
    indexer_payload = {
        "name": indexer_name,
        "dataSourceName": datasource_name,
        "targetIndexName": index_name,
        "skillsetName": skillset_name,
        "schedule" : { "interval" : "PT10M"}, # How often do you want to check for new content in the data source
        "fieldMappings": [
            {
            "sourceFieldName" : "metadata_storage_name",
            "targetFieldName" : "name"
            },
            {
            "sourceFieldName" : "metadata_storage_path",
            "targetFieldName" : "imgloc"
            },
            {
            "sourceFieldName" : "metadata_storage_name",
            "targetFieldName" : "id",
            "mappingFunction": { "name": "base64Encode" }
            }
        ],
        "outputFieldMappings":[
            {
            "sourceFieldName": "/document/vector/*",
            "targetFieldName": "imageVector"
            },
            {
            "sourceFieldName": "/document/imgdesc",
            "targetFieldName": "imgdesc"
            },
            {
            "sourceFieldName": "/document/imgentity",
            "targetFieldName": "imgentity"
            },
            {
            "sourceFieldName": "/document/imgdescVector/*",
            "targetFieldName": "imgdescVector"
            }
        ],
        "parameters" : {
            "maxFailedItems": -1,
            "maxFailedItemsPerBatch": -1,
        }
    }
    r = requests.put(os.environ['AZURE_SEARCH_ENDPOINT'] + "/indexers/" + indexer_name,
                    data=json.dumps(indexer_payload), headers=headers, params=params)
    print(f"Indexer call returned with \n Text: {r.text} \n Code: {r.status_code}")

def create_datasource(datasource_name):
    headers = {'Content-Type': 'application/json','api-key': os.environ['AZURE_SEARCH_KEY']}
    params = {'api-version': os.environ['AZURE_SEARCH_API_VERSION']}
    datasource_payload = {
        "name": datasource_name,
        "description": "Rendered images provided by VFX team",
        "type": "azureblob",
        "credentials": {
            "connectionString": os.environ['BLOB_CONNECTION_STRING']
        },
        "dataDeletionDetectionPolicy" : {
            "@odata.type" :"#Microsoft.Azure.Search.NativeBlobSoftDeleteDeletionDetectionPolicy" # this makes sure that if the item is deleted from the source, it will be deleted from the index
        },
        "container": {
            "name": os.environ['BLOB_CONTAINER_NAME'],
        }
    }
    r = requests.put(os.environ['AZURE_SEARCH_ENDPOINT'] + "/datasources/" + datasource_name,
                    data=json.dumps(datasource_payload), headers=headers, params=params)
    print(f"Datasource call returned with \n Text: {r.text} \n Code: {r.status_code}")

def query_search(index_name, question):
    headers = {'Content-Type': 'application/json','api-key': os.environ['AZURE_SEARCH_KEY']}
    params = {'api-version': os.environ['AZURE_SEARCH_API_VERSION']}
    # Define the text query
    QUESTION = question
    k=5

    search_payload = {
        "search": QUESTION, # Text query
        "select": "id, name, imgloc",
        "queryType": "semantic",
        "vectorQueries": [{"text": QUESTION, "fields": "imageVector", "kind": "text", "k": k}, {"text": QUESTION, "fields": "imgdescVector", "kind": "text", "k": k}], # Vector query
        "semanticConfiguration": "my-semantic-config",
        "captions": "extractive",
        "answers": "extractive",
        "count":"true",
        "top": k
    }

    r = requests.post(os.environ['AZURE_SEARCH_ENDPOINT'] + "/indexes/" + index_name + "/docs/search",
                     data=json.dumps(search_payload), headers=headers, params=params)

    search_results = r.json()
    print(f"Search results: \n{search_results}")

if __name__ == '__main__':
    index_name = "vfx-index"
    skillset_name = "vfx-skillset"
    datasource_name = "vfx-datasource"
    indexer_name = "vfx-indexer"
    create_index = True
    load_dotenv("credentials.env")
    if create_index:
        print("Creating Datasource")
        create_datasource(datasource_name)
        print("Creating Index")
        create_azure_ai_search_index(index_name)
        print("Creating Skillset")
        create_skillset(index_name, skillset_name)
        print("Creating Indexer")
        create_indexer(indexer_name, skillset_name, index_name, datasource_name)

    # question = "Get me trees or trunks from the database"
    # question = "I'm looking to create a Car, can you find the relevant images for me?"
    # query_search(index_name, question)