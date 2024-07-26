from mimetypes import init
from flask import redirect, request
from informatics_classroom.azure_func import init_blob_service_client
from informatics_classroom.imageupload import image_bp


@image_bp.route("/figures")
def view_photos():
    container_client=init_blob_service_client()
    blob_items = container_client.list_blobs() # list all the blobs in the container
    img_html = "<div style='display: flex; justify-content: space-between; flex-wrap: wrap;'>"
    for blob in blob_items:
        blob_client = container_client.get_blob_client(blob=blob.name) # get blob client to interact with the blob and get blob url
        img_html += "<img src='{}' width='auto' height='200' style='margin: 0.5em 0;'/>".format(blob_client.url) # get the blob url and append it to the html 
    img_html += "</div>"

    # return the html with the images
    return """
    <head>
    <!-- CSS only -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/">BIDS Class Figure Upload</a>
            </div>
        </nav>
        <div class="container">
            <div class="card" style="margin: 1em 0; padding: 1em 0 0 0; align-items: center;">
                <h3>Upload new File</h3>
                <div class="form-group">
                    <form method="post" action="/upload-figures" 
                        enctype="multipart/form-data">
                        <div style="display: flex;">
                            <input type="file" accept=".png, .jpeg, .jpg, .gif" name="figures" multiple class="form-control" style="margin-right: 1em;">
                            <input type="submit" class="btn btn-primary">
                        </div>
                    </form>
                </div> 
                <h4>class_module_filenum naming convention (ie 250-782_1_01)</h4>
            </div>
        
    """ + img_html + "</div></body>"

#flask endpoint to upload a photo
@image_bp.route("/upload-figures", methods=["POST"])
def upload_photos():
    filenames = ""
    container_client=init_blob_service_client()
    for file in request.files.getlist("figures"):
        try:
            container_client.upload_blob(file.filename, file) # upload the file to the container using the filename as the blob name
            filenames += file.filename + "<br /> "
        except Exception as e:
            print(e)
            print("Ignoring duplicate filenames") # ignore duplicate filenames  
        print(filenames)    
    return redirect('/figures')     
