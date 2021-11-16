# telliot-feed-examples

## Setup

1. navigate to your home directory:
    ```
    cd ~/
    ```
2. get the code:
    ```
    git clone https://github.com/tellor-io/telliot-feed-examples.git
    ```
3. install python 3.8
    - if using ubuntu 18 or 20:
    ```
    sudo apt-get update
    sudo apt-get install python3.8 python3-pip
    ```
4. create virtual environment:
    ```
    python3 -m venv env
    source env/bin/activate
    ```
5. install dependencies:
    ```
    pip3 install -r requirements-dev.txt
    ```
6. generate default `telliot` configs:
    ```
    telliot config init
    ```
7. generate default AMPL configs:
    ```
    python src/telliot_ampl_feeds/config.py
    ```
8. add your private key to `~/telliot/main.yaml`
9. add your node api key to `~/telliot/endpoints.yaml`
10. add your AMPL api keys to `~/telliot/ampl.yaml`

### Report legacy id 41 on Rinkeby
1. run bash script:
    ```
    source scripts/report_id_41.sh
    ```
2. enter a value (example: 1234.1234)
3. press `[ENTER]` to confirm
