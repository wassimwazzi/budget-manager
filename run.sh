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

    # clone repo
    echo "Cloning repo to $HOME"
    git clone git@github.com:wassimwazzi/budget-manager.git
    cd budget-manager
fi

pwd
ls

# Check if python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Installing python3"
    brew install python@3.11

    # create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    echo "Installing dependencies"
    pip3 install -r requirements.txt
fi

# Run program
python3 main.py --env prod --log_level INFO