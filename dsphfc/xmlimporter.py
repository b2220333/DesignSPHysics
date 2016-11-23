#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DesignSPHysics XML Importer.

This script contains functionality useful for
unpacking an XML file from disk and process it as
a dictionary.

"""

"""
Copyright (C) 2016 - Andrés Vieira (anvieiravazquez@gmail.com)
EPHYSLAB Environmental Physics Laboratory, Universidade de Vigo

This file is part of DesignSPHysics.

DesignSPHysics is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

DesignSPHysics is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with DesignSPHysics.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Andrés Vieira"
__copyright__ = "Copyright 2016, DualSHPysics Team"
__credits__ = ["Andrés Vieira", "Alejandro Jacobo Cabrera Crespo"]
__license__ = "GPL"
__version__ = "v0.1 BETA SNAPSHOT.01"
__maintainer__ = "Andrés Vieira"
__email__ = "anvieiravazquez@gmail.com"
__status__ = "Development"

import FreeCAD
import FreeCADGui
import json
import sys
sys.path.append(FreeCAD.getUserAppDataDir() + "Macro/dsphfc")
import xmltodict
import xml.etree.ElementTree as ET
import utils

def import_xml_file(filename):
    """ Returns data dictionary with values found
        in a GenCase/DSPH compatible XML file and a
       list of objects to add to simulation """
    
    r = dict() #Dictionary to return
    target_file = open(filename, "rb")
    target_xml = target_file.read().replace('\n', '')
    target_file.close()

    #Converts XML in python dictionary
    raw_data = json.loads(json.dumps(xmltodict.parse(target_xml)))

    config = filter_data(raw_data)
    objects = create_fc_objects(target_xml)

    return config, objects

def filter_data(raw):
    """ Filters a raw json representing an XML file to
        a compatible data dictionary. """
    
    fil = dict()

    #Case constants related code
    fil['lattice_bound'] = int(raw['case']['casedef']['constantsdef']['lattice']['@bound'])
    fil['lattice_fluid'] = int(raw['case']['casedef']['constantsdef']['lattice']['@fluid'])
    fil['gravity'] = [float(raw['case']['casedef']['constantsdef']['gravity']['@x']), float(raw['case']['casedef']['constantsdef']['gravity']['@y']), float(raw['case']['casedef']['constantsdef']['gravity']['@z'])]
    fil['rhop0'] = float(raw['case']['casedef']['constantsdef']['rhop0']['@value'])
    fil['hswl'] = float(raw['case']['casedef']['constantsdef']['hswl']['@value'])
    fil['hswl_auto'] = raw['case']['casedef']['constantsdef']['hswl']['@auto'].lower() == "true"
    fil['gamma'] = float(raw['case']['casedef']['constantsdef']['gamma']['@value'])
    fil['speedsystem'] = float(raw['case']['casedef']['constantsdef']['speedsystem']['@value'])
    fil['speedsystem_auto'] = raw['case']['casedef']['constantsdef']['speedsystem']['@auto'].lower() == "true"
    fil['coefsound'] = float(raw['case']['casedef']['constantsdef']['coefsound']['@value'])
    fil['speedsound'] = float(raw['case']['casedef']['constantsdef']['speedsound']['@value'])
    fil['speedsound_auto'] = raw['case']['casedef']['constantsdef']['speedsound']['@auto'].lower() == "true"
    fil['coefh'] = float(raw['case']['casedef']['constantsdef']['coefh']['@value'])
    fil['cflnumber'] = float(raw['case']['casedef']['constantsdef']['cflnumber']['@value'])
    fil['h'] = float(raw['case']['casedef']['constantsdef']['h']['@value'])
    fil['h_auto'] = raw['case']['casedef']['constantsdef']['h']['@auto'].lower() == "true"
    fil['b'] = float(raw['case']['casedef']['constantsdef']['b']['@value'])
    fil['b_auto'] = raw['case']['casedef']['constantsdef']['b']['@auto'].lower() == "true"
    fil['massbound'] = float(raw['case']['casedef']['constantsdef']['massbound']['@value'])
    fil['massbound_auto'] = raw['case']['casedef']['constantsdef']['massbound']['@auto'].lower() == "true"
    fil['massfluid'] = float(raw['case']['casedef']['constantsdef']['massfluid']['@value'])
    fil['massfluid_auto'] = raw['case']['casedef']['constantsdef']['massbound']['@auto'].lower() == "true"
    
    #Getting dp
    fil['dp'] = float(raw['case']['casedef']['geometry']['definition']['@dp'])

    #Execution parameters related code
    execution_parameters = raw['case']['execution']['parameters']['parameter']
    for parameter in execution_parameters:
        if '#' in parameter['@key']:
            fil[parameter['@key'].replace('#', '').lower()] = float(parameter['@value'])
            fil[parameter['@key'].replace('#', '').lower() + "_auto"] = True
        else:
            fil[parameter['@key'].lower()] = float(parameter['@value'])
    
    #Getting project name
    fil['project_name'] = raw['case']['@app']

    #Finding used mkfluids and mkbounds
    fil['mkboundused'] = []
    fil['mkfluidused'] = []
    try:
        mkbounds = raw['case']['casedef']['geometry']['commands']['mainlist']['setmkbound']
        if type(mkbounds) == type(dict()):
            #Only one mkfluid statement
            fil['mkboundused'].append(int(mkbounds['@mk']))
        else:
            #Multiple mkfluids
            for setmkbound in mkbounds:
                fil['mkboundused'].append(int(setmkbound['@mk']))
    except KeyError as e:
        #No mkbounds found
        pass
    try:
        mkfluids = raw['case']['casedef']['geometry']['commands']['mainlist']['setmkfluid']
        if type(mkfluids) == type(dict()):
            #Only one mkfluid statement
            fil['mkfluidused'].append(int(mkfluids['@mk']))
        else:
            #Multiple mkfluids
            for setmkfluid in mkfluids:
                fil['mkfluidused'].append(int(setmkfluid['@mk']))
    except KeyError as e:
        #No mkfluids found
        pass
            
    return fil

