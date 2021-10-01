# TappingBot

The TappingBot projects features a full-stack architecture currently capable of playing the Candy Crush Saga videogame using a real robotic arm tapping on a mobile screen.

- **Authors**: Giovambattista Ianni, Mario Avolio.
- **Licensed** under the Apache-2.0 License.

[<img src="new.png" width="25">Download Latest Release</img>](https://github.com/DeMaCS-UNICAL/TappingBot/releases/tag/v0.1-alpha)

<div>Icons made by <a href="https://www.freepik.com" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>

# Important notes on cloning and pulling updates

Don't forget to 
    
    git submodule update --init --recursive
    
after your first cloning in order to pull submodules. To keep submodules up to date:
    
    git pull --recurse-submodules

# Required hardware

1.  **PH**: an Android mobile phone. This is the device where the game will be played on;
2.  **TP**: an assembled Tapsterbot. This robotic arm can programmatically perform actions on a given touch screen (taps, swipes, etc.);
3.  **LI**: a Linux host. The Linux host will host the Tapsterbot server commanding the robot, will collect screenshots from PH and run the AI module.

# Installation and set up

You will need to make several applications up and running:

## ScreenshotServer

The ScreenshotServer is an Android application which opens an HTTP server on PH. You can HTTP GET screenshots on demand from the Screenshotserver this way:

    curl http://<PHone-IP>:5432/?name=requestimage --output screen.png

You can find a pre-built apk for the ScreenshotServer in the ScreenshotServer folder. Just push it to PH, install it and start the server. Take note of <PHone-IP>.

## Tapsterbot

The robotic arm needs to be 3D-printed and assembled as described in several tutorials online like: https://www.instructables.com/Tapsterbot-20-Servo-Arm-Assembly/.
The software on the embedded Arduino board must be the Standard Firmata script: from the Arduino IDE find and upload the "Firmata" script:

    File -> Open -> Examples > Firmata > StandardFirmata

Calibration and testing of the robot can be done by following the installation guide of the Tappy server: https://github.com/DeMaCS-UNICAL/tappy-original

## Tappy server

You find a fork of the tappy project under the tappy-original submodule. Follow installation instructions there. The Tappy server is expected to run on the **LI** subsystem on port 80. The `config.js` file under the `tappy-original` folder allows to customize the listening port and other physical parameters of the robot.
Recall you can use `nvm` for managing the required node.js version, (currently 10.11.0).
If your current user has no access rights to serial ports, recall to use `sudo npm start` when starting the tappy server instead of a plain `npm start`.

## Python client

This python client for the tappy server is located under the `tapsterbot-original/clients/python` folder. You will possibly need to tweak IP and listening port of the Tappy server and other stuff in the `config.py` file. There is also a python API, which is currently incompatible with the rest of tappingbot, but you can use command line calls. Example usage:

    python client.py --url http://127.0.0.1 --light 'swipe 325 821 540 821'

Detailed documentation for the python client can be found in the README of the https://github.com/DeMaCS-UNICAL/tapsterbot-original/tree/master/clients/python folder.

## AI

The AI module takes screenshots from PH and produces swipe coordinates to be sent to the robot arm using the Tappy server. Installation requires a bit of a tweak:

1.  Prepare an anaconda environment with Python 3.6:

            conda create --name=p36 python=3.6

2.  Activate the environment

            conda activate p36

3.  The command `conda install --file=requirements.txt` will likely not work, as some packages are not available from default repositories. I suggest to manually install the packages listed in `requirements.txt` from your default repository, then install separately `mahotas`, `antlr` and `embasp`. I.e., move in the `AI` folder, and:

            conda install --file=requirements.txt
            conda install -c conda-forge mahotas=1.4.11
            conda install -c carta antlr4-python3-runtime=4.7
            pip install EmbASP-7.4.0-py2.py3-none-any.whl

    **EmbASP Info** : The `whl` file for EmbASP 7.4.0 is located under the `AI/src/resources` folder.

4.  Customize the IP and port of ScreenshotServer (which is running on PH and reachable on your <Phone-IP> value) by modifying `AI/examples/main.py`.

## Sample usage

All the modules are currently loosely integrated. You can however test the full stack of the application (ScreenshotServer -> Vision -> Decision making -> Python Client -> Tappy server -> Tapsterbot, this way:

1. Ensure ScreenshotServer and Tappy server are up and running and reachable from your configured IP:Ports.
2. On a first terminal, move to the `AI` folder, and switch to your environment:

   conda activate p36
   export PYTHONPATH=.:$PYTHONPATH

3. On a second terminal, move to the `tapsterbot-original/clients/python` folder and keep the following command running. (**note: the python client invoked from within runstream.pl currently requires Python 2.7 and NOT Python 3**):

   tail -f -n0 ../../../AI/coord.txt | perl runstream.pl

Open the Candy Crush Saga game and start a game on a level of choice. Then run on the first terminal:

      python examples/main.py | tee -a coord.txt

This will take a screenshot, then perform computer vision and decision making on it. You will see the just made decision appear graphically on the screen. After closing the screenshot viewer, some output will appear on terminal and will be piped in the `coord.txt` file. If everything is correct, the runstream.pl script will collect the swipe coordinates from the coord.txt file and execute the actual move with the robot arm.

# Collaborators

- Hardware, Actuation modules: Giovambattista Ianni ([@iannigb](https://github.com/iannigb))
- Screenshotserver, Vision & AI : Mario Avolio ([@MarioAvolio](https://github.com/MarioAvolio))
