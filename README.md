⚠️ This project is now archived and any new pull requests or issues will not be reviewed. You are however, welcome to fork this repository.

# ValoRPC

Discord rich presence for Valorant.

Displays a fancy status under your Discord profile through Discord's rich presence feature about your Valorant game/status, through a combination of screen reading with [Google's optical character recognition](https://github.com/tesseract-ocr/tesseract) and Valorant's internal API. Don't worry, this won't touch the Valorant process's memory at all :)

## NOTE

- Please go to Discord settings -> Activity Settings -> Activity Privacy -> Display current activity as a status message. -> Enabled, for any rich presences to be shown under your profile.
- As this program heavily relies on its screen reading ability, it has not been yet tested on any resolutions other than 1920x1080, 16:9 for Valorant windowed fullscreen/fullscreen. This means that this program cannot guarantee that it will function with screen resolutions of other than this tested size.

## Features

- Standard, swiftplay, replication, and deathmatch gamemodes are supported
- Escalation, spike rush, snowball gamemode rpc are not fully supported yet. Only a basic rpc will be displayed.

## Screenshots

![Standard](https://i.imgur.com/xvllLWJ.png)
![Deathmatch](https://i.imgur.com/nOzcMHF.png)
![Deathmatch](https://i.imgur.com/3i1XQqh.png)
![Competitive](https://i.imgur.com/v6CKH5Z.png)
![Idling](https://i.imgur.com/TNmCBfK.png)

## Installation

Download the exe file from the [latest release](https://github.com/PenguinDevs/ValoRPC/releases/latest) and then run the file.

Note that windows will by default block the application from running, responding with a message 'Microsoft Defender SmartScreen prevented an unrecognized app from starting...' This is because the application is unsigned like many other open source executables out there on the internet. This project is therefore open source for not only contributions/forks, but for you to trust the source code of this application-- although the code is indeed arguably quite a mess.

If you trust that my project is free from malware, go ahead and click 'more info' and then 'Run anyways'.

## Acknowledgements

 - [Colinhartigan's Python Valclient](https://github.com/colinhartigan/valclient.py)
 - [Techchrism's Valorant API docs](https://github.com/techchrism/valorant-api-docs)
 - [Floxay's Riot Auth](https://github.com/floxay/python-riot-auth)
 - [Google's Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
 - [Buliasz's GUI for Tesseract OCR training](https://github.com/buliasz/tesstrain-windows-gui)