def create_fc_objects(f):
    """ Creates supported objects on scene. Iterates over
        <mainlist> items and tries to recreate the commands in
        the current opened scene. """
    #mainlist = f.split("<mainlist>")[1].split("</mainlist>")[0].replace("\t","").replace("\r", "")
    movement = (0.0, 0.0, 0.0)
    rotation = (0.0, 0.0, 0.0, 0.0)
    mk = ("void", "0")
    drawmode = "full"
    elementnum = 0
    toAddDSPH = dict()
    
    root = ET.fromstring(f);
    mainlist = root.findall("./casedef/geometry/commands/mainlist/*")
    for command in mainlist:
        if command.tag == "matrixreset":
            movement = (0.0, 0.0, 0.0)
            rotation = (0.0, 0.0, 0.0, 0.0)
            pass
        elif command.tag == "setmkfluid":
            mk = ("fluid", command.attrib["mk"]) 
            pass
        elif command.tag == "setmkbound":
            mk = ("bound", command.attrib["mk"]) 
            pass
        elif command.tag == "setdrawmode":
            drawmode = command.attrib["mode"]
        elif command.tag == "move":
            movement = (float(command.attrib["x"]) * 1000, float(command.attrib["y"]) * 1000, float(command.attrib["z"]) * 1000)
        elif command.tag == "rotate":
            rotation = (float(command.attrib["ang"]), float(command.attrib["x"]) * 1000, float(command.attrib["y"]) * 1000, float(command.attrib["z"]) * 1000)
        elif command.tag == "drawbox":
            for subcommand in command:
                boxfill = "full"
                point = (0.0, 0.0, 0.0)
                size = (1.0, 1.0, 1.0)
                if subcommand.tag == "boxfill":
                    boxfill = subcommand.text
                elif subcommand.tag == "point":
                    point = (float(subcommand.attrib["x"]) * 1000, float(subcommand.attrib["y"]) * 1000, float(subcommand.attrib["z"]) * 1000)
                elif subcommand.tag == "size":
                    size = (float(subcommand.attrib["x"]) * 1000, float(subcommand.attrib["y"]) * 1000, float(subcommand.attrib["z"]) * 1000)
                else:
                    utils.warning("Modifier unknown ("+subcommand.tag+") for the command: " + command.tag + ". Ignoring...")
            #Box creation in FreeCAD
            FreeCAD.ActiveDocument.addObject("Part::Box","Box" + str(elementnum))
            FreeCAD.ActiveDocument.ActiveObject.Label = "Box" + str(elementnum)
            FreeCAD.ActiveDocument.getObject("Box" + str(elementnum)).Placement = FreeCAD.Placement(FreeCAD.Vector(point[0] + movement[0], point[1] + movement[1], point[2] + movement[2]),FreeCAD.Rotation(FreeCAD.Vector(rotation[1], rotation[2], rotation[3]), rotation[0]))
            FreeCAD.ActiveDocument.getObject("Box" + str(elementnum)).Length = str(size[0]) + ' mm'
            FreeCAD.ActiveDocument.getObject("Box" + str(elementnum)).Width = str(size[1]) + ' mm'
            FreeCAD.ActiveDocument.getObject("Box" + str(elementnum)).Height = str(size[2]) + ' mm'
            #Suscribe Box for creation in DSPH Objects
            #Structure: [name] = [mknumber, type, fill]
            toAddDSPH["Box" + str(elementnum)] = [mk[1], mk[0], drawmode]
        else:
            #Command not supported, report and ignore
            utils.warning("The command: " + command.tag + " is not yet supported. Ignoring...")
        
        elementnum += 1

    FreeCAD.ActiveDocument.recompute()
    FreeCADGui.SendMsgToActiveView("ViewFit")
    return toAddDSPH