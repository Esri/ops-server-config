# ops-server-config

The **Operations Server Configuration** is a collection of Python scripts and batch files that automate the installation of 
the ArcGIS platform on Windows machines and the publication of Portal for ArcGIS content and ArcGIS for Server services. 
While developed for an implementation of the ArcGIS Platform with a specific software configuration and content (i.e. _Operations Server_), 
the scripts can be modified to meet your requirements.

The goals of the scripts are to:

* Automate the software installation and configuration process as much as possible.
* Ensure a consistent and repeatable process.
* Reduce the time necessary to install software and deploy content.
* Simplify the complete portal deployment of Esri’s Military and Intelligence solution.

![Image of Ops Server](ScreenShot.png "ops-server-config")

## Features

* Automates the installation of the following software:
  * ArcGIS for Server (Windows) 10.4
  * Portal for ArcGIS (Windows) 10.4
  * ArcGIS Web Adaptor (IIS) 10.4
  * ArcGIS Data Store (Windows) 10.4
  * ArcGIS GeoEvent Extension for Server (Windows) 10.4
  * Portal Resources for Esri Maps for Office 3.1
  * Deployment of Operations Dashboard configured for Portal for ArcGIS
  * PostgreSQL 9.3.5
  * IIS and .NET Framework 3.5
* Automates Enterprise Geodatabase creation and registration of these data stores with ArcGIS for Server.
* Automates the publishing of ArcGIS for Server services from service definition files (.sd).
* Automates the publishing of Portal for ArcGIS content to/from disk files.
* Automates the publishing of hosted services from service definition file items uploaded to Portal for ArcGIS.
* Python module for working with the ArcGIS for Server REST API.

## Sections

* [Requirements](#requirements)
* [Instructions](#instructions)
* [Resources](#resources)
* [Issues](#issues)
* [Contributing](#contributing)
* [Licensing](#licensing)

## Requirements

For requirements, please refer to:
* The **_Install Software Preparation_** section of the [Ops Server Configuration Preparation](./Docs/Ops%20Server%20Config%20Preparation.pdf) document.
* The **_Ops Server System Requirements_** and **_Installation Prerequisites_** sections of the [Ops Server Installation Guide](./Docs/Ops%20Server%20Installation%20Guide.pdf).

## Instructions

1. Follow the instructions in the [Ops Server Configuration Preparation](./Docs/Ops%20Server%20Config%20Preparation.pdf) document.
2. Follow the instructions in the [Ops Server Installation Guide](./Docs/Ops%20Server%20Installation%20Guide.pdf).

## Resources

* [Ops Server Installation Guide](./Docs/Ops%20Server%20Installation%20Guide.pdf)
* While the following guides are not necessary to use the scripts contained in this repo, they are useful for understanding the procedures executed by the scripts:
  * [ArcGIS for Server (Windows) installation guide](http://server.arcgis.com/en/server/latest/install/windows/welcome-to-the-arcgis-for-server-install-guide.htm)
  * [Portal for ArcGIS (Windows) installation guide](http://server.arcgis.com/en/portal/latest/install/windows/welcome-to-the-portal-for-arcgis-installation-guide.htm)
  * [ArcGIS Web Adaptor (IIS) installation guide](http://server.arcgis.com/en/web-adaptor/latest/install/iis/welcome-to-the-arcgis-web-adaptor-installation-guide.htm)
  * [ArcGIS Data Store (Windows) installation guide](http://server.arcgis.com/en/data-store/latest/install/windows/welcome-to-arcgis-data-store-installation-guide.htm)
  * [ArcGIS GeoEvent Extension for Server (Windows) installation steps](http://server.arcgis.com/en/geoevent-extension/latest/install/windows/installation-steps.htm)

## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Licensing
Copyright 2014 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [license.txt](./license.txt) file.

A portion of this code uses a third-party library:

* Use of the [walkingDirTrees.py](./SupportFiles/walkingDirTrees.py) module is governed by the modified Berkeley license available in the repository's [LICENSE-ThirdParty.txt](https://github.com/ArcGIS/ops-server-config/blob/master/LICENSE-ThirdParty.txt) file.

[](Esri Tags: ArcGIS Defense Intelligence Military ArcGISSolutions)
[](Esri Language: Python)
