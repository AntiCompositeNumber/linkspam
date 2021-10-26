# linkspam

# This project is no longer maintained and has been disabled.

Generates reports of domain usage in external links across all Wikimedia wikis. Written in Python by AntiCompositeNumber. This tool runs on Wikimedia Toolforge at https://tools.wmflabs.org/linkspam/.

## Configuration
Configuration for this tool is stored in two places. Configuration relating to the webserver is stored in config.json in the same directory as the code. Currently, the only config variable accepted is `"linkspam_data_dir"` which defines where the data directory is.

The other configuration file is `linkspam_config.json` and it is stored in the data directory. It holds the status of each report, if the report is manually run or automatic, and the preloaded edit summaries in the edit links for that report. 

## Deployment
This is written based on Toolforge and uwsgi

1. Clone this repository to the tool's home folder
2. Create `~/www/python/` and symlink or copy the src directory there.
3. Follow the instructions on [wikitech](https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool#Step_2:_Create_a_basic_Flask_WSGI_webservice) to create a venv and install the dependencies from requirements.txt.
4. Remove `.default` from `linkspam_config.json` and `config.json`. Edit as necessary. 
4. Unfortunately, kubernetes can't see the SGE grid engine and isn't a good replacement for one-off jobs yet, so this tool has to be run from a grid webservice. The built-in gridengine uwsgi-python webservice is python 2, so we have to use uwsgi-plain. Grab the uwsgi.ini from [here](https://phabricator.wikimedia.org/T104374#1911373), replace `jshint` with the tool name, and save that to the home directory.
6. Start the webservice with `webservice --backend=gridengine uwsgi-plain start`.

*These instructions are probably not complete, and are subject to change as I improve the operation of the tool.*

## linkspam\_config.json

| Field | Description |
| --- | --- |
| title | User-facing title of the report. Must be the domain that was scanned to generate the report. Should match the name of the report file and the key in linkspam\_config.json. Required.
| frequency | `"manual"` or human-readable text describing how often the report is updated. Required.
| last\_update | ISO-format UTC date time string of when the most recent report was started. If the report is not run, this field is an empty string. Required.
| status | `"new"`, `"automatic"`, `"disabled"`. TODO: #17. Required.
| description | User-facing description of the report. Should contain why the report exists and what should be done with the links. Required for automatic reports, optional for manual reports.
| summary | Contains the preloaded edit summaries used in the edit links. This is an object with the wiki's language code as the key and the edit summary as the value. English is used as the default. If no edit summaries are specified, the object is empty. 
