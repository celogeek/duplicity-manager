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
    process(config, *sys.argv)


def process(config, program, action=None, src=None, dest=None):
    if (action == None):
        for k in [
            "list                        - list all possibile backups",
            "backup [SRC]                - backup the SRC",
            "backup-script [SRC]         - display the backup script",
            "backup-all [server]         - backup everything",
            "restore [SRC] [DEST]        - restore the src",
            "restore-script [SRC] [DEST] - restore the src",
            "restore-force [SRC] [DEST]  - restore with force the src"
        ]:
            print sys.argv[0] + " " + k
        sys.exit(0)
    elif (action == "list"):
        print("Actions:")
        for k in config.get("Actions", {}).keys():
            print("  * " + program + " backup " + k)
    elif (action == "backup"):
        script_name = generate(config, src)
        os.system(script_name)
    elif (action == "backup-script"):
        script_name = generate(config, src)
        os.system("cat \"" + script_name+"\"")
        os.remove(script_name)
    elif(action == "backup-all"):
        for k in config.get("Actions", {}).keys():
            if config["Actions"][k]["server"] == src:
                process(config, program, "backup", k)
    elif(action == "restore"):
        script_name = generate_restore(config, src, dest)
        os.system(script_name)
    elif(action == "restore-script"):
        script_name = generate_restore(config, src, dest)
        os.system("cat \"" + script_name+"\"")
        os.remove(script_name)
    elif(action == "restore-force"):
        script_name = generate_restore(config, src, dest, force=True)
        os.system(script_name)

def generate(config, action):
    if (action == None):
        print("Missing action")
        sys.exit(1)

    globalParams = config.get("Global", [])
    actionParams = config.get("Actions", {}).get(action)
    if (actionParams == None):
        print("Action \"" + action + "\" doesn't exists !")
        sys.exit(1)
    serverParams = config.get("Servers", {}).get(actionParams.get("server", ""), {})

    def get_all(key, defaults=None):
        return globalParams.get(key, defaults) + serverParams.get(key, defaults) + actionParams.get(key, defaults)

    content = ["#!/usr/bin/env bash", "set -ex"]
    # export envs
    content.extend(["export " + k for k in get_all("envs", [])])
    # go to base path of action
    content.append("cd \""+actionParams.get("base", os.getenv("HOME"))+"\"")
    # pre commands if any
    content.extend([k for k in actionParams.get("pre_commands", [])])
    # setup minimum limit
    content.append("ulimit -n 1024")
    # create duplicity commands
    content.append(" \\\n    ".join(
            itertools.chain(
                ["duplicity"],
                ["--" + k for k in  get_all("options", [])],
                ["\"" + actionParams.get("from", "") + "\""],
                ["\"" + serverParams.get("base", "") + actionParams.get("to", "") + "\""]
            )
        )
    )
    # pre commands if any
    content.extend([k for k in actionParams.get("post_commands", [])])
    # clean old backup
    content.append(" \\\n    ".join(
            itertools.chain(
                ["duplicity"],
                ["remove-all-but-n-full"],
                [str(actionParams.get("keep", "3"))],
                ["--force"],
                ["\"" + serverParams.get("base", "") + actionParams.get("to", "") + "\""]
            )
        )
    )
    # cleanup script
    content.append("rm $0")

    script = tempfile.NamedTemporaryFile(delete=False)
    script.write("\n".join(map(lambda x: x.encode("utf-8"), content)))
    script.write("\n")
    script.close()

    os.chmod(script.name, 0700)
    return script.name

def generate_restore(config, action, dest, force=False):
    if (action == None):
        print("Missing action")
        sys.exit(1)

    if (dest == None):
        print("Missing destination")
        sys.exit(1)

    globalParams = config.get("Global", [])
    actionParams = config.get("Actions", {}).get(action)
    if (actionParams == None):
        print("Action \"" + action + "\" doesn't exists !")
        sys.exit(1)
    serverParams = config.get("Servers", {}).get(actionParams.get("server", ""), {})

    def get_all(key, defaults=None):
        return globalParams.get(key, defaults) + serverParams.get(key, defaults) + actionParams.get(key, defaults)

    content = ["#!/usr/bin/env bash", "set -ex"]
    # export envs
    content.extend(["export " + k for k in get_all("envs", [])])
    # setup minimum limit
    content.append("ulimit -n 1024")
    # create duplicity commands
    content.append("duplicity \\")
    content.append("    --verbosity=info \\")
    content.append("    --num-retries=3 \\")
    if force:
        content.append("    --force \\")
    content.append("    \"" + serverParams.get("base", "") + actionParams.get("to", "") + "\" \\")
    content.append("    \"" + dest + "\"")
    # cleanup script
    content.append("rm $0")

    script = tempfile.NamedTemporaryFile(delete=False)
    script.write("\n".join(map(lambda x: x.encode("utf-8"), content)))
    script.write("\n")
    script.close()

    os.chmod(script.name, 0700)
    return script.name

if __name__ == '__main__':
    main()
