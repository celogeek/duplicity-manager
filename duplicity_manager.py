import sys, os, os.path
from yaml import load

def main():
    config_filename = os.getenv("HOME") + "/.duplicity_manager.conf"

    if (not os.path.exists(config_filename)):
        print("Missing config: " + config_filename)
        sys.exit(1)

    config = load(file(config_filename))
    print(config)

if __name__ == '__main__':
    main()