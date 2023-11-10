# for noobs to download and run the program
# Install git and python3 first

# Only on mac for now
# Install homebrew if not installed
if ! command -v brew &> /dev/null
then
    echo "Installing homebrew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check if git is installed
if ! command -v git &> /dev/null
then
    echo "Installing git"
    brew install git
    # setup git
    # Prompt user for name and email
    echo "Enter your full name: "
    read name
    git config --global user.name "$name"
    echo "Enter your email: "
    read email
    git config --global user.email "$email"

    # Generate ssh key
    # don't ask user for passphrase or file location
    ssh-keygen -t rsa -b 4096 -C "$email" -f ~/.ssh/id_rsa -q -N ""

fi

# if repo is not cloned, clone it
if [ ! -d "$HOME/budget-manager" ];
then
    cd $HOME
    echo "Cloning repo to $HOME"
    git clone git@github.com:wassimwazzi/budget-manager.git
fi

cd $HOME/budget-manager
git checkout main &> /dev/null
git pull

# Check if python3 is installed and version is 3.11
if ! command -v python3 &> /dev/null || ! python3 --version | grep -q "3.11"
then
    echo "Installing python3"
    brew install python@3.11

    # add python3 to path
    echo "export PATH=/usr/local/opt/python@3.11/bin:$PATH" >> ~/.zshrc
    source ~/.zshrc

fi

brew install python-tk@3.11

if [ ! -d "$HOME/budget-manager/venv" ]
then
    echo "Creating virtual environment"
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing dependencies"
pip3 install -r requirements.txt

# Check if config file exists
if [ ! -f "$HOME/budget-manager/env.prod" ]
then
    echo "Creating env file"
    touch .env.prod
    echo "DB_FILE=db.prod.sqlite3" >> .env.prod
fi

# Run program
python3 main.py --env prod --log_level INFO
