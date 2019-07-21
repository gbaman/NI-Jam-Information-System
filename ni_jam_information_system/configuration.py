import configparser

config_file_location = "configs/config.ini"


class Modules:
    module_core = ["module_core", ]
    module_attendees = ["module_core", "module_attendees"]
    module_public_schedule = ["module_core", "module_public_schedule", "module_workshops"]
    module_booking = ["module_core", "module_booking", "module_public_schedule", "module_workshops"]
    module_workshops = ["module_core", "module_workshops"]
    module_volunteer_attendance = ["module_core", "module_volunteer_attendance"]
    module_volunteer_signup = ["module_core", "module_volunteer_signup", "module_workshops"]
    module_api = ["module_core", "module_api", "module_volunteer_attendance"]
    module_equipment = ["module_core", "module_equipment", "module_workshops"]
    module_badge = ["module_core", "module_badge", "module_workshops"]
    module_finance = ["module_core", "module_finance"]
    module_email = ["module_core", "module_email"]


def _get_config_file():
    config = configparser.ConfigParser()
    config.read(config_file_location)
    return config


def verify_config_item(section, config_key):
    config = _get_config_file()
    if section in config:
        if config_key in config[section]:
            return config[section][config_key]
    else:
        return None


def verify_config_item_bool(section, config_key):
    config_item = verify_config_item(section, config_key)
    if config_item:
        if type(config_item) == str:
            if config_item.lower() == "true":
                return True
            elif config_item.lower() == "false":
                return False
    return None


def verify_modules_enabled() -> Modules:
    modules_object = Modules()
    modules = [x for x in dir(modules_object) if not x.startswith('__')]
    to_return = Modules()
    for module in modules:
        for module_name in getattr(Modules, module):
            if not verify_config_item_bool("modules", module_name):
                setattr(to_return, module, False)
                break
            setattr(to_return, module, True)

    return to_return


def output_modules_enabled():
    config = _get_config_file()
    print("--------------------")
    print("Modules enabled")
    print("--------------------")
    if config["modules"] and len(config["modules"]) > 0:
        for key in config["modules"].keys():
            print("- {}".format(key))
    else:
        print("No modules enabled!")
    print("--------------------")
    print("")