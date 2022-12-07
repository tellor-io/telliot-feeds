FROM python:3.9

RUN pip install telliot-feeds

CMD echo "telliot image built"

# # push new image to docker hub
# - login to docker hub: `docker login --username=tellorofficial` (asks for password)
# - build image: `docker build -t tellorofficial/telliot:latest`
# - setup image builder: `docker buildx create --name mybuilder`
# - use image builder: `docker buildx use mybuilder`
# - build image for multiple platforms: `docker buildx build --platform linux/amd64,linux/arm64 -t tellorofficial/telliot:latest --push .`
# - get image id: `docker images`
# - tag image: `docker tag {img_id} tellorofficial/telliot:latest` (replace {img_id} with the image id)
# - push image: `docker push tellorofficial/telliot:latest`
