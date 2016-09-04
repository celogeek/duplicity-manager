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


def process(config, program, action, *args):
    if (action == "list"):
        print("Actions:")
        for k in config.get("Actions", {}).keys():
            print("  * " + program + " backup " + k)
    elif (action == "backup"):
        script = generate(config, args[0])


def generate(config, action):
    params = config.get("Global", [])
    actionParams = config.get("Actions", {}).get(action)
    if (actionParams == None):
        print("Action \"" + action + "\" doesn't exists !")
        sys.exit(1)
    serverParams = config.get("Servers", {}).get(actionParams.get("proto", ""), {})

    content = ["""#!/usr/bin/env bash"""]
    content.extend(["export " + k for k in serverParams.get("envs", [])])
    content.extend(["cd \""+actionParams.get("base", os.getenv("HOME"))+"\""])
    content.extend(["ulimit -n 1024"])
    content.append(" \\\n    ".join(
            itertools.chain(
                ["duplicity"],
                ["--" + k for k in params + actionParams.get("options", [])],
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
    os.execl(script.name, script.name)

if __name__ == '__main__':
    main()
