# Python Development

There are two Python applications created, the *main program* and the *updater program*.
Both files are located in the `backend` folder. The API used to connect both ends are found in `api` with their 
respective names.

The file `support/vars.py` contains the *default* and *runtime* values used for the program. Adding a new option
or setting option is as simple as adding a new key to the dictionary starting with `DEFAULTS*`.
- Do note that adding or deleting keys will also need equivalent changes on the front end, which uses Zustand as
the context library

## JSON Files

Program configurations are stored as *JSON files*. In order to read and write to these files efficiently,
a class named `Reader` is used to perform these operations, found at `backend/core/json_reader.py`.

There are four types of categories used with the configuration files:
1. Microsoft Graph
2. Operating Company Mapping: Can also be known as Organization Mapping, used for mapping domains to an organization/opco
3. Settings: General settings of the program
4. Excel Mapping: The mapping of the CSV/Excel headers to the internal names used in the program

By default if these do not exist, it will be *re-created upon launch*. It is also stored in-memory, which will *re-create*
the file if it is missing.
The default values for these configuration files can be found at `support/vars.py`. If a key is added or removed from
the default mapping, it will *automatically be updated upon relaunch*.