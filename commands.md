docker ps                    # find the container ID
docker stop <container-id>   # stop it

to run doc 
docker run -d -p 8000:8000 bg-remover

start doc
docker build -t bg-remover .
