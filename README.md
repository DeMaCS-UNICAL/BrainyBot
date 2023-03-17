<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/DeMaCS-UNICAL/BrainyBot">
    <img src="images/logo.png" alt="Logo" width="100" height="100">
  </a>

<h3 align="center">BrainyBot</h3>

  <p align="center">
    The BrainyBot project features a full-stack architecture currently capable of solving the Candy Crush Saga and Ball Sort Puzzle video game using a real robotic arm touching a moving screen. Based on the great TapsterBot design from Jason Huggins (https://github.com/tapsterbot/tapsterbot, https://tapster.io/)
    <br />
    <a href="https://github.com/DeMaCS-UNICAL/BrainyBot/tree/main/docs/index.md"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://www.youtube.com/watch?v=pgNjBhVs7_4">View Demo</a>
    ·
    <a href="https://github.com/DeMaCS-UNICAL/BrainyBot/issues">Report Bug</a>
    ·
    <a href="https://github.com/DeMaCS-UNICAL/BrainyBot/issues">Request Feature</a>
  </p>

</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

![operating-workflow]
<!-- ![product-screenshot] -->

In this project, we propose a delta robot capable of
playing match-3 games and ball-sorting puzzles by acting on
mobile phones. The robot recognizes objects of different colors
and shapes through a vision module, is capable of making
strategic decisions based on declarative models of the game’s
rules and of the game playing strategy, and features an effector
that execute moves on physical devices.
Our solution integrates multiple AI methods, including vision
processing and answer set programming. Helpful and
reusable infrastructure is provided: the vision task is facilitated,
while robot motion control is inherently simplified by
the usage of a delta robot layout.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### How it works

The main hardware parts of a BrainyBot are a mobile device PH,
a computer C and the robotic effector E controlled using an Arduino board. 
The figure shows the operating workflow of an instance of
a BrainyBot. Software components are placed respectively on PH or on C, 
which in turn controls all the parts of the system. 
A game G of choice runs on PH. BrainyBot cyclically processes information taken
from PH’s display, then decides and executes arm moves on
the touch display itself. More in detail, in each iteration, the
Sense-Think-Act workflow is executed.

### Built With

- Python
- Java
- Answer Set Programming
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is a list of prerequisites for using the project:
* **PH**: an Android mobile phone. This is the device where the ScreenshotServer application is installed and where the game will be played on.
You can find a pre-built apk for the ScreenshotServer in the ScreenshotServer folder. Just push it to PH, install it and start the server. Take note of the value of PH IP address.
* **TP**: an assembled Tapsterbot. This robotic arm can programmatically perform actions on a given touch screen (taps, swipes, etc.)
* **LI**: a Linux host. The Linux host will host the Tapsterbot server commanding the robot, will collect screenshots from PH and run the AI module.

* npm
  ```sh
  npm install npm@latest -g
  ```


### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/DeMaCS-UNICAL/BrainyBot.git
   ```
2. Pull submodules
   ```sh
   git submodule update --init --recursive
   ```
3. Keep submodules up to date
    ```sh
   git pull --recurse-submodules
   ```
4. Prepare an anaconda environment with Python 3.6:
    ```sh
    conda create --name=p36 python=3.6
   ```
5. Activate the environment
    ```sh
    conda activate p36
   ```
6. The command `conda install --file=requirements.txt` will likely not work, 
as some packages are not available from default repositories. 
We suggest to manually install the packages listed in `requirements.txt` 
from your default repository, 
then install separately `mahotas`, `antlr` and `embasp`, i.e., 
move in the `AI` folder, and:
    ```sh
    conda install --file=requirements.txt
    conda install -c conda-forge mahotas=1.4.11
    conda install -c carta antlr4-python3-runtime=4.7
    pip install EmbASP-7.4.0-py2.py3-none-any.whl
   ```
    
**EmbASP Info** : The `whl` file mentioned above for EmbASP 7.4.0 is located under the `AI/src/resources` folder.
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://github.com/DeMaCS-UNICAL/BrainyBot/tree/main/docs/index.md)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature

See the [open issues](https://github.com/DeMaCS-UNICAL/BrainyBot/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Mario Avolio - [@linkedin](https://www.linkedin.com/in/MarioAvolio/) - marioavolio@protonmail.com

Project Link: [https://github.com/DeMaCS-UNICAL/BrainyBot](https://github.com/DeMaCS-UNICAL/BrainyBot)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/DeMaCS-UNICAL/BrainyBot.svg?style=for-the-badge
[contributors-url]: https://github.com/DeMaCS-UNICAL/BrainyBot/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/DeMaCS-UNICAL/BrainyBot.svg?style=for-the-badge
[forks-url]: https://github.com/DeMaCS-UNICAL/BrainyBot/network/members
[stars-shield]: https://img.shields.io/github/stars/DeMaCS-UNICAL/BrainyBot.svg?style=for-the-badge
[stars-url]: https://github.com/DeMaCS-UNICAL/BrainyBot/stargazers
[issues-shield]: https://img.shields.io/github/issues/DeMaCS-UNICAL/BrainyBot.svg?style=for-the-badge
[issues-url]: https://github.com/DeMaCS-UNICAL/BrainyBot/issues
[license-shield]: https://img.shields.io/github/license/DeMaCS-UNICAL/BrainyBot.svg?style=for-the-badge
[license-url]: https://github.com/DeMaCS-UNICAL/BrainyBot/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/BrainyBot.jpg
[operating-workflow]: images/Sense-Think-Act.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
