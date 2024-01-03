# `mining-prometheus-collector`

Collects mining status data from detected miners for prometheus ingestion. Each scrape translates to a call to the
miner's API, so the data received will be live (not cached).

Some of the supported miners don't have great (or any) API documentation so in those cases I may have had to guess what
specific parts are to "standardize" them between miners.

**NOTE** This was designed to be run inside a Minerstat MSOS instance, so IPs/ports, etc, are hard-coded. I might be
changing this to be more independent in the near future (1/2024).


### Supported miners

- `t-rex`

I will add to these as I support new miners in my mining rig. Dual mining is not supported (yet).


### Installation

Bootstrap it onto a new box with:

```shell
curl -L https://raw.githubusercontent.com/gdhaworth/mining-prometheus-collector/main/scripts/bootstrap.sh | bash -
```

The bootstrap and installation scripts assume you have the packages installed and environment of a Minerstat MSOS
installation. That means:

- `sudo` does not require a password
- `git` is installed
- `systemd` is present

The bootstrap/installation will set up [pyenv](https://github.com/pyenv/pyenv) for itself and selfishly install
packages without a `virtualenv` (because this is on a MSOS box that shouldn't care). If I extend this project
beyond Minerstat I will add ways to make this more portable (can turn parts off, etc).

**NOTE** This is an update from code I had written 3 years ago in a private repo which originally supported both Linux
and Windows. I have only been using Linux since updating and starting this repository, but it shouldn't take much effort
to get it running on Windows.


### Implementation notes

- `Metric`s are created on each `collect()` because I don't want to show stale data; I'm assuming it's being scraped
often enough that it will catch metrics that show up from time to time (like if the miner API shows a value only
sometimes). This is a side effect from not having complete documentation on the APIs from some miners so I don't know
if they will consistently return the same set of data each time.
