# DarkSilk Sentinel

An all-powerful toolset for DarkSilk.

Sentinel is an autonomous agent for persisting, processing and automating DarkSilk governance objects and tasks.

Sentinel is implemented as a Python application that binds to a local version darksilkd instance on each DarkSilk Stormnode.

This guide covers installing Sentinel onto an existing Stormnode in Ubuntu 14.04 / 16.04.

## Installation

### 1. Install Prerequisites

Make sure Python version 2.7.x or above is installed:

    python --version

Update system packages and ensure virtualenv is installed:

    $ sudo apt-get update
    $ sudo apt-get -y install python-virtualenv

Make sure the local DarkSilk daemon running

    $ darksilk-cli getinfo | grep version

### 2. Install Sentinel

Clone the Sentinel repo and install Python dependencies.

    $ git clone https://github.com/silknetwork/darksilk-sentinel.git && cd darksilk-sentinel
    $ virtualenv ./venv
    $ ./venv/bin/pip install -r requirements.txt

### 3. Set up Cron

Set up a crontab entry to call Sentinel regularly, recommended every 2 minutes, by first opening a crontab editor.

    $ crontab -e

In the crontab editor, add the lines below, replacing '/home/YOURUSERNAME/sentinel' to the path where you cloned sentinel to:

    */2 * * * * cd /home/YOURUSERNAME/sentinel && ./venv/bin/python scripts/crontab.py >/dev/null 2>&1

### 4. Test the Configuration

Test the config by runnings all tests from the sentinel folder you cloned into

    $ ./venv/bin/py.test ./test

With all tests passing and crontab setup, Sentinel will stay in sync with darksilkd and the installation is complete

## Configuration

An alternative (non-default) path to the `darksilk.conf` file can be specified in `sentinel.conf`:

    darksilk_conf=/path/to/darksilk.conf

## Troubleshooting

To view debug output, set the `SENTINEL_DEBUG` environment variable to anything non-zero, then run the script manually:

    $ SENTINEL_DEBUG=1 ./venv/bin/python scripts/crontab.py

## Contributing

Please follow the [DarkSilk guidelines for contributing](https://github.com/silknetwork/darksilk-core/blob/master/CONTRIBUTING.md).

Specifically:

* [Contributor Workflow](https://github.com/silknetwork/darksilk-core/blob/master/CONTRIBUTING.md#contributor-workflow)

    To contribute a patch, the workflow is as follows:

    * Fork repository
    * Create topic branch
    * Commit patches

    In general commits should be atomic and diffs should be easy to read. For this reason do not mix any formatting fixes or code moves with actual code changes.

    Commit messages should be verbose by default, consisting of a short subject line (50 chars max), a blank line and detailed explanatory text as separate paragraph(s); unless the title alone is self-explanatory (like "Corrected typo in main.cpp") then a single title line is sufficient. Commit messages should be helpful to people reading your code in the future, so explain the reasoning for your decisions. Further explanation [here](http://chris.beams.io/posts/git-commit/).

### License

Released under the MIT license, under the same terms as DarkSilk Core itself. See [LICENSE](LICENSE) for more info.
