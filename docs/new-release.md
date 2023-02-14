# Steps for releasing a new version of telliot-feeds

1. Make sure the latest changes in `telliot-core` are released to PyPI. Follow the steps [here](https://tellor-io.github.io/telliot-core/contributing/#new-release-processchecklist) to release a new version of `telliot-core`.
2. Update the `telliot-core` dependency version in `setup.cfg` to the latest version.
3. The steps for releasing a new version of `telliot-feeds` are very similar to the steps for `telliot-core` releases, so follow the steps in the link above, after you've completed step 2.
4. Update the `telliot-feeds` version in the `Dockerfile` to the latest version. For example, if the latest version is `0.1.0`, then the line in the `Dockerfile` should be `RUN pip install telliot-feeds==0.1.0`.
5. Now, release a new image to Docker Hub. Here are the commands to do so once in the home directory of the repo:
    - login to docker hub: `docker login --username=tellorofficial` (asks for password)
    - build image: `docker build -t tellorofficial/telliot:latest .`
    - setup image builder: `docker buildx create --name mybuilder`
    - use image builder: `docker buildx use mybuilder`
    - build image for multiple platforms: `docker buildx build --platform linux/arm64,linux/amd64 -t tellorofficial/telliot:latest --push .`
    - get image id: `docker images`
    - tag image: `docker tag {img_id} tellorofficial/telliot:latest` (replace {img_id} with the image id)
    - push image: `docker push tellorofficial/telliot:latest`
6. Test the new image using the steps in the docker getting started section of the docs [here](https://tellor-io.github.io/telliot-feeds/getting-started/#optional-docker-setup).
