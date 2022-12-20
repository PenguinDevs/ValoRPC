
# ValoRPC

Discord rich presence for Valorant.

Displays a fancy status under your Discord profile through Discord's rich presence feature about your Valorant game/status, through a combination of screen reading with [Google's optical character recognition](https://github.com/tesseract-ocr/tesseract) and Valorant's internal API. Don't worry, this won't touch the Valorant process's memory at all :)

## NOTE

As this program heavily relies on its screen reading ability, it has not been yet tested on any resolutions other than 1920x1080, 16:9 for Valorant windowed fullscreen/fullscreen. This means that this program cannot guarantee that it will function with screen resolutions of other than this tested size.

## Features

- Standard, swiftplay, replication, and deathmatch gamemodes are supported
- Escalation, spike rush, snowball gamemode rpc are not fully supported yet. Only a basic rpc will be displayed.

## Screenshots

![Standard](https://i.imgur.com/xvllLWJ.png)
![Deathmatch](https://i.imgur.com/nOzcMHF.png)
![Deathmatch](https://i.imgur.com/3i1XQqh.png)

## Installation



## Acknowledgements

 - [Colinhartigan's Python Valclient](https://github.com/colinhartigan/valclient.py)
 - [Techchrism's Valorant API docs](https://github.com/techchrism/valorant-api-docs)
 - [Floxay's Riot Auth](https://github.com/floxay/python-riot-auth)
 - [Google's Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
 - [Buliasz's GUI for Tesseract OCR training](https://github.com/buliasz/tesstrain-windows-gui)