rsyncrun
============================
Rsync your code to server and run. [![Build Status](https://img.shields.io/travis/luiti/rsyncrun/master.svg?style=flat)](https://travis-ci.org/luiti/rsyncrun)

Deploy changing dependent projects faster, such as batch processing
tasks, e.g. submit a Python script or a Hive script to YARN.


How does `rsyncrun` deploy projects ?
--------------------------------------------------------
1. Change your code in your serveral related projects.
2. `rsync` these projects to server, it's really fast, except for full sync in the first time.
3. Detect some changed codes, and re-install related projects.
4. Launch your project and debug ...

Benefits
----------------------------
1. Every command is print to console detailly, not a black box, RAW SHELL SCRIPT rocks!
2. To run this script, only Python and its standard library is needed, no need to install thirty-party libraries.
3. Create a `virtualenv` environment automatically.

Usage
----------------------------
```bash
pip install rsyncrun
rsyncrun
```


TODO
----------------------------
1. compact with canceled, e.g. catch event, keep the log

I want a feature X ? ... please [create an issue](https://github.com/luiti/rsyncrun/issues), or [fork it](https://github.com/luiti/rsyncrun/).
