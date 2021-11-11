# install python 3.8
sudo apt-get update
sudo apt-get install python3.8 python3-pip

# setup virtual environment
python3.8 -m venv env
source env/bin/activate

# install dependencies
pip install -r requirements-dev.txt

# generate default Telliot configs
python get_default_configs.py

# generate default AMPL configs
python src/telliot_ampl_feeds/config.py

echo ""
echo "TODO:"
echo "Add private key to ~/telliot/main.yaml"
echo "Add node url to ~/telliot/endpoints.yaml"
echo "Add api keys to ~/telliot/ampl.yaml"