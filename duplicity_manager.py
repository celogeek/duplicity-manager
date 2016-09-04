import sys, os, os.path
import yaml
import tempfile
import itertools

def main():
    config_filename = os.getenv("HOME") + "/.duplicity_manager.conf"

    if (not os.path.exists(config_filename)):
        print("Missing config: " + config_filename)
        sys.exit(1)

    config = yaml.load(file(config_filename))

    if (len(sys.argv) == 1):
        for k in [
            "list                - list all possibile backups",
            "backup [SRC]        - backup the SRC",
            "backup-script [SRC] - display the backup script"
        ]:
            print sys.argv[0] + " " + k
        sys.exit(0)

    process(config, *sys.argv)


def process(config, program, action, *args):
    if (action == "list"):
        print("Actions:")
        for k in config.get("Actions", {}).keys():
            print("  * " + program + " backup " + k)
    elif (action == "backup"):
        script_name = generate(config, args[0])
        os.system(script_name)
    elif (action == "backup-script"):
        script_name = generate(config, args[0])
        os.system("cat \"" + script_name+"\"")
        os.remove(script_name)

def generate(config, action):
    globalParams = config.get("Global", [])
    actionParams = config.get("Actions", {}).get(action)
    if (actionParams == None):
        print("Action \"" + action + "\" doesn't exists !")
        sys.exit(1)
    serverParams = config.get("Servers", {}).get(actionParams.get("server", ""), {})

    content = ["""#!/usr/bin/env bash"""]
    # export envs
    content.extend([
        "export " + k for k in (globalParams.get("envs", []) + serverParams.get("envs", []) + actionParams.get("envs", []))
    ])
    # go to base path of action
    content.extend(["cd \""+actionParams.get("base", os.getenv("HOME"))+"\""])
    # setup minimum limit
    content.extend(["ulimit -n 1024"])
    # create duplicity commands
    content.append(" \\\n    ".join(
            itertools.chain(
                ["duplicity"],
                ["--" + k for k in  globalParams.get("options", []) + serverParams.get("options", []) + actionParams.get("options", [])],
                ["\"" + actionParams.get("from", "") + "\""],
                ["\"" + serverParams.get("base", "") + actionParams.get("to", "") + "\""]
            )
        )
    )
    content.append("rm $0")

    script = tempfile.NamedTemporaryFile(delete=False)
    script.write("\n".join(content))
    script.write("\n")
    script.close()

    os.chmod(script.name, 0700)
    return script.name

if __name__ == '__main__':
    main()
