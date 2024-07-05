# Vectorize and Index Images with Azure Search
This repository contains code for a project that vectorizes images, generates descriptive metadata, and indexes them in Azure Search. The goal is to provide an efficient and scalable solution for image search and retrieval using Azure's powerful search capabilities.

## Features
- **Image Vectorization**: Convert images into vector representations for efficient processing and storage.
- **Image description generation**: Generate image description and identify main object within image using GPT4o Custom web skill to improve search accuracy.
- **Azure Search Integration**: Index the vectorized images and vectorized metadata in Azure Search to enable fast and accurate search results.

## Getting Started
1. **Clone the Repository**: `git clone https://github.com/yourusername/vectorize-index-images-azure-search.git`
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Create `credentials.env`**: Rename the `.crendentials.env` file to `credentials.env` and fill in the service details.
4. **Configure Azure Search**: Set up your Azure Search service and update the credentials.env file with your service details.
5. **Configure Azure Function for Custom web skill**: Follow the steps [here](https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code?tabs=node-v4%2Cpython-v2%2Cisolated-process&pivots=programming-language-python) to create a function in Azure using VS Code. The function code is available in [function_app.py](./function_app.py). Read about creating custom skills [Custom skill interface](https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-interface)
6. **Configure Azure BLOB**: Set up your Azure BLOB store and create a container that will store images. Update the credentials.env with details.
7. **Run the Script**: Execute the indexing.py script to vectorize images and index them in Azure Search. Script will do the following

    - Create Datasource
    - Create Skillset
    - Create Index
    - Create Indexer - Indexer is scheduled to run every 10 mins, you can change this setting in the indexer.
    
NOTE: You may face service denial if you are using PAYGO deployment of GPT4o, to avoid this make sure you upload images in batches of 20 per indexer run.

## Requirements

- Python 3.x
- Azure Search Service
- Azure BLOB Store and container with images
- Azure OpenAI with GPT4o & text-embedding-3-large models deployed
- Azure Vision Service (can be same as the Cognitive service below)
- Azure Cognitive Service
- Required Python libraries (listed in `requirements.txt`)

## Usage

1. Place your images in the designated input directory.
2. Run the vectorization and indexing script.
3. Use Azure Search to query and retrieve images based on the generated metadata.

## Contributing

Feel free to submit issues, fork the repository, and send pull requests. Contributions are welcome!

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

This repository aims to provide a comprehensive solution for image search and retrieval using Azure Search. Whether you're building a photo library, an e-commerce site, or any application that requires image search capabilities, this codebase will help you get started quickly and efficiently.
