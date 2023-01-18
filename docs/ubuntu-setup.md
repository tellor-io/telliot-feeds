How to Install Telliot on Ubuntu.

This is a step by step guide for how to install Telliot. Telliot is an open source client for interacting with the Tellor oracle. The methods outlined here will work on a fresh installation of Ubuntu 20.04 LTS Amazon t2.micro AWS instance. Individual commands will differ with other environments (particularly for installing python 3.9), but the process is relatively similar for setting up Telliot on Mac (use homebrew) or on Windows (WSL).  

Prerequisites:
A computer, virtual machine, or windows subsystem for linux running ubuntu version 20.04. (other versions are probably fine, but 20.04 was used for testing this guide)
An ethereum address that has TRB tokens and native tokens (gas) for the network on which you want to report oracle data.
Node endpoints for Ethereum Mainnet, and other network(s) on which you want to report. You can use your own node, or use a provider like Infura. https://www.alchemy.com/list-of/rpc-node-providers-on-ethereum 


The Guide

This is a beginner-friendly guide. Familiarity with the command line will be helpful, but otherwise no assumptions are made about your technical skills. We will go over in detail the commands necessary to:
Install python 3.9 (Python 3.9 is required for running Telliot)
Create a python virtual machine
Install Telliot
Configure RPC endpoints 
Verify Installation
Install python3.9
Check your python version with the command [ python3 -V ]. This will output your current version of python3. For example: [Python 3.8.10]. Make a note of your current version for step 4.
Download the python repository for ubuntu: [sudo add-apt-repository ppa:deadsnakes/ppa]
Install Python 3.9: [sudo apt install python3.9]
Python 3.9 is now installed, but we need to make sure that it’s the default python3 version on our machine. 
Configure versions. 
Enter the following command, but replace “/usr/bin/python3.8” with your current version if different. (for example use “/usr/bin/python3.10” if your system currently running 3.10 from step 1)

[sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1]

	Set python3.9 as option 2:

[sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2]

Finally, check your available versions;

[sudo update-alternatives --config python3]

You should see a list of python versions and a prompt to choose your version. Press enter to confirm python3.9. 
Finally, triple check your python version with [python3 -V] 

Important: If you’ve completed the steps and your python3 version is anything other than 3.9.xx, you will not be able to use telliot. Please make sure you are running python 3.9 before you continue.

Create a Python Virtual Machine

A python virtual machine is like a container where telliot will be installed on your machine. Working in a virtual environment is not mandatory, but it helps in avoiding dependency conflicts if you plan on using the computer/VM for running other python software. 

Install venv: [sudo apt-get install python3.9-venv]
Create a python virtual environment directory called tenv: [python3 -m venv tenv]
Activate the virtual environment: [source tenv/bin/activate]

Install Telliot

Install Telliot with the command [pip install telliot-feeds]

Configure a mainnet RPC Endpoint
Create the Telliot configuration files: [telliot config init] 
You now have a telliot folder in your home directory.
Note: At the time of writing this command results in “IndexError.” This can be ignored.
Edit endpoints.yaml. Since this guide works for an AWS ubuntu machine, we will use a cli based text editor called nano. Open endpoints.yaml with:
[nano telliot/endpoints.yaml] 
Your screen should look something like this:

Use the arrow keys to navigate around the document and edit the mainnet node endpoint URLs to match your own. Telliot requires that you configure at least the Ethereum mainnet endpoint for its functionality. (You can add endpoints for other networks like this also.)
If you make a mistake, exit the document with [ctrl+x]  [n] (don’t save changes) and press enter to confirm. Then open the document and start editing again.
When you’re done editing and you want to save your changes, use [ctrl+x]  [y] and press enter to confirm.
2) 

Verify if Telliot was installed correctly: [telliot –help]
If Telliot was installed properly, the log should look like this:

If this command results in a python error / traceback, Here are some things to try:
Quadruple check your version on python 
Check that your python virtual machine is activated and that telliot is installed there
Check your endpoint URLs in endpoints.yaml. 
Feel free to reach out in our discord if you need help! 
Thanks for reading! Now that you have Telliot installed, you’re ready to become a Tellor reporter. Head over to using Telliot (link).
