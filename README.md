# ops-server-config


Operations Server Configuration scripts

## Features

* Automates the installation of the following software:
  * ArcGIS for Server (Windows) 10.3
  * Portal for ArcGIS (Windows) 10.3
  * ArcGIS Web Adaptor (IIS) 10.3
  * ArcGIS Data Store (Windows) 10.3 
  * ArcGIS GeoEvent Extension for Server (Windows) 10.3
  * Deployment of Operations Dashboard configured for Portal for ArcGIS
  * PostgreSQL 9.2.2
  * IIS and .NET Framework 3.5
* Automates Enterprise Geodatabase creation and registration of these data stores with ArcGIS for Server.
* Contains scripts for:
  * Publishing ArcGIS for Server services from service definition files (.sd).
  * Extracting/publishing Portal for ArcGIS content to/from disk.
  * Working with ArcGIS for Server REST API


## Instructions

## Requirements

Please refer to _Ops Server System Requirements_ and _Installation Prerequisites_ sections of the [Ops Server Installation Guide](https://github.com/ArcGIS/ops-server-config/blob/master/Docs/Ops%20Server%20Installation%20Guide.pdf) for more information.
## Resources

* [Ops Server Installation Guide](https://github.com/ArcGIS/ops-server-config/blob/master/Docs/Ops%20Server%20Installation%20Guide.pdf)
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

A copy of the license is available in the repository's [license.txt](https://github.com/ArcGIS/ops-server-config/blob/master/license.txt) file.

A portion of this code uses a third-party library:

* Use of the [walkingDirTrees.py](https://github.com/ArcGIS/ops-server-config/blob/master/SupportFiles/walkingDirTrees.py) module is governed by the modified Berkeley license available in the repository's [LICENSE-ThirdParty.txt](https://github.com/ArcGIS/ops-server-config/blob/master/LICENSE-ThirdParty.txt) file.
